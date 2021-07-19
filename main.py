# Set environment to DEV and import Settings and Keys - remove these lines if using production
import os

os.environ.setdefault("LPD_OFFICER_MONITOR_ENVIRONMENT", "dev")

import Settings
import Keys

####################
### Main Imports ###
####################

# Standard Library Imports
import logging
import asyncio
import nest_asyncio
from nest_asyncio import apply
import datetime
import time
import sys
import traceback
import argparse

# Community Library Imports
import discord
from discord.errors import HTTPException
from discord.ext import commands

# Custom Library Imports
from BusinessLayer.test_functions import *
from BusinessLayer.extra_functions import *
import UILayer

apply()

loop = asyncio.get_event_loop()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=Settings.BOT_PREFIX, intents=intents)
bot.remove_command("help")

bot.has_been_started = False
bot.everything_ready = False


##############
### Checks ###
##############


@bot.check
def dms_not_supported(ctx):
    if ctx.guild is None:
        print(f"{ctx.author} tried to DM me in {ctx.channel}")
        raise commands.NoPrivateMessage(
            "This bot does not support direct messages. Please use a server channel instead."
        )
    else:
        return True


######################
### Discord Events ###
######################


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

    if bot.has_been_started:
        await clean_shutdown(
            bot, location="disconnection", person="automatic recovery", exit=False
        )

    # This should be the last line in this function
    bot.has_been_started = True


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    elif message.channel.id in Settings.ALLOWED_COMMAND_CHANNELS:
        await bot.process_commands(message)

    elif message.channel.id == Settings.LEAVE_OF_ABSENCE_CHANNEL:
        # Process the LOA request
        pass

    elif message.channel.id == Settings.REQUEST_RANK_CHANNEL:
        # Process the rank request
        pass

    if message.channel.id not in Settings.IGNORED_CATEGORIES:
        # Archive the message activity
        pass


@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id:
        return

    if after.channel == before.channel:
        return

    if (
        after.channel.category_id not in Settings.ON_DUTY_CATEGORY
        or before.channel.category_id not in Settings.ON_DUTY_CATEGORY
    ):
        return

    # If member is not an officer, return
    if not is_officer(member.id):
        return

    if after.channel is None:
        # User left the voice channel
        pass

    elif after.channel.id == Settings.VOICE_CHANNEL_ID:
        # User joined the voice channel
        pass

    elif after.channel.id != before.channel.id:
        # User changed voice channels
        pass

    if after.channel is not None:
        # Archive the voice activity
        pass


@bot.event
async def on_member_update(before, after):
    if before.bot or after.bot:
        return

    officer_before = is_officer(before.id)
    officer_after = is_officer(after.id)

    if officer_before and officer_after:
        return

    elif not officer_before and not officer_after:
        return

    elif not officer_before and officer_after:
        create_officer(after.id)

    elif officer_before and not officer_after:
        remove_officer(after.id)


@bot.event
async def on_member_remove(member):
    if is_officer(member.id):
        remove_officer(member.id)


@bot.event
async def on_member_ban(member):
    if is_officer(member.id):
        remove_officer(member.id)


@bot.event
async def on_error(event, *args, **kwargs):
    if isinstance(args[0], HTTPException):
        return

    print(f"Error in {event}: {args}")
    traceback.print_exc()


@bot.event
async def on_raw_message_delete(payload):
    # If the channel the LEAVE_OF_ABSENCE_CHANNEL, delete the LOA
    if payload.channel_id == Settings.LEAVE_OF_ABSENCE_CHANNEL:
        pass


@bot.event
async def on_raw_bulk_message_delete(payload):
    # If the channel the LEAVE_OF_ABSENCE_CHANNEL, delete the LOA
    if payload.channel_id == Settings.LEAVE_OF_ABSENCE_CHANNEL:
        pass


@bot.event
async def on_raw_reaction_add(payload):
    if not bot.everything_ready:
        return

    # if someone reacts :x: in REQUEST_RANK_CHANNEL, and they are a trainer, delete the message
    if (
        payload.channel_id == Settings.REQUEST_RANK_CHANNEL
        and payload.emoji.name == "❌"
        and is_any_trainer(payload.user_id)
    ):
        message = await bot.get_message(payload.channel_id, payload.message_id)
        await bot.delete_message(message)


@bot.event
async def on_command_error(ctx, exception):
    exception_string = str(exception).replace(
        "raised an exception", "encountered a problem"
    )

    try:
        await ctx.send(exception_string)
    except discord.Forbidden:
        bot.get_channel(Settings.ERROR_LOG_CHANNEL).send(
            f"**{ctx.author}**, I'm not allowed to send messages in {ctx.channel}**"
        )
        pass

    if exception_string.find("encountered a problem") != -1:
        print(
            exception_string, "".join(traceback.format_exception(None, exception, None))
        )


@bot.event
async def on_member_join(member):
    if member.bot:
        return

    # If the member is a detainee, make sure to give them the detention role
    pass


################
### Add cogs ###
################

for cog in UILayer.cogs:
    bot.add_cog(cog(bot))


#####################
### Start the bot ###
#####################


async def runner():
    try:
        await bot.start(Keys.DISCORD_TOKEN)
    finally:
        if not bot.is_closed():
            await bot.close()


future = asyncio.ensure_future(runner(), loop=loop)
try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(clean_shutdown(bot))
