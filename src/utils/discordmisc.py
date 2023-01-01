import os

import discord

import config
from core.clogs import logger
from processing.ffprobe import mediatype


async def count_emoji(guild: discord.Guild):
    anim = 0
    static = 0
    for emoji in guild.emojis:
        if emoji.animated:
            anim += 1
        else:
            static += 1
    return {"animated": anim, "static": static}


async def add_emoji(file, guild: discord.Guild, name):
    """
    adiciona emoji ao servidor
    :param file: emoji para adicionar
    :param guild: Servidor para adicioná-lo
    :param name: nome do emoji
    :return: texto do resultado
    """
    with open(file, "rb") as f:
        data = f.read()
    try:
        emoji = await guild.create_custom_emoji(name=name, image=data, reason="$addemoji command")
    except discord.Forbidden:
        return f"{config.emojis['x']} Não tenho permissão para criar um emoji. Certifique-se de que eu tenho o Manage Emojis " \
               f"Permissão. "
    except discord.HTTPException as e:
        logger.error(e, exc_info=(type(e), e, e.__traceback__))
        return f"{config.emojis['2exclamation']} Algo deu errado ao tentar adicionar seu emoji! ```{e}```"
    else:
        count = await count_emoji(guild)
        if emoji.animated:
            return f"{config.emojis['check']} Emoji animado adicionado com sucesso: " \
                   f"{emoji}\n{guild.emoji_limit - count['animated']} sobraram slots."
        else:
            return f"{config.emojis['check']} Emoji adicionado com sucesso: " \
                   f"{emoji}\n{guild.emoji_limit - count['static']} sobraram slots."


async def add_sticker(file, guild: discord.Guild, sticker_emoji, name):
    """
    adiciona adesivo ao servidor
    :param file: adesivo para adicionar
    :param guild: Servidor para adicioná-lo
    :param sticker_emoji "related" emoji do adesivo
    :param name: nome do adesivo
    :return: texto do resultado
    """
    size = os.path.getsize(file)
    file = discord.File(file)
    try:
        await guild.create_sticker(name=name, emoji=sticker_emoji, file=file, reason="$addsticker command",
                                   description=" ")
        # description MUST NOT be empty. see https://github.com/nextcord/nextcord/issues/165
    except discord.Forbidden:
        return f"{config.emojis['x']} Não tenho permissão para criar um adesivo. Verifique se eu tenho o Gerenciar " \
               f"Permissão de Emojis e Adesivos. "
    except discord.HTTPException as e:
        logger.error(e, exc_info=(type(e), e, e.__traceback__))
        toreturn = f"{config.emojis['2exclamation']} Algo deu errado ao tentar adicionar seu adesivo! ```{e}```"
        if "Invalid Asset" in str(e):
            toreturn += "\nNota: `Invalid Asset` significa que o Discord não aceita este formato de arquivo. Os adesivos são apenas " \
                        "permitido ser png ou apng."
        if "O recurso excede o tamanho máximo" in str(e):
            toreturn += f"\nNota: Os adesivos devem ter menos de ~500kb. seu adesivo é {humanize.naturalsize(size)}"
        return toreturn
    else:
        return f"{config.emojis['check']} Adesivo adicionado com sucesso.\n" \
               f"\n{guild.sticker_limit - len(guild.stickers)} sobraram slots."


async def set_banner(file, guild: discord.Guild):
    """
    define o banner do servidor
    :param file: arquivo de banner
    :param guild: Servidor para adicioná-lo
    :return:
    """
    with open(file, "rb") as f:
        data = f.read()
    try:
        await guild.edit(banner=bytes(data))
    except discord.Forbidden:
        return f"{config.emojis['x']} Não tenho permissão para definir seu banner. Certifique-se de que tenho a permissão de gerenciar Servidor " \
               f"permission. "
    except discord.HTTPException as e:
        return f"{config.emojis['2exclamation']} Algo deu errado ao tentar definir seu banner! ```{e}```"
    else:
        return f"{config.emojis['check']} Estandarte do servidor alterado com sucesso."


async def set_icon(file, guild: discord.Guild):
    """
    define o ícone do servidor
    :param file: arquivo de ícone
    :param guild: Servidor para adicioná-lo
    :return:
    """
    if (await mediatype(file)) == "GIF" and "ANIMATED_ICON" not in guild.features:
        return f"{config.emojis['x']} Este servidor não suporta ícones animados."
    with open(file, "rb") as f:
        data = f.read()
    try:
        await guild.edit(icon=bytes(data))
    except discord.Forbidden:
        return f"{config.emojis['x']} Não tenho permissão para definir seu ícone. Certifique-se de que tenho a permissão de gerenciar servidor " \
               f"permission. "
    except discord.HTTPException as e:
        return f"{config.emojis['2exclamation']} Algo deu errado ao tentar definir seu ícone! ```{e}```"
    else:
        return "Ícone do servidor alterado com sucesso."


async def iconfromsnowflakeid(snowflake: int, bot, ctx):
    try:
        user = await bot.fetch_user(snowflake)
        return str(user.avatar.url)
    except (discord.NotFound, discord.Forbidden):
        pass
    try:
        guild = await bot.fetch_guild(snowflake)
        return str(guild.icon.url)
    except (discord.NotFound, discord.Forbidden):
        pass
    try:  # get the icon through a message author to support webhook/pk icons
        msg = await ctx.channel.fetch_message(snowflake)
        return str(msg.author.avatar.url)
    except (discord.NotFound, discord.Forbidden):
        pass
    return None


