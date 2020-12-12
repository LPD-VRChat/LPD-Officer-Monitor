import vrcpy
import asyncio

loop = asyncio.get_event_loop()
client = vrcpy.Client(loop=loop)


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
    print("{} is now in {}.".format(friend_a.display_name,
                                    "a private world" if friend_a.location is None else friend_a.location))


@client.event
async def on_friend_offline(friend_b, friend_a):
    print("{} went offline.".format(friend_a.display_name))


@client.event
async def on_friend_active(friend_b, friend_a):
    print("{} is now {}.".format(friend_a.display_name, friend_a.state))


@client.event
async def on_friend_online(friend_b, friend_a):
    print("{} is now online.".format(friend_a.display_name))


@client.event
async def on_friend_add(friend_b, friend_a):
    print("{} is now your friend.".format(friend_a.display_name))


@client.event
async def on_friend_delete(friend_b, friend_a):
    print("{} is no longer your friend.".format(friend_a.display_name))


@client.event
async def on_friend_update(friend_b, friend_a):
    print("{} has updated their profile/account.".format(friend_a.display_name))


@client.event
async def on_notification(notification):
    print("Got a {} notification from {}.".format(
        notification.type, notification.senderUsername))


@client.event
async def on_connect():
    print("Connected to wss pipeline.")


@client.event
async def on_disconnect():
    print("Disconnected from wss pipeline.")
