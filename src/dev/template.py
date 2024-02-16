"selene-actions ignore"
import discord
from discord import app_commands
from discord.ext import commands
import yaml


cd = 2


class className(commands.GroupCog, name="cmdname"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="name",
        description="description",
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 60)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def follow(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # 処理
        await interaction.followup.send(
            embed=discord.Embed(title="title"),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    with open("./config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        if config["guild"] == []:
            await bot.add_cog(className(bot))
        elif config["guild"] is not None:
            guild = []
            for i in config["guild"]:
                guild.append(discord.Object(i))
            await bot.add_cog(className(bot), guilds=guild)
