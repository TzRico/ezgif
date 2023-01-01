import asyncio
import os
import sys
from multiprocessing import Process

import psutil

import config
from core.clogs import logger
from utils.common import fetch


async def send_heartbeat():
    try:
        resp = await fetch(config.heartbeaturl)
        logger.debug(f"Heartbeat enviado com sucesso. {resp}")
    # except aiohttp.ClientError as e:
    except Exception as e:
        logger.error(e, exc_info=(type(e), e, e.__traceback__))


async def parent_status():
    # last case scenario, terminate status program if parent terminates. this can happen due to segfaults.
    ppid = os.getppid()
    logger.debug(f"ID do processo pai: {ppid}")
    if psutil.pid_exists(ppid):
        logger.debug("O processo pai está ativo.")
    else:
        logger.error("O processo pai foi encerrado")
        sys.exit(11)


async def heartbeat():
    while True:
        await asyncio.gather(
            send_heartbeat(),
            asyncio.sleep(config.heartbeatfrequency),
            parent_status()
        )


def start_heartbeat():
    logger.debug("batimento cardíaco inicial")
    loop = asyncio.get_event_loop()
    task = loop.create_task(heartbeat())
    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        task.cancel()


heartbeat_active: bool
heartbeatprocess: Process


def init():
    global heartbeat_active
    global heartbeatprocess
    heartbeat_active = hasattr(config, "batimento cardíaco") and config.heartbeaturl
    if heartbeat_active:
        logger.debug(f"URL de pulsação é {config.heartbeaturl}")
        heartbeatprocess = Process(target=start_heartbeat)
        heartbeatprocess.start()
    else:
        logger.debug("Nenhum url de pulsação definido.")
