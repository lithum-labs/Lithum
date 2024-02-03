import traceback
import math

import discord
from discord import app_commands
from discord.ext import commands
import yaml

from .lib.func import PERMISSIONS
from .lib.logger import log

logger = log().getlogger()
with open("./config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


class ExceptionHandler(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error) -> None:
        if ctx.interaction is None:
            if isinstance(error, commands.CommandNotFound):
                embed = discord.Embed(
                    title="404 Not Found",
                    description=f"入力されたコマンド「**{ctx.message.content}**」は存在しませんでした。\n入力ミスなどがないかご確認ください。",
                )
            elif isinstance(error, commands.NotOwner):
                embed = discord.Embed(
                    title="404 Not Found",
                    description=f"入力されたコマンド「**{ctx.message.content}**」は存在しませんでした。\n入力ミスなどがないかご確認ください。",
                )
            elif isinstance(error, commands.MissingRequiredArgument):
                embed = discord.Embed(
                    title="400 Bad Request",
                    description="引数が不足しています。\nヘルプコマンドで引数を確認してください。",
                )
            elif isinstance(error, commands.TooManyArguments):
                embed = discord.Embed(
                    title="400 Bad Request",
                    description="過剰な引数が渡されました。\nヘルプコマンドで引数を確認してください。",
                )
            elif isinstance(error, commands.CommandOnCooldown):
                embed = discord.Embed(
                    title="429 Too Many Requests",
                    description=f"コマンドの連続実行数の制限に達しました。\n{error.retry_after}秒後に再試行できます。",
                )
            elif isinstance(error, commands.MissingPermissions):
                embed = discord.Embed(
                    title="403 Forbidden",
                    description="実行者の権限が不足しています。\n以下の権限を取得して再試行してください。\n"
                    + ", ".join(
                        f"`{PERMISSIONS.get(name)}`"
                        for name in error.missing_permissions
                    ),
                )
            elif isinstance(error, commands.BotMissingPermissions):
                embed = discord.Embed(
                    title="403 Forbidden",
                    description="botの権限が不足しています。\n以下の権限を付与して再試行してください。\n"
                    + ", ".join(
                        f"`{PERMISSIONS.get(name)}`"
                        for name in error.missing_permissions
                    ),
                )
            elif isinstance(error, commands.BadArgument):
                if isinstance(error, commands.MessageNotFound):
                    embed = discord.Embed(
                        title="404 Not Found",
                        description="指定されたメッセージは存在しませんでした。\n入力ミスなどがないかご確認ください。",
                    )
                elif isinstance(error, commands.RoleNotFound):
                    embed = discord.Embed(
                        title="404 Not Found",
                        description="指定されたロールは存在しませんでした。\n入力ミスなどがないかご確認ください。",
                    )
                elif isinstance(error, commands.UserNotFound):
                    embed = discord.Embed(
                        title="404 Not Found",
                        description="指定されたユーザーは存在しませんでした。\n入力ミスなどがないかご確認ください。",
                    )
                elif isinstance(error, commands.GuildNotFound):
                    embed = discord.Embed(
                        title="404 Not Found",
                        description="指定されたサーバーは存在しませんでした。\n入力ミスなどがないかご確認ください。",
                    )
                elif isinstance(error, commands.EmojiNotFound):
                    embed = discord.Embed(
                        title="404 Not Found",
                        description="指定された絵文字は存在しませんでした。\n入力ミスなどがないかご確認ください。",
                    )
                elif isinstance(error, commands.ChannelNotFound):
                    embed = discord.Embed(
                        title="404 Not Found",
                        description="指定されたチャンネルは存在しませんでした。\n入力ミスなどがないかご確認ください。",
                    )
                elif isinstance(error, commands.ThreadNotFound):
                    embed = discord.Embed(
                        title="404 Not Found",
                        description="指定されたスレッドは存在しませんでした。\n入力ミスなどがないかご確認ください。",
                    )
                else:
                    embed = discord.Embed(
                        title="400 Bad Request", description="引数が不正です。"
                    )
            else:
                errorm = "".join(traceback.format_exception(error))
                serror = errorm if len(errorm) < 990 else errorm[:990] + "..."
                embed = discord.Embed(
                    title="500 Internal Server Error",
                    description=f"コマンド「{ctx.message.content}」を実行中に不明なエラーが発生しました。[サポートサーバー](https://discord.gg/F6SUCkcSyZ)にて以下のエラーを添えてご報告ください。",
                )
                embed.add_field(name="", value=f"```{error}```")
                channel = self.bot.get_channel(config["admin_guild"]["error_channel"])
                error_log = discord.Embed(
                    title="コマンドの実行中にエラーが発生しました。"
                )
                error_log.add_field(
                    name="エラー発生サーバー名/ID",
                    value=ctx.guild.name + "/" + str(ctx.guild.id),
                )
                error_log.add_field(
                    name="エラー発生ユーザー名/ID",
                    value=ctx.author.name + "/" + str(ctx.author.id),
                )
                error_log.add_field(
                    name="エラー発生コマンド", value=ctx.message.content
                )
                error_log.add_field(name="Traceback", value="```" + serror + "```")
                await channel.send(embed=error_log)
            await ctx.send(embed=embed)
            logger.error(errorm)
        elif ctx.interaction is not None:
            interaction = ctx.interaction
            if isinstance(error, app_commands.CommandNotFound):
                embed = discord.Embed(
                    title="404 Not Found",
                    description=f"入力されたコマンド「**{ctx.message.content}**」は存在しませんでした。\n入力ミスなどがないかご確認ください。",
                )
            elif isinstance(error, app_commands.CommandOnCooldown):
                embed = discord.Embed(
                    title="429 Too Many Requests",
                    description=f"コマンドの連続実行数の制限に達しました。\n{error.retry_after}秒後に再試行できます。",
                )
            elif isinstance(error, app_commands.MissingPermissions):
                embed = discord.Embed(
                    title="403 Forbidden",
                    description="実行者の権限が不足しています。\n以下の権限を取得して再試行してください。\n"
                    + ", ".join(
                        f"`{PERMISSIONS.get(name)}`"
                        for name in error.missing_permissions
                    ),
                )
            elif isinstance(error, app_commands.BotMissingPermissions):
                embed = discord.Embed(
                    title="403 Forbidden",
                    description="botの権限が不足しています。\n以下の権限を付与して再試行してください。\n"
                    + ", ".join(
                        f"`{PERMISSIONS.get(name)}`"
                        for name in error.missing_permissions
                    ),
                )
            else:
                errorm = "".join(traceback.format_exception(error))
                serror = errorm if len(errorm) < 990 else errorm[:990] + "..."
                embed = discord.Embed(
                    title="500 Internal Server Error",
                    description=f"コマンド「{interaction.message.content}」を実行中に不明なエラーが発生しました。[サポートサーバー](https://discord.gg/F6SUCkcSyZ)にて以下のエラーを添えてご報告ください。",
                )
                embed.add_field(name="", value=f"```{error}```")
                channel = self.bot.get_channel(config["admin_guild"]["error_channel"])
                error_log = discord.Embed(
                    title="コマンドの実行中にエラーが発生しました。"
                )
                error_log.add_field(
                    name="エラー発生サーバー名/ID",
                    value=interaction.guild.name + "/" + str(interaction.guild.id),
                )
                error_log.add_field(
                    name="エラー発生ユーザー名/ID",
                    value=interaction.user.name + "/" + str(interaction.user.id),
                )
                error_log.add_field(
                    name="エラー発生コマンド", value=ctx.message.content
                )
                error_log.add_field(name="Traceback", value="```" + serror + "```")
                await channel.send(embed=error_log)
            await interaction.followup.send(embed=embed)
            logger.error(errorm)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ExceptionHandler(bot))


