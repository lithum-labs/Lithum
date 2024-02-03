"selene-actions ignore"
import asyncio
from collections import defaultdict, deque
import random
import os
import re
import wave
import yaml

import discord
from discord.ui import Select, View
from discord.ext import commands
from discord import app_commands
import orjson as json
from sqids import Sqids

from voicevox import Client


class SelectView(View):
    @discord.ui.select(cls=Select, placeholder="this is placeholder")
    async def selectMenu(self, interaction: discord.Interaction, select: Select):
        await interaction.response.send_message(f"You selected {select.values}")


class voice_config(commands.GroupCog, name="voice-settings"):
    def __init__(self, bot: commands.Bot, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot

    @app_commands.command(
        name="show", description="このサーバーの読み上げ設定を表示します"
    )
    @app_commands.describe(kaki="書き方", yomi="読み方")
    @app_commands.checks.cooldown(4, 60)
    async def show(self, interaction: discord.Interaction, yomi: str, kaki: str):
        await interaction.response.defer()
        view = SelectView()
        view.selectMenu.add_option(
            label="user can see this",
            value="user can not see this",
            description="this is description",
        )
        if os.path.isfile(f"./data/tts/dict/{interaction.user.id}.json"):
            with open(
                "./data/tts/userconf/{}.json".format(interaction.user.id),
                "r",
                encoding="utf-8",
            ) as f:
                dictionary = json.loads(f.read())
        else:
            dictionary = {}
        with open(
            "./data/tts/userconf/{}.json".format(interaction.user.id),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(json.dumps(dictionary).decode("utf-8"))
        await interaction.followup.send(
            embed=discord.Embed(
                title="辞書にテキストを追加しました。",
                description="{}の読み: {}".format(kaki, yomi),
            )
        )

    @app_commands.command(name="add-dict", description="辞書にテキストを追加します")
    @app_commands.describe(kaki="書き方", yomi="読み方")
    @app_commands.checks.cooldown(4, 60)
    async def addDict(self, interaction: discord.Interaction, yomi: str, kaki: str):
        await interaction.response.defer()
        with open(
            "./data/tts/dict/{}.json".format(interaction.guild.id),
            "r",
            encoding="utf-8",
        ) as f:
            dictionary = json.loads(f.read())
        dictionary[kaki] = yomi
        with open(
            "./data/tts/dict/{}.json".format(interaction.guild.id),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(json.dumps(dictionary).decode("utf-8"))
        await interaction.followup.send(
            embed=discord.Embed(
                title="辞書にテキストを追加しました。",
                description="{}の読み: {}".format(kaki, yomi),
            )
        )

    @app_commands.command(
        name="delete-dict", description="辞書からテキストを削除します"
    )
    @app_commands.describe(kaki="書き方")
    @app_commands.checks.cooldown(4, 60)
    async def delDict(self, interaction: discord.Interaction, kaki: str):
        await interaction.response.defer()
        try:
            with open(
                "./data/tts/dict/{}.json".format(interaction.guild.id),
                "r",
                encoding="utf-8",
            ) as f:
                dictionary = json.loads(f.read())
            dictionary.pop(kaki)
            with open(
                "./data/tts/dict/{}.json".format(interaction.guild.id),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(json.dumps(dictionary).decode("utf-8"))
        except KeyError:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="エラー",
                    description="指定されたテキスト「**{}**」は登録されていません。".format(
                        kaki
                    ),
                    color=0xFF0000,
                )
            )
            return
        await interaction.followup.send(
            embed=discord.Embed(
                title="辞書からテキストを削除しました。",
                description="削除したテキスト: {}".format(kaki),
            )
        )


class tts(commands.GroupCog, name="tts"):
    def __init__(self, bot: commands.Bot, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot
        self.vc_channels = {}
        self.queue_dict = defaultdict(deque)
        with open("config.yml", "r") as f:
            conf = yaml.safe_load(f)
            self.ffmpeg = conf["ffmpeg"]

    async def enqueue(self, voice_client, guild, source):
        queue = self.queue_dict[guild.id]
        queue.append(source)
        if not voice_client.is_playing():
            await self.play(voice_client, queue)

    async def play(self, voice_client, queue):
        if not queue or voice_client.is_playing():
            return
        source = queue.popleft()
        voice_client.play(
            source, after=lambda e: asyncio.run(self.play(voice_client, queue))
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        sqids = Sqids()
        if message.author.bot:
            return
        if (
            self.vc_channels.get(str(message.guild.id)) is None
            or self.vc_channels.get(str(message.guild.id)) == {}
        ):
            return
        read_msg = message.content
        with open("./data/tts/dict/default.json", "r", encoding="utf-8") as f:
            dct = json.loads(f.read())
        rl = []
        for i, t_y in enumerate(dct.items()):
            read_msg = read_msg.replace(t_y[0], "{" + str(i) + "}")
            rl.append(t_y[1])
        read_msg = read_msg.format(*rl)
        if os.path.isfile(f"./data/tts/dict/{message.guild.id}.json"):
            with open(
                f"./data/tts/dict/{message.guild.id}.json", "r", encoding="utf-8"
            ) as f:
                dct = json.loads(f.read())
            rl = []
            for i, t_y in enumerate(dct.items()):
                read_msg = read_msg.replace(t_y[0], "{" + str(i) + "}")
                rl.append(t_y[1])
            read_msg = read_msg.format(*rl)
        read_msg = re.sub(r"https?://.*?\s|https?://.*?$", "URL", read_msg)
        read_msg = re.sub(r"\|\|.*?\|\|", "スポイラー", read_msg)
        if "<@" and ">" in message.content:
            Temp = re.findall("<@!?([0-9]+)>", message.content)
            for i in range(len(Temp)):
                Temp[i] = int(Temp[i])
                user = message.guild.get_member(Temp[i])
                read_msg = re.sub(
                    f"<@!?{Temp[i]}>", "あっとまーく" + user.display_name, read_msg
                )
        read_msg = re.sub(r"<:(.*?):[0-9]+>", r"\1", read_msg)
        read_msg = re.sub(r"\*(.*?)\*", r"\1", read_msg)
        read_msg = re.sub(r"_(.*?)_", r"\1", read_msg)
        fname = sqids.encode([message.author.id, int(random.randint(0, 100))])
        if os.path.isfile(f"./data/tts/userconf/{message.author.id}.json"):
            with open(
                f"./data/tts/userconf/{message.author.id}.json", "r", encoding="utf-8"
            ) as f:
                ucfg = json.loads(f.read())
                if ucfg["speaker"] is not None:
                    speaker = ucfg["speaker"]
                else:
                    speaker = 3
        else:
            speaker = 3
        async with Client() as client:
            audio_query = await client.create_audio_query(read_msg, speaker=speaker)
            with open("./temp/tts/{}.wav".format(fname), "wb") as f:
                f.write(await audio_query.synthesis(speaker=speaker))
        await self.enqueue(
            message.guild.voice_client,
            message.guild,
            discord.FFmpegPCMAudio(
                "./temp/tts/{}.wav".format(fname),
                options="-af atempo=" + str(100 / 100),
                executable=self.ffmpeg,
            ),
        )
        with wave.open("./temp/tts/{}.wav".format(fname), "rb") as f:
            wave_length = f.getnframes() / f.getframerate() / (100 / 100)
            await asyncio.sleep(wave_length + 10)
            os.remove("./temp/tts/{}.wav".format(fname))

    @app_commands.command(name="c", description="読み上げを開始します")
    @app_commands.checks.cooldown(4, 60)
    async def c(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.voice is None:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="エラー",
                    description="あなたはボイスチャンネルに接続していません。",
                    color=0xFF0000,
                )
            )
            return
        if interaction.guild.voice_client is not None:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="エラー",
                    description="既にボイスチャンネルに接続しています。",
                    color=0xFF0000,
                )
            )
            return
        vc = await interaction.user.voice.channel.connect()
        self.vc_channels[str(interaction.guild.id)] = {}
        self.vc_channels[str(interaction.guild.id)]["vc"] = vc
        self.vc_channels[str(interaction.guild.id)][
            "tts_channel"
        ] = interaction.channel.id
        await interaction.followup.send(
            embed=discord.Embed(
                title="接続しました！",
                description="**tips**: ボイスチャンネルからBotを切断させたい場合は</tts dc:1186687747457560596>で切断できます。",
            )
        )

    @app_commands.command(name="mv", description="接続するボイスチャンネルを変更します")
    @app_commands.checks.cooldown(4, 60)
    async def mv(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.voice is None:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="エラー",
                    description="あなたはボイスチャンネルに接続していません。",
                    color=0xFF0000,
                )
            )
            return
        if interaction.guild.voice_client is None:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="エラー",
                    description="Botがボイスチャンネルに接続されていません。",
                    color=0xFF0000,
                )
            )
            return
        await interaction.guild.voice_client.disconnect()
        vc = await interaction.user.voice.channel.connect()
        self.vc_channels[str(interaction.guild.id)] = {}
        self.vc_channels[str(interaction.guild.id)]["vc"] = vc
        self.vc_channels[str(interaction.guild.id)][
            "tts_channel"
        ] = interaction.channel.id
        await interaction.followup.send(
            embed=discord.Embed(
                title="接続しました！",
                description="**tips**: ボイスチャンネルからBotを切断させたい場合は</tts dc:1186687747457560596>で切断できます。",
            )
        )

    @app_commands.command(name="dc", description="読み上げを終了します")
    @app_commands.checks.cooldown(4, 60)
    async def dc(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild.voice_client is None:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="エラー",
                    description="Botがボイスチャンネルに接続されていません。",
                    color=0xFF0000,
                )
            )
            return
        await interaction.guild.voice_client.disconnect()
        embed = discord.Embed(title="切断しました", description="")
        try:
            self.vc_channels[str(interaction.guild.id)] = {}
        except KeyError:
            pass
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(voice_config(bot))
    await bot.add_cog(tts(bot))
