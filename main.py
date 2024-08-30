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
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
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
    expiration_time = (datetime.now() + timedelta(days=7)).isoformat()  # Example: 7 days expiration

    if str(user_id) not in data:
        data[str(user_id)] = {"strikes": [{"reason": "Strike added", "expires_at": expiration_time}]}
    else:
        data[str(user_id)]["strikes"].append({"reason": "Strike added", "expires_at": expiration_time})

    save_data(data)


def get_strikes(user_id):
    data = load_data()
    if str(user_id) in data:
        strikes_info = data[str(user_id)]["strikes"]
        # Convert expiration dates to datetime for comparison
        current_time = datetime.now()
        return [strike for strike in strikes_info if datetime.fromisoformat(strike["expires_at"]) > current_time]
    return []


def clear_expired_strikes():
    data = load_data()
    current_time = datetime.now()
    for user_id, info in list(data.items()):
        data[user_id]["strikes"] = [strike for strike in info["strikes"] if
                                    datetime.fromisoformat(strike["expires_at"]) > current_time]
        if not data[user_id]["strikes"]:
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
async def strike(ctx, member: discord.Member, reason: str):
    add_strike(member.id)
    strikes = get_strikes(member.id)
    expiry = (datetime.now() + timedelta(weeks=1)).strftime('%m-%d-%Y %H:%M:%S')

    await ctx.send(f"{member.name} has recieved 1 strike for {reason}.")
    await member.send(f"You have recieved 1 strike for {reason}.")



@bot.command(name='strikes')
async def strikes(ctx, member: discord.Member):
    expiry = (datetime.now() + timedelta(weeks=1)).strftime('%m-%d-%Y %H:%M:%S')
    strikes_info = get_strikes(member.id)
    if not strikes_info:
        await ctx.send(f'{member.name} currently has no strikes.')
        return

    strike_messages = [f"Reason: {strike['reason']} | Expires At: {expiry}" for strike in strikes_info]
    strikes_message = '\n'.join(strike_messages)
    await ctx.send(f'{member.name} currently has the following strikes:\n{strikes_info}\n')


@bot.command(name='clear')
@commands.has_permissions(administrator=True)
async def clear_strikes(ctx, member: discord.Member):
    data = load_data()
    if str(member.id) in data:
        del data[str(member.id)]
        save_data(data)
        await ctx.send(f'{member.name}\'s strikes have been cleared. They have 0 strikes.')
    else:
        await ctx.send(f'{member.name} has no strikes to clear.')


@bot.command(name='dm')
async def dm_strikes(ctx, member: discord.Member):
    expiry = (datetime.now() + timedelta(weeks=1)).strftime('%m-%d-%Y %H:%M:%S')
    strikes_info = get_strikes(member.id)
    if not strikes_info:
        await ctx.send(f'{member.name} currently has no strikes.')
        return

    message = (f'You have ***{len(strikes_info)}*** strike(s), which expire(s) on ***{expiry}.***\n')

    await member.send(message)
    await ctx.send(f'Sent strike information to {member.name}')

# Run the bot with your token
bot.run(TOKEN)
