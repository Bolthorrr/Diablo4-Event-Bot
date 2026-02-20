import discord
from discord.ext import commands, tasks
import os
from datetime import datetime
import random

TOKEN = os.getenv("TOKEN")

INTEGRATION_CHANNEL_ID = int(os.getenv("INTEGRATION_CHANNEL_ID"))
TRACKER_CHANNEL_ID = int(os.getenv("TRACKER_CHANNEL_ID"))

LEGION_ROLE = os.getenv("LEGION_ROLE")
HELLTIDE_ROLE = os.getenv("HELLTIDE_ROLE")
BOSS_ROLE = os.getenv("BOSS_ROLE")
TERROR_ROLE = os.getenv("TERROR_ROLE")
CLONE_ROLE = os.getenv("CLONE_ROLE")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

statuses = [
    discord.Activity(type=discord.ActivityType.watching, name="Helltides"),
    discord.Activity(type=discord.ActivityType.watching, name="World Bosses"),
    discord.Activity(type=discord.ActivityType.watching, name="Terror Zones"),
    discord.Activity(type=discord.ActivityType.playing, name="Diablo Events"),
    discord.Activity(type=discord.ActivityType.competing, name="Sanctuary")
]

@tasks.loop(minutes=5)
async def rotate_status():
    await bot.change_presence(activity=random.choice(statuses))


# SLOT SYSTEM
event_slots = {
    "Legion Event": None,
    "Helltide": None,
    "World Boss": None,
    "Terror Zone Tracker": None,
    "Diablo Clone Tracker": None
}

last_pinged = {event: None for event in event_slots}


def event_started(embed):
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


def detect_event_type(message, embed):
    """
    D4 detection unchanged.
    D2 detection uses:
      - "Diablo Clone Tracker"
      - "@TZ"
    """

    title = embed.title.lower() if embed.title else ""
    description = embed.description.lower() if embed.description else ""
    full_text = str(embed.to_dict()).lower()

    # ------------------------
    # Diablo II Detection
    # ------------------------

    # Diablo Clone Tracker
    if "diablo clone tracker" in title or "diablo clone tracker" in full_text:
        return "Diablo Clone Tracker"

    # Terror Zones (prefixed with @TZ)
    if "@tz" in message.content.lower() or "@tz" in full_text:
        return "Terror Zone Tracker"

    # ------------------------
    # Diablo IV Detection
    # ------------------------

    if "helltide" in full_text:
        return "Helltide"

    if "legion" in full_text:
        return "Legion Event"

    if "world boss" in full_text:
        return "World Boss"

    return None


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    if not rotate_status.is_running():
        rotate_status.start()

    tracker_channel = bot.get_channel(TRACKER_CHANNEL_ID)

    # Locate existing slot messages
    async for msg in tracker_channel.history(limit=100):
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

            msg = await tracker_channel.send(embed=embed)
            event_slots[event] = msg


@bot.event
async def on_message(message):

    # ONLY read from integration channel
    if message.channel.id != INTEGRATION_CHANNEL_ID:
        return

    # Allow followed announcement posts (webhooks / bots)
    if not (message.webhook_id or message.author.bot):
        return

    if not message.embeds:
        return

    embed = message.embeds[0]

    event_type = detect_event_type(message, embed)

    if not event_type:
        return

    tracker_channel = bot.get_channel(TRACKER_CHANNEL_ID)
    slot_message = event_slots.get(event_type)

    if not slot_message:
        return

    # Update slot embed
    await slot_message.edit(embed=embed)

    # Handle pings (30 min cooldown per event)
    if event_started(embed):
        now = datetime.utcnow()

        if last_pinged[event_type] is None or (now - last_pinged[event_type]).seconds > 1800:

            role = get_role(event_type)

            if role:
                await tracker_channel.send(
                    f"<@&{role}> **{event_type} is LIVE!**"
                )

            last_pinged[event_type] = now

    # Clean up integration channel to prevent clutter
    try:
        await message.delete()
    except:
        pass


bot.run(TOKEN)
