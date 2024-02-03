import asyncio
from time import time

import discord
from discord import app_commands
from discord.ext import commands
import orjson as json
import yaml

from .lib.dispander import dispand, delete_dispand
from .lib.vxtwitter import parse, get_twinf
from .lib.func import func_inter
from .lib.mongo import MongoDB

cd = 2


class server_tool(commands.GroupCog, name="server-setting"):
    def __init__(self, bot: commands.Bot, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot
        with open("./config.yml", "r", encoding="utf-8") as f:
            conf = yaml.safe_load(f)
            self.conf = conf
            self.client = MongoDB(
                conf["database"]["address"],
                conf["database"]["port"],
                conf["database"]["user"],
                conf["database"]["password"],
            )
            self.db = self.client.selene
        self.regex_discord_message_url = (
            "(?!<)https://(ptb.|canary.)?discord(app)?.com/channels/"
            "(?P<guild>[0-9]{18,20})/(?P<channel>[0-9]{18,20})/(?P<message>[0-9]{18,20})(?!>)"
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        settings = await self.db.selene.find_one({"serverId": message.guild.id})
        if message.author.bot and message.embeds:
            if (
                message.author.id == 302050872383242240
                and message.embeds[0].description
            ):
                if (
                    message.embeds[0].description.find("表示順をアップしたよ") != -1
                    or message.embeds[0].description.find("Bump done") != -1
                ):
                    if settings["bump"]:
                        bumptime = time() + 7200
                        embed = discord.Embed(
                            title="bumpを検知",
                            description=f"bumpを検知しました。\n<t:{str(int(bumptime))}:R>に通知します。",
                            color=discord.Colour.blue(),
                        )
                        await message.channel.send(embed=embed)
                        await asyncio.sleep(7200)
                        await message.channel.send(
                            embed=discord.Embed(
                                title="bump通知",
                                description="bumpの時間です！\n</bump:947088344167366698>を実行してサーバーの順位を上げましょう！",
                                color=discord.Colour.blue(),
                            )
                        )
            if message.author.id == 761562078095867916:
                if "をアップしたよ" in message.embeds[0].fields[0].name:
                    if settings["up"]:
                        bumptime = time() + 7200
                        embed = discord.Embed(
                            title="upを検知",
                            description=f"upを検知しました。\n<t:{str(int(bumptime))}:R>に通知します。",
                            color=discord.Colour.blurple(),
                        )
                        await message.channel.send(embed=embed)
                        await asyncio.sleep(3600)
                        await message.channel.send(
                            embed=discord.Embed(
                                title="up通知",
                                description="upの時間です！\n</dissoku up:828002256690610256>を実行してサーバーの順位を上げましょう！",
                                color=discord.Colour.blurple(),
                            )
                        )

        if message.author.bot:
            return
        gd = True
        if not message.guild:
            gd = False
        try:
            if gd:
                if str(message.channel.id) in settings["auto_publish"]["channels"]:
                    if message.channel.type == discord.ChannelType.news:
                        await message.publish()
                        await message.add_reaction("✅")
                    else:
                        print(False)
        except KeyError:
            pass
        try:
            if settings["vxtwitter"]["enable"]:
                urls = await parse(message.content)
                if urls == []:
                    return
                await message.reply(embeds=await get_twinf(urls))
        except KeyError:
            pass
        try:
            if settings["dispander"]["enable"]:
                await dispand(message)
        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await delete_dispand(self.bot, payload=payload)

    @app_commands.command(
        name="expand",
        description="有効の場合、DiscordのメッセージURLが投稿された場合に自動で展開します",
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(cd, 60)
    @app_commands.checks.has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    async def cfg_dispander(self, interaction: discord.Interaction):
        settings = await self.db.selene.find_one({"serverId": interaction.guild.id})
        await interaction.response.defer()
        if settings["dispander"]["enable"]:
            enable = False
            embed = discord.Embed(
                title="", description="メッセージURLの自動展開を**無効**に設定しました"
            )
        else:
            enable = True
            embed = discord.Embed(
                title="", description="メッセージURLの自動展開を**有効**に設定しました"
            )
        await self.db.selene.update_one(
            {"serverId": interaction.guild.id},
            {"$set": {"dispander": {"enable": enable}}},
        )
        if settings["customize"]["name"] is not None:
            if settings["customize"]["avatar"] is not None:
                await interaction.followup.send(
                    embed=embed,
                    avatar_url=settings["customize"]["avatar"],
                    username=settings["customize"]["name"],
                    ephemeral=True,
                )
            await interaction.followup.send(
                embed=embed, avatar_url=settings["customize"]["avatar"], ephemeral=True
            )
            return
        if settings["customize"]["name"] is not None:
            await interaction.followup.send(
                embed=embed, avatar_url=settings["customize"]["avatar"], ephemeral=True
            )
            return
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="vxtwitter",
        description="有効の場合、twitter.com/x.comのURLが投稿された場合に自動で展開します",
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(cd, 60)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.choices(
        status=[
            app_commands.Choice(name="有効化", value="active"),
            app_commands.Choice(name="無効化", value="deactive"),
        ],
        type=[
            app_commands.Choice(name="API", value="api"),
            app_commands.Choice(name="URL", value="url"),
        ],
    )
    @app_commands.describe(
        status="有効/無効を変更できます。",
        type="APIを利用する場合は、URLを表示しないため、見栄えが多少良くなる可能性があります。",
    )
    async def vxtwitter(self, interaction: discord.Interaction, status: str, type: str):
        await interaction.response.defer()
        settings = await self.db.selene.find_one({"serverId": interaction.guild.id})

        if status == "active":
            if settings["vxtwitter"]["enable"]:
                embed = discord.Embed(title="エラー", description="既に有効です。")
                enable = True
            else:
                enable = True
                embed = discord.Embed(
                    title="", description="vxTwitterの自動展開を**有効**に設定しました"
                )
        elif status == "deactive":
            if not settings["vxtwitter"]["enable"]:
                embed = discord.Embed(title="エラー", description="既に無効です。")
                enable = False
            else:
                enable = False
                embed = discord.Embed(
                    title="", description="vxTwitterの自動展開を**無効**に設定しました"
                )
        await self.db.selene.update_one(
            {"serverId": interaction.guild.id},
            {"$set": {"vxtwitter": {"enable": enable}}},
        )
        if settings["customize"]["name"] is not None:
            if settings["customize"]["avatar"] is not None:
                await interaction.followup.send(
                    embed=embed,
                    avatar_url=settings["customize"]["avatar"],
                    username=settings["customize"]["name"],
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                embed=embed, avatar_url=settings["customize"]["avatar"], ephemeral=True
            )
            return
        if settings["customize"]["name"] is not None:
            await interaction.followup.send(
                embed=embed, avatar_url=settings["customize"]["avatar"], ephemeral=True
            )
            return
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="bump",
        description="有効の場合、disboardのbumpを検知し、一定時間経過した際に通知します",
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 60)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.choices(
        status=[
            app_commands.Choice(name="有効化", value="active"),
            app_commands.Choice(name="無効化", value="deactive"),
        ]
    )
    async def cfg_bump(self, interaction: discord.Interaction, status: str):
        await interaction.response.defer()
        settings = await self.db.selene.find_one({"serverId": interaction.guild.id})
        if status == "active":
            if settings["bump"]:
                enable = None
                embed = discord.Embed(title="エラー", description="既に有効です。")
            else:
                enable = True
                embed = discord.Embed(
                    title="", description="bump通知を**有効**に設定しました"
                )
        elif status == "deactive":
            if not settings["bump"]:
                enable = None
                embed = discord.Embed(title="エラー", description="既に無効です。")
            else:
                enable = False
                embed = discord.Embed(
                    title="", description="bump通知を**無効**に設定しました"
                )
        if enable:
            await self.db.selene.update_one(
                {"serverId": interaction.guild.id},
                {"$set": {"bump": enable}},
            )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="up",
        description="有効の場合、ディス速のupを検知し、一定時間経過した際に通知します",
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 60)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.choices(
        status=[
            app_commands.Choice(name="有効化", value="active"),
            app_commands.Choice(name="無効化", value="deactive"),
        ]
    )
    async def cfg_up(self, interaction: discord.Interaction, status: str):
        await interaction.response.defer()
        settings = await self.db.selene.find_one({"serverId": interaction.guild.id})
        if status == "active":
            if settings["up"]:
                enable = None
                embed = discord.Embed(title="エラー", description="既に有効です。")
            else:
                enable = True
                embed = discord.Embed(
                    title="成功", description="up通知を**有効**に設定しました"
                )
        elif status == "deactive":
            if not settings["up"]:
                enable = None
                embed = discord.Embed(title="エラー", description="既に無効です。")
            else:
                enable = False
                embed = discord.Embed(
                    title="成功", description="up通知を**無効**に設定しました"
                )
        if enable:
            await self.db.selene.update_one(
                {"serverId": interaction.guild.id},
                {"$set": {"up": enable}},
            )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="publish",
        description="有効なアナウンスチャンネルでメッセージが送信された場合に自動的に公開します",
    )
    @app_commands.guilds()
    @app_commands.guild_only()
    @app_commands.checks.cooldown(cd, 60)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def publish(self, interaction: discord.Interaction):
        return
        if await func_inter.disable_dm(interaction):
            return
        await interaction.response.defer()
        with open("./data/settings.json", "r") as f:
            cfg = json.loads(f.read())
        try:
            if str(interaction.channel.id) in cfg["auto_publish"]["channels"]:
                cfg["auto_publish"]["channels"].remove(str(interaction.channel.id))
                embed = discord.Embed(title="自動公開を無効にしました。")
            else:
                cfg["auto_publish"]["channels"].append(str(interaction.channel.id))
                embed = discord.Embed(title="自動公開を有効にしました。")
        except KeyError:
            cfg["auto_publish"]["channels"] = [
                str(interaction.channel.id),
            ]
            embed = discord.Embed(title="自動公開を有効にしました。")
        with open("./data/settings.json", "w") as f:
            f.write(json.dumps(cfg).decode("utf-8"))
        await interaction.followup.send(embed=embed, ephemeral=True)


