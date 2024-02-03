import math
import yaml

# import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# import orjson as json
from reactionmenu import ViewMenu, ViewButton

from .lib.convert import UserFlags
from .lib.data import i18n
from .lib.mongo import MongoDB

getText = i18n.getText

"""
class mst_modal(discord.ui.Modal):
    def __init__(self, cid, secret, address, params):
        super().__init__(
            title="Mastodonの認証コードを入力",
            timeout=None,
        )
        self.params = params
        self.address = address
        self.cid = cid
        self.secret = secret

        self.code = discord.ui.InputText(
            label="認証コード",
            style=discord.InputTextStyle.short,
            placeholder="入力...",
            required=True,
        )
        self.add_item(self.code)

    async def callback(self, interaction: discord.Interaction) -> None:
        async with aiohttp.ClientSession() as session:
            await interaction.response.defer()
            try:
                res = await session.post(
                    "https://{}/oauth/authorize?".format(self.address) + self.params,
                    dict(
                        grant_type="authorization_code",
                        redirect_uri="urn:ietf:wg:oauth:2.0:oob",
                        client_id=self.cid,
                        client_secret=self.secret,
                        code=self.code.value,
                    ),
                ).json()
                with open("./data/user.json", "r") as f:
                    uc = json.loads(f.read())
                uc[str(interaction.user.id)]["application"]["mastodon"]["token"] = res[
                    "access_token"
                ]
                await interaction.followup.send(
                    embed=discord.Embed(title="エラー", description="Mastodonとの連携に失敗しました。")
                )
            except:
                await interaction.followup.send(
                    embed=discord.Embed(title="エラー", description="Mastodonとの連携に失敗しました。")
                )
                return
        return
"""

cd = 4
VerificationLevel = discord.VerificationLevel
lang = "en"


