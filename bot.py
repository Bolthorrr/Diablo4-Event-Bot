import discord
from discord.ext import commands, tasks
import os
from datetime import datetime
import random
from flask import Flask
from threading import Thread

# ---------------------------
# RENDER KEEP-ALIVE SERVER
# ---------------------------

app = Flask(__name__)

@app.route('/')
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

    re
