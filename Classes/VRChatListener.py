import vrcpy
import asyncio
from termcolor import colored
from datetime import datetime

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

async def start(username, password):
    loop.create_task(main(username, password))


@client.event
async def on_friend_location(friend_b, friend_a):
    #printd(friend_a.__dict__)
    printd("{} is now in {}#{}.".format(colored(friend_a.display_name, 'green'),
                                       colored(friend_a.location, 'yellow'), friend_a.instance_id))
    #                                "a private world" if friend_a.location is None else friend_a.location))


#@client.event
#async def on_friend_offline(friend_a):
#    printd("{} went offline.".format(colored(friend_a.display_name, 'green')))


@client.event
async def on_friend_active(friend_a):
    printd("{} is now {}.".format(colored(friend_a.display_name, 'green'), friend_a.state))


@client.event
async def on_friend_online(friend_a):
    printd("{} is now {}.".format(colored(friend_a.display_name, 'green'), colored(('online'), 'cyan')))


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
