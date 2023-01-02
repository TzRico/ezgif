import asyncio
import typing

import aiohttp
import discord
import emojis
import regex as re
import yt_dlp as youtube_dl
from discord.ext import commands

import config
import processing.ffmpeg
import processing.ffprobe
import utils.discordmisc
import utils.web
from core.clogs import logger
from core.process import process
from processing.common import run_parallel
from processing.other import ytdownload
from utils.common import prefix_function
from utils.dpy import UnicodeEmojisConverter
from utils.scandiscord import tenorsearch
from utils.tempfiles import reserve_tempfile


class Conversion(commands.Cog, name="Conversão"):
    """
    Comandos para converter tipos de mídia e baixar mídia hospedada na Internet.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["filename", "nome", "setname"])
    async def rename(self, ctx, filename: str):
        """
        Renomeia a mídia.
        Observação: o recurso de spoiler do Discord depende de nomes de arquivos que começam com "SPOILER_". renomear arquivos pode
        desembalá-los.

        :param ctx: contexto de discórdia
        :param filename: o novo nome do arquivo
        :mediaparam mídia: qualquer mídia válida.
        """
        file = await process(ctx, lambda x: x, [["VIDEO", "GIF", "IMAGE", "AUDIO"]])
        await ctx.reply(file=discord.File(file, filename=filename))

    @commands.hybrid_command(aliases=["spoil", "censor", "cw", "tw"])
    async def spoiler(self, ctx):
        """
        Mídia de spoilers.

        :param ctx: contexto de discórdia
        :mediaparam mídia: qualquer mídia válida.
        """
        file = await process(ctx, lambda x: x, [["VIDEO", "GIF", "IMAGE", "AUDIO"]])
        await ctx.reply(file=discord.File(file, spoiler=True))

    @commands.hybrid_command(aliases=["avatar", "pfp", "Fotodoperfil", "profilepic", "ayowhothismf", "av"])
    async def icon(self, ctx, *, body=None):
        """
        Pega o URL do ícone de um usuário ou servidor do Discord.

        Este comando funciona com IDs. as menções do usuário contêm o ID
        internamente, portanto, mencionar um usuário funcionará. Para obter o ícone de um servidor, copie o ID do servidor e use-o como
        o parâmetro. Para obter o ícone de uma mensagem de webhook, copie o ID da mensagem e ***no mesmo canal que
        a mensagem*** usa o ID da mensagem como parâmetro. Isso também funcionará para usuários normais, embora eu não tenha
        idéia de por que você faria dessa maneira.


        :param ctx: contexto de discórdia
        :param body: deve conter um ID de usuário, guilda ou mensagem. se deixado em branco, será enviado o avatar do autor.
        """
        if body is None:
            result = [await utils.discordmisc.iconfromsnowflakeid(ctx.author.id, self.bot, ctx)]
        else:
            id_regex = re.compile(r'([0-9]{15,20})')
            tasks = []
            for m in re.finditer(id_regex, body):
                tasks.append(utils.discordmisc.iconfromsnowflakeid(int(m.group(0)), self.bot, ctx))
            result = await asyncio.gather(*tasks)
            result = list(filter(None, result))  # remover nenhum
        if result:
            await ctx.reply("\n".join(result)[0:2000])
        else:
            await ctx.send(f"{config.emojis['warning']} Nenhum usuário, servidor ou ID de mensagem válido encontrado.")

    @commands.hybrid_command(
        aliases=["youtube", "youtubebaixar", "youtubedl", "ytbaixar", "baixar", "dl", "ytdl"])
    async def videodl(self, ctx, videourl, videoformat: typing.Literal["video", "audio"] = "video"):
        """
        Baixa um vídeo hospedado na web de sites como o youtube.
        Qualquer site aqui funciona: https://ytdl-org.github.io/youtube-dl/supportedsites.html

        :param ctx: contexto de discórdia
        :param videourl: o URL de um vídeo ou o título de um vídeo do youtube.
        :param videoformat: baixar áudio ou vídeo.
        """
        msg = await ctx.reply(f"{config.emojis['working']} Baixando do site...", mention_author=False)
        try:
            async with utils.tempfiles.TempFileSession():
                r = await run_parallel(ytdownload, videourl, videoformat)
                if r:
                    r = await processing.ffmpeg.assurefilesize(r, re_encode=False)
                    if not r:
                        return
                    txt = ""
                    vcodec = await processing.ffprobe.get_vcodec(r)
                    acodec = await processing.ffprobe.get_acodec(r)
                    # sometimes returns av1 codec
                    if vcodec and vcodec["codec_name"] not in ["h264", "gif", "webp", "png", "jpeg"]:
                        txt += f"O vídeo retornado está no `{vcodec['codec_name']}` " \
                               f"({vcodec['codec_long_name']}) codec. O Discord pode não conseguir incorporar isso " \
                               f"formato. Você pode usar " \
                               f"`{await prefix_function(self.bot, ctx.message, True)}reencode` para mudar o codec, " \
                               f"embora isso possa aumentar o tamanho do arquivo ou diminuir a qualidade.\n"
                    if acodec and acodec["codec_name"] not in ["aac", "mp3"]:
                        txt += f"O áudio do vídeo retornado está no `{vcodec['codec_name']}` " \
                               f"({vcodec['codec_long_name']}) codec. Alguns dispositivos não podem reproduzir isso. " \
                               f"Você pode usar `{await prefix_function(self.bot, ctx.message, True)}reencode` " \
                               f"para mudar o codec, " \
                               f"embora isso possa aumentar o tamanho do arquivo ou diminuir a qualidade."
                    await msg.edit(content=f"{config.emojis['working']} Carregando no Discord...")
                    await ctx.reply(txt, file=discord.File(r))
                else:
                    await ctx.reply(f"{config.emojis['warning']} Nenhum download disponível encontrado no Discord "
                                    f"limite de upload de arquivo.")
                # os.remove(r)
                await msg.delete()
        except youtube_dl.DownloadError as e:
            await ctx.reply(f"{config.emojis['2exclamation']} {e}")

    @commands.hybrid_command(aliases=["gif", "videoparagif"])
    async def togif(self, ctx):
        """
        Converte um vídeo em um GIF.

        :param ctx: contexto de discórdia
        :mediaparam vídeo: Um vídeo.
        """
        await process(ctx, processing.ffmpeg.mp4togif, [["VIDEO"]])

    @commands.hybrid_command(aliases=["apng", "videoparapng", "gifparapng"])
    async def toapng(self, ctx):
        """
        Converte um vídeo ou gif em um png animado.

        :param ctx: contexto de discórdia
        :mediaparam video: Um vídeo ou gif.
        """
        await process(ctx, processing.ffmpeg.toapng, [["VIDEO", "GIF"]], resize=False)

    @commands.hybrid_command(aliases=["audio", "mp3", "paramp3", "aac", "paraaac"])
    async def toaudio(self, ctx):
        """
        Converte um vídeo em apenas áudio.

        :param ctx: contexto de discórdia
        :mediaparam video: Um vídeo.
        """
        await process(ctx, processing.ffmpeg.toaudio, [["VIDEO", "AUDIO"]])

    @commands.hybrid_command(aliases=["tenorgif", "tenormp4", "rawtenor"])
    async def tenorurl(self, ctx, gif: bool = True):
        """
        Envia o URL bruto para um gif tenor.
        a compactação mp4 é quase invisível em comparação com a compactação GIF, que é muito visível

        :param gif: se verdadeiro, envia url GIF. se falso, envia url mp4.
        :param ctx: contexto de discórdia
        :mediaparam gif: qualquer gif enviado pelo tenor.
        """
        file = await tenorsearch(ctx, gif)
        if file:
            await ctx.send(file)
        else:
            await ctx.send(f"{config.emojis['x']} Nenhum gif de tenor encontrado.")

    @commands.hybrid_command(aliases=["video", "gifparavideo", "paramp4", "mp4"])
    async def tovideo(self, ctx):
        """
        Converte um GIF em um vídeo.

        :param ctx: discord context
        :mediaparam gif: para gif.
        """
        await process(ctx, processing.ffmpeg.giftomp4, [["GIF"]])

    @commands.hybrid_command(aliases=["png", "mediatopng"])
    async def topng(self, ctx):
        """
        Converte mídia para PNG

        :param ctx: contexto de discórdia
        :mediaparam media: Um vídeo, gif ou imagem.
        """
        await process(ctx, processing.ffmpeg.mediatopng, [["VIDEO", "GIF", "IMAGE"]])

    @commands.command(aliases=["emoji", "emojiimage", "emote", "emoteurl"])  # TODO: hybrid
    async def emojiurl(self, ctx, *custom_emojis: discord.PartialEmoji):
        """
        Envia a imagem bruta para um emoji personalizado do Discord.
        Cada emoji é enviado como uma mensagem separada intencionalmente para permitir a resposta com um comando de mídia.

        :param ctx: contexto de discórdia
        :param custom_emojis: Emojis personalizados para enviar a URL. Certifique-se de deixar um espaço entre eles.
        """
        if emojis:
            out = []
            for emoji in custom_emojis[:5]:
                if emoji.is_custom_emoji():
                    out.append(str(emoji.url))
            await ctx.send("\n".join(out))
        else:
            raise commands.BadArgument(f"Sua mensagem não contém emojis personalizados!")

    @commands.hybrid_command()
    async def twemoji(self, ctx: commands.Context, *, twemojis: UnicodeEmojisConverter):
        """
        Envia a imagem twemoji para um emoji.
        Twemoji é o conjunto de emojis de código aberto que a área de trabalho do Discord e o Twitter usam. https://twemoji.twitter.com/

        :param ctx: contexto de discórdia
        :param twemojis: Até 5 emojis discórdia/unicode padrão
        """
        if ctx.message.reference:
            msg = ctx.message.reference.resolved.content
        urls = []
        if twemojis:
            for emoj in twemojis[:5]:
                chars = []
                for char in emoj:
                    chars.append(f"{ord(char):x}")  # get hex code of char
                chars = "-".join(chars).replace("/", "")
                urls.append(f"https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/{chars}.png")
        else:
            raise commands.BadArgument(f"Nenhum emoji padrão encontrado!")

        async def upload_url(url: str):
            try:
                await ctx.reply(file=discord.File(await utils.web.saveurl(url)))
            except aiohttp.ClientResponseError as e:
                await ctx.reply(f"Falha ao carregar {url}: Código {e.status}: {e.message}")

        if urls:
            await asyncio.gather(*[upload_url(url) for url in urls])
