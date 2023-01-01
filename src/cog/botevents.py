import discord
from discord.ext import commands

from core.clogs import logger
from utils.common import prefix_function


class BotEventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.log(35, f"logado como {self.bot.user.name}!")
        logger.log(25, f"{len(self.bot.guilds)} Servidores")
        logger.log(25, f"{len(self.bot.shards)} shards")

    @commands.Cog.listener()
    async def on_shard_connect(self, shardid):
        logger.log(35, f"Shard {shardid} Conectado")

    @commands.Cog.listener()
    async def on_disconnect(self):
        logger.error("on_disconnect")

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shardid):
        logger.error(f"Shard {shardid} Desconectado")

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if ctx.interaction:
            command = f"/{ctx.command} {ctx.kwargs}"
        else:
            command = ctx.message.content
        if isinstance(ctx.channel, discord.DMChannel):
            logger.log(25,
                       f"@{ctx.message.author.name}#{ctx.message.author.discriminator} ({ctx.message.author.id}) Corrido "
                       f"'{command}' em mensagens diretas")
        else:
            logger.log(25,
                       f"@{ctx.message.author.name}#{ctx.message.author.discriminator}"
                       f" ({ctx.message.author.display_name}) ({ctx.message.author.id}) "
                       f"executou '{command}' no canal "
                       f"#{ctx.channel.name} ({ctx.channel.id}) no servidor {ctx.guild} ({ctx.guild.id})")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        if message.content.strip() in [f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"]:
            pfx = await prefix_function(self.bot, message, True)
            await message.reply(f"Meu prefixo de comando é `{pfx}`, ou você pode "
                                f"me mencione! Execute `{pfx}ajuda` para obter ajuda do bot.", delete_after=10,
                                mention_author=False)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.interaction:
            command = f"/{ctx.command} {ctx.kwargs}"
        else:
            command = ctx.message.content
        logger.log(35,
                   f"Comando '{command}' por "
                   f"@{ctx.message.author.name}#{ctx.message.author.discriminator} ({ctx.message.author.id}) "
                   f"está completo!")
    # comando aqui


'''
Passos para converter:
@bot.command() -> @commands.hybrid_command()
@bot.listen() -> @commands.Cog.listener()
function(ctx, ...): -> function(self, ctx, ...)
bot -> self.bot
'''
