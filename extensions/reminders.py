import asyncio
import logging
from datetime import datetime as dt, timedelta

import asyncpg
import discord
from discord.ext import commands

import core
from core.bot import CustomBot
from core.context import CustomContext
from utils.time import human_timedelta, parse_time

log = logging.getLogger(__name__)


class Reminders(commands.Cog):
    def __init__(self, bot: CustomBot):
        self.bot = bot

        self._current_reminder = None
        self._event = asyncio.Event(loop=self.bot.loop)

        self._task = self.bot.loop.create_task(self._reminder_dispatch())

    async def get_active_reminder(self, days: int = 10, *, connection=None):
        query = """
            SELECT * 
            FROM 
                reminders 
            WHERE
                expires < (CURRENT_DATE + $1::interval) 
            ORDER BY 
                expires 
            LIMIT
                1
            """
        conn = connection or self.bot.pool

        ret = await conn.fetchrow(query, timedelta(days=days))
        return ret or None

    async def wait_for_reminders(self, *, days=10):
        async with self.bot.pool.acquire() as conn:
            reminder = await self.get_active_reminder(days, connection=conn)
            if reminder is not None:
                self._event.set()
                return reminder

            self._event.clear()

            self._current_reminder = None

            await self._event.wait()

            return await self.get_active_reminder(days, connection=conn)

    async def call_reminder(self, reminder):
        await self.bot.pool.execute("DELETE FROM reminders WHERE id = $1", reminder["id"])

        self.bot.dispatch("reminder_complete", reminder)

    async def _reminder_dispatch(self):
        await self.bot.wait_until_ready()
        try:
            while not self.bot.is_closed():
                reminder = self._current_reminder = await self.wait_for_reminders()

                if (expires := reminder["expires"]) >= (now := dt.utcnow()):
                    to_sleep = (expires - now).total_seconds()
                    await asyncio.sleep(to_sleep)

                await self.call_reminder(reminder)
        except asyncio.CancelledError:
            raise
        except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError):
            # re-run the loop
            self._task.cancel()
            self._task = self.bot.loop.create_task(self._reminder_dispatch())

    async def create_timer(
        self, ctx: CustomContext, content, expires: dt, created: dt = dt.utcnow()
    ):
        query = """
            INSERT INTO
                reminders (guild, author, channel, message, expires, created, content)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
        values = (
            ctx.guild.id,
            ctx.author.id,
            ctx.channel.id,
            ctx.message.id,
            expires.replace(tzinfo=None),
            created.replace(tzinfo=None),
            content,
        )
        await self.bot.pool.execute(query, *values)

        delta = (expires - created).total_seconds()

        if delta <= (86400 * 10):
            self._event.set()

        if self._current_reminder and expires < self._current_reminder["expires"]:
            self._task.cancel()
            self._task = self.bot.loop.create_task(self._reminder_dispatch())

        return True

    @core.command(
        examples=(
            "1w take out the trash",
            '"4 months and 2 days" william\'s birthday',
            "1week",
            "1week2days fix this code",
        ),
        params={
            "time": "The time when you want me to remind you for something.",
            "thing": "The thing you want me to remind you to do.",
        },
        returns="Confirmation that I have registered your reminder.",
    )
    async def remind(self, ctx: CustomContext, time: str, *, thing: str = "Nothing"):
        """A command to remind yourself of things
        Times are in UTC.
        """
        expires = parse_time(ctx, time)

        await self.create_timer(ctx, thing, expires, created=ctx.message.created_at)

        delta = human_timedelta(expires, source=ctx.message.created_at)
        await ctx.send(f"In {delta}: {thing}")

    @commands.Cog.listener()
    async def on_reminder_complete(self, reminder):
        channel_id = reminder["channel"]
        try:
            channel = self.bot.get_channel(channel_id) or (await self.bot.fetch_channel(channel_id))
        except discord.HTTPException:
            return

        delta = human_timedelta(reminder["created"])

        msg = f"<@{reminder['author']}>, {delta}: {reminder['content']}"
        msg += (
            "\n\n"
            + f"<https://discord.com/channels/{channel.guild.id}/{channel.id}/{reminder['message']}>"
        )

        try:
            await channel.send(msg)
        except discord.HTTPException:
            return


def setup(bot):
    bot.add_cog(Reminders(bot))
