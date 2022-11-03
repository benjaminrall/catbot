import json
import discord
from discord.ext import tasks
from valorant_addons import *
from constants import *
import copy

# Discord Settings
intents = discord.Intents.all()

valorant_call: ValorantCall = None
valorant_channel: discord.TextChannel = None

current_vote = None

data = {}
try:
    with open("data.json", "r") as f:
        data = json.load(f)
except:
    with open("data.json", "w") as f:
        json.dump(data, f)
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    global valorant_channel
    valorant_channel = bot.get_channel(PINGS_CHANNEL)
    print(f"Logged in succesfully as {bot.user}")

# VALORANT COMMAND
@bot.slash_command(description="Valorant time. Get on.")
async def valorant(ctx,
        user1: discord.Member = None, 
        user2: discord.Member = None, 
        user3: discord.Member = None,
        user4: discord.Member = None, 
        user5: discord.Member = None
    ):

    global valorant_call

    # Exit method if valorant call already being executed to avoid re-execution
    if valorant_call is not None and valorant_call.active:
        await ctx.respond("Previous valorant call still ongoing.")
        return

    creator = ctx.author.id

    # Getting users list
    all_users = [user1, user2, user3, user4, user5]
    if not any(all_users):
        all_users = [bot.get_user(user) for user in ALL_USERS]
    users = []
    for user in all_users:
        if user is not None and not user.bot and user.id != creator and user not in users:
            users.append(user.id)
    
    valorant_call = ValorantCall(creator, users, ctx.interaction) 

    update_valorant_call.start()

    await ctx.respond(
        embed = await generate_embed(bot, valorant_call),
        view = await generate_view(bot, valorant_call)
    )

# CANCEL COMMAND
@bot.slash_command(description="Cancels a Valorant Call you created.")
async def cancel(ctx):
    global valorant_call
    if valorant_call is None or not valorant_call.active:
        await ctx.respond(
            content="No valorant call is active to be cancelled.",
            ephemeral=True
        )
        return
    interaction = ctx.interaction
    if interaction.user.id != valorant_call.creator \
            and interaction.user.id not in ADMINS:
        await ctx.respond(content="You cannot cancel a call " 
            + "that you did not create.", ephemeral=True)
        return
    valorant_call.deactivate()
    cancelled_embed = Embed()
    cancelled_embed.set_author(name="Valorant call cancelled.", icon_url=VALORANT_ICON)
    await valorant_call.interaction.edit_original_message(embed=cancelled_embed, view=None)
    await ctx.respond(content="Valorant call cancelled succesfully.", ephemeral=True)

# ACCEPT COMMAND
@bot.slash_command(description="Accepts the current valorant call.")
async def accept(ctx):
    global valorant_call
    if valorant_call is None or not valorant_call.active:
        await ctx.respond(
            content="No valorant call is active to be accepted.",
            ephemeral=True
        )
        return
    accept_response = valorant_call.respond(ctx.interaction.user.id, 1)
    # User not in call
    if accept_response == -1:
        await ctx.respond(content="You are unable to accept a call " 
            + "that you are not a part of.", ephemeral=True)
    # Valid acceptance
    elif accept_response == 0:
        await valorant_call.interaction.edit_original_message(embed=await generate_embed(bot, valorant_call))
        followup_embed = Embed()
        followup_embed.set_author(name=ctx.interaction.user.display_name 
            + " has accepted the call.", icon_url=VALORANT_ICON)
        await valorant_call.interaction.followup.send(embed=followup_embed)
        await ctx.respond(content="Valorant call accepted successfully." 
            + "\nYou have 15 minutes to join call or else you will receive a penalty.", ephemeral=True)
    # Already accepted
    elif accept_response == 1:
        await ctx.respond(content="You have already accepted this call.", ephemeral=True)
    # Already rejected
    elif accept_response == 2 or accept_response == 3:
        await ctx.respond(content="You cannot accept a call that you have already rejected.", 
            ephemeral=True)

