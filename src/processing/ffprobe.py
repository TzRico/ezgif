import json
import sys
import apng
if sys.platform == "win32":  # espero que isso não cause nenhum problema :>
    from winmagic import magic
else:
    import magic
from PIL import Image, UnidentifiedImageError

from processing.common import *


async def is_apng(filename):
    out = await run_command("ffprobe", filename, "-v", "panic", "-select_streams", "v:0", "-print_format", "json",
                            "-show_entries", "stream=codec_name")
    data = json.loads(out)
    if len(data["streams"]):  # 0 if audio file because it selects v:0, audio cannot be apng
        return data["streams"][0]["codec_name"] == "apng"
    else:
        return False


# https://askubuntu.com/questions/110264/how-to-find-frames-per-second-of-any-video-file
async def get_frame_rate(filename):
    """
    gets the FPS of a file
    :param filename: filename
    :return: FPS
    """
    logger.info("Getting FPS...")
    out = await run_command("ffprobe", filename, "-v", "panic", "-select_streams", "v:0", "-print_format", "json",
                            "-show_entries", "stream=r_frame_rate,codec_name")
    data = json.loads(out)
    if data["streams"][0]["codec_name"] == "apng":  # ffmpeg no likey apng
        parsedapng = apng.APNG.open(filename)
        apnglen = 0
        # https://wiki.mozilla.org/APNG_Specification#.60fcTL.60:_The_Frame_Control_Chunk
        for png, control in parsedapng.frames:
            if control.delay_den == 0:
                control.delay_den = 100
            apnglen += control.delay / control.delay_den
        return len(parsedapng.frames) / apnglen
    else:
        rate = data["streams"][0]["r_frame_rate"].split("/")
        if len(rate) == 1:
            return float(rate[0])
        if len(rate) == 2:
            return float(rate[0]) / float(rate[1])
        return -1


# https://superuser.com/questions/650291/how-to-get-video-duration-in-seconds
async def get_duration(filename):
    """
    obtém a duração de um arquivo
    :param nome do arquivo: filename
    :return: duração
    """
    logger.info("Obtendo duração...")
    out = await run_command("ffprobe", "-v", "panic", "-show_entries", "format=duration", "-of",
                            "default=noprint_wrappers=1:nokey=1", filename)
    if out == "N/A":  # acontece com APNGs
        # não há garantia de que é um PNG aqui, mas não tenho outros planos, então quero abrir uma exceção
        parsedapng = apng.APNG.open(filename)
        apnglen = 0
        # https://wiki.mozilla.org/APNG_Specification#.60fcTL.60:_The_Frame_Control_Chunk
        for png, control in parsedapng.frames:
            if control.delay_den == 0:
                control.delay_den = 100
            apnglen += control.delay / control.delay_den
        return apnglen
    else:
        return float(out)


async def get_resolution(filename):
    """
    Obtém a resolução de um arquivo
    :param filename: nome do arquivo
    :return: [largura altura]
    """
    out = await run_command("ffprobe", "-v", "panic", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height:stream_tags=rotate",
                            "-print_format", "json", filename)
    out = json.loads(out)
    w = out["streams"][0]["width"]
    h = out["streams"][0]["height"]
    # if girado em metadados, troca de largura e altura
    if "tags" in out["streams"][0]:
        if "rotate" in out["streams"][0]["tags"]:
            rot = float(out["streams"][0]["tags"]["rotate"])
            if rot % 90 == 0 and not rot % 180 == 0:
                w, h = h, w
    return [w, h]


async def get_vcodec(filename):
    """
    obtém o codec de um vídeo
    :param filename: nome do arquivo
    :return: ditado contendo "codec_name" and "codec_long_name"
    """
    out = await run_command("ffprobe", "-v", "panic", "-select_streams", "v:0", "-show_entries",
                            "stream=codec_name,codec_long_name",
                            "-print_format", "json", filename)
    out = json.loads(out)
    if out["streams"]:
        return out["streams"][0]
    else:
        # verifica apenas o codec de vídeo, os arquivos de áudio retornam Nothing
        return None