async def handler(
    bot: commands.Bot,
    interaction: discord.Interaction,
    error: discord.app_commands.AppCommandError,
) -> None:
    if isinstance(error, app_commands.CommandNotFound):
        embed = discord.Embed(
            title="404 Not Found",
            description=f"入力されたコマンド「**{interaction.command.name}**」は存在しませんでした。\n入力ミスなどがないかご確認ください。",
        )
    elif isinstance(error, app_commands.CommandOnCooldown):
        embed = discord.Embed(
            title="429 Too Many Requests",
            description=f"コマンドの連続実行数の制限に達しました。\n{str(math.floor(error.retry_after))}秒後に再試行できます。",
        )
    elif isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(
            title="403 Forbidden",
            description="実行者の権限が不足しています。\n以下の権限を取得して再試行してください。\n"
            + ", ".join(
                f"`{PERMISSIONS.get(name)}`" for name in error.missing_permissions
            ),
        )
    elif isinstance(error, app_commands.BotMissingPermissions):
        embed = discord.Embed(
            title="403 Forbidden",
            description="botの権限が不足しています。\n以下の権限を付与して再試行してください。\n"
            + ", ".join(
                f"`{PERMISSIONS.get(name)}`" for name in error.missing_permissions
            ),
        )
    elif isinstance(error, app_commands.errors.CommandSignatureMismatch):
        embed = discord.Embed(
            title="588 Commands Signature Mismatch",
            description="Discord側とシステム側でコマンドの著名が一致しないため、実行できません。\n通常これは、Botのアップデート直後などコマンドの同期が未完了の場合に発生します。\n[サポートサーバー](https://discord.gg/F6SUCkcSyZ)で報告してください。",
        )
    else:
        errorm = "".join(traceback.format_exception(error))
        serror = errorm if len(errorm) < 990 else errorm[:990] + "..."
        embed = discord.Embed(
            title="500 Internal Server Error",
            description=f"コマンド「{interaction.command.name}」を実行中に不明なエラーが発生しました。[サポートサーバー](https://discord.gg/F6SUCkcSyZ)にて以下のエラーを添えてご報告ください。",
        )
        embed.add_field(name="", value=f"```{error}```")
        channel = bot.get_channel(config["admin_guild"]["error_channel"])
        error_log = discord.Embed(title="コマンドの実行中にエラーが発生しました。")
        error_log.add_field(
            name="エラー発生サーバー名/ID",
            value=interaction.guild.name + "/" + str(interaction.guild.id),
        )
        error_log.add_field(
            name="エラー発生ユーザー名/ID",
            value=interaction.user.name + "/" + str(interaction.user.id),
        )
        error_log.add_field(name="エラー発生コマンド", value=interaction.command.name)
        error_log.add_field(name="Traceback", value="```" + serror + "```")
        await channel.send(embed=error_log)
    try:
        await interaction.response.defer()
    except discord.InteractionResponded:
        pass
    await interaction.followup.send(embed=embed)
    logger.error("".join(traceback.format_exception(error)))