# REJECT COMMAND
@bot.slash_command(description="Rejects the current valorant call. (Dumb) (Bad)")
async def reject(ctx, reason: str = None):
    global valorant_call
    if valorant_call is None or not valorant_call.active:
        await ctx.respond(
            content="No valorant call is active to be rejected.",
            ephemeral=True
        )
        return
    if reason is None:
        reject_response = valorant_call.respond(ctx.interaction.user.id, 2)
    else:
        reject_response = valorant_call.give_reason(ctx.interaction.user.id, reason)
    # User not in call
    if reject_response == -1:
        await ctx.respond(content="You are unable to reject a call " 
            + "that you are not a part of.", ephemeral=True)
    # Valid rejection
    elif reject_response == 0:
        await valorant_call.interaction.edit_original_message(embed=await generate_embed(bot, valorant_call))
        followup_embed = Embed(description=f"Reason" + " yet to be provided." if reason is None else reason)
        followup_embed.set_author(name=ctx.interaction.user.display_name 
            + " has rejected the call" + (" with a reason." if reason is not None else "."), icon_url=VALORANT_ICON)
        await valorant_call.interaction.followup.send(embed=followup_embed)
        await ctx.respond(content="Valorant call rejected successfully.", ephemeral=True)
    # Already accepted
    elif reject_response == 1:
        await ctx.respond(content="You cannot reject a call that you "
                + "have already accepted.\nYou must wait until the acception timer runs out, "
                + "suffer the penalty, and then reject it.", ephemeral=True)
    # Already rejected
    elif reject_response == 2 or reject_response == 3:
        await ctx.respond(content="You have already rejected this call.", ephemeral=True)

# REASON COMMAND
@bot.slash_command(description="Gives a reason if you have already rejected the valorant call. (Dumb) (Bad)")
async def reason(ctx, reason: str):
    global valorant_call
    if valorant_call is None or not valorant_call.active:
        await ctx.respond(
            content="No valorant call is active to be rejected.",
            ephemeral=True
        )
        return
    reject_response = valorant_call.give_reason(ctx.interaction.user.id, reason)
    # User not in call
    if reject_response == -1:
        await ctx.respond(content="You are unable to reject a call " 
            + "that you are not a part of.", ephemeral=True)
    # Valid rejection
    elif reject_response == 0:
        await valorant_call.interaction.edit_original_message(embed=await generate_embed(bot, valorant_call))
        followup_embed = Embed(description=f"Reason" + " yet to be provided." if reason is None else reason)
        followup_embed.set_author(name=ctx.interaction.user.display_name 
            + " has rejected the call" + (" with a reason." if reason is not None else "."), icon_url=VALORANT_ICON)
        await valorant_call.interaction.followup.send(embed=followup_embed)
        await ctx.respond(content="Valorant call rejected successfully with reason.", ephemeral=True)
    # Already accepted
    elif reject_response == 1:
        await ctx.respond(content="You cannot reject a call that you "
                + "have already accepted.\nYou must wait until the acception timer runs out, "
                + "suffer the penalty, and then reject it.", ephemeral=True)
    # Already rejected
    elif reject_response == 2 or reject_response == 3:
        await ctx.respond(content="You have already rejected this call with a reason.", ephemeral=True)

