import os

import aiohttp
import websockets
import discord
from discord.ext import commands
from discord import app_commands
import orjson as json
import yaml

from src.lib.logger import log
from ..lib.mongo import MongoDB


class eew(app_commands.Group):
    def __init__(self, bot: commands.Bot, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot
        self.logger = log.getlogger()
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

    @commands.Cog.listener()
    async def on_ready(self):
        color = {
                                "10": 0x3C5A82,
                                "20": 0x1E82E6,
                                "30": 0x78E6DC,
                                "40": 0xFFFF96,
                                "50": 0xFFD200,
                                "55": 0xFF9600,
                                "60": 0xF03200,
                                "65": 0xBE0000,
                                "70": 0x8C0028,
        }
        scale = {
                                "10": "震度1",
                                "20": "震度2",
                                "30": "震度3",
                                "40": "震度4",
                                "50": "震度5弱",
            "55": "震度5強",
            "60": "震度6弱",
            "65": "震度6強",
            "70": "震度7",
        }
        self.logger.info("connecting P2PQuake Websocket...")
        async for connection in websockets.connect("wss://api.p2pquake.net/v2/ws"):
            try:
                while True:
                    recv = await connection.recv()
                    embed = discord.Embed()
                    if recv["code"] == "551":
                        if (
                            recv["earthquake"]["hypocenter"]["depth"] <= -1
                            or recv["earthquake"]["hypocenter"]["magnitude"] <= -1
                        ):  # まれにあり得ない数値の場合がある
                            pass
                        else:
                            color = {
                                "10": 0x3C5A82,
                                "20": 0x1E82E6,
                                "30": 0x78E6DC,
                                "40": 0xFFFF96,
                                "50": 0xFFD200,
                                "55": 0xFF9600,
                                "60": 0xF03200,
                                "65": 0xBE0000,
                                "70": 0x8C0028,
                            }
                            scale = {
                                "10": "震度1",
                                "20": "震度2",
                                "30": "震度3",
                                "40": "震度4",
                                "50": "震度5弱",
                                "55": "震度5強",
                                "60": "震度6弱",
                                "65": "震度6強",
                                "70": "震度7",
                            }
                            if recv["earthquake"]["domesticTsunami"] == "None":
                                tsunami = "この地震による津波の心配はありません。"
                            elif recv["earthquake"]["domesticTsunami"] == "Warning":
                                tsunami = "現在、津波警報が発表されている可能性があります。"
                            embed.title = "地震情報"
                            embed.description = (
                                "{}頃、{}で最大{}の地震が発生しました。\nマグニチュードは{}、震源の深さは{}kmと推定されています。\n{}".format(
                                    recv["earthquake"]["time"],
                                    recv["earthquake"]["hypocenter"]["name"],
                                    scale[recv["earthquake"]["maxScale"]],
                                    recv["earthquake"]["hypocenter"]["magnitude"],
                                    recv["earthquake"]["hypocenter"]["depth"],
                                    tsunami
                                )
                            )
                            embed.color = color[recv["earthquake"]["maxScale"]]
                            embed.footer(
                                "この地震情報は不正確な場合があります。 ソース: {}".format(
                                    recv["issue"]["source"]
                                )
                            )
                            async with aiohttp.ClientSession() as session:
                                for servers in self.db.eew_servers.find():
                                    webhook = discord.Webhook.from_url(servers["url"], session=session)
                                    await webhook.send(embed=embed, username="Selene Earthquake Early Warning", avatar_url=self.bot.user.avatar.url)
                    if recv["code"] == "556":
                        if (
                            recv["earthquake"]["hypocenter"]["depth"] <= -1
                            or recv["earthquake"]["hypocenter"]["magnitude"] <= -1
                        ):  # まれにあり得ない数値の場合がある
                            pass
                        else:
                            if recv["earthquake"]["domesticTsunami"] == "None":
                                tsunami = "この地震による津波の心配はありません。"
                            elif recv["earthquake"]["domesticTsunami"] == "Warning":
                                tsunami = "現在、津波警報が発表されている可能性があります。"
                            embed.title = "地震情報"
                            embed.description = (
                                "{}頃、{}で最大{}の地震が発生しました。\nマグニチュードは{}、震源の深さは{}kmと推定されています。\n{}".format(
                                    recv["earthquake"]["time"],
                                    recv["earthquake"]["hypocenter"]["name"],
                                    scale[recv["earthquake"]["maxScale"]],
                                    recv["earthquake"]["hypocenter"]["magnitude"],
                                    recv["earthquake"]["hypocenter"]["depth"],
                                    tsunami
                                )
                            )
                            embed.color = color[recv["earthquake"]["maxScale"]]
                            embed.footer(
                                "この地震情報は不正確な場合があります。 ソース: {}".format(
                                    recv["issue"]["source"]
                                )
                            )
                            async with aiohttp.ClientSession() as session:
                                for servers in self.db.eew_servers.find():
                                    webhook = discord.Webhook.from_url(servers["url"], session=session)
                                    await webhook.send(embed=embed, username="Selene Earthquake Early Warning", avatar_url=self.bot.user.avatar.url)
            except websockets.ConnectionClosed:
                continue

    @app_commands.command(
        name="regist", description="このチャンネルで地震情報を受信します。"
    )
    async def regist(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not os.path.isfile("./data/eew/{}.json".format(str(interaction.guild.id))):
            with open(
                "./data/eew/{}.json".format(str(interaction.guild.id)),
                "r",
                encoding="utf-8",
            ) as f:
                eew_servers = json.loads(f.read())
                wh = await interaction.channel.create_webhook("IceCube EEW Service")
                eew_servers[str(interaction.guild.id)] = {
                    "minScale": 40,
                    "image": False,
                    "channel": {"id": interaction.channel.id, "webhook": wh.url},
                }
                with open(
                    "./data/eew/{}.json".format(str(interaction.guild.id)),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(json.dumps(eew_servers).decode("utf-8"))
                embed = discord.Embed(title="OK", description="登録しました。")
        else:
            embed = discord.Embed(title="エラー", description="既に設定されています。")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    bot.tree.add_command(
        eew(bot, name="earthquake", description="地震情報に関する設定")
    )
