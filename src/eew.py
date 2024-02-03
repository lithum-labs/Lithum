import os

import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
import orjson as json


class eew(app_commands.Group):
    def __init__(self, bot: commands.Bot, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot
        self.session = aiohttp.ClientSession()

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
