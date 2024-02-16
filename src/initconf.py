import discord
from discord.ext import commands
import yaml

from .lib.mongo import MongoDB


class initconf(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("./config.yml", "r", encoding="utf-8") as f:
            conf = yaml.safe_load(f)
            self.client = MongoDB(
                conf["database"]["address"],
                conf["database"]["port"],
                conf["database"]["user"],
                conf["database"]["password"],
            )
            self.db = self.client.selene

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        server = self.db.selene
        tts = self.db.tts
        if not await tts.find_one({"serverId": guild.id}):
            await tts.insert_one({"serverId": guild.id})
        if not await server.find_one({"serverId": guild.id}):
            await server.insert_one(
                {
                    "serverId": guild.id,
                    "bump": True,
                    "up": True,
                    "auto_publish": {"channels": []},
#                     "vxtwitter": {"enable": True},
                    "dispander": {"enable": True},
                    "customize": {"avatar": None, "name": None},
                }
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(initconf(bot))
