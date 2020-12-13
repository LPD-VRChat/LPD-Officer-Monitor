import vrcpy
import asyncio
from termcolor import colored
from datetime import datetime, timezone
loop = asyncio.get_event_loop()
client = vrcpy.Client(loop=loop)

def printd(string):
    timestamp = (str(datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")))
    string = colored(timestamp, 'magenta') + ' - ' + string
    print(string)


async def main(username, password):
    await client.login(
        username=username,
        password=password
    )

    try:
        # Start the ws event loop
        await client.start()
    except KeyboardInterrupt:
        await client.logout()

async def start(username, password, Bot):
    loop.create_task(main(username, password))
    bot=Bot

async def stop():
    await client.logout()

@client.event
async def on_friend_location(friend_b, friend_a):
    world_name = await client.fetch_world_name_via_id(friend_a.world_id)
    instance_number = friend_a.instance_id.split('~')[0]
    if instance_numer == 'private':
        world_string = colored('a Private World', yellow)
    else:
        world_string = colored(world_name, 'yellow') + '#' + instance_number
    printd("{} is now in {}".format(colored(friend_a.display_name, 'green'), world_string))
    officer_id = userbot.user_manager.get_discord_by_vrc(friend_a.display_name)
    officer = bot.officer_manager.get_officer(officer_id)
    if officer.is_on_duty():
        vrc_name = friend_a.display_name
        enter_time = datetime.now(timezone.utc)
        avatar_image_url = friend_a.avatar_image_url
        allow_avatar_copying = friend_a.allow_avatar_copying
        bot.officer_manager.send_db_request(f"INSERT INTO VRChatActivity (officer_id, vrc_name, enter_time, avatar_image_url, allow_avatar_copying) VALUES ({officer_id}, '{vrc_name}', '{enter_time}', '{avatar_image_url}', {allow_avatar_copying})", None)
        print('is on duty')
    

@client.event
async def on_friend_active(friend_a):
    if friend_a.state == 'online':
        await on_friend_online(friend_a)
        return
    printd("{} is now {}.".format(colored(friend_a.display_name, 'green'), friend_a.state))


@client.event
async def on_friend_online(friend_a):
    printd("{} is now {}.".format(colored(friend_a.display_name, 'green'), colored('online', 'cyan')))


@client.event
async def on_friend_add(friend_b, friend_a):
    printd("{} is now your friend.".format(colored(friend_a.display_name, 'green')))


@client.event
async def on_friend_delete(friend_b, friend_a):
    printd("{} is no longer your friend.".format(colored(friend_a.display_name, 'green')))


#@client.event
#async def on_friend_update(friend_b, friend_a):
#    printd("{} has updated their profile/account.".format(colored(friend_a.display_name, 'green')))


#@client.event
#async def on_notification(notification):
#    printd("Got a {} notification from {}.".format(
#        notification.type, notification.senderUsername))


@client.event
async def on_connect():
    printd("Connected to wss pipeline.")


@client.event
async def on_disconnect():
    printd("Disconnected from wss pipeline.")


async def join_user(user_id):
    user = await client.fetch_user_via_id(user_id)
    join_link = 'vrchat://launch?' + user.location
    return join_link
    
async def send_invite(user_id):
    user = await client.fetch_user_via_id(user_id)
    join_link = 'vrchatL//launch?' + user.location
    return join_link