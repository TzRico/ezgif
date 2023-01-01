import math
import typing

import pyvips

from processing.vips.vipsutils import ImageSize, escape, outline, overlay_in_middle
from utils.tempfiles import reserve_tempfile
from processing.vips.vipsutils import normalize

twemoji = "rendering/fonts/TwemojiCOLR0.otf"


def esmcaption(captions: typing.Sequence[str], size: ImageSize):
    captions = escape(captions)
    # https://github.com/esmBot/esmBot/blob/121615df63bdcff8ee42330d8a67a33a18bb463b/natives/caption.cc#L28-L50
    # constantes usadas pelo esmbot
    fontsize = size.width / 10
    textwidth = size.width * .92
    # tecnicamente redundante, mas adiciona fonte twemoji
    # NÃO FUNCIONA NO WINDOWS IDK PORQUE
    out = pyvips.Image.text(".", fontfile=twemoji)
    # generate text
    out = pyvips.Image.text(
        captions[0],
        font=f"Twemoji Color Emoji,FuturaExtraBlackCondensed {fontsize}px",
        rgba=True,
        fontfile="rendering/fonts/caption.otf",
        align=pyvips.Align.CENTRE,
        width=textwidth
    )
    # fundo branco sobreposto
    out = out.composite((255, 255, 255, 255), mode=pyvips.BlendMode.DEST_OVER)
    # pad texto para largura da imagem
    out = out.gravity(pyvips.CompassDirection.CENTRE, size.width, out.height + fontsize, extend=pyvips.Extend.WHITE)
    # salve e volte
    # porque é executado no executor, tempfiles
    outfile = reserve_tempfile("png")
    out.pngsave(outfile)
    return outfile


def mediaforge_caption(captions: typing.Sequence[str], size: ImageSize):
    captions = escape(captions)
    # https://github.com/esmBot/esmBot/blob/121615df63bdcff8ee42330d8a67a33a18bb463b/natives/caption.cc#L28-L50
    # constantes usadas pelo esmbot
    fontsize = size.width / 10
    textwidth = size.width * .92
    # tecnicamente redundante, mas adiciona fonte twemoji
    # NÃO FUNCIONA NO WINDOWS IDK PORQUE
    out = pyvips.Image.text(".", fontfile=twemoji)
    # gerar texto
    out = pyvips.Image.text(
        captions[0],
        font=f"Twemoji Color Emoji, Atkinson Hyperlegible Bold {fontsize}px",
        rgba=True,
        fontfile="rendering/fonts/AtkinsonHyperlegible-Bold.ttf",
        align=pyvips.Align.CENTRE,
        width=textwidth
    )
    # fundo branco sobreposto
    out = out.composite((255, 255, 255, 255), mode=pyvips.BlendMode.DEST_OVER)
    # pad texto para largura da imagem
    out = out.gravity(pyvips.CompassDirection.CENTRE, size.width, out.height + fontsize, extend=pyvips.Extend.WHITE)
    # salve e volte
    # porque é executado no executor, tempfiles
    outfile = reserve_tempfile("png")
    out.pngsave(outfile)
    return outfile


def motivate_text(captions: typing.Sequence[str], size: ImageSize):
    captions = escape(captions)
    textsize = size.width / 5
    width = math.floor(size.width + (size.width / 60))
    width = math.floor(width + (width / 30))
    toptext = None
    bottomtext = None
    if captions[0]:
        # tecnicamente redundante, mas adiciona fonte twemoji
        toptext = pyvips.Image.text(".", fontfile=twemoji)
        # gerar texto
        toptext = pyvips.Image.text(
            f"<span foreground=\"white\">{captions[0]}</span>",
            font=f"Twemoji Color Emoji,TimesNewRoman {textsize}px",
            rgba=True,
            fontfile="rendering/fonts/times new roman.ttf",
            align=pyvips.Align.CENTRE,
            width=width
        )
        toptext = toptext.gravity(pyvips.CompassDirection.CENTRE, toptext.width, toptext.height + (textsize / 4),
                                  extend=pyvips.Extend.BLACK)
    if captions[1]:
        # tecnicamente redundante, mas adiciona fonte twemoji
        bottomtext = pyvips.Image.text(".", fontfile=twemoji)
        # gerar texto
        bottomtext = pyvips.Image.text(
            f"<span foreground=\"white\">{captions[1]}</span>",
            font=f"Twemoji Color Emoji,TimesNewRoman {int(textsize * 0.4)}px",
            rgba=True,
            fontfile="rendering/fonts/times new roman.ttf",
            align=pyvips.Align.CENTRE,
            width=width
        )
        bottomtext = bottomtext.gravity(pyvips.CompassDirection.CENTRE, bottomtext.width,
                                        bottomtext.height + (textsize / 4),
                                        extend=pyvips.Extend.BLACK)
    if toptext and bottomtext:
        out = toptext.join(bottomtext, pyvips.Direction.VERTICAL, expand=True, background=[0, 0, 0, 255],
                           align=pyvips.Align.CENTRE)
    else:
        if toptext:
            out = toptext
        elif bottomtext:
            out = bottomtext
        else:  # não deveria acontecer, mas por que não
            raise Exception("missing toptext and bottomtext")
            # Fora = pyvips.Image.new_from_list([[0, 0, 0, 255]])
    # sobreposição de fundo preto
    out = out.composite2((0, 0, 0, 255), pyvips.BlendMode.DEST_OVER)
    # texto de preenchimento para largura de destino
    out = out.gravity(pyvips.CompassDirection.CENTRE, width, out.height, extend=pyvips.Extend.BACKGROUND,
                      background=[0, 0, 0, 255])
    outfile = reserve_tempfile("png")
    out.pngsave(outfile)
    return outfile


