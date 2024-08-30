import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from typing import Final


load_dotenv()
TOKEN: Final[str] = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
end_time = (datetime.now() - timedelta(days=60)).isoformat().split('.')[0]

DATA_FILE = 'strikes.json'

# Load or initialize the strikes data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)


# Helper functions
def add_strike(user_id):
    data = load_data()
    now = datetime.now().isoformat()

    if str(user_id) not in data:
        data[str(user_id)] = {"strike_count": 1, "last_strike": now}
    else:
        data[str(user_id)]["strike_count"] += 1
        data[str(user_id)]["last_strike"] = now

    save_data(data)


def get_strikes(user_id):
    data = load_data()
    if str(user_id) in data:
        return data[str(user_id)]["strike_count"]
    return 0


def clear_expired_strikes():
    threshold_date = (datetime.now() - timedelta(days=60)).isoformat()
    data = load_data()
    to_delete = [user_id for user_id, info in data.items() if info["last_strike"] < threshold_date]

    for user_id in to_delete:
        del data[user_id]

    save_data(data)


# Background task to clear expired strikes daily
@tasks.loop(hours=24)
async def daily_cleanup():
    clear_expired_strikes()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    daily_cleanup.start()


@bot.command(name='strike')
@commands.has_permissions(administrator=True)
async def strike(ctx, member: discord.Member):
    end_time = (datetime.now() - timedelta(days=60)).isoformat().split('.')[0]
    add_strike(member.id)
    await ctx.send(f'{member.name} has been given a strike. They now have {get_strikes(member.id)} strikes, which expires on {end_time}.')


@bot.command(name='strikes')
async def strikes(ctx, member: discord.Member):
    strikes_count = get_strikes(member.id)
    await ctx.send(f'{member.name} currently has {strikes_count} strikes.')


# Run the bot with your token
bot.run(token=TOKEN)
