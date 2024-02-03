import discord
from discord import app_commands
from discord.ext import commands
import yaml

from ..lib.data import i18n

getText = i18n.getText

cd = 2


class auth(commands.GroupCog, name="auth"):
    def __init__(self, bot):
        self.bot = bot
        with open("./data/info.yml", "r", encoding="utf-8") as r:
            self.info = yaml.safe_load(r)

    @app_commands.command(
        name="setup",
        description="認証パネルを設置します",
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 60)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def follow(self, interaction: discord.Interaction):
        await interaction.response.defer()
        announcementChannel = self.bot.get_channel(962656965044109342)
        await announcementChannel.follow(destination=interaction.channel, reason=None)
        await interaction.followup.send(
            embed=discord.Embed(title=getText("Followed Announcement Channel.")),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    with open("./config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        if config["guild"] == []:
            await bot.add_cog(auth(bot))
        elif config["guild"] is not None:
            guild = []
            for i in config["guild"]:
                guild.append(discord.Object(i))
            await bot.add_cog(auth(bot), guilds=guild)