def meme(captions: typing.Sequence[str], size: ImageSize):
    captions = escape(captions)
    # imagem em branco
    overlay = pyvips.Image.black(size.width, size.height).new_from_image([0, 0, 0, 0]).copy(
        interpretation=pyvips.enums.Interpretation.SRGB)

    if captions[0]:
        # tecnicamente redundante, mas adiciona fonte twemoji
        toptext = pyvips.Image.text(".", fontfile=twemoji)
        # gerar texto
        toptext = pyvips.Image.text(
            f"<span foreground=\"white\">{captions[0].upper()}</span>",
            font=f"Twemoji Color Emoji,ImpactMix",
            rgba=True,
            fontfile="rendering/fonts/ImpactMix.ttf",
            align=pyvips.Align.CENTRE,
            width=int(size.width * .95),
            height=int((size.height * .95) / 3)
        )
        overlay = overlay.composite2(toptext, pyvips.BlendMode.OVER,
                                     x=((size.width - toptext.width) / 2),
                                     y=int(size.height * .025))
    if captions[1]:
        # tecnicamente redundante, mas adiciona fonte twemoji
        bottomtext = pyvips.Image.text(".", fontfile=twemoji)
        # gerar texto
        bottomtext = pyvips.Image.text(
            f"<span foreground=\"white\">{captions[1].upper()}</span>",
            font=f"Twemoji Color Emoji,ImpactMix",
            rgba=True,
            fontfile="rendering/fonts/ImpactMix.ttf",
            align=pyvips.Align.CENTRE,
            width=int(size.width * .95),
            height=int((size.height * .95) / 3)
        )
        overlay = overlay.composite2(bottomtext, pyvips.BlendMode.OVER,
                                     x=((size.width - bottomtext.width) / 2),
                                     y=int((size.height * .975) - bottomtext.height))

    overlay = outline(overlay, overlay.width // 200)
    outfile = reserve_tempfile("png")
    overlay.pngsave(outfile)
    return outfile


def tenor(captions: typing.Sequence[str], size: ImageSize):
    captions = escape(captions)
    # imagem em branco
    overlay = pyvips.Image.black(size.width, size.height).new_from_image([0, 0, 0, 0]).copy(
        interpretation=pyvips.enums.Interpretation.SRGB)
    textsize = size.width // 10
    if captions[0]:
        # tecnicamente redundante, mas adiciona fonte twemoji
        toptext = pyvips.Image.text(".", fontfile=twemoji)
        # gerar texto
        toptext = pyvips.Image.text(
            f"<span foreground=\"white\">{captions[0]}</span>",
            font=f"Twemoji Color Emoji,Ubuntu {textsize}px",
            rgba=True,
            fontfile="rendering/fonts/Ubuntu-R.ttf",
            align=pyvips.Align.CENTRE,
            width=int(size.width * .95),
            height=int((size.height * .95) / 3)
        )
        overlay = overlay.composite2(toptext, pyvips.BlendMode.OVER,
                                     x=((size.width - toptext.width) / 2),
                                     y=int(size.height * .025))
    if captions[1]:
        # tecnicamente redundante, mas adiciona fonte twemoji
        bottomtext = pyvips.Image.text(".", fontfile=twemoji)
        # gerar texto
        bottomtext = pyvips.Image.text(
            f"<span foreground=\"white\">{captions[1]}</span>",
            font=f"Twemoji Color Emoji,Ubuntu {textsize}px",
            rgba=True,
            fontfile="rendering/fonts/Ubuntu-R.ttf",
            align=pyvips.Align.CENTRE,
            width=int(size.width * .95),
            height=int((size.height * .95) / 3)
        )
        overlay = overlay.composite2(bottomtext, pyvips.BlendMode.OVER,
                                     x=((size.width - bottomtext.width) / 2),
                                     y=int((size.height * .975) - bottomtext.height))

    overlay = outline(overlay, overlay.width // 250)
    outfile = reserve_tempfile("png")
    overlay.pngsave(outfile)
    return outfile


def whisper(captions: typing.Sequence[str], size: ImageSize):
    captions = escape(captions)
    # imagem em branco
    overlay = pyvips.Image.black(size.width, size.height).new_from_image([0, 0, 0, 0]).copy(
        interpretation=pyvips.enums.Interpretation.SRGB)

    # tecnicamente redundante, mas adiciona fonte twemoji
    text = pyvips.Image.text(".", fontfile=twemoji)
    # gerar texto
    text = pyvips.Image.text(
        f"<span foreground=\"white\">{captions[0]}</span>",
        font=f"Twemoji Color Emoji,Upright {size.width // 6}px",
        rgba=True,
        fontfile="rendering/fonts/whisper.otf",
        align=pyvips.Align.CENTRE,
        width=int(size.width * .95),
        height=int(size.height * .95)
    )
    overlay = overlay_in_middle(overlay, text)

    overlay = outline(overlay, overlay.width // 175)
    outfile = reserve_tempfile("png")
    overlay.pngsave(outfile)
    return outfile


def snapchat(captions: typing.Sequence[str], size: ImageSize):
    # tecnicamente redundante, mas adiciona fonte twemoji
    text = pyvips.Image.text(".", fontfile=twemoji)
    # gerar texto
    text = pyvips.Image.text(
        f"<span foreground=\"white\">{captions[0]}</span>",
        font=f"Twemoji Color Emoji,Helvetica Neue {size.width // 20}px",
        rgba=True,
        fontfile="rendering/fonts/HelveticaNeue.otf",
        align=pyvips.Align.CENTRE,
        width=int(size.width * .98),
        height=size.height // 3
    )
    # fundo
    bg = pyvips.Image.black(size.width, text.height + size.width // 25).new_from_image([0, 0, 0, 178]).copy(
        interpretation=pyvips.enums.Interpretation.SRGB)
    # sobreposição
    text = overlay_in_middle(bg, text)
    # almofada para o tamanho da imagem
    blank_bg = pyvips.Image.black(size.width, size.height).new_from_image([0, 0, 0, 0]).copy(
        interpretation=pyvips.enums.Interpretation.SRGB)
    # sobreposição
    out = overlay_in_middle(blank_bg, text)
    # Salve 
    outfile = reserve_tempfile("png")
    out.pngsave(outfile)
    return outfile


def generic_image_caption(image: str, captions: typing.Sequence[str], size: ImageSize):
    # constantes usadas pelo esmbot
    fontsize = size.width / 10
    textwidth = size.width * (2 / 3) * .92
    # tecnicamente redundante, mas adiciona fonte twemoji
    out = pyvips.Image.text(".", fontfile=twemoji)
    # gerar texto
    out = pyvips.Image.text(
        captions[0],
        font=f"Twemoji Color Emoji,Atkinson Hyperlegible Bold {fontsize}px",
        rgba=True,
        fontfile="rendering/fonts/AtkinsonHyperlegible-Bold.ttf",
        align=pyvips.Align.CENTRE,
        width=textwidth
    )
    # carregar coisas
    im = normalize(pyvips.Image.new_from_file(image))

    # o que diabos está errado com as coisas png??
    if im.bands == 2:
        im = im[0].bandjoin(im[0]).bandjoin(im[0]).bandjoin(im[1]).copy(interpretation=pyvips.Interpretation.SRGB)

    # redimensionar
    im = im.resize((size.width / 3) / im.width)
    # pad texto para largura da imagem
    padded = out.gravity(pyvips.CompassDirection.CENTRE, size.width * (2 / 3), max(out.height + fontsize, im.height),
                         extend=pyvips.Extend.BLACK)

    # Junte-se
    final = padded.join(im, pyvips.Direction.HORIZONTAL, expand=True, background=0xffffff)

    # fundo branco sobreposto
    final = final.composite((255, 255, 255, 255), mode=pyvips.BlendMode.DEST_OVER)
    # Salve 
    outfile = reserve_tempfile("png")
    final.pngsave(outfile)
    return outfile


def twitter_text(captions: typing.Sequence[str], size: ImageSize, dark: bool):
    captions = escape(captions)
    fontsize = size.width / 20
    # tecnicamente redundante, mas adiciona fonte twemoji
    out = pyvips.Image.text(".", fontfile=twemoji)
    # gerar texto
    out = pyvips.Image.text(
        f"<span foreground=\"{'white' if dark else 'black'}\">{captions[0]}</span>",
        font=f"Twemoji Color Emoji,TwitterChirp {fontsize}px",
        rgba=True,
        fontfile="rendering/fonts/chirp-regular-web.woff2",
        align=pyvips.Align.LOW,
        width=size.width
    )
    # texto de preenchimento para a largura da imagem alinhada à esquerda
    out = out.gravity(pyvips.CompassDirection.WEST, size.width, out.height + fontsize,
                      extend=pyvips.Extend.BLACK)
    # adicionar preenchimento
    out = out.gravity(pyvips.CompassDirection.CENTRE, size.width + math.floor(size.width * (12 / 500) * 2),
                      out.height,
                      extend=pyvips.Extend.BLACK)

    # salve e volte
    # porque é executado no executor, tempfiles
    outfile = reserve_tempfile("png")
    out.pngsave(outfile)
    return outfile

# print(esmcaption(["h👍💜🏳️‍🌈🏳️‍⚧️i"], 1000))
# print(meme_text(["topto top topt otp otp top", "bottom"], ImageSize(1000, 1000)))
