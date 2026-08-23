# Standard
import asyncio
from collections.abc import Callable, Coroutine
import functools
from typing import List, Optional, TypeVar, Union
import discord
from nest_asyncio import apply
from io import StringIO, BytesIO
from datetime import datetime
from sys import stdout
import settings
import datetime as dt
from typing import Any, Sequence, TypeVar
import inspect
import logging

# Community
import discord
from discord.ext import commands
import aiohttp
from icalendar import Calendar
from dateutil.rrule import rrulestr

from settings.classes import RoleLadderElement

MISSING: Any = discord.utils.MISSING

apply()

log = logging.getLogger("lpd-officer-monitor")


def now():
    return dt.datetime.utcnow()


def get_guild(bot: commands.Bot) -> discord.Guild:
    guild = bot.get_guild(settings.SERVER_ID)
    assert guild is not None, "Guild from settings could not be found in cache."
    return guild


async def send_long(channel, string, code_block=False, mention=True):
    """Send output as a text file, or optionally a code block if code_block=True is passed"""

    # Set allowed mentions
    allowed_mentions = (
        discord.AllowedMentions.all() if mention else discord.AllowedMentions.none()
    )

    # Make a function to check the length of all the lines
    str_list_len = lambda str_list: sum(len(i) + 1 for i in str_list)

    # Add a code block around the string if needed.
    if code_block:
        input_string_list = ("```\n" + string + "\n```").splitlines()
    else:
        input_string_list = string.splitlines()

    output_list = []
    for line in input_string_list:
        # If the line is longer that 2000, send it as a file and exit.
        if len(line) > 2000:
            await send_str_as_file(
                channel=channel,
                file_data=string,
                filename="long_output.txt",
                msg_content="The output is too big to fit in a discord message so it is instead in a file.",
            )
            return

        # Calculate the output length
        #            Previous output            \n   this line   the backticks if that is enabled
        output_len = (
            str_list_len(output_list)
            + 1
            + len(line)
            + (len("```") if code_block else 0)
        )

        # Check the output length
        if output_len < 2000:
            output_list.append(line)
        else:
            # Send the full message and add backticks if needed
            await channel.send(
                "\n".join(output_list) + ("```" if code_block else ""),
                allowed_mentions=allowed_mentions,
            )
            # Add the backticks if the message should be in a codeblock
            output_list = [("```" if code_block else "") + line]

    await channel.send("\n".join(output_list), allowed_mentions=allowed_mentions)


async def send_str_as_file(
    channel: discord.TextChannel,
    file_data: str,
    filename: Optional[str] = None,
    msg_content: Optional[str] = None,
) -> None:
    with BytesIO(file_data.encode("utf8")) as error_file:
        await channel.send(
            msg_content, file=discord.File(error_file, filename=filename)
        )


async def interaction_reply(
    interaction: discord.Interaction,
    content: Optional[str] = None,
    embed: discord.Embed = MISSING,
    embeds: Sequence[discord.Embed] = MISSING,
    files: Sequence[discord.File] = MISSING,
    view: discord.ui.View = MISSING,
    ephemeral: bool = False,
):
    """Guaranty reply to an interaction what ever it was defer or not, already answered by message or not"""
    match interaction.response.type:
        case None:
            await interaction.response.send_message(
                content=content,
                embed=embed,
                embeds=embeds,
                files=files,
                view=view,
                ephemeral=ephemeral,
            )
            return await interaction.original_response()
        case _:
            # it's fine if `content=None`, you need to at least one item
            # followup reply to the first message that answered the command
            # it's the best way as reply have a lot some limitation
            return await interaction.followup.send(
                content=content,
                embed=embed,
                embeds=embeds,
                files=files,
                view=view,
                ephemeral=ephemeral,
            )


async def interaction_send_long(
    interaction: discord.Interaction,
    data: str,
    code_block: bool = False,
    ephemeral: bool = False,
) -> None:
    if len(data) > 2000:
        await interaction_send_str_as_file(
            interaction,
            data,
            "output.txt",
            msg_content="The output is too big to fit in a discord message so it is instead in a file.",
            ephemeral=ephemeral,
        )
    else:
        await interaction_reply(
            interaction,
            ("```" if code_block else "") + data + ("```" if code_block else ""),
        )


async def interaction_send_str_as_file(
    interaction: discord.Interaction,
    data: str,
    filename: str,
    msg_content: str,
    ephemeral: bool = False,
) -> None:
    with BytesIO(data.encode("utf8")) as vfile:
        await interaction_reply(
            interaction,
            msg_content,
            files=[discord.File(vfile, filename=filename)],
            ephemeral=ephemeral,
        )


def has_role_id(member: discord.Member, role_id: int) -> bool:
    """Returns true if the member has the given role"""
    if isinstance(member, discord.User):
        raise discord.errors.InvalidData("cannot get roles on `User`")
    return role_id in [r.id for r in member.roles]


