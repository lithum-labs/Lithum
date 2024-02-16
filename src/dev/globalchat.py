import asyncio
import re

import aiohttp
import discord
from discord import app_commands, Webhook
from discord.ext import commands
import orjson as json
import yaml

from ..lib.mongo import MongoDB

cd = 2


class GlobalChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invite = re.compile(
            "(https?://)?((ptb|canary)\.)?(discord\.(gg|io)|discord(app)?.com/invite)/[0-9a-zA-Z]+",
            re.IGNORECASE,
        )
        self.token = re.compile(
            r"[A-Za-z0-9\-_]{23,30}\.[A-Za-z0-9\-_]{6,7}\.[A-Za-z0-9\-_]{27,40}",
            re.IGNORECASE,
        )
        with open("./config.yml", "r", encoding="utf-8") as f:
            conf = yaml.safe_load(f)
            self.admin = conf["admin"]
            self.client = MongoDB(
                conf["database"]["address"],
                conf["database"]["port"],
                conf["database"]["user"],
                conf["database"]["password"],
            )
            self.db = self.client.selene

    async def mod_msg(self, message: discord.Message):
        if self.db.mutes.get(str(message.author.id)):
            await message.remove_reaction("🔄", message.guild.me)
            await message.add_reaction("❌")
            embed = discord.Embed(
                description="あなたはグローバルチャットで発言できません。",
                colour=discord.Colour.red(),
            )
            embed.add_field(
                name="理由", value=self.db.mutes[str(message.author.id)]["reason"]
            )
            msg = await message.reply(embed=embed)
            await asyncio.sleep(2.5)
            await msg.delete()
            return True
        if self.db.globalchat["lockdown"]:
            await message.remove_reaction("🔄", message.guild.me)
            await message.add_reaction("❌")
            embed = discord.Embed(
                description="現在グローバルチャットはBotの管理者によってロックされています。利用できません。",
                colour=discord.Colour.red(),
            )
            msg = await message.reply(embed=embed)
            await asyncio.sleep(2.5)
            await msg.delete()
            return True
        token = self.token.search(message.content)
        invite = self.invite.search(message.content)
        if token:
            await message.remove_reaction("🔄", message.guild.me)
            await message.add_reaction("❌")
            embed = discord.Embed(
                description="Discordのトークンをグローバルチャットに送信することはできません。",
                colour=discord.Colour.red(),
            )
            msg = await message.reply(embed=embed)
            await asyncio.sleep(2.5)
            await msg.delete()
            return True
        elif invite:
            await message.remove_reaction("🔄", message.guild.me)
            await message.add_reaction("❌")
            embed = discord.Embed(
                description="Discordの招待リンクをグローバルチャットに送信することはできません。",
                colour=discord.Colour.red(),
            )
            msg = await message.reply(embed=embed)
            await asyncio.sleep(2.5)
            await msg.delete()
            return True

    async def send_message(self, url, username, guild, message, avatar, image, stat=""):
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(url, session=session)
            if image is None:
                if message is None:
                    await webhook.send(
                        username="@"
                        + username
                        + "{} | {} (ID: {})".format(stat, guild.name, str(guild.id)),
                        avatar_url=avatar,
                    )
                else:
                    await webhook.send(
                        content=message,
                        username="@"
                        + username
                        + "{} | {} (ID: {})".format(stat, guild.name, str(guild.id)),
                        avatar_url=avatar,
                    )
            else:
                if message is None:
                    await webhook.send(
                        username="@"
                        + username
                        + "{} | {} (ID: {})".format(stat, guild.name, str(guild.id)),
                        avatar_url=avatar,
                        embeds=image,
                    )
                else:
                    await webhook.send(
                        content=message,
                        username="@"
                        + username
                        + "{} | {} (ID: {})".format(stat, guild.name, str(guild.id)),
                        avatar_url=avatar,
                        embeds=image,
                    )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        stat = ""
        if not message.guild:
            return
        if message.author.bot:
            return
        if message.author.id in self.admin:
            stat = " (管理者)"
        try:
            gc_guilds = self.db.globalchat.find_one({"id": str(message.guild.id)})
            if gc_guilds.get(str(message.guild.id)) is None:
                return
            if not gc_guilds["ch"] == message.channel.id:
                return
            await message.add_reaction("🔄")
            if await self.mod_msg(message):
                return
            for i in self.db.globalchat.find():
                if i["id"] == str(message.guild.id):
                    pass
                else:
                    if message.attachments != []:
                        imgs = []
                        limit = 1
                        max_a = len(message.attachments)
                        if max_a >= 5:
                            max_a = "5"
                        else:
                            max_a = str(max_a)
                        for attachments in message.attachments:
                            if limit >= 6:
                                break
                            if attachments.content_type in (
                                "image/jpeg",
                                "image/jpg",
                                "image/png",
                                "image/gif",
                                "image/webp",
                            ):
                                if attachments.width is not None:
                                    embed = discord.Embed(
                                        title="添付ファイル ({}/{})".format(
                                            limit, max_a
                                        )
                                    )
                                    embed.set_image(url=attachments.url)
                                    imgs.append(embed)
                                    limit = limit + 1
                            # discord.Embed(title="あなたは一時的にグローバルチャットへの接続が禁止されています", description="不適切な画像を検知したため、あなたはグローバルチャットから切断されました。\nこの判断が間違いだと思われる場合は、画像とともにサポートサーバーのお問合せからご報告ください。")
                    else:
                        imgs = None

                    await self.send_message(
                        i["url"],
                        message.author.name,
                        message.guild,
                        message.content,
                        message.author.avatar.url,
                        image=imgs,
                        stat=stat,
                    )
            await message.remove_reaction("🔄", message.guild.me)
            await message.add_reaction("✅")
        except KeyError:
            pass

    @app_commands.command(
        name="global",
        description="グローバルチャットを有効にします。既に存在する場合は無効にしてwebhookを削除します。",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(cd, 60)
    @commands.has_permissions(administrator=True)
    async def globalchat(self, interaction: discord.Interaction):
        gc_guilds = self.db.globalchat.find_one({"id": str(interaction.guild.id)})
        await interaction.response.defer()
        if gc_guilds is None:
            wh = await interaction.channel.create_webhook(
                name="Selene GlobalChat", reason="webhook is created by Selene"
            )
            self.globalchat.insert_one(
                {
                    str(interaction.guild.id): {
                        "url": wh.url,
                        "ch": interaction.channel.id,
                    }
                }
            )
            await interaction.followup.send(
                "グローバルチャットに接続しました。", ephemeral=True
            )
        else:
            url = gc_guilds["url"]
            channel = self.bot.get_channel(gc_guilds["ch"])
            channel_webhooks = await channel.webhooks()
            for webhook in channel_webhooks:
                if webhook.url == url:
                    await webhook.delete()
                    self.db.globalchat.delete_one(
                        {"id": str(interaction.guild.id), "url": url}
                    )
                    await interaction.followup.send(
                        "グローバルチャットから切断しました！", ephemeral=True
                    )
                    break


async def setup(bot: commands.Bot):
    with open("./config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        if config["guild"] == []:
            await bot.add_cog(GlobalChat(bot))
        elif config["guild"] is not None:
            guild = []
            for i in config["guild"]:
                guild.append(discord.Object(i))
            await bot.add_cog(GlobalChat(bot), guilds=guild)
