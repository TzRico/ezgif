import asyncio
import inspect
import typing

import discord
from discord.ext import commands

import config
import processing.common
import processing.ffmpeg
import processing.ffprobe
from core import v2queue
from core.clogs import logger
from utils.scandiscord import imagesearch
from utils.web import saveurls
import utils.tempfiles


async def process(ctx: commands.Context, func: callable, inputs: list, *args,
                  resize=True, expectimage=True, uploadresult=True, queue=True, run_parallel=False, **kwargs):
    """
    A função principal do bot. Reúne a mídia e a envia para a função apropriada.

    :param ctx: discord context. a mídia é coletada usando imagesearch() com this.
    :param func: função para processar mídia de entrada com
    :param inputs: lista de listas de strings. cada lista interna é um argumento, as strings que ela contém são os
        tipos que arg deve ser. ou apenas False/[] se nenhuma mídia for necessária
    :param args: quaisquer argumentos que não sejam de mídia, passados ​​para func ()
    :param resize: automaticamente aumentar/diminuir o tamanho das entradas?
    :param expectimage: func() deveria retornar um resultado? se verdadeiro, ele espera uma imagem. se falso, pode usar um
        string.
    :param uploadresult: se true, carrega o resultado automaticamente.
    :param queue: se verdadeiro, o comando deve aguardar o slot aberto na fila para processar.
    :param run_parallel: apenas para funções de sincronização, execute sem bloquear
    :return: nome do arquivo da mídia processada
    """

    result = None
    msg: typing.Optional[discord.Message] = None

    async def reply(st):
        return await ctx.reply(f"{config.emojis['working']} {st}", mention_author=False)

    async def updatestatus(st):
        nonlocal msg
        try:
            if msg is None:
                msg = await reply(st)
            else:
                msg = await msg.edit(content=f"{config.emojis['working']} {st}",
                                     allowed_mentions=discord.AllowedMentions.none())
        except discord.NotFound:
            msg = await reply(st)

    if inputs:
        # nothing to download sometimes
        await updatestatus(f"Baixando...")

    try:
        async with utils.tempfiles.TempFileSession():
            # get media from channel
            if inputs:
                urls = await imagesearch(ctx, len(inputs))
                files = await saveurls(urls)
            else:
                files = []
            # if media found or none needed
            if files or not inputs:
                # check that each file is correct type
                for i, file in enumerate(files):
                    # if file is incorrect type
                    if (imtype := await processing.ffprobe.mediatype(file)) not in inputs[i]:
                        # send message and break
                        await ctx.reply(
                            f"{config.emojis['warning']} A mídia #{i + 1} é {imtype}, deve ser: "
                            f"{', '.join(inputs[i])}")
                        logger.info(f"Mídia {i} tipo {imtype} não está em {inputs[i]}")
                        break
                    else:
                        # send warning for apng
                        if await processing.ffmpeg.is_apng(file):
                            asyncio.create_task(ctx.reply(f"{config.emojis['warning']} Media #{i + 1} is an apng, w"
                                                          f"para o qual o FFmpeg e o Gifmaker têm suporte limitado. Ex"
                                                          f"pect errors.", delete_after=10))
                        # resize if needed
                        if resize:
                            files[i] = await processing.ffmpeg.ensuresize(ctx, file, config.min_size, config.max_size)
                # files are of correcte type, begin to process
                else:
                    # only update with queue message if there is a queue
                    if queue and v2queue.sem.locked():
                        await updatestatus("Seu comando está na fila...")

                    # run func
                    async def run():
                        nonlocal args
                        nonlocal files
                        logger.info("Em processamento...")
                        await updatestatus("Em processamento...")
                        # remove too long videossss
                        for i, f in enumerate(files):
                            files[i] = await processing.ffmpeg.ensureduration(f, ctx)
                        # prepare args
                        if inputs:
                            args = files + list(args)
                        # some commands arent coros (usually no-ops) so this is a good check to make
                        if inspect.iscoroutinefunction(func):
                            command_result = await func(*args, **kwargs)
                        else:
                            if run_parallel:
                                command_result = await processing.common.run_parallel(func, *args, **kwargs)
                            else:
                                logger.warning(f"{func} não é corrotina")
                                command_result = func(*args, **kwargs)
                        if expectimage and command_result:
                            mt = await processing.ffmpeg.mediatype(command_result)
                            if mt == "VIDEO":
                                command_result = await processing.ffmpeg.reencode(command_result)
                            command_result = await processing.ffmpeg.assurefilesize(command_result)
                        return command_result

                    # only queue if needed
                    if queue:
                        async with v2queue.sem:
                            result = await run()
                    else:
                        result = await run()
                    # check results are as expected
                    if expectimage:  # file expected
                        if not result:
                            raise processing.common.ReturnedNothing(f"Imagem esperada, {func} não retornou nada.")
                    else:  # status string expected
                        if not result:
                            raise processing.common.ReturnedNothing(f"String esperada, {func} não retornou nada.")
                        else:
                            await ctx.reply(result)

                    # if we need to upload image, do that
                    if result and expectimage:
                        logger.info("Enviando...")
                        await updatestatus("Enviando...")
                        if uploadresult:
                            if ctx.interaction:
                                await msg.edit(content="", attachments=[discord.File(result)])
                            else:
                                await ctx.reply(file=discord.File(result))

            else:  # no media found but media expected
                logger.info("Nenhuma mídia encontrada.")
                if ctx.interaction:
                    await msg.edit(content=f"{config.emojis['x']} Nenhum arquivo encontrado.")
                else:
                    await ctx.reply(f"{config.emojis['x']} Nenhum arquivo encontrado.")
    except Exception as e:
        if msg is not None and not ctx.interaction:
            await msg.delete()
        raise e
    # delete message
    if msg is not None and not ctx.interaction:
        await msg.delete()
    return result
