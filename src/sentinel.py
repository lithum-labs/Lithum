import datetime

import discord
from discord import app_commands
from discord.ext import commands
import yaml

from .lib.mongo import MongoDB

cd = 2


class sentinel(commands.GroupCog, name="sentinel"):
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
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        settings = await self.db.selene.find_one({"serverId": member.guild.id})
        if settings["sentinel"]["gatekeeper"]["enable"]:
            now_dt = datetime.datetime.now().strftime("%Y%m%d")
            birth_dt = member.created_at.strftime("%Y%m%d")
            now = datetime.datetime.strptime(now_dt, "%Y%m%d").date()
            birth = datetime.datetime.strptime(birth_dt, "%Y%m%d").date()
            if now - birth <= settings["sentinel"]["gatekeeper"]["date"]:
                dm = await member.create_dm()
                await dm.send(
                    f"あなたはDiscordに登録して{str(settings["sentinel"]["gatekeeper"]["date"])}日以下のため、このサーバーからkickされました。"
                )

    @app_commands.command(
        name="gatekeeper",
        description="参加したユーザーがにDiscord登録までの日数が指定された日数以下の場合にメッセージを送信してkickします。",
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 60)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(date="日数 (数字のみ/1か月(30)以上は設定不可)")
    async def gatekeeper(self, interaction: discord.Interaction, date: int):
        await interaction.response.defer()
        embed = discord.Embed(title="", description="", color=0x00FF00)
        if date >= 30:
            embed.title = "エラー"
            embed.description = "30日以上に設定することはできません。"
            embed.color = 0xFF0000
            dt = None
        else:
            embed.title = "設定完了"
            embed.description = (
                "Discordに登録してから`{}`日以下のアカウントはkickされます".format(date)
            )
            dt = date
        if dt:
            await self.db.selene.update_one(
                {"serverId": interaction.guild.id},
                {"$set": {"sentinel": {"gatekeeper": {"date": dt}}}},
            )
        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    with open("./config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        if config["guild"] == []:
            await bot.add_cog(sentinel(bot))
        elif config["guild"] is not None:
            guild = []
            for i in config["guild"]:
                guild.append(discord.Object(i))
            await bot.add_cog(sentinel(bot), guilds=guild)
