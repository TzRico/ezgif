import discord
import emojis
import regex as re
from discord.ext import commands


def add_long_field(embed: discord.Embed, name: str, value: str) -> discord.Embed:
    """
    adicione campos a cada 1024 caracteres a uma embed do discord
    :param embed: embed
    :param name: título de embed
    :param value: valor longo
    :return: embed atualizada
    """
    if len(value) <= 1024:
        return embed.add_field(name=name, value=value, inline=False)
    else:
        for i, section in enumerate(re.finditer('.{1,1024}', value, flags=re.S)):
            embed.add_field(name=name + f" {i + 1}", value=section[0], inline=False)
    if len(embed) > 6000:
        raise Exception(f"A embed gerada excede o tamanho máximo. ({len(embed)} > 6000)")
    return embed


def showcog(cog):
    show_cog = False
    # verifique se há algum comando não oculto na engrenagem, caso contrário, não o mostre no menu de ajuda.
    for com in cog.get_commands():
        if not com.hidden:
            show_cog = True
            break
    return show_cog


class UnicodeEmojiConverter(commands.Converter):
    async def convert(self, ctx, argument):
        emoji = emojis.get(argument)
        if not emoji:
            raise UnicodeEmojiNotFound(argument)
        return list(emoji)[0]


class UnicodeEmojisConverter(commands.Converter):
    async def convert(self, ctx, argument):
        emoji = emojis.get(argument)
        if not emoji:
            raise UnicodeEmojiNotFound(argument)
        return list(emoji)


class UnicodeEmojiNotFound(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'Unicode emoji `{argument}` not found.')
