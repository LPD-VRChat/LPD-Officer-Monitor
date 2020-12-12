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
async def on_friend_location(friend, world, location, instance):
    print("{} is now in {}.".format(friend.displayName,
                                    "a private world" if location is None else world.name))


@client.event
async def on_friend_offline(friend):
    print("{} went offline.".format(friend.displayName))


@client.event
async def on_friend_active(friend):
    print("{} is now {}.".format(friend.displayName, friend.state))


@client.event
async def on_friend_online(friend):
    print("{} is now online.".format(friend.displayName))


@client.event
async def on_friend_add(friend):
    print("{} is now your friend.".format(friend.displayName))


@client.event
async def on_friend_delete(friend):
    print("{} is no longer your friend.".format(friend.displayName))


@client.event
async def on_friend_update(friend):
    print("{} has updated their profile/account.".format(friend.displayName))


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