# VOTE COMMAND
@bot.slash_command(description="Vote for whether an extra penalty should be applied to somebody's excuse")
async def vote(ctx, user: discord.Member):
    global valorant_call, current_vote, data 
    if user is None:
        await ctx.respond(content="Invalid user given.", ephemeral=True)
        return
    if valorant_call is None:
        await ctx.respond(content="No valid valorant call to vote on.", ephemeral=True)
        return
    if user.id not in valorant_call.users:
        await ctx.respond(content="That user was not part of the most recent valorant call, so cannot be voted for.", ephemeral=True)
        return
    if current_vote is not None:
        await ctx.respond(content="There is already an ongoing vote. Wait for the current vote to end and then try again.", ephemeral=True)
        return
    valorant_call_index = valorant_call.users.index(user.id)
    if valorant_call.responses[valorant_call_index] != 3:
        await ctx.respond(content="That user has not rejected the most recent valorant call with a reason, so cannot be voted for.", ephemeral=True)
        return
    if valorant_call.voted[valorant_call_index]:
        await ctx.respond(content="That user has already been voted for during the most recent valorant call, so cannot be voted for again.", ephemeral=True)
        return
        
    current_vote = {
        "creator": ctx.user,
        "target": user,
        "interaction": ctx.interaction,
        "voters": [u for u in ALL_USERS if u != ctx.user.id and u != user.id],
        "voted": [],
        "total_votes": 0,
        "valid_votes": 0,
        "invalid_votes": 0
    }

    creator_key = str(ctx.user.id)
    target_key = str(user.id)

    if creator_key not in data:
        data[creator_key] = copy.copy(TEMPLATE_DATA)
    if target_key not in data:
        data[target_key] = copy.copy(TEMPLATE_DATA)

    data[creator_key]["votes_started"] += 1
    data[target_key]["voted_against"] += 1

    embed = Embed()
    embed.set_author(name=f"{ctx.author.display_name} has started a vote for {user.display_name}'s excuse.", icon_url=user.display_avatar)
    embed.add_field(name="The excuse in question is: ", value=f"{valorant_call.reasons[valorant_call_index]}")
    embed.set_footer(text="Vote using the buttons below. \nIf the majority votes for the reason being invalid, a penalty will be added.")
    
    view = View()

    async def valid_button_callback(interaction: Interaction):
        global current_vote
        if interaction.user.id not in current_vote["voters"]:
            await interaction.response.send_message(
                content="You are not allowed to vote in this matter.", ephemeral=True)
            return
        if interaction.user.id in current_vote["voted"]:
            await interaction.response.send_message(
                content="You have already voted in this matter.", ephemeral=True)
            return
        current_vote["voted"] += [interaction.user.id]
        current_vote["total_votes"] += 1
        current_vote["valid_votes"] += 1
        voter_key = str(interaction.user.id)
        if voter_key not in data:
            data[voter_key] = copy.copy(TEMPLATE_DATA)
        data[voter_key]["valid_votes"] += 1
        voted_embed = Embed(description=f"{current_vote['total_votes']}/{len(current_vote['voters'])} votes submitted.")
        voted_embed.set_author(name=f"{interaction.user.display_name} has voted 'Valid'", 
            icon_url=interaction.user.display_avatar)
        await interaction.response.send_message(embed=voted_embed)
        if current_vote["total_votes"] == len(current_vote["voters"]) \
                or current_vote["invalid_votes"] > len(current_vote["voters"]) // 2 \
                or current_vote["valid_votes"] > len(current_vote["voters"]) // 2:
            await finalise_current_vote()

    async def invalid_button_callback(interaction: Interaction):
        global current_vote
        if interaction.user.id not in current_vote["voters"]:
            await interaction.response.send_message(
                content="You are not allowed to vote in this matter.", ephemeral=True)
            return
        if interaction.user.id in current_vote["voted"]:
            await interaction.response.send_message(
                content="You have already voted in this matter.", ephemeral=True)
            return
        current_vote["voted"] += [interaction.user.id]
        current_vote["total_votes"] += 1
        current_vote["invalid_votes"] += 1
        voter_key = str(interaction.user.id)
        if voter_key not in data:
            data[voter_key] = copy.copy(TEMPLATE_DATA)
        data[voter_key]["invalid_votes"] += 1
        voted_embed = Embed(description=f"{current_vote['total_votes']}/{len(current_vote['voters'])} votes submitted.")
        voted_embed.set_author(name=f"{interaction.user.display_name} has voted 'Invalid'", 
            icon_url=interaction.user.display_avatar)
        await interaction.response.send_message(embed=voted_embed)
        if current_vote["total_votes"] == len(current_vote["voters"]) \
                or current_vote["invalid_votes"] > len(current_vote["voters"]) // 2 \
                or current_vote["valid_votes"] > len(current_vote["voters"]) // 2:
            await finalise_current_vote()

    async def cancel_button_callback(interaction: Interaction):
        global current_vote
        if interaction.user.id != current_vote["creator"].id \
                and interaction.user.id not in ADMINS:
            await interaction.response.send_message(content="You cannot cancel a vote " 
                + "that you did not create.", ephemeral=True)
            return
        cancelled_embed = Embed()
        cancelled_embed.set_author(name="Vote cancelled.", icon_url=current_vote["creator"].display_avatar)
        await interaction.response.edit_message(embed=cancelled_embed, view=None)
        current_vote = None
        with open("data.json", "w") as f:
            f.write(json.dumps(data, indent=4))

    valid_button = Button(label="Valid", style=ButtonStyle.green)
    invalid_button = Button(label="Invalid", style=ButtonStyle.red)
    cancel_button = Button(label="Cancel", style=ButtonStyle.blurple)

    valid_button.callback = valid_button_callback
    invalid_button.callback = invalid_button_callback
    cancel_button.callback = cancel_button_callback

    view.add_item(valid_button)
    view.add_item(invalid_button)
    view.add_item(cancel_button)

    await ctx.respond(embed=embed, view=view)

