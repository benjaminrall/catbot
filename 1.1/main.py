import json
import discord
import requests
import copy
import time
from discord.ext import tasks

# Settings
START_DATA_FILE = "start_data.json"
TIMINGS_DATA_FILE = "timings_data.json"

# Discord Settings
intents = discord.Intents.all()
allowed_mentions = discord.AllowedMentions(everyone=True)

# Attempts to load essential data from the start data file
try:
    with open(START_DATA_FILE, "r") as f:
        start_data = json.load(f)
    CAT_API = start_data["CAT_API"]
    BOT_TOKEN = start_data["BOT_TOKEN"]
    VALORANT_ID = start_data["VALORANT_ID"]
    ADMIN_ID = start_data["ADMIN_ID"]
    GUILD_ID = start_data["GUILD_ID"]
    DISAPPOINTMENT_ROLE_ID = start_data["DISAPPOINTMENT_ROLE_ID"]
except:
    print("Error while loading start data, exiting program.")
    exit()

# Attempts to load data from the timings data file, otherwise it creates it
try:
    with open(TIMINGS_DATA_FILE, "r") as f:
        timings_data = json.load(f)
except:
    timings_data = {
        "active_members": [],
    }

# Initialising Variables
valorant_called = False
valorant_channel = None
valorant_pings = []

# Creates Bot
bot = discord.Bot(intents=intents)

# Called on Bot Startup
@bot.event
async def on_ready():
    global valorant_channel
    valorant_channel = bot.get_channel(VALORANT_ID)
    await valorant_channel.send("Catbot successfully started.")
    print(f"Logged in succesfully as {bot.user}")

@bot.event
async def on_message(message):
    global timings_data, valorant_called, valorant_pings

    # Returns if not necessary case
    if message.author == bot.user or not valorant_called:
        return

    # Removes message author from pings, and calculates and saves timings
    if message.author.id in valorant_pings:
        valorant_pings.remove(message.author.id)
        timings_data[str(message.author.id)]["total"] += time.time() - timings_data[str(message.author.id)]["start"]
        with open("timings_data.json", "w") as f:
            json.dump(timings_data, f)

    # Stop case
    if ("STOP" in message.content and message.author.id == ADMIN_ID) or len(valorant_pings) == 0:
        valorant_called = False
        valorant_ping.stop()


# Cat Command
@bot.slash_command(description="Get some pussssyyyyyyy")
async def cat(ctx):
    request = requests.get(CAT_API)
    x = dict(request.json()[0])
    await ctx.respond(x["url"])

# Say Command
@bot.slash_command(description="Force the catbot to speak against its will")
async def say(ctx, text):
    await ctx.respond(text)

# Slay Command
@bot.slash_command(description="stop. fucking end yourself you pitiful scum.")
async def slay(ctx):
    await ctx.respond("i hope you die")

# Judgement Command
@bot.slash_command(description="gives out judgement")
async def judgement(ctx):
    global timings_data

    judgement_list = []

    # Gets all member's timings
    for key in timings_data:
        if key == "active_members" or key == "disappointment":
            continue
        judgement_list.append((key, round(timings_data[key]["total"], 1)))

    # Makes judgement text
    judgement_text = "Total Response Times:\n"
    disappointment = None
    for i, data in enumerate(sorted(judgement_list, key=lambda x: x[1], reverse=True)):
        judgement_text += f"{i + 1}. <@{data[0]}>: {data[1]} seconds\n"
        if i == 0:
            disappointment = int(data[0])
    judgement_text += f"\n<@{disappointment}> is the biggest disappointment.\nYou now have the role of shame, dirty 5 stack ruiner."

    # Reassigns disappointment role
    old_disappointment = timings_data["disappointment"]
    if disappointment != old_disappointment:
        timings_data["disappointment"] = disappointment
        old_disappointment_member = None
        disappointment_member = None
        for member in bot.get_all_members():
            if member.id == old_disappointment:
                old_disappointment_member = member
            if member.id == disappointment:
                disappointment_member = member
        await old_disappointment_member.remove_roles(bot.get_guild(GUILD_ID).get_role(DISAPPOINTMENT_ROLE_ID))
        await disappointment_member.add_roles(bot.get_guild(GUILD_ID).get_role(DISAPPOINTMENT_ROLE_ID))

    await ctx.respond(judgement_text)

# Valorant Command
@bot.slash_command(description="5 Stack Time. Get on.")
async def valorant(ctx, 
        member1: discord.Member = None, 
        member2: discord.Member = None, 
        member3: discord.Member = None,
        member4: discord.Member = None, 
        member5: discord.Member = None
    ):

    global timings_data, valorant_called, valorant_pings

    # Exit method if valorant call already being executed to avoid re-execution
    if valorant_called:
        await ctx.respond("Valorant pings already ongoing")
        return

    # Getting members list
    members = []
    if member1 and not member1.bot:
        members.append(member1.id)
    if member2 and not member2.bot:
        members.append(member2.id)
    if member3 and not member3.bot:
        members.append(member3.id)
    if member4 and not member4.bot:
        members.append(member4.id)
    if member5 and not member5.bot:
        members.append(member5.id)    

    # Sets up active members
    for member in members:
        if member not in timings_data["active_members"]:
            timings_data["active_members"].append(member)

    # Everyone case
    if len(members) == 0:
        members = copy.copy(timings_data["active_members"])

    # Initialises timings
    for member in members:
        if str(member) not in timings_data:
            timings_data[str(member)] = {
                "start": 0,
                "total": 0
            }
        timings_data[str(member)]["start"] = time.time()

    # Sets up pinging settings
    ping = await get_ping(members)
    valorant_called = True
    valorant_pings = members

    valorant_ping.start()
    
    await ctx.respond(f"{ping} valorant", allowed_mentions=allowed_mentions)

# Gets ping list
async def get_ping(ids):
    return " ".join([f"<@{user}>" for user in ids])

# Valorant ping loop
@tasks.loop(seconds=1)
async def valorant_ping():
    await valorant_channel.send(f"{await get_ping(valorant_pings)} valorant", allowed_mentions=allowed_mentions)

# Run Bot
bot.run(BOT_TOKEN)