import yaml

import discord
from discord import app_commands
from discord.ext import commands

from .lib.data import i18n
from .lib.mongo import MongoDB

root = []
getText = i18n.getText


class manage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("config.yml", "r", encoding="utf-8") as f:
            self.conf = yaml.safe_load(f)
            self.client = MongoDB(
                self.conf["database"]["address"], self.conf["database"]["port"]
            )
            self.db = self.client.selene

    """
    @app_commands.command(name="sudo", description=getText("Promoted to root"))
    async def publish(self, interaction: discord.Interaction):
        if interaction.user.id in root:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="rootを終了しました。",
                ),
                ephemeral=True,
            )
        else:
            if interaction.user.id in self.conf["admin"]:
                root.append(interaction.user.id)
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="rootに昇格しました",
                        description="あなたはシステム管理者から通常の講習を受けたはずです。\nこれは通常、以下の3点に要約されます:\n\n    #1) 他人のプライバシーを尊重すること。\n    #2) タイプする前に考えること。\n    #3) 大いなる力には大いなる責任が伴うこと。",
                    ),
                    ephemeral=True,
                )
    """

    @app_commands.command(
        name="sync",
        description=getText("(administrative commands) Synchronize Bot commands."),
    )
    async def sync(self, interaction: discord.Interaction):
        if interaction.user.id in self.conf["admin"]:
            await interaction.response.defer()
            await self.bot.tree.sync(guild=discord.Object(1192514910505156728))
            await interaction.followup.send("tree synced.", ephemeral=True)
        else:
            await interaction.followup.send(
                getText("Unable to run due to lack of required permissions (`dev`)"),
                ephemeral=True,
            )

    @app_commands.command(
        name="mute", description=getText("(administrative commands) mute user")
    )
    async def mute(
        self, interaction: discord.Interaction, member: discord.Member, reason: str
    ):
        if interaction.user.id in self.conf["admin"]:
            await interaction.response.defer()
            if self.db.mutes.get(str(member.id)) is None:
                await self.db.mutes.insert_one({"id": str(member.id), "reason": reason})
            await interaction.followup.send("muteしました。", ephemeral=True)
        else:
            await interaction.followup.send(
                getText("Unable to run due to lack of required permissions (`dev`)"),
                ephemeral=True,
            )

    @app_commands.command(
        name="leave", description=getText("(administrative commands) leave server")
    )
    async def leave(self, interaction: discord.Interaction, id: str, reason: str):
        embed = discord.Embed()
        if interaction.user.id in self.conf["admin"]:
            await interaction.response.defer()
            try:
                await self.bot.leave_guild(int(id))
            except ValueError:
                embed.title = "400 Bad Request"
                embed.description = "IDに不正な文字が含まれています"
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            await interaction.followup.send(embed, ephemeral=True)
        else:
            embed.title = "403 forbidden"
            embed.description = getText(
                "Unable to run due to lack of required permissions (`admin`)"
            )
            await interaction.response.send_message(
                embed,
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    with open("./config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    await bot.add_cog(
        manage(bot), guilds=[discord.Object(id=config["admin_guild"]["id"])]
    )
