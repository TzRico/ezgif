import asyncio
import datetime
import difflib
import glob
import io
import traceback
import urllib.parse

import aiofiles.os
import discord
from aiohttp import client_exceptions as aiohttp_client_exceptions
from discord.ext import commands

import config
import processing.common
import utils.tempfiles
from core.clogs import logger
from utils.common import now, prefix_function, get_full_class_name


class ErrorHandlerCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.antispambucket = {}

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, commanderror: commands.CommandError):
        async def dmauthor(*args, **kwargs):
            try:
                return await ctx.reply(*args, **kwargs)
            except discord.Forbidden:
                logger.info(f"A resposta para {ctx.message.id} e dm para {ctx.author.id} falhou. Abortando.")

        async def reply(msg, file=None, embed=None):
            if ctx.interaction:
                if ctx.interaction.response.is_done():
                    return await ctx.interaction.edit_original_response(content=msg,
                                                                        attachments=[file] if file else None,
                                                                        embed=embed)
                else:
                    return await ctx.reply(msg, file=file, embed=embed)
            else:
                try:
                    if ctx.guild and not ctx.channel.permissions_for(ctx.me).send_messages:
                        logger.debug(f"Sem permissão para responder a {ctx.message.id}, tentando o autor do DM.")
                        return await dmauthor(msg, file=file, embed=embed)
                    return await ctx.reply(msg, file=file, embed=embed)
                except discord.Forbidden:
                    logger.debug(f"Proibido responder a {ctx.message.id}, tentando DM autor")
                    return await dmauthor(msg, file=file, embed=embed)

        async def logandreply(message):
            if ctx.guild:
                ch = f"canal #{ctx.channel.name} ({ctx.channel.id}) no servidor {ctx.guild} ({ctx.guild.id})"
            else:
                ch = "DMs"
            logger.info(f"Comando '{ctx.message.content}' por "
                        f"@{ctx.message.author.name}#{ctx.message.author.discriminator} ({ctx.message.author.id}) "
                        f"em {ch} falhou devido a {message}.")
            await reply(message)

        errorstring = str(commanderror)
        if isinstance(commanderror, discord.Forbidden):
            await dmauthor(f"{config.emojis['x']} Não tenho permissão para enviar mensagens nesse canal.")
            logger.info(commanderror)
        if isinstance(commanderror, discord.ext.commands.errors.CommandNotFound):
            # to prevent funny 429s, error cooldowns are only sent once before the cooldown is over.
            if ctx.author.id in self.antispambucket.keys():
                if self.antispambucket[ctx.author.id] > now():
                    logger.debug(f"Ignorando resposta de erro para {ctx.author} ({ctx.author.id}): {errorstring}")
                    return
            if ctx.message.content.strip().lower() in ["$w", "$wa", "$waifu", "$h", "$ha", "$husbando", "$wx", "$hx",
                                                       "$m", "$ma", "$marry", "$mx", "$g", "$tu", "$top", "$mmrk",
                                                       "$rolls"]:
                # this command is spammed so much, fuckn ignore it
                # https://mudae.fandom.com/wiki/List_of_Commands#.24waifu_.28.24w.29
                logger.debug(f"ignorando {ctx.message.content}")
                return

            # remove money
            is_decimal = True
            for char in ctx.message.content.strip().split(" ")[0]:
                # if non-decimal character found, we're ok to reply with an error
                if not (char.isdecimal() or char in ",.$"):
                    is_decimal = False
                    break
            if is_decimal:
                logger.debug(f"ignorando {ctx.message.content}")
                return

            # remove prefix, remove excess args
            cmd = ctx.message.content[len(ctx.prefix):].split(' ')[0]
            allcmds = []
            for botcom in self.bot.commands:
                if not botcom.hidden:
                    allcmds.append(botcom.name)
                    allcmds += botcom.aliases
            prefix = await prefix_function(self.bot, ctx.message, True)
            match = difflib.get_close_matches(cmd, allcmds, n=1, cutoff=0)[0]
            err = f"{config.emojis['exclamation_question']} O comando `{prefix}{cmd}` não existe. " \
                  f"Você quis dizer **{prefix}{match}**?"
            await logandreply(err)
            self.antispambucket[ctx.author.id] = now() + config.cooldown
        elif isinstance(commanderror, discord.ext.commands.errors.NotOwner):
            err = f"{config.emojis['x']} Você não está autorizado a usar este comando."
            await logandreply(err)
        elif isinstance(commanderror, discord.ext.commands.errors.CommandOnCooldown):
            # to prevent funny 429s, error cooldowns are only sent once before the cooldown is over.
            if ctx.author.id in self.antispambucket.keys():
                if self.antispambucket[ctx.author.id] > now():
                    logger.debug(f"Ignorando resposta de erro para {ctx.author} ({ctx.author.id}): {errorstring}")
                    return
            err = f"{config.emojis['clock']} {errorstring}"
            await logandreply(err)
            self.antispambucket[ctx.author.id] = now() + commanderror.retry_after
        elif isinstance(commanderror, discord.ext.commands.errors.UserInputError):
            err = f"{config.emojis['warning']} {errorstring}"
            if ctx.command:
                prefix = await prefix_function(self.bot, ctx.message, True)
                err += f" Execute `{prefix}ajuda {ctx.command}` para ver como usar este comando."
            await logandreply(err)
        elif isinstance(commanderror, discord.ext.commands.errors.NoPrivateMessage):
            err = f"{config.emojis['warning']} {errorstring}"
            await logandreply(err)
        elif isinstance(commanderror, discord.ext.commands.errors.CheckFailure):
            err = f"{config.emojis['x']} {errorstring}"
            await logandreply(err)
        elif isinstance(commanderror, discord.ext.commands.errors.CommandInvokeError) and \
                isinstance(commanderror.original, processing.common.NonBugError):
            await logandreply(f"{config.emojis['2exclamation']} {str(commanderror.original)[:1000]}")
        else:
            if isinstance(commanderror, discord.ext.commands.errors.CommandInvokeError) or \
                    isinstance(commanderror, discord.ext.commands.HybridCommandError):
                commanderror = commanderror.original
            logger.error(commanderror, exc_info=(type(commanderror), commanderror, commanderror.__traceback__))
            if "OSError: [Errno 28] Sem espaço no dispositivo" in str(commanderror):
                logger.warn("Não há mais espaço no dispositivo, forçando a limpeza da pasta temporária")
                files = glob.glob(utils.tempfiles.temp_dir + "/*")
                logger.warn(f"deleting {len(files)} files")
                logger.debug(files)
                fls = await asyncio.gather(*[aiofiles.os.remove(file) for file in files],
                                           return_exceptions=True)
                for f in fls:
                    if isinstance(f, Exception):
                        logger.debug(f)
            is_hosting_issue = isinstance(commanderror, (aiohttp_client_exceptions.ClientOSError,
                                                         aiohttp_client_exceptions.ServerDisconnectedError,
                                                         asyncio.exceptions.TimeoutError))
            # concurrent.futures.process.BrokenProcessPool))

            if is_hosting_issue:
                desc = "Se esse erro continuar ocorrendo, relate isso com o arquivo traceback anexado ao GitHub."
            else:
                desc = "Relate este erro com o arquivo traceback anexado ao GitHub."
            embed = discord.Embed(color=0xed1c24, description=desc)
            embed.add_field(name=f"{config.emojis['2exclamation']} Relatar problema ao GitHub",
                            value=f"[Criar novo problema](https://github.com/Tzputao/ezgif"
                                  f"/issues/new?labels=bug&template=bug_report.md&title"
                                  f"={urllib.parse.quote(str(commanderror), safe='')[:848]})\n[View Issu"
                                  f"es](https://github.com/Tzputao/ezgif/issues)")
            with io.BytesIO() as buf:
                trheader = f"DATETIME:{datetime.datetime.now()}\nCOMMAND:{ctx.message.content}\nTRACEBACK:\n"
                buf.write(bytes(trheader + ''.join(
                    traceback.format_exception(commanderror)), encoding='utf8'))
                buf.seek(0)
                if is_hosting_issue:
                    errtxt = f"{config.emojis['2exclamation']} Seu comando encontrou um erro devido a limitação " \
                             f"recursos no servidor. Se você gostaria de apoiar a manutenção do Ezgif e " \
                             f"obtendo um servidor melhor, me apoie no Ko-Fi aqui: <https://ko-fi.com/reticivis>"
                else:
                    errtxt = (f"{config.emojis['2exclamation']} `{get_full_class_name(commanderror)}: "
                              f"{errorstring}`")[:2000]
                await reply(errtxt, file=discord.File(buf, filename="traceback.txt"), embed=embed)
