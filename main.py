import asyncio
import os
import statistics
import math
import logging

import discord
from discord.ext import commands
from discord_ext_help import helpExtension, command_list, options

import yaml

from src.error import handler
from src.lib.logger import log

with open("config.yml", "r", encoding="utf-8") as f:
    conf = yaml.safe_load(f)
    log_ = log()
    logger = log_.getlogger()
    if conf["debug"]:
        prefix = conf["bot"]["prefix_debug"]
        log_.logger.setLevel(logging.DEBUG)
        logger.info(
            "It is currently operating in development mode! Please set debug in config.yml to false in the production environment!"
        )
        token = conf["token_debug"]
    else:
        prefix = conf["bot"]["prefix"]
        log_.logger.setLevel(logging.INFO)
        token = conf["token"]
os.environ["PATH"] += os.pathsep + conf["ffmpeg"]


class Bot(commands.AutoShardedBot):
    async def is_owner(self, user: discord.User):
        if user.id in conf["admin"]:
            return True
        return await super().is_owner(user)


bot = Bot(command_prefix=prefix, intents=discord.Intents.all(), help_command=None)

with open("./data/commands.yml", "r", encoding="utf-8") as help:
    command = yaml.safe_load(help)
    command_list.cmdlist = command["help"]

    options.botname = "Lithum"
    options.description = "コマンド一覧を表示します。"
    options.embed_title = "コマンド一覧"
    options.embed_desc = ""
    options.cmd_desc = "{cmdname}の説明"
    options.optional = "任意"
    options.required = "必須"
    options.args_desc = "指定したコマンドの詳細な使用法を表示します。"
    options.nodesc = "このコマンドについての説明はありません。"
    options.nodesc_args = "この引数についての説明はありません。"

    helpExtension.setup()


@bot.tree.error
async def on_error(
    interaction: discord.Interaction, error: discord.app_commands.AppCommandError
) -> None:
    await handler(bot=bot, interaction=interaction, error=error)


@bot.event
async def on_ready():
    logger.info("logged in: {}".format(bot.user.name))
    while True:
        servers = str("{:,}".format(int(len(bot.guilds))))
        await bot.change_presence(
            activity=discord.Activity(
                name="/help | {} servers".format(servers),
                type=discord.ActivityType.playing,
            ),
            status=discord.Status.dnd,
        )
        await asyncio.sleep(15)
        servers = str("{:,}".format(int(len(bot.guilds))))
        users = str("{:,}".format(int(len(bot.users))))
        await bot.change_presence(
            activity=discord.Activity(
                name="{} servers | {} users".format(servers, users),
                type=discord.ActivityType.playing,
            ),
            status=discord.Status.dnd,
        )
        pings = []
        for i in range(15):
            raw = bot.latency
            ping = round(raw * 1000)
            pings.append(ping)
            await asyncio.sleep(1)
        users = str("{:,}".format(int(len(bot.users))))
        ping = str(math.floor(statistics.mean(pings)))
        await bot.change_presence(
            activity=discord.Activity(
                name="{} users | ping: {}ms".format(users, ping),
                type=discord.ActivityType.playing,
            ),
            status=discord.Status.dnd,
        )
        await asyncio.sleep(15)


@bot.event
async def setup_hook():
    await bot.load_extension("jishaku")
    for file in os.listdir("./src"):
        if os.path.isfile(os.path.join("./src", file)):
            if file.endswith(".py"):
                await bot.load_extension(f"src.{file[:-3]}")
                logger.info("loaded extension: " + f"src.{file[:-3]}")
    if conf["debug"]:
        for file in os.listdir("./src/dev"):
            if os.path.isfile(os.path.join("./src/dev", file)):
                if file.endswith(".py"):
                    await bot.load_extension(f"src.dev.{file[:-3]}")
                    logger.info("loaded extension: " + f"src.dev.{file[:-3]}")

    await bot.tree.sync()
    logger.info("tree synced.")


bot.run(token)
bot.get_channel().follow()
