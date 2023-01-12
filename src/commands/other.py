import difflib
import io
import time
import typing

import discord
import docstring_parser
import regex as re
from discord.ext import commands

import config
import core.v2queue
import processing.common
import processing.ffmpeg
import processing.ffprobe
import utils.discordmisc
from core import database
from core.process import process
from utils.common import prefix_function
from utils.dpy import UnicodeEmojiConverter, showcog
from utils.dpy import add_long_field
from utils.scandiscord import imagesearch
from utils.web import saveurls
import utils.tempfiles


class Other(commands.Cog, name="Outros"):
    """
    Comandos que não se enquadram nas outras categorias.
    """

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.cooldown(60, config.cooldown, commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.hybrid_command(aliases=["pfx", "setprefix", "changeprefix", "botprefix", "commandprefix"])
    async def prefix(self, ctx, prefix=None):
        """
        Changes the bot's prefix for this guild.

        :param ctx: discord context
        :param prefix: The new prefix for the bot to use.
        """
        if prefix is None or prefix == config.default_command_prefix:
            await database.db.execute("DELETE FROM guild_prefixes WHERE guild=?", (ctx.guild.id,))
            await database.db.commit()
            await ctx.reply(f"{config.emojis['check']} Defina o prefixo do servidor de volta ao padrão global "
                            f"(`{config.default_command_prefix}`).")

        else:
            if not 50 >= len(prefix) > 0:
                raise commands.BadArgument(f"prefixo deve ter entre 1 e 50 caracteres.")
            # check for invalid characters by returning all invalid characters
            invalids = re.findall(r"[^a-zA-Z0-9!$%^&()_\-=+,<.>\/?;'[{\]}|]", prefix)
            if invalids:
                raise commands.BadArgument(f"{config.emojis['x']} Caracteres inválidos encontrados: "
                                           f"{', '.join([discord.utils.escape_markdown(i) for i in invalids])}")
            else:
                await database.db.execute("REPLACE INTO guild_prefixes(guild, prefix) VALUES (?,?)",
                                          (ctx.guild.id, prefix))
                await database.db.commit()
                await ctx.reply(f"{config.emojis['check']} Defina o prefixo do servidor para `{prefix}`")
                if prefix.isalpha():  # only alphabetic characters
                    await ctx.reply(f"{config.emojis['warning']} Your prefix only contains alphabetic characters. "
                                    f"Isso pode fazer com que frases/palavras normais sejam interpretadas como comandos. "
                                    f"Isso pode incomodar os usuários.")

    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_guild_permissions(manage_emojis=True)
    @commands.hybrid_command(aliases=["createemoji"])
    async def addemoji(self, ctx, name):
        """
        Adiciona um arquivo como emoji a um servidor.

        Tanto o Ezgif quanto o chamador do comando devem ter a permissão Gerenciar Emojis.

        :param ctx: discord context
        :param name: The emoji name. Must be at least 2 characters.
        :mediaparam media: Um gif ou imagem.
        """
        await process(ctx, utils.discordmisc.add_emoji, [["GIF", "IMAGE"]], ctx.guild, name, expectimage=False,
                      resize=False)

    # TODO: fix?
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_guild_permissions(manage_emojis=True)
    @commands.hybrid_command(aliases=["createsticker"])
    async def addsticker(self, ctx, stickeremoji: UnicodeEmojiConverter, *, name: str):
        """
        Adds a file as a sticker to a server.

        Tanto o Ezgif quanto o chamador do comando devem ter a permissão Gerenciar Emojis e Adesivos.

        :param ctx: discord context
        :param stickeremoji: O emoji relacionado. Deve ser um único emoji padrão.
        :param name: O nome do adesivo. Deve ter pelo menos 2 caracteres.
        :mediaparam media: Um gif ou imagem.
        """
        await process(ctx, utils.discordmisc.add_sticker, [["GIF", "IMAGE"]], ctx.guild, stickeremoji, name,
                      expectimage=False, resize=False)

    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_guild=True)
    @commands.hybrid_command(aliases=["guildatabase.dbanner", "serverbanner", "banner"])
    async def setbanner(self, ctx):
        """
        Define um arquivo como o banner do servidor.
        O servidor deve suportar banners.

        :param ctx: discord context
        :mediaparam media: Uma imagem.
        """
        if "BANNER" not in ctx.guild.features:
            await ctx.reply(f"{config.emojis['x']} Esta guilda não suporta banners.")
            return
        await process(ctx, utils.discordmisc.set_banner, [["IMAGE"]], ctx.guild, expectimage=False,
                      resize=False)

    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_guild=True)
    @commands.hybrid_command(aliases=["setguildicon", "guildicon", "servericon", "seticon"])
    async def setservericon(self, ctx):
        """
        Define um arquivo como o ícone do servidor.
        Se definir um gif, o servidor deve suportar ícones animados.

        :param ctx: discord context
        :mediaparam media: Uma imagem ou gif.
        """
        await process(ctx, utils.discordmisc.set_icon, [["IMAGE", "GIF"]], ctx.guild, expectimage=False,
                      resize=False)

    @commands.hybrid_command(aliases=["statistics"])
    async def stats(self, ctx):
        """
        Exibe algumas estatísticas sobre o que o bot está fazendo no momento.

        :param ctx: discord context
        """
        embed = discord.Embed(color=discord.Color(0xe74c3c), title="Statistics")
        embed.add_field(name="Tarefas na fila", value=f"{core.v2queue.queued}")
        embed.add_field(name="Número de tarefas que esta instância pode executar de uma só vez", value=f"{core.v2queue.workers}")
        if isinstance(self.bot, discord.AutoShardedClient):
            embed.add_field(name="Total de fragmentos de bot", value=f"{len(self.bot.shards)}")
        await ctx.reply(embed=embed)

    @commands.hybrid_command(aliases=["shard", "shardstats", "shardinfo"])
    async def shards(self, ctx):
        """
        Exibe informações sobre fragmentos de bot

        :param ctx: discord context
        """
        embed = discord.Embed(color=discord.Color(0xe74c3c), title="Shards",
                              description="Cada fragmento é uma conexão separada com o Discord que lida com uma fração "
                                          "de todos os servidores em que o Ezgif está.")
        for i, shard in self.bot.shards.items():
            shard: discord.ShardInfo
            embed.add_field(name=f"Shard #{shard.id}", value=f"{round(shard.latency * 1000)}ms latency")
        await ctx.reply(embed=embed)

    @commands.hybrid_command(aliases=["discord", "invite", "botinfo"])
    async def about(self, ctx):
        """
        Lista links importantes relacionados ao MediaForge, como o servidor oficial.

        :param ctx: discord context
        """
        embed = discord.Embed(color=discord.Color(0xe74c3c), title="Ezgif")
        embed.add_field(name="O servidor de discord oficial do MediaForge", value=f"https://discord.gg/xwWjgyVqBz")
        embed.add_field(name="top.gg link", value=f"https://top.gg/bot/780570413767983122")
        embed.add_field(name="Vote no Ezgif em top.gg", value=f"https://top.gg/bot/780570413767983122/vote")
        embed.add_field(name="Adicione o Ezgif ao seu servidor",
                        value=f"https://discord.com/api/oauth2/authorize?client_id=780570413767983122&permissions=3"
                              f"79968&scope=bot")
        embed.add_field(name="Ezgif GitHub", value=f"https://github.com/Tzrico/ezgif")
        await ctx.reply(embed=embed)

    @commands.hybrid_command(aliases=["privacypolicy"])
    async def privacy(self, ctx):
        """
        Mostra a política de privacidade do Ezgif

        :param ctx: discord context
        """
        embed = discord.Embed(color=discord.Color(0xe74c3c), title="Política de Privacidade")
        embed.add_field(name="O que o MediaForge coleta",
                        value=f"MediaForge has a sqlite database with the **sole purpose** of storing "
                              f"guild-specific prefixos de comando. **Todos** os outros dados são *sempre* excluídos quando são "
                              f"feito com. Ezgif exibe informações limitadas "
                              f"sobre comandos sendo executados no console da máquina host para fins de depuração."
                              f" Esses dados também não são armazenados.")
        embed.add_field(name="Contato sobre dados", value=f"Realmente não há nada para entrar em contato comigo desde "
                                                         f"O Ezgif não possui nenhuma forma de dados de longo prazo "
                                                         f"armazenamento, mas você pode entrar no discord do Ezgif "
                                                         f"server (https://discord.gg/QhMyz3n4V7) ou levantar um "
                                                         f"problema no GitHub ("
                                                         f"https://github.com/Tzrico/ezgif).")
        await ctx.reply(embed=embed)

    @commands.hybrid_command(aliases=["github", "git"])
    async def version(self, ctx):
        """
        Mostra informações sobre como esta cópia do Ezgif se compara ao código mais recente no github.
        https://github.com/Tzrico/ezgif
        Este comando retorna a saída de `git status`.

        :param ctx: discord context
        """
        await processing.common.run_command("git", "fetch")
        status = await processing.common.run_command("git", "status")
        with io.StringIO() as buf:
            buf.write(status)
            buf.seek(0)
            await ctx.reply("Saída do `git status` (as diferenças entre esta cópia do Ezgif e o último"
                            " código no GitHub)", file=discord.File(buf, filename="gitstatus.txt"))

    @commands.hybrid_command(aliases=["ffmpeginfo"])
    async def ffmpegversion(self, ctx):
        """
        Mostra informações da versão do FFmpeg em execução nesta cópia.
        Este comando retorna a saída de `ffmpeg -version`.

        :param ctx: discord context
        """
        status = await processing.common.run_command("ffmpeg", "-version")
        with io.StringIO() as buf:
            buf.write(status)
            buf.seek(0)
            await ctx.reply("Saída de `ffmpeg -version`", file=discord.File(buf, filename="ffmpegversion.txt"))

    @commands.hybrid_command()
    async def ajuda(self, ctx, *, inquiry: typing.Optional[str] = None):
        """
        Mostra a ajuda nos comandos do bot.

        :param ctx: discord context
        :param inquiry: o nome de um comando ou categoria de comando. Se nenhum for fornecido, todas as categorias serão mostradas.
        :return: o texto de ajuda se encontrado
        """
        prefix = await prefix_function(self.bot, ctx.message, True)
        # unspecified inquiry
        if inquiry is None:
            embed = discord.Embed(title="<a:ezfogo:1059267224235413544> ajuda", color=discord.Color(0xe74c3c),
                                  description=f"Execute `{prefix}ajuda <categoria>` para listar comandos de "
                                              f"uma categoria.")
            # for every cog
            for c in self.bot.cogs.values():
                # if there is 1 or more non-hidden command
                if showcog(c):
                    # add field for every cog
                    if not c.description:
                        c.description = "Sem descrição."
                    embed.add_field(name=c.qualified_name, value=c.description)
            await ctx.reply(embed=embed)
        # if the command argument matches the name of any of the cogs that contain any not hidden commands
        elif inquiry.lower() in (coglist := {k.lower(): v for k, v in self.bot.cogs.items() if showcog(v)}):
            # get the cog found
            cog = coglist[inquiry.lower()]
            embed = discord.Embed(title=cog.qualified_name,
                                  description=cog.description + f"\nExecute `{prefix}ajuda comando` para "
                                                                f"mais informações sobre um comando.",
                                  color=discord.Color(0xe74c3c))
            # add field with description for every command in the cog
            for cmd in sorted(cog.get_commands(), key=lambda x: x.name):
                if not cmd.hidden:
                    desc = cmd.short_doc if cmd.short_doc else "sem descrição."
                    embed.add_field(name=f"{prefix}{cmd.name}", value=desc)
            await ctx.reply(embed=embed)
        else:
            # for every bot command
            for bot_cmd in self.bot.commands:
                # if the name matches inquiry or alias and is not hidden
                if (bot_cmd.name == inquiry.lower() or inquiry.lower() in bot_cmd.aliases) and not bot_cmd.hidden:
                    # set cmd and continue
                    cmd: discord.ext.commands.Command = bot_cmd
                    break
            else:
                # inquiry doesnt match cog or command, not found

                # get all cogs n commands n aliases
                allcmds = []
                for c in self.bot.cogs.values():
                    if showcog(c):
                        allcmds.append(c.qualified_name.lower())
                for cmd in self.bot.commands:
                    if not cmd.hidden:
                        allcmds.append(cmd.qualified_name)
                        allcmds += cmd.aliases
                match = difflib.get_close_matches(inquiry, allcmds, n=1, cutoff=0)[0]
                raise commands.BadArgument(
                    f"`{inquiry}` não é o nome de um comando ou uma categoria de comando. "
                    f"Você quis dizer `{match}`?")
                # past this assume cmd is defined
            embed = discord.Embed(title=prefix + cmd.name, description=cmd.cog_name,
                                  color=discord.Color(0xe74c3c))
            # if command func has docstring
            if cmd.ajuda:
                # parse it
                docstring = docstring_parser.parse(cmd.ajuda, style=docstring_parser.DocstringStyle.REST)
                # format short/long descriptions or say if there is none.
                if docstring.short_description or docstring.long_description:
                    command_information = \
                        f"{f'**{docstring.short_description}**' if docstring.short_description else ''}" \
                        f"\n{docstring.long_description if docstring.long_description else ''}"
                else:
                    command_information = "Este comando não tem informações."
                embed = add_long_field(embed, "Informação de comando", command_information)

                paramtext = []
                # for every "clean paramater" (no self or ctx)
                for param in list(cmd.clean_params.values()):
                    # get command description from docstring
                    paramajuda = discord.utils.get(docstring.params, arg_name=param.name)
                    # not found in docstring
                    if paramajuda is None:
                        paramtext.append(f"**{param.name}** - sem descrição")
                        continue
                    # optional argument (param has a default value)
                    if param.default != param.empty:  # param.empty != None
                        pend = f" (opcional, o padrão é `{param.default}`)"
                    else:
                        pend = ""
                    # format and add to paramtext list
                    paramajuda.description = paramajuda.description.replace('\n', ' ')
                    paramtext.append(f"**{param.name}** - "
                                     f"{paramajuda.description if paramajuda.description else 'sem descrição'}"
                                     f"{pend}")
                mediaparamtext = []
                for mediaparam in re.finditer(re.compile(":mediaparam ([^ :]+): ([^\n]+)"), cmd.ajuda):
                    argname = mediaparam[1]
                    argdesc = mediaparam[2]
                    mediaparamtext.append(f"**{argname}** - {argdesc}")
                # if there are params found
                if len(paramtext):
                    # entrar na lista e adicionar para ajudar
                    embed = add_long_field(embed, "Parameters", "\n".join(paramtext))
                if len(mediaparamtext):
                    mval = "*Os parâmetros de mídia são coletados automaticamente do canal.*\n" + \
                           "\n".join(mediaparamtext)
                    embed = add_long_field(embed, "Parâmetros de mídia", mval)
                if docstring.returns:
                    embed.add_field(name="Returns", value=docstring.returns.description, inline=False)
            else:
                # if no docstring
                embed.add_field(name="Informações do Comando", value="Este comando não possui informações.", inline=False)
            # cmd.signature is a human readable list of args formatted like the manual usage
            embed.add_field(name="Use", value=prefix + cmd.name + " " + cmd.signature)
            # if aliases, add
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join([prefix + a for a in cmd.aliases]))

            await ctx.reply(embed=embed)

    @commands.hybrid_command(aliases=["ffprobe"])
    async def info(self, ctx):
        """
        Fornece informações sobre um arquivo de mídia.
        As informações fornecidas são de ffprobe e libmagic.

        :param ctx: discord context
        :mediaparam media: Qualquer arquivo de mídia.
        """
        async with utils.tempfiles.TempFileSession():
            file = await imagesearch(ctx, 1)
            if file:
                file = await saveurls(file)
                result = await processing.ffprobe.ffprobe(file[0])
                await ctx.reply(f"`{result[1]}` `{result[2]}`\n```{result[0]}```")
                # os.remove(file[0])
            else:
                await ctx.send(f"{config.emojis['x']} Nenhum arquivo encontrado.")

    @commands.hybrid_command()
    async def feedback(self, ctx):
        """
        Forneça feedatabase.dback para o bot.
        Isso envia vários links do repositório github para relatar problemas ou fazer perguntas.

        :param ctx: discord context
        """
        embed = discord.Embed(title="Feedback",
                              description="Feedatabase.dback é melhor fornecido por meio do repositório GitHub, vários "
                                          "links são fornecidos abaixo.",
                              color=discord.Color(0xe74c3c))
        embed.add_field(name="Reportar um erro",
                        value="Para relatar um bug, crie um problema em\nhttps://github.com/Tzrico/ezgif/issues",
                        inline=False)
        embed.add_field(name="Faça uma pergunta", value="Ter uma questão? Use a discussão de perguntas e respostas "
                                                     "Página.\nhttps://github.com/Tzrico/ezgif/discussions/c"
                                                     "ategories/q-a", inline=False)
        embed.add_field(name="Dê uma ideia",
                        value="Tem uma ideia ou sugestão? Use a página de discussão de ideias.\nhtt"
                              "ps://github.com/Tzrico/ezgif/discussions/categories/id"
                              "eas", inline=False)
        embed.add_field(name="Algo mais?",
                        value="Qualquer coisa é bem-vinda na página de discussão!\nhttps://github."
                              "com/Tzrico/ezgif/discussions", inline=False)
        embed.add_field(name="Por que o GitHub?",
                        value="Usar o GitHub para feedback torna muito mais fácil organizar qualquer i"
                              "ssues e implementá-los no código do bot.")
        await ctx.reply(embed=embed)

    @commands.hybrid_command()
    async def attributions(self, ctx):
        """
        Lista a maioria das bibliotecas e programas que este bot usa.

        :param ctx: discord context
        """
        with open("media/active/attributions.txt", "r") as f:
            await ctx.send(f.read())

    @commands.hybrid_command(aliases=["pong"])
    async def ping(self, ctx):
        """
        Pong!

        :param ctx: discord context
        :return: Latência de API e websocket
        """
        start = time.perf_counter()
        message = await ctx.send("Ping...")
        end = time.perf_counter()
        duration = (end - start) * 1000
        await message.edit(content=f'🏓 Pong!\n'
                                   f'Latência da API: `{round(duration)}ms`\n'
                                   f'Latência do Websocket: `{round(self.bot.latency * 1000)}ms`')
