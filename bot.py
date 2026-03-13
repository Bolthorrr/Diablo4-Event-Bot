import discord
from discord.ext import commands, tasks
import os
import random
from flask import Flask
from threading import Thread

# ---------------------------
# RENDER KEEP-ALIVE SERVER
# ---------------------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    server = Thread(target=run_web)
    server.start()


# ---------------------------
# DISCORD BOT SETUP
# ---------------------------

TOKEN = os.getenv("TOKEN")

INTEGRATION_CHANNEL_ID = int(os.getenv("INTEGRATION_CHANNEL_ID"))
TRACKER_CHANNEL_ID = int(os.getenv("TRACKER_CHANNEL_ID"))

LEGION_ROLE = os.getenv("LEGION_ROLE")
HELLTIDE_ROLE = os.getenv("HELLTIDE_ROLE")
BOSS_ROLE = os.getenv("BOSS_ROLE")
TERROR_ROLE = os.getenv("TERROR_ZONE")
CLONE_ROLE = os.getenv("DIABLO_CLONE")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------------
# BOT STATUS ROTATION
# ---------------------------

statuses = [
    discord.Activity(type=discord.ActivityType.watching, name="Helltides"),
    discord.Activity(type=discord.ActivityType.watching, name="World Bosses"),
    discord.Activity(type=discord.ActivityType.watching, name="Terror Zones"),
    discord.Activity(type=discord.ActivityType.playing, name="Diablo Events"),
]

@tasks.loop(minutes=5)
async def rotate_status():
    await bot.change_presence(activity=random.choice(statuses))


# ---------------------------
# EVENT SLOT SYSTEM
# ---------------------------

event_slots = {
    "Legion Event": None,
    "Helltide": None,
    "World Boss": None,
    "Terror Zone Tracker": None,
    "Diablo Clone Tracker": None
}


def identify_event(embed_title):

    title = embed_title.lower()

    if "legion" in title:
        return "Legion Event"

    if "helltide" in title:
        return "Helltide"

    if "boss" in title:
        return "World Boss"

    if "@tz" in title or "terror zone" in title:
        return "Terror Zone Tracker"

    if "diablo clone tracker" in title:
        return "Diablo Clone Tracker"

    return None


# ---------------------------
# MESSAGE LISTENER
# ---------------------------

@bot.event
async def on_message(message):

    if message.channel.id != INTEGRATION_CHANNEL_ID:
        return

    if not message.embeds:
        return

    embed = message.embeds[0]

    if not embed.title:
        return

    event_type = identify_event(embed.title)

    if not event_type:
        return

    tracker_channel = bot.get_channel(TRACKER_CHANNEL_ID)

    # Delete old message if it exists
    if event_slots[event_type]:
        try:
            old_msg = await tracker_channel.fetch_message(event_slots[event_type])
            await old_msg.delete()
        except:
            pass

    # Send new message
    new_msg = await tracker_channel.send(embed=embed)

    event_slots[event_type] = new_msg.id


# ---------------------------
# BOT READY
# ---------------------------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    rotate_status.start()


# ---------------------------
# START SERVICES
# ---------------------------

keep_alive()
bot.run(TOKEN)
