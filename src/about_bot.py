import discord
from discord import app_commands
from discord.ext import commands
import yaml
from discord_ext_help import helpExtension, options
from reactionmenu import ViewMenu, ViewButton

from .lib.data import i18n
from .lib import info

getText = i18n.getText

cd = 2


class About(commands.GroupCog, name="about"):
    def __init__(self, bot):
        self.bot = bot
        with open("./data/info.yml", "r", encoding="utf-8") as r:
            self.info = yaml.safe_load(r)

    @app_commands.command(
        name="follow",
        description="Follow Selene's announcements channel.",
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 60)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def follow(self, interaction: discord.Interaction):
        await interaction.response.defer()
        announcementChannel = self.bot.get_channel(962656965044109342)
        await announcementChannel.follow(destination=interaction.channel, reason=None)
        await interaction.followup.send(
            embed=discord.Embed(title=getText("Followed Announcement Channel.")),
            ephemeral=True,
        )

    @app_commands.command(
        name="show",
        description="About Selene",
    )
    @app_commands.checks.cooldown(4, 60)
    async def about(self, interaction: discord.Interaction):
        await interaction.response.defer()

        title = getText("About Selene")

        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)

        p1 = discord.Embed(title=title)
        p1.add_field(name=getText("Author"), value=info.author)
        p1.add_field(name=getText("version"), value=info.version)
        p1.add_field(name=getText("license"), value=info.license)
        p1.add_field(name=getText("GitHub"), value=info.repository)
        p1.add_field(name=getText("support"), value=info.support)
        menu.add_page(p1)
        menu.add_page(
            discord.Embed(
                title=getText("Libraries used (partial)"),
                description=getText("All the libraries we use can be found on GitHub.")
                + "\n```\n{}\n```".format("\n".join(info.oss)),
            )
        )

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()


class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Displays a list of commands.",
    )
    @app_commands.choices(command=options.cmds)
    @app_commands.checks.cooldown(cd, 60)
    async def help(self, interaction: discord.Interaction, command: str = None):
        await interaction.response.defer()
        res = await helpExtension.response(interaction, command)
        menu = res["resp"]

        if res["type"] == "menu":
            await menu.start()
            return
        await interaction.followup.send(embed=menu)


async def setup(bot: commands.Bot):
    with open("./config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        if config["guild"] == []:
            await bot.add_cog(About(bot))
            await bot.add_cog(help(bot))
        elif config["guild"] is not None:
            guild = []
            for i in config["guild"]:
                guild.append(discord.Object(i))
            await bot.add_cog(About(bot), guilds=guild)
            await bot.add_cog(help(bot), guilds=guild)
