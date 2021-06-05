import asyncio
import logging
from typing import List, Union

import discord
from aiohttp import ClientSession
from discord.ext import commands

from core import config

log = logging.getLogger("bot")
logging.basicConfig(level=logging.INFO)


def get_prefix(bot: "CustomBot", message: discord.Message) -> Union[List[str], str]:
    return commands.when_mentioned_or(*config.prefix)(bot, message)


class CustomBot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.loop.create_task(self.__prep())
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()

        self.context = commands.Context

    async def __prep(self):
        self.session = ClientSession(
            headers={"User-Agent": "Walrus (https://github.com/ppotatoo/bot-rewrite)"}
        )

    def load_extensions(self):
        extensions = ["jishaku", "core.context", "extensions.osu"]
        for ext in extensions:
            self.load_extension(ext)
        log.info("Loaded extensions")

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or self.context)

    def run(self, *args, **kwargs):
        self.load_extensions()
        super().run(*args, **kwargs)

    async def on_ready(self):
        log.info("Connected to Discord.")

    @staticmethod
    def embed(**kwargs):
        color = kwargs.pop("color", discord.Color.blurple())
        return discord.Embed(**kwargs, color=color)