# Standard
from typing import Optional, Union
import discord
from nest_asyncio import apply
from io import StringIO, BytesIO
from datetime import datetime
from sys import stdout
import settings
import datetime as dt
from typing import Any, Sequence

# Community
import discord
from discord.ext import commands

from settings.classes import RoleLadderElement

MISSING: Any = discord.utils.MISSING

apply()


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
                msg_content="The output is too big to fit in a discord message so it is insted in a file.",
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
            msg_content="The output is too big to fit in a discord message so it is insted in a file.",
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
):
    if isinstance(ctx, discord.Interaction):
        user_id = ctx.user.id
    else:
        user_id = ctx.author.id
    view = Confirm(user_id, timeout=timeout)
    if isinstance(ctx, discord.Interaction):
        msg = await interaction_reply(
            ctx, message, embed=embed, embeds=embeds, view=view
        )
    else:
        msg = await ctx.send(message, embed=embed, embeds=embeds, view=view)
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
    return r