def is_lpd_member(member: Optional[discord.Member]):
    """
    Returns if a member is an LPD member based on their discord roles.
    """
    if member is None:
        return False

    if has_role_id(member, settings.LPD_ROLE):
        return True  # early out on correct setup
    # in the rare event someone have a rank but not LPD role
    lpd_role_set = {v.id for k, v in settings.ROLE_LADDER.items()}
    member_rank_roles = set(r.id for r in member.roles).intersection(lpd_role_set)
    return len(member_rank_roles) != 0


def get_lpd_member_rank(member: discord.Member) -> Optional[RoleLadderElement]:
    """
    Returns the first lowest rank a member have
    """
    for k, rank in settings.ROLE_LADDER.items():
        if has_role_id(member, rank.id):
            return rank
    return None


def parse_iso_date(date_string: str) -> dt.date:
    return dt.date.fromisoformat(date_string)


class Confirm(discord.ui.View):
    def __init__(self, user_id: int, timeout: float = 30):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.value: Optional[bool] = None

    async def interaction_check(self, interaction: discord.Interaction):
        return self.user_id == interaction.user.id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.edit_message(content="Confirmed", view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelling", view=None)
        self.value = False
        self.stop()


async def msgbox_confirm(
    ctx: Union[discord.Interaction, commands.Context],
    message: str = "Do you want to continue?",
    timeout=30,
    ephemeral=False,
    embed: discord.Embed = MISSING,
    embeds: Sequence[discord.Embed] = MISSING,
) -> Optional[bool]:
    """
    returns None on timeout
    """
    if isinstance(ctx, discord.Interaction):
        user_id = ctx.user.id
    else:
        user_id = ctx.author.id
    view = Confirm(user_id, timeout=timeout)
    if isinstance(ctx, discord.Interaction):
        msg = await interaction_reply(
            ctx,
            message,
            embed=embed,
            embeds=embeds,
            view=view,
            ephemeral=ephemeral,
        )
    else:
        msg = await ctx.send(
            message,
            embed=embed,
            embeds=embeds,
            view=view,
            ephemeral=ephemeral,
        )
    await view.wait()
    if view.value is None:
        await msg.edit(content="Timeout", view=None)
    return view.value


def timedelta_to_nice_string(dt: dt.timedelta) -> str:
    r: str = ""
    if dt.days != 0:
        r += f"{dt.days} day{'s' if abs(dt.days)>1 else ''} "
    sec = dt.seconds
    if sec > 3600:
        h = sec // 3600  # floordiv op
        r += f"{h} hour{'s' if h>1 else ''} "
        sec -= h * 3600  # remaining
    if sec > 60:
        m = sec // 60  # floordiv op
        r += f"{m:02} minute{'s' if m>1 else ''} "
        sec -= m * 60  # remaining
    if sec > 0:
        r += f"{sec:02} second{'s' if sec>1 else ''} "
    return len(r) > 0 and r or "0 seconds"


def debounce(*, seconds: float):
    """
    A simple debounce decorator using python async.

    Any function using this decorator will wait for `seconds` before it calls the
    wrapped function, resetting this wait each time the function is called.

    The wrapped function can be both sync or async. Do not await the result of the
    wrapped function, no matter what should return, when wrapped, it returns None.
    """

    def decorator(function: Callable[..., Any | Coroutine[Any, None, None]]):
        timer: asyncio.TimerHandle | None = None

        def new_debounced_func(*args: Any, **kwargs: Any) -> None:
            nonlocal timer

            def callback() -> None:
                nonlocal timer
                timer = None
                result = function(*args, **kwargs)
                if isinstance(result, Coroutine):
                    asyncio.create_task(result)

            if timer is not None:
                timer.cancel()

            loop = asyncio.get_event_loop()
            timer = loop.call_later(seconds, callback)

        functools.update_wrapper(new_debounced_func, function)
        return new_debounced_func

    return decorator


T = TypeVar("T")


def not_none(val: Union[T, None]) -> T:
    """
    Asserts that something isn't None and returns the not None value.

    Kind of inspired from TypeScript's ! operator to assert something isn't null, since
    python doesn't have anything similar this seems to be the closest we can get.
    """
    assert val is not None
    return val


async def mention_slash_cmd(bot, commandName: str, hybridCmd: bool = False) -> str:
    onlineList = await bot.tree.fetch_commands(
        guild=discord.Object(id=settings.SERVER_ID)
    )
    for ol in onlineList:
        if ol.name == commandName:
            return ol.mention
    else:
        if hybridCmd:
            return f"`{settings.BOT_PREFIX}{commandName}`"
        caller_frame = inspect.currentframe().f_back
        log.error(
            f"mentionSlashCmd failed to find `{commandName}` caller:{caller_frame.f_code.co_name} {caller_frame.f_code.co_filename}:{caller_frame.f_lineno} "
        )
        return f"`/{commandName}`"


def get_monday_from_week(year: int, week: int) -> dt.datetime:
    first_day_of_year = dt.datetime(year, 1, 1)
    days_to_monday = (week - 1) * 7 - first_day_of_year.weekday()
    monday_of_week = first_day_of_year + dt.timedelta(days=days_to_monday)
    return monday_of_week.replace(tzinfo=dt.timezone.utc)


async def get_calendar_events(
    filter: Optional[str] = None,
    year: Optional[int] = None,
    week_number: Optional[int] = None,
) -> dict:

    calendar_data = ""
    async with aiohttp.ClientSession() as session:
        async with session.get(settings.SCHEDULE_URL) as response:
            if response.status != 200:
                log.error("Failed to fetch the calendar file from the provided URL.")
                return {}
            calendar_data = await response.text()

    calendar = Calendar.from_ical(calendar_data)

    today = datetime.now(tz=dt.timezone.utc)
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    if year:
        year = today.year
    if week_number is None:
        week_number = today.isocalendar()[1] + 1

    start_dt = get_monday_from_week(year, week_number)
    end_dt = start_dt + dt.timedelta(days=7)
    start_date = start_dt.date()
    end_date = end_dt.date()

    unsortedEvents = dict()

    for component in calendar.walk("VEVENT"):

        event_start = component.get("DTSTART").dt
        event_end = component.get("DTEND").dt

        if type(event_start) != type(event_end):
            log.error("weird event \n" + str(component))
            continue

        if filter:
            cat = component.get("CATEGORIES").to_ical().decode()
            if not filter in cat:
                continue

        if "RRULE" in component:
            rrule = rrulestr(
                component["RRULE"].to_ical().decode("utf-8"),
                dtstart=component.get("DTSTART").dt,
            )
            if not component.get("DTSTART").dt.tzinfo:  #
                continue
            occurrences = list(rrule.between(start_dt, end_dt, inc=True))
            if len(occurrences) > 0:
                for o in occurrences:
                    unsortedEvents[o.timestamp()] = [component, o]
            else:
                continue
        else:
            if not isinstance(event_start, datetime):
                if not (start_date <= event_start <= end_date) and not (
                    start_date <= event_end <= end_date
                ):
                    continue
            else:
                if not (start_dt <= event_start <= end_dt) and not (
                    start_dt <= event_end <= end_dt
                ):
                    continue
                unsortedEvents[event_start.timestamp()] = component
    return unsortedEvents


class EmbedSelectorView(discord.ui.View):
    def __init__(
        self,
        user_id: int,
        embeds: List[discord.Embed],
        button_labels: Optional[List[str]] = None,
        timeout: float = 60,
        cancel_button: bool = True,
    ):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.embeds = embeds
        self.selected_index: int = -1

        if button_labels is None:
            button_labels = [f"Option {i + 1}" for i in range(len(embeds))]

        if len(button_labels) != len(embeds):
            raise ValueError("button_labels must have the same length as embeds")

        for index, label in enumerate(button_labels):
            self.add_item(_EmbedSelectButton(label, index))
        if cancel_button:
            self.add_item(_EmbedSelectButton("Cancel", -1, discord.ButtonStyle.danger))

    async def interaction_check(self, interaction: discord.Interaction):
        return self.user_id == interaction.user.id

    def get_selected_index(self) -> Optional[int]:
        return self.selected_index


class _EmbedSelectButton(discord.ui.Button):
    def __init__(
        self,
        label: str,
        index: int,
        style: discord.ButtonStyle = discord.ButtonStyle.primary,
    ):
        super().__init__(label=label, style=style)
        self.index = index
        self.label = label

    async def callback(self, interaction: discord.Interaction):
        view: EmbedSelectorView = self.view

        view.selected_index = self.index

        # Disable all buttons after selection
        for item in view.children:
            item.disabled = True

        # await interaction.edit_original_response(
        #     content=f"Choosen `{self.label}`", view=None, embeds=[]
        # )
        view.stop()


async def multi_choice_embed(
    ctx: Union[discord.Interaction, commands.Context],
    embeds: List[discord.Embed],
    message: str = "Choose one",
    timeout=30,
    ephemeral=False,
    button_labels: Optional[List[str]] = None,
    cancel_button: bool = True,
) -> int:
    """
    returns -1 on timeout or cancelation
    """
    if isinstance(ctx, discord.Interaction):
        user_id = ctx.user.id
    else:
        user_id = ctx.author.id
    view = EmbedSelectorView(
        user_id,
        embeds=embeds,
        timeout=timeout,
        button_labels=button_labels,
        cancel_button=callable,
    )
    if isinstance(ctx, discord.Interaction):
        msg = await interaction_reply(
            ctx,
            message,
            embeds=embeds,
            view=view,
            ephemeral=ephemeral,
        )
    else:
        msg = await ctx.send(
            message,
            embeds=embeds,
            view=view,
            ephemeral=ephemeral,
        )
    await view.wait()
    if view.get_selected_index() in [-1, None]:
        await msg.edit(content="Timeout/Canceled", view=None, embeds=[])
    else:
        await msg.edit(
            content=f"Choosed {view.get_selected_index()}", view=None, embeds=[]
        )
    return view.get_selected_index()
