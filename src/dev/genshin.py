"selene-actions ignore"


import discord
from discord import app_commands
from discord.ext import commands


cd = 4


class genshin(commands.GroupCog, name="genshin"):
    def __init__(self, bot: commands.Bot, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot

    @app_commands.command(name="user", description="ユーザー情報を取得します。")
    async def user(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer()
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(genshin(bot), guilds=[discord.Object(id=961559815191134229)])
