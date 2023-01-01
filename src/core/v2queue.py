import asyncio
import os
import typing

import config

workers = config.workers or os.cpu_count() or 1
sem = asyncio.Semaphore(workers)
queued = 0


async def enqueue(task: typing.Coroutine):
    global queued
    queued += 1
    # permite apenas uma certa quantidade de tarefas dentro do contexto de uma só vez
    # testes rápidos mostram que é aproximadamente FIFO, mas existem bibliotecas, se necessário
    async with sem:
        try:
            res = await task
        except Exception as e:
            queued -= 1
            raise e
        else:
            queued -= 1
            return res
