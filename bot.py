import discord
from discord.ext import commands
import os
import re
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

LEGION_ROLE = os.getenv("LEGION_ROLE")
HELLTIDE_ROLE = os.getenv("HELLTIDE_ROLE")
BOSS_ROLE = os.getenv("BOSS_ROLE")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

event_slots = {
    "Legion Event": None,
    "Helltide": None,
    "World Boss": None
}

last_pinged = {
    "Legion Event": None,
    "Helltide": None,
    "World Boss": None
}


def event_started(embed):
    """Detect if event has begun based on 'ago' text."""
    text = str(embed.to_dict())

    if "ago" in text.lower():
        return True

    return False


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    channel = bot.get_channel(CHANNEL_ID)

    # Create slot messages if missing
    for event in event_slots:
        async for msg in channel.history(limit=50):
            if msg.author == bot.user and msg.embeds:
                if msg.embeds[0].title == event:
                    event_slots[event] = msg

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

    # EDIT SLOT MESSAGE
    await slot_message.edit(embed=embed)

    # PING ONLY WHEN EVENT STARTS
    if event_started(embed):

        now = datetime.utcnow()

        if last_pinged[title] is None or (now - last_pinged[title]).seconds > 1800:

            role = {
                "Legion Event": LEGION_ROLE,
                "Helltide": HELLTIDE_ROLE,
                "World Boss": BOSS_ROLE
            }[title]

            await message.channel.send(f"<@&{role}> **{title} is LIVE!**")

            last_pinged[title] = now

    # DELETE WEBHOOK MESSAGE
    await message.delete()


bot.run(TOKEN)