class botConfig(commands.GroupCog, name="bot-setting"):
    def __init__(self, bot: commands.Bot, **kwargs):
        super().__init__(**kwargs)
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
        name="gatekeeper",
        description="ゲートキーパーの有効/無効を切り替えます。",
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 60)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(status="ゲートキーパーの有効/無効を切り替えます。")
    @app_commands.choices(
        status=[
            app_commands.Choice(name="有効化", value="enable"),
            app_commands.Choice(name="無効化", value="disable"),
        ]
    )
    async def gatekeeper(self, interaction: discord.Interaction, status: str = None):
        await interaction.response.defer()
        settings = await self.db.selene.find_one({"serverId": interaction.guild.id})
        embed = discord.Embed(title="", description="", color=0x00FF00)
        if status == "active":
            if settings["sentinel"]["gatekeeper"]["enable"]:
                enable = None
                embed = discord.Embed(title="エラー", description="既に有効です。")
            else:
                enable = True
                embed = discord.Embed(
                    title="成功", description="ゲートキーパーを**有効**に設定しました"
                )
        elif status == "deactive":
            if not settings["sentinel"]["gatekeeper"]["enable"]:
                enable = None
                embed = discord.Embed(title="エラー", description="既に無効です。")
            else:
                enable = False
                embed = discord.Embed(
                    title="成功", description="ゲートキーパーを**無効**に設定しました"
                )
        if enable:
            await self.db.selene.update_one(
                {"serverId": interaction.guild.id},
                {"$set": {"sentinel": {"gatekeeper": {"enable": enable}}}},
            )
        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
        )

    """
    @app_commands.command(
        name="avatar",
        description="Seleneのレスポンスの一部で確認できるカスタムアイコンを設定できます。引数を何も設定しない場合はカスタムアイコンを削除できます。",
    )
    @app_commands.guilds()
    @app_commands.guild_only()
    @app_commands.checks.cooldown(cd, 60)
    @app_commands.checks.has_permissions(manage_nicknames=True, manage_guild=True)
    async def botconfig(self, interaction: discord.Interaction, avatar: str = None):
        await interaction.response.defer()
        settings = await self.db.selene.find_one({"serverId": interaction.guild.id})
        embed = discord.Embed()
        if avatar is None:
            embed.title = "カスタムアバターを削除しました。"
            url = None
            if settings["customize"]["avatar"] is None:
                embed.title = "エラー"
                embed.description = "カスタムアバターが未設定です。"
                embed.color = 0xFF0000
        else:
            pattern = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
            if not re.match(pattern, avatar):
                embed.title = "エラー"
                embed.description = "これは有効なhttpsリンクではありません。"
                embed.color = 0xFF0000
                url = None
            else:
                embed.title = "カスタムアバターを設定しました。"
                url = avatar

        await self.db.selene.update_one(
            {"serverId": interaction.guild.id}, {"$set": {"customize": {"avatar": url}}}
        )
        if url is not None:
            if settings["customize"]["name"] is not None:
                await interaction.followup.send(
                    embed=embed, avatar_url=url, username=settings["customize"]["name"]
                )
            await interaction.followup.send(embed=embed, avatar_url=url)
            return
        if settings["customize"]["name"] is not None:
            await interaction.followup.send(
                embed=embed, username=settings["customize"]["name"]
            )
            return
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="name",
        description="Seleneのレスポンスの一部で確認できる表示名を設定できます。引数を何も設定しない場合は表示名を削除できます。",
    )
    @app_commands.guilds()
    @app_commands.guild_only()
    @app_commands.checks.cooldown(cd, 60)
    @app_commands.checks.has_permissions(manage_nicknames=True, manage_guild=True)
    async def botconfig(self, interaction: discord.Interaction, name: str = None):
        await interaction.response.defer()
        settings = await self.db.selene.find_one({"serverId": interaction.guild.id})
        embed = discord.Embed()
        if name is None:
            embed.title = "カスタムアバターを削除しました。"
            username = None
            if settings["customize"]["avatar"] is None:
                embed.title = "エラー"
                embed.description = "カスタムアバターが未設定です。"
                embed.color = 0xFF0000
        else:
            pattern = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
            if not re.match(pattern, name):
                embed.title = "エラー"
                embed.description = "これは有効なhttpsリンクではありません。"
                embed.color = 0xFF0000
                username = None
            else:
                embed.title = "カスタムアバターを設定しました。"
                username = name

        await self.db.selene.update_one(
            {"serverId": interaction.guild.id},
            {"$set": {"customize": {"name": username}}},
        )
        if username is not None:
            if settings["customize"]["avatar"] is not None:
                await interaction.followup.send(
                    embed=embed,
                    avatar_url=settings["customize"]["avatar"],
                    username=username,
                )
            await interaction.followup.send(
                embed=embed, avatar_url=settings["customize"]["avatar"]
            )
            return
        if settings["customize"]["name"] is not None:
            await interaction.followup.send(
                embed=embed, avatar_url=settings["customize"]["avatar"]
            )
            return
        await interaction.followup.send(embed=embed)
    """


async def setup(bot: commands.Bot):
    with open("./config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        if config["guild"] == []:
            await bot.add_cog(server_tool(bot))
            # await bot.add_cog(botConfig(bot))
        elif config["guild"] is not None:
            guild = []
            for i in config["guild"]:
                guild.append(discord.Object(i))
            await bot.add_cog(server_tool(bot), guilds=guild)
            # await bot.add_cog(botConfig(bot), guilds=guild)