async def get_acodec(filename):
    """
    obtém o codec de áudio
    :param filename: nome do arquivo
    :return: ditado contendo "codec_name" e "codec_long_name"
    """
    out = await run_command("ffprobe", "-v", "panic", "-select_streams", "a:0", "-show_entries",
                            "stream=codec_name,codec_long_name",
                            "-print_format", "json", filename)
    out = json.loads(out)
    if out["streams"]:
        return out["streams"][0]
    else:
        return None


async def va_codecs(filename):
    out = await run_command('ffprobe', '-v', 'panic', '-show_entries', 'stream=codec_name,codec_type', '-print_format',
                            'json', filename)
    out = json.loads(out)
    acodec = None
    vcodec = None
    if out["streams"]:
        for stream in out["streams"]:
            if stream["codec_type"] == "video" and vcodec is None:
                vcodec = stream["codec_name"]
            elif stream["codec_type"] == "audio" and acodec is None:
                acodec = stream["codec_name"]
        return vcodec, acodec
    else:
        return None


async def mediatype(image):
    """
    Obtém o tipo básico de mídia
    :param image: nome do arquivo de mídia
    :return: pode ser VÍDEO, ÁUDIO, GIF, IMAGEM ou Nenhum (inválido ou outro).
    """
    # O ffmpeg não funciona bem com a detecção de imagens, então deixe o PIL fazer isso
    mime = magic.from_file(image, mime=True)
    try:
        with Image.open(image) as im:
            anim = getattr(im, "is_animated", False)
        if anim:
            logger.debug(f"tipo identificado {mime} com quadros animados como GIF")
            return "GIF"  # os gifs não precisam ser animados, mas se não forem, é mais fácil tratá-los como pngs
        else:
            logger.debug(f"tipo identificado {mime} sem quadros animados como IMAGE")
            return "IMAGE"
    except UnidentifiedImageError:
        logger.debug(f"UnidentifiedImageError ativado {image}")
    # PIL não tem certeza, então deixe o ffmpeg assumir o controle
    probe = await run_command('ffprobe', '-v', 'panic', '-count_packets', '-show_entries',
                              'stream=codec_type,codec_name,nb_read_packets',
                              '-print_format', 'json', image)
    props = {
        "video": False,
        "audio": False,
        "gif": False,
        "image": False
    }
    probe = json.loads(probe)
    for stream in probe["streams"]:
        if stream["codec_type"] == "audio":  # só pode ser áudio puro
            props["audio"] = True
        elif stream["codec_type"] == "video":  # pode ser vídeo ou imagem ou gif infelizmente
            if "nb_read_packets" in stream and int(stream["nb_read_packets"]) != 1:  # se houver vários quadros
                if stream["codec_name"] == "gif":  # se gif
                    # deveria ter sido detectado na etapa anterior, mas não custa nada ter certeza
                    props["gif"] = True  # gif
                else:  #vários quadros, não gif
                    props["video"] = True  # video!!
            else:  # se houver apenas um quadro
                props["image"] = True  # é uma imagem
                # sim, isso marcará 1 quadro/gifs não animados como imagens.
                # este é um comportamento intencional, pois a maioria dos comandos trata os gifs como vídeos
    # ok, então um container pode ter vários formatos, precisamos retornar com base na prioridade esperada
    if props["video"]:
        return "VIDEO"
    if props["gif"]:
        return "GIF"
    if props["audio"]:
        return "AUDIO"
    if props["image"]:
        return "IMAGE"
    logger.debug(f"mediatype Nenhum devido ao tipo não classificado {mime}")
    return None


async def ffprobe(file):
    return [await run_command("ffprobe", "-hide_banner", file), magic.from_file(file, mime=False),
            magic.from_file(file, mime=True)]


async def count_frames(video):
    # https://stackoverflow.com/a/28376817/9044183
    return int(await run_command("ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                                 "stream=nb_read_packets", "-of", "csv=p=0", video))


async def frame_n(video, n: int):
    framecount = await count_frames(video)
    if not -1 <= n < framecount:
        raise NonBugError(f"Quadro {n} não existe.")
    if n == -1:
        n = framecount - 1
    frame = reserve_tempfile("png")
    await run_command("ffmpeg", "-hide_banner", "-i", video, "-vf", f"select='eq(n,{n})'", "-vframes", "1",
                      frame)
    return frame