class utils(commands.GroupCog, name="tools"):
    def __init__(self, bot: commands.Bot, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot
        self.verification_level = {
            VerificationLevel.none: "unlimited",
            VerificationLevel.low: "Email authentication required",
            VerificationLevel.medium: "Members must authenticate their email and 5 minutes must elapse after account registration.",
            VerificationLevel.high: "Members must authenticate their email and have been in the guild for at least 5 minutes after registering their Discord account and for at least 10 minutes.",
            VerificationLevel.highest: "Members must complete the phone number verification for their Discord account.",
        }
        with open("./config.yml", "r", encoding="utf-8") as f:
            conf = yaml.safe_load(f)
            self.client = MongoDB(
                conf["database"]["address"],
                conf["database"]["port"],
                conf["database"]["user"],
                conf["database"]["password"],
            )
            self.db = self.client.selene

    @app_commands.command(name="guild", description="Retrieve guild information.")
    async def guild(self, interaction: discord.Interaction, guild_id: str):
        await interaction.response.defer()
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
        acolor = discord.Color.default()
        guild: discord.Guild = await self.bot.fetch_guild(int(guild_id))
        title = getText("{servername} information", lang).replace(
            "{servername}", guild.name
        )
        embed = discord.Embed(title=title, color=acolor)
        discriminator = ""
        owner = getText("Unknown", lang)
        owner_id = ""
        if guild.owner is not None:
            owner = guild.owner.name
            owner_id = " (ID:" + guild.owner.id + ")"
            if guild.owner.discriminator is not None:
                if not guild.owner.discriminator == "0":
                    discriminator = "#" + guild.owner.discriminator
        embed.add_field(
            name=getText("Guild Owner", lang), value=owner + discriminator + owner_id
        )

        embed.add_field(
            name=getText("Guild's Member Count", lang), value=str(guild.member_count)
        )
        embed.add_field(
            name=getText("Guild's VerificationLevel", lang),
            value=getText(self.verification_level[guild.verification_level], lang),
        )
        embed.add_field(
            name=getText("Guild's BoostLevel", lang),
            value=getText("level " + str(guild.premium_tier), lang),
        )
        embed.add_field(
            name=getText("Guild's BoostCount", lang),
            value=str(guild.premium_subscription_count),
        )

        times = guild.created_at.timestamp()
        embed.add_field(
            name=getText("creation date", lang), value=f"<t:{math.floor(times)}:R>"
        )

        badges = discord.Embed(title=title, color=acolor)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        menu.add_page(embed)
        menu.add_page(badges)

        menu.add_button(
            ViewButton(
                style=discord.ButtonStyle.primary,
                label=getText("Back", lang),
                custom_id=ViewButton.ID_PREVIOUS_PAGE,
            )
        )
        menu.add_button(
            ViewButton(
                style=discord.ButtonStyle.success,
                label=getText("Next", lang),
                custom_id=ViewButton.ID_NEXT_PAGE,
            )
        )

        await menu.start()

    @app_commands.command(name="user", description="Retrieve user information.")
    async def user(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer()
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
        acolor = discord.Color.default()
        discriminator = ""
        if user.accent_color:
            acolor = user.accent_colour
        if not user.discriminator == "0":
            discriminator = "#" + user.discriminator
        title = getText("{username}'s information").replace(
            "{username}", user.name + discriminator
        )
        embed = discord.Embed(title=title, color=acolor)
        embed.add_field(name=getText("Bot"), value=user.bot)
        times = user.created_at.timestamp()
        embed.add_field(
            name=getText("creation date"), value=f"<t:{math.floor(times)}:R>"
        )
        in_guild = False
        if interaction.guild.get_member(user.id):
            in_guild = True

        embed.add_field(name=getText("Are you on this server?"), value=in_guild)
        badges = discord.Embed(title=title, color=acolor)
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
            badges.set_thumbnail(url=user.avatar.url)
        badges.add_field(name=getText("Badges owned"), value="", inline=False)
        if not user.public_flags.all() == []:
            for i in user.public_flags.all():
                try:
                    badges.add_field(
                        name="",
                        value=UserFlags[i] + " | " + UserFlags["name"][i],
                        inline=False,
                    )
                except KeyError:
                    pass
        else:
            badges.add_field(
                name="", value=getText("This user does not own a badge."), inline=False
            )

        menu.add_page(embed)
        menu.add_page(badges)

        menu.add_button(
            ViewButton(
                style=discord.ButtonStyle.primary,
                label=getText("Back", lang),
                custom_id=ViewButton.ID_PREVIOUS_PAGE,
            )
        )
        menu.add_button(
            ViewButton(
                style=discord.ButtonStyle.success,
                label=getText("Next", lang),
                custom_id=ViewButton.ID_NEXT_PAGE,
            )
        )

        await menu.start()

    """
    @app_commands.command(
        name="mcstatus",
        description="Minecraftサーバーのステータスを取得します",
    )
    @app_commands.choices(
        choices=[
            app_commands.Choice(name="統合版", value="bedrock"),
            app_commands.Choice(name="Java版", value="java"),
        ]
    )
    @app_commands.checks.cooldown(cd, 60)
    async def mcstatus(
        self,
        interaction: discord.Interaction,
        address: str,
        edition=app_commands.Choice[str],
    ):
        await interaction.response.defer()
        if edition == "java":
            server = await JavaServer.async_lookup(address)
            status = await server.async_status()
            file = discord.File(
                io.BytesIO(base64.b64decode(status.icon)), filename="mcicon"
            )
            embed = discord.Embed(title="{}のサーバー情報".format(address))
            embed.set_thumbnail(url="attachment://{}".format())
            embed.add_field(name="")

    
    @app_commands.command(
        name="connect",
        description="/tools userで表示されるソーシャルアカウントを追加します。",
    )
    @app_commands.choices(
        choices=[
            app_commands.Choice(name="Mastodon", value="mst"),
            app_commands.Choice(name="Misskey", value="msk"),
        ]
    )
    @app_commands.describe(address="インスタンスのアドレス")
    @app_commands.checks.cooldown(cd, 60)
    async def connect(
        self,
        interaction: discord.Interaction,
        address,
        application=app_commands.Choice[str],
    ):
        await interaction.response.defer()
        if application == "mst":
            with open("./data/mst_server.json", "r") as f:
                servers = json.loads(f.read())
                if servers.get(address) is not None:
                    async with aiohttp.ClientSession() as session:
                        resp = await session.post(
                            "https://{}/api/v1/apps".format(address),
                            dict(
                                client_name="IceCube Mastodon Integration",
                                redirect_uris="urn:ietf:wg:oauth:2.0:oob",
                                scopes="read",
                            ),
                        ).json()
                        cid = resp["client_id"]
                        secret = resp["client_secret"]
                        params = urlencode(dict(
                            client_id=cid,
                            response_type="code",
                            redirect_uri="urn:ietf:wg:oauth:2.0:oob",   # ブラウザ上にcode表示
                            scope="read"
                        ))
                        await interaction.followup.send("連携を完了するには、以下のURLから認証後、下のボタンを押してコピーしたコードを入力してください。", modal=mst_modal(cid, secret, address, params))
    """


async def setup(bot: commands.Bot):
    with open("./config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        if config["guild"] == []:
            await bot.add_cog(utils(bot))
        elif config["guild"] is not None:
            guild = []
            for i in config["guild"]:
                guild.append(discord.Object(i))
            await bot.add_cog(utils(bot), guilds=guild)
