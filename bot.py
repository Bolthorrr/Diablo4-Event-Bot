import discord
from discord.ext import commands, tasks
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

LEGION_ROLE = os.getenv("LEGION_ROLE")
HELLTIDE_ROLE = os.getenv("HELLTIDE_ROLE")
BOSS_ROLE = os.getenv("BOSS_ROLE")
TERROR_ROLE = os.getenv("TERROR_ROLE")
CLONE_ROLE = os.getenv("CLONE_ROLE")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
statuses = [
    discord.Activity(type=discord.ActivityType.Watching, name="Helltides"),
    discord.Activity(type=discord.ActivityType.Watching, name="World Bosses"),
    discord.Activity(type=discord.ActivityType.Watching, name="Terror Zones"),
    discord.Activity(type=discord.ActivityType.Playing, name="Diablo Events"),
    discord.Activity(type=discord.ActivityType.Competing, name="Sanctuary")
]

@tasks.loop(minutes=5)
async def rotate_status():
    import random
    await bot.change_presence(activity=random.choice(statuses))



# ALL EVENTS LIVE HERE
event_slots = {
    "Legion Event": None,
    "Helltide": None,
    "World Boss": None,
    "Terror Zone Tracker": None,
    "Diablo Clone Tracker": None
}

last_pinged = {
    event: None for event in event_slots
}


def event_started(embed):
    """
    Detect if event has begun.

    Many trackers switch to phrases like:
    NOW
    ACTIVE
    TERRORIZED
    SPAWNED
    ago
    """

    text = str(embed.to_dict()).lower()

    trigger_words = [
        "now",
        "active",
        "terrorized",
        "spawned",
        "ago"
    ]

    return any(word in text for word in trigger_words)


def get_role(title):
    return {
        "Legion Event": LEGION_ROLE,
        "Helltide": HELLTIDE_ROLE,
        "World Boss": BOSS_ROLE,
        "Terror Zone Tracker": TERROR_ROLE,
        "Diablo Clone Tracker": CLONE_ROLE
    }.get(title)


@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    if not rotate_status.is_running():
        rotate_status.start()

    channel = bot.get_channel(CHANNEL_ID)

    # Locate existing slot messages
    async for msg in channel.history(limit=100):

        if msg.author != bot.user:
            continue

        if not msg.embeds:
            continue

        title = msg.embeds[0].title

        if title in event_slots:
            event_slots[title] = msg

    # Create missing slots
    for event in event_slots:

        if event_slots[event] is None:

            embed = discord.Embed(
                title=event,
                description="Waiting for event data...",
                color=discord.Color.dark_gray()
            )

            msg = await channel.send(embed=embed)
            event_slots[event] = msg


@bot.event
async def on_message(message):

    # Only webhook / followed announcement messages
    if not message.webhook_id:
        return

    if message.channel.id != CHANNEL_ID:
        return

    if not message.embeds:
        return

    embed = message.embeds[0]
    title = embed.title

    if title not in event_slots:
        return

    slot_message = event_slots[title]

    # EDIT SLOT
    await slot_message.edit(embed=embed)

    # PING WHEN EVENT STARTS
    if event_started(embed):

        now = datetime.utcnow()

        if last_pinged[title] is None or (now - last_pinged[title]).seconds > 1800:

            role = get_role(title)

            if role:
                await message.channel.send(
                    f"<@&{role}> **{title} is LIVE!**"
                )

            last_pinged[title] = now

    # DELETE SOURCE MESSAGE (keeps channel clean)
    await message.delete()


bot.run(TOKEN)
