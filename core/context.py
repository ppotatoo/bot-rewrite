from discord.ext import commands

from core.bot import CustomBot


class CustomContext(commands.Context):
    bot: CustomBot



    


def setup(bot: CustomBot) -> None:
    bot.context = CustomContext


def teardown(bot: CustomBot) -> None:
    bot.context = commands.Context
