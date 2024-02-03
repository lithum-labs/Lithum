"selene-actions ignore"
import discord
from discord import app_commands
from discord.ext import commands
import yaml

from ..lib.mongo import MongoDB

cd = 2


class auth(commands.GroupCog, name="automod"):
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

    @app_commands.command(
        name="setup",
        description="automodを自動で設定します。",
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 60)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def am_setup(self, interaction: discord.Interaction):
        await interaction.response.defer()
        amra = discord.AutoModRuleAction
        amra.type = discord.AutoModRuleActionType.block_message
        await interaction.guild.create_automod_rule(
            name="Discord認証トークンの削除",
            event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(
                regex_patterns=[
                    r"[A-Za-z0-9\-_]{23,30}\.[A-Za-z0-9\-_]{6,7}\.[A-Za-z0-9\-_]{27,40}"
                ]
            ),
            actions=[amra],
        )
        await interaction.followup.send(
            embed=discord.Embed(title="title"),
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
