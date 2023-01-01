import discordlists
from discord.ext import commands

import config


class DiscordListsPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = discordlists.Client(self.bot)  # Create a Client instance
        if config.bot_list_data:
            for k, v in config.bot_list_data.items():
                if "token" in v and v["token"]:
                    self.api.set_auth(k, v["token"])
        self.api.start_loop()  # Posts the server count automatically every 30 minutes

    @commands.hybrid_command(hidden=True)
    @commands.is_owner()
    async def post(self, ctx: commands.Context):
        """
        Posta manualmente a contagem de servidor usando discordlists.py (BotBlock)
        """
        try:
            result = await self.api.post_count()
        except Exception as e:
            await ctx.send(f"Falha na solicitação: `{e}`")
            return

        await ctx.send("Contagem de servidor postada manualmente com sucesso ({:,}) para {:,} listas."
                       "\nFalha ao postar a contagem de servidores nas listas {:,}.".format(self.api.server_count,
                                                                             len(result["success"].keys()),
                                                                             len(result["failure"].keys())))
