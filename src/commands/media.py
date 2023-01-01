import typing

import discord
from discord import app_commands
from discord.ext import commands

import config
import processing.ffmpeg
from core.process import process
from utils.common import prefix_function
import processing.vips.other
import processing.other


class Media(commands.Cog, name="<:setared:1059251849791803443>Edição"):
    """
    Comandos básicos de edição/processamento de mídia.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["copy", "nothing", "noop"])
    async def repost(self, ctx):
        """
        Repassa a mídia como está.

        :param ctx: contexto de discord
        :mediaparam media: Qualquer mídia válida.
        """
        await process(ctx, lambda x: x, [["VIDEO", "GIF", "IMAGE", "AUDIO"]])

    @commands.hybrid_command(aliases=["clean", "remake"])
    async def reencode(self, ctx):
        """
        Recodifica a mídia.
        Os vídeos se tornam libx264 mp4s, os arquivos de áudio se tornam libmp3lame mp3s, as imagens se tornam pngs.

        :param ctx: contexto de discord
        :mediaparam media: Um arquivo de vídeo, imagem ou áudio.
        """
        await process(ctx, processing.ffmpeg.allreencode, [["VIDEO", "IMAGE", "AUDIO"]])

    @commands.hybrid_command(aliases=["audioadd", "dub"])
    async def addaudio(self, ctx, loops: commands.Range[int, -1, 100] = -1):
        """
        Adiciona áudio à mídia.

        :param ctx: contexto de discord
        :param loops: Quantidade de vezes para repetir um gif. -1 loops infinitamente, 0 apenas uma vez. Deve estar entre -1 e 100.
        :mediaparam media: Qualquer arquivo de mídia válido.
        :mediaparam audio: Um arquivo de áudio.
        """
        await process(ctx, processing.ffmpeg.addaudio, [["IMAGE", "GIF", "VIDEO", "AUDIO"], ["AUDIO"]], loops)

    @commands.hybrid_command()
    async def jpeg(self, ctx, strength: commands.Range[int, 1, 100] = 30,
                   stretch: commands.Range[int, 0, 40] = 20,
                   quality: commands.Range[int, 1, 95] = 10):
        """
        Transforma a mídia em um jpeg de baixa qualidade

        :param ctx: contexto de discord
        :param strength: quantidade de vezes para jpegify imagem. deve estar entre 1 e 100.
        :param stretch: estique aleatoriamente a imagem por esse número em cada jpegificação. pode causar efeitos estranhos
        em vídeos. deve estar entre 0 e 40.
        :param quality: qualidade da compressão JPEG. deve estar entre 1 e 95.
        :mediaparam media: Uma imagem.
        """
        await process(ctx, processing.vips.other.jpeg, [["IMAGE"]], strength, stretch, quality, run_parallel=True)

    @commands.hybrid_command()
    async def deepfry(self, ctx, brightness: commands.Range[float, -1, 1] = 0.5,
                      contrast: commands.Range[float, 0, 5] = 1.5,
                      sharpness: commands.Range[float, 0, 5] = 1.5,
                      saturation: commands.Range[float, 0, 3] = 1.5,
                      noise: commands.Range[float, 0, 100] = 20):
        """
        Aplica muitos filtros à entrada para fazê-la parecer "frita" no estilo de memes fritos.


        :param ctx: contexto de discord
        :param brightness: valor de 0 não faz nenhuma alteração na imagem. deve estar entre -1 e 1.
        :param contrast: valor de 1 não faz nenhuma alteração na imagem. deve estar entre 0 e 5.
        :param sharpness: valor de 0 não faz nenhuma alteração na imagem. deve estar entre 0 e 5.
        :param saturation: valor de 1 não faz nenhuma alteração na imagem. deve estar entre 0 e 3.
        :param noise: valor de 0 não faz nenhuma alteração na imagem. deve estar entre 0 e 100.
        :mediaparam media: um vídeo, gif ou imagem.
        """
        await process(ctx, processing.ffmpeg.deepfry, [["VIDEO", "GIF", "IMAGE"]], brightness, contrast, sharpness,
                      saturation, noise)

    @commands.hybrid_command(aliases=["pad"])
    async def square(self, ctx):
        """
        Preenche a mídia em um formato quadrado.

        :param ctx: contexto de discord
        :mediaparam media: Um vídeo, gif ou imagem.
        """
        await process(ctx, processing.ffmpeg.pad, [["VIDEO", "GIF", "IMAGE"]])

    @commands.hybrid_command(aliases=["size"])
    async def resize(self, ctx, width: int, height: int):
        """
        Redimensiona uma imagem.

        :param ctx: contexto de discord
        :param width: largura da imagem de saída. defina como -1 para determinar automaticamente com base na altura e proporção.
        :param height: altura da imagem de saída. também pode ser definido como -1.
        :mediaparam media: Um vídeo, gif ou imagem.
        """
        if not (1 <= width <= config.max_size or width == -1):
            raise commands.BadArgument(f"A largura deve estar entre 1 e "
                                       f"{config.max_size} ou ser -1.")
        if not (1 <= height <= config.max_size or height == -1):
            raise commands.BadArgument(f"A altura deve estar entre 1 e "
                                       f"{config.max_size} ou ser -1.")
        await process(ctx, processing.ffmpeg.resize, [["VIDEO", "GIF", "IMAGE"]], width, height, resize=False)

    @commands.hybrid_command(aliases=["short", "kyle"])
    async def wide(self, ctx):
        """
        torna a mídia duas vezes mais larga

        :param ctx: contexto de discord
        :mediaparam media: Um vídeo, gif ou imagem.
        """
        await process(ctx, processing.ffmpeg.resize, [["VIDEO", "GIF", "IMAGE"]], "iw*2", "ih")

    @commands.hybrid_command(aliases=["tall", "long", "antikyle"])
    async def squish(self, ctx):
        """
        torna a mídia duas vezes mais alta


        """
        await process(ctx, processing.ffmpeg.resize, [["VIDEO", "GIF", "IMAGE"]], "iw", "ih*2")

    @commands.hybrid_command(aliases=["magic", "magik", "contentawarescale", "liquidrescale"])
    async def magick(self, ctx, strength: commands.Range[int, 1, 99] = 50):
        """
        Aplique a escala de reconhecimento de líquido/conteúdo do imagemagick a uma imagem.
        Este comando é um pouco lento.
        https://legacy.imagemagick.org/Usage/resize/#liquid-rescale

        :param ctx: contexto de discord
        :param strength: quão forte para comprimir a imagem. menor é mais forte. imagem de saída será força% de
        o tamanho original. deve estar entre 1 e 99.
        :mediaparam media: Uma imagem.
        """
        # TODO: add support for gifs/videos
        await process(ctx, processing.other.magickone, [["IMAGE"]], strength)

    @commands.hybrid_command(aliases=["repeat"], hidden=True)
    async def loop(self, ctx):
        """Vejo $gifloop ou $videoloop"""
        await ctx.reply("MediaForge tem 2 comandos de loop.\nUse `$gifloop` to alterar/limitar a quantidade de vezes que um GIF "
                        "rotações. Isso só funciona em GIFs.\nUse `$videoloop` para repetir um vídeo. Este comando "
                        "duplica o conteúdo do vídeo.")

    @commands.hybrid_command(aliases=["gloop"])
    async def gifloop(self, ctx, loop: commands.Range[int, -1] = 0):
        """
        Altera a quantidade de vezes que um gif é repetido
        Ver $videoloop for videos.

        :param ctx: contexto de discord
        :param loop: número de vezes para loop. -1 para nenhum loop, 0 para loop infinito.
        :mediaparam media: para gif.
        """

        await process(ctx, processing.ffmpeg.gifloop, [["GIF"]], loop)

    @commands.hybrid_command(aliases=["vloop"])
    async def videoloop(self, ctx, loop: commands.Range[int, 1, 15] = 1):
        """
        repete um vídeo
        Ver $gifloop para gifs.

        :param ctx: contexto de discord
        :param loop: número de vezes para loop.
        :mediaparam mídia: um vídeo.
        """
        await process(ctx, processing.ffmpeg.videoloop, [["VIDEO"]], loop)

    @commands.hybrid_command(aliases=["flip", "rot"])
    async def rotate(self, ctx, rottype: typing.Literal["90", "90ccw", "180", "vflip", "hflip"]):
        """
        Gira e/ou vira a mídia

        :param ctx: contexto de discord
        :param rottype: 90: 90° no sentido horário, 90ccw: 90° no sentido anti-horário, 180: 180°, vflip: giro vertical, hflip:
        giro horizontal
        :mediaparam media: Um vídeo, gif ou imagem.
        """
        await process(ctx, processing.ffmpeg.rotate, [["GIF", "IMAGE", "VIDEO"]], rottype)

    @commands.hybrid_command()
    async def hue(self, ctx, h: float):
        """
        Altere a tonalidade da mídia.
        Vejo https://ffmpeg.org/ffmpeg-filters.html#hue

        :param ctx: contexto de discord
        :param h: O ângulo de matiz como um número de graus.
        :mediaparam media: Um vídeo, gif ou imagem.
        """
        await process(ctx, processing.ffmpeg.hue, [["GIF", "IMAGE", "VIDEO"]], h)

    @commands.hybrid_command(aliases=["color", "recolor"])
    async def tint(self, ctx, color: discord.Color):
        """
        Tingir a mídia com uma cor.
        Este comando primeiro torna a imagem em tons de cinza e, em seguida, substitui o branco pela sua cor.
        A imagem resultante não deve ser nada além de tons de sua cor.

        :param ctx: contexto de discord
        :param color: A cor hexadecimal ou RGB para tingir.
        :mediaparam media: Um vídeo, gif ou imagem.
        """
        await process(ctx, processing.ffmpeg.tint, [["GIF", "IMAGE", "VIDEO"]], color)

    @commands.hybrid_command(aliases=["round", "circlecrop", "roundcrop", "circle", "roundedcorners"])
    async def roundcorners(self, ctx, radius: int = 10):
        """
        Cantos arredondados da mídia
        Vejo https://developer.mozilla.org/en-US/docs/Web/CSS/border-radius

        :param ctx: contexto de discord
        :param radius: to tamanho dos cantos arredondados em pixels
        :mediaparam media: Um vídeo, gif ou imagem.
        """
        if not 0 <= radius:
            raise commands.BadArgument(f"A porcentagem do raio da borda deve estar acima de 0")
        await process(ctx, processing.ffmpeg.round_corners, [["GIF", "IMAGE", "VIDEO"]], radius)

    @commands.hybrid_command()
    async def volume(self, ctx, volume: commands.Range[float, 0, 32]):
        """
        Altera o volume da mídia.
        Para fazer 2x mais alto, use `$volume 2`.
        Este comando altera o *volume percebido*, não o nível de áudio bruto.
        AVISO: ***MUITO*** ÁUDIO ALTO PODE SER CRIADO

        :param ctx: contexto de discord
        :param volume: número para multiplicar o nível de áudio percebido. Deve estar entre 0 e 32.
        :mediaparam media: Um arquivo de vídeo ou áudio.
        """
        if not 0 <= volume <= 32:
            raise commands.BadArgument(f"{config.emojis['warning']} O volume deve estar entre 0 e 32.")
        await process(ctx, processing.ffmpeg.volume, [["VIDEO", "AUDIO"]], volume)

    @commands.hybrid_command()
    async def mute(self, ctx):
        """
        alias para $volume 0

        :param ctx: contexto de discord
        :mediaparam media: Um arquivo de vídeo ou áudio.
        """
        await process(ctx, processing.ffmpeg.volume, [["VIDEO", "AUDIO"]], 0)

    @commands.hybrid_command()
    async def vibrato(self, ctx, frequency: commands.Range[float, 0.1, 20000.0] = 5,
                      depth: commands.Range[float, 0, 1] = 1):
        """
        Aplica um efeito de "pitch ondulado"/vibrato ao áudio.
        oficialmente descrito como "modulação de fase senoidal"
        Vejo https://ffmpeg.org/ffmpeg-filters.html#tremolo

        :param ctx: contexto de discord
        :param frequency: Frequência de modulação em Hertz. deve estar entre 0,1 e 20000.
        :param depth: Profundidade de modulação em porcentagem. deve estar entre 0 e 1.
        :mediaparam media: Um arquivo de vídeo ou áudio.
        """
        await process(ctx, processing.ffmpeg.vibrato, [["VIDEO", "AUDIO"]], frequency, depth)

    @commands.hybrid_command()
    async def pitch(self, ctx, numofhalfsteps: commands.Range[float, -12, 12] = 12):
        """
        Altera o tom do áudio

        :param ctx: contexto de discord
        :param numofhalfsteps: o número de semitons para alterar o tom. `12` aumenta o tom uma oitava e
        `-12` diminui o tom uma oitava. deve estar entre -12 e 12.
        :mediaparam media: Um arquivo de vídeo ou áudio.
        """
        if not -12 <= numofhalfsteps <= 12:
            raise commands.BadArgument(f"numofhalfsteps must be between -12 and 12.")
        await process(ctx, processing.ffmpeg.pitch, [["VIDEO", "AUDIO"]], numofhalfsteps)

    @commands.hybrid_command(aliases=["concat", "combinev"])
    async def concatv(self, ctx):
        """
        Makes one video file play right after another.
        The output video will take on all of the settings of the FIRST video.
        The second video will be scaled to fit.

        :param ctx: contexto de discord
        :mediaparam video1: A video or gif.
        :mediaparam video2: A video or gif.
        """
        await process(ctx, processing.ffmpeg.concatv, [["VIDEO", "GIF"], ["VIDEO", "GIF"]])

    @commands.hybrid_command()
    async def hstack(self, ctx):
        """
        Stacks 2 videos horizontally

        :param ctx: contexto de discord
        :mediaparam video1: A video, image, or gif.
        :mediaparam video2: A video, image, or gif.
        """
        await process(ctx, processing.ffmpeg.stack, [["VIDEO", "GIF", "IMAGE"], ["VIDEO", "GIF", "IMAGE"]],
                      "hstack")

    @commands.hybrid_command()
    async def vstack(self, ctx):
        """
        Stacks 2 videos horizontally

        :param ctx: contexto de discord
        :mediaparam video1: A video, image, or gif.
        :mediaparam video2: A video, image, or gif.
        """
        await process(ctx, processing.ffmpeg.stack, [["VIDEO", "GIF", "IMAGE"], ["VIDEO", "GIF", "IMAGE"]],
                      "vstack")

    @commands.hybrid_command(aliases=["blend"])
    async def overlay(self, ctx, alpha: commands.Range[float, 0, 1] = 0.5):
        """
        Overlays the second input over the first

        :param ctx: contexto de discord
        :param alpha: the alpha (transparency) of the top video. must be between 0 and 1.
        :mediaparam video1: A video or gif.
        :mediaparam video2: A video or gif.
        """
        await process(ctx, processing.ffmpeg.overlay, [["VIDEO", "GIF", "IMAGE"], ["VIDEO", "GIF", "IMAGE"]], alpha,
                      "overlay")

    @commands.hybrid_command(aliases=["overlayadd", "addition"])
    async def add(self, ctx):
        """
        Adds the pixel values of the second video to the first.

        :param ctx: contexto de discord
        :mediaparam video1: A video or gif.
        :mediaparam video2: A video or gif.
        """
        await process(ctx, processing.ffmpeg.overlay, [["VIDEO", "GIF", "IMAGE"], ["VIDEO", "GIF", "IMAGE"]], 1,
                      "add")

    @commands.hybrid_command(name="speed")
    async def spcommand(self, ctx, speed: commands.Range[float, 0.25, 100.0] = 2):
        """
        Changes the speed of media.
        This command preserves the original FPS, which means speeding up will drop frames. See $fps.

        :param ctx: contexto de discord
        :param speed: Multiplies input video speed by this number. must be between 0.25 and 100.
        :mediaparam media: A video, gif, or audio.
        """
        await process(ctx, processing.ffmpeg.speed, [["VIDEO", "GIF", "AUDIO"]], speed)

    @commands.hybrid_command(aliases=["shuffle", "stutter", "nervous"])
    async def random(self, ctx, frames: commands.Range[int, 2, 512] = 30):
        """
        Shuffles the frames of a video around.
        Currently, this command does NOT apply to audio. This is an FFmpeg limitation.
        see https://ffmpeg.org/ffmpeg-filters.html#random

        :param ctx: contexto de discord
        :param frames: Set size in number of frames of internal cache. must be between 2 and 512. default is 30.
        :mediaparam video: A video or gif.
        """
        await process(ctx, processing.ffmpeg.random, [["VIDEO", "GIF"]], frames)

    @commands.hybrid_command()
    async def reverse(self, ctx):
        """
        Reverses media.

        :param ctx: contexto de discord
        :mediaparam video: A video or gif.
        """
        await process(ctx, processing.ffmpeg.reverse, [["VIDEO", "GIF"]])

    @commands.hybrid_command(aliases=["compress", "quality", "lowerquality", "crf", "qa"])
    async def compressv(self, ctx, crf: commands.Range[float, 28, 51] = 51,
                        qa: commands.Range[float, 10, 112] = 20):
        """
        Makes videos terrible quality.
        The strange ranges on the numbers are because they are quality settings in FFmpeg's encoding.
        CRF info is found at https://trac.ffmpeg.org/wiki/Encode/H.264#crf
        audio quality info is found under https://trac.ffmpeg.org/wiki/Encode/AAC#fdk_cbr

        :param ctx: contexto de discord
        :param crf: Controls video quality. Higher is worse quality. must be between 28 and 51.
        :param qa: Audio bitrate in kbps. Lower is worse quality. Must be between 10 and 112.
        :mediaparam video: A video or gif.
        """
        await process(ctx, processing.ffmpeg.quality, [["VIDEO", "GIF"]], crf, qa)

    @commands.hybrid_command(name="fps")
    async def fpschange(self, ctx, fps: commands.Range[float, 1, 60]):
        """
        Changes the FPS of media.
        This command keeps the speed the same.
        BEWARE: Changing the FPS of gifs can create strange results due to the strange way GIFs store FPS data.
        GIFs are only stable at certain FPS values. These include 50, 30, 15, 10, and others.
        An important reminder that by default tenor "gifs" are interpreted as mp4s,
        which do not suffer this problem.

        :param ctx: contexto de discord
        :param fps: Frames per second of the output. must be between 1 and 60.
        :mediaparam video: A video or gif.
        """
        await process(ctx, processing.ffmpeg.changefps, [["VIDEO", "GIF"]], fps)

    @commands.hybrid_command(aliases=["negate", "opposite"])
    async def invert(self, ctx):
        """
        Inverts colors of media

        :param ctx: contexto de discord
        :mediaparam video: A video or gif.
        """
        await process(ctx, processing.ffmpeg.invert, [["VIDEO", "GIF", "IMAGE"]])

    @commands.hybrid_command()
    async def trim(self, ctx, length: commands.Range[float, 0, None],
                   start: commands.Range[float, 0, None] = 0):
        """
        Trims media.

        :param ctx: contexto de discord
        :param length: Length in seconds to trim the media to.
        :param start: Time in seconds to start the trimmed media at.
        :mediaparam media: A video, gif, or audio file.
        """
        await process(ctx, processing.ffmpeg.trim, [["VIDEO", "GIF", "AUDIO"]], length, start)

    @commands.hybrid_command(aliases=["uncap", "nocaption", "nocap", "rmcap", "removecaption", "delcap", "delcaption",
                                      "deletecaption", "trimcap", "trimcaption"])
    async def uncaption(self, ctx, frame_to_try: int = 0, threshold: commands.Range[float, 0, 255] = 10):
        """
        try to remove esm/default style captions from media
        scans the leftmost column of pixels on one frame to attempt to determine where the caption is.

        :param ctx:
        :param frame_to_try: which frame to run caption detection on. -1 uses the last frame.
        :param threshold: a number 0-255 how similar the caption background must be to white
        :mediaparam media: A video, image, or GIF file
        """
        await process(ctx, processing.vips.other.uncaption, [["VIDEO", "IMAGE", "GIF"]], frame_to_try, threshold)