async def finalise_current_vote():
    global valorant_call, current_vote, data
    if current_vote is None:
        return
    interaction: Interaction = current_vote["interaction"]
    vote_embed = Embed()
    vote_embed.set_author(name="This vote has now ended.", icon_url=current_vote["target"].display_avatar)
    await interaction.edit_original_message(embed=vote_embed, view=None)
    ended_embed = Embed()
    ended_embed.set_author(name=f"The vote against {current_vote['target'].display_name} has concluded.", 
        icon_url=current_vote['target'].display_avatar)
    verdict = ""
    if current_vote["invalid_votes"] > current_vote["valid_votes"]:
        verdict = "The reason was deemed to be invalid, and the" \
                + " full rejection penalty has been administered."
        target_id = current_vote["target"].id
        valorant_call.reasons[valorant_call.users.index(target_id)] += "\nVOTED INVALID"
        data[str(target_id)]["score"] += REJECTION_PENALTY - REASON_PENALTY
        data[str(target_id)]["vote_penalties"] += REJECTION_PENALTY - REASON_PENALTY 
    elif current_vote["invalid_votes"] < current_vote["valid_votes"]:
        verdict = "The reason was deemed to be valid, and no" \
                + " further penalty has been administered."
    else:
        verdict = "The vote ended in a draw, so no action has been taken."
    ended_embed.add_field(name="Final Verdict:", value=verdict)
    valorant_call.voted[valorant_call.users.index(current_vote["target"].id)] = True
    await valorant_call.interaction.edit_original_message(
        embed = await generate_embed(bot, valorant_call),
        view = await generate_view(bot, valorant_call)
    )
    await interaction.followup.send(embed=ended_embed)
    current_vote = None
    with open("data.json", "w") as f:
        f.write(json.dumps(data, indent=4))

@bot.slash_command(description="Give a further punishment to someone in particularly disappointing cases.")
async def punish(ctx, user: discord.Member, amount: int):
    pass

# LOOP TASK
@tasks.loop(seconds=1)
async def update_valorant_call():
    global valorant_call, valorant_channel, data
    await valorant_call.update(bot)
    if any(valorant_call.pinging):
        await valorant_channel.send(f"valorant {await valorant_call.get_pings()}")
    if not valorant_call.active:
        for u in valorant_call.users:
            user = str(u)
            new_data = valorant_call.get_data(u)
            if user not in data:
                data[user] = copy.copy(TEMPLATE_DATA)
            for key in new_data:
                if key not in data[user]:
                    data[user][key] = 0
                data[user][key] += new_data[key]
        with open("data.json", "w") as f:
            f.write(json.dumps(data, indent=4))
        update_valorant_call.stop()

bot.run(BOT_TOKEN)