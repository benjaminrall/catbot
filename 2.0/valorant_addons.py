from discord import Bot, Embed, ButtonStyle, Interaction
from discord.ui import Button, View
from constants import *

class ValorantCall:
    def __init__(self, creator, users, interaction):
        self.creator = creator
        self.active = True
        self.users = users
        self.interaction: Interaction = interaction
        self.responses = [0 for _ in range(len(users))] # 0: No Response, 1: Accepted, 2: Rejected No Reason, 3: Rejected Reason
        self.reasons = [None for _ in range(len(users))]
        self.voted = [False for _ in range(len(users))]
        self.pinging = [True for _ in range(len(users))]
        self.confirmed = [False for _ in range(len(users))]
        self.acceptance_times = [-1 for _ in range(len(users))]
        self.joined_call = [False for _ in range(len(users))]
        self.time_pinging = [0 for _ in range(len(users))]
        self.penalties = [0 for _ in range(len(users))]
        self.data = [
            {
                "score": 0, 
                "ping_time": 0,
                "penalties": 0,
                "acceptances": 0, 
                "acceptance_time": 0, 
                "acceptances_missed": 0,
                "no_reasons": 0, 
                "reasons": 0
            } 
            for _ in range(len(users))
        ]

    def get_users(self):
        return self.users

    def get_data(self, user):
        if user not in self.users:
            return 0
        return self.data[self.users.index(user)]

    def get_response_string(self, user):
        if user not in self.users:
            print(f"User {user} not found.")
            return None
        response_num = self.responses[self.users.index(user)]
        if response_num == 0:
            return "Not responded"
        elif response_num == 1:
            return "Accepted"
        elif response_num == 2:
            return "Rejected - No Reason Given"
        elif response_num == 3:
            return f"Rejected:\n{self.reasons[self.users.index(user)]}"
    
    def deactivate(self):
        self.active = False
        for i in range(len(self.users)):
            self.data[i]["score"] = self.time_pinging[i] / 60 + self.penalties[i]
            self.data[i]["ping_time"] = self.time_pinging[i] / 60
            self.data[i]["penalties"] = self.penalties[i]
            self.data[i]["acceptances"] = 1 if self.responses[i] == 1 else 0
            self.data[i]["no_reasons"] = 1 if self.responses[i] == 2 else 0
            self.data[i]["reasons"] = 1 if self.responses[i] == 3 else 0

    def respond(self, user, response_num):
        # Returns 0 if success, otherwise returns current response value or -1 if invalid user
        if user not in self.users:
            return -1
        response = self.responses[self.users.index(user)]
        if response == 0:
            self.responses[self.users.index(user)] = response_num
            if response_num == 2:
                self.penalties[self.users.index(user)] += REJECTION_PENALTY
                self.confirmed[self.users.index(user)] = True
            return 0
        return response

    def give_reason(self, user, reason):
        # Returns same value as respond() method, but also sets a reason if valid
        if user not in self.users:
            return -1
        response = self.responses[self.users.index(user)]
        if response == 0 or response == 2:
            self.responses[self.users.index(user)] = 3
            self.reasons[self.users.index(user)] = reason
            if response == 0:
                self.penalties[self.users.index(user)] += REASON_PENALTY
                self.confirmed[self.users.index(user)] = True
            else:
                self.penalties[self.users.index(user)] -= REJECTION_PENALTY - REASON_PENALTY
            return 0
        return response

    async def get_pings(self):
        return " ".join([f"<@{user}>" for i, user in enumerate(self.users) if self.pinging[i]])

    async def update(self, bot: Bot):
        for i, response in enumerate(self.responses):
            self.pinging[i] = response == 0
            if self.pinging[i]:
                self.time_pinging[i] += 1
            if response == 1 and not self.joined_call[i]:
                if self.interaction.guild.get_member(self.users[i]).voice is not None:
                    self.joined_call[i] = True
                    self.confirmed[i] = True
                    self.data[i]["acceptance_time"] = (JOINING_TIME_LIMIT - self.acceptance_times[i]) / 60
                    continue
                if self.acceptance_times[i] == -1:
                    self.acceptance_times[i] = JOINING_TIME_LIMIT
                self.acceptance_times[i] -= 1
                if self.acceptance_times[i] == 0:
                    self.acceptance_times[i] = -1
                    no_time_embed = Embed(description="Status returned to 'Not Accepted' and penalty administered.")
                    no_time_embed.set_author(name=f"{bot.get_user(self.users[i]).display_name} failed to join call in time.",
                        icon_url=VALORANT_ICON)
                    await self.interaction.followup.send(embed=no_time_embed)
                    self.responses[i] = 0
                    self.penalties[i] += NO_JOINING_PENALTY
                    self.data[i]["acceptances_missed"] += 1
            if response == 2:
                self.time_pinging[i] += NO_REASON_TIME_MULTIPLIER
        if all(self.confirmed):
            self.deactivate()
            ended_embed = await generate_embed(bot, self)
            await self.interaction.edit_original_message(embed=ended_embed, view=None)
            

async def generate_embed(bot: Bot, valorant_call: ValorantCall) -> Embed:
    users = [bot.get_user(user) for user in valorant_call.users]

    embed = Embed(description="Join now, or risk becoming the 5 STACK RUINER.")
    embed.set_author(name=bot.get_user(valorant_call.creator).display_name
        + " is calling for Valorant.", icon_url=VALORANT_ICON)
    
    for user in users:
        embed.add_field(
            name=f"{user.display_name}",
            value=f"{valorant_call.get_response_string(user.id)}"
        )

    if not valorant_call.active:
        embed.set_footer(text="This call has ended.")
    
    return embed

async def generate_view(bot, valorant_call: ValorantCall) -> View:
    if not valorant_call.active:
        return None

    view = View()

    async def accept_button_callback(interaction: Interaction):
        accept_response = valorant_call.respond(interaction.user.id, 1)
        # User not in call
        if accept_response == -1:
            await interaction.response.send_message(content="You are unable to accept a call " 
                + "that you are not a part of.", ephemeral=True)
        # Valid acceptance
        elif accept_response == 0:
            await interaction.response.edit_message(embed=await generate_embed(bot, valorant_call))
            followup_embed = Embed()
            followup_embed.set_author(name=interaction.user.display_name 
                + " has accepted the call.", icon_url=VALORANT_ICON)
            await interaction.followup.send(embed=followup_embed)
            await interaction.followup.send(content="Valorant call accepted successfully." 
            + "\nYou have 15 minutes to join call or else you will receive a penalty.", ephemeral=True)
        # Already accepted
        elif accept_response == 1:
            await interaction.response.send_message(content="You have already accepted this call.",
                ephemeral=True)
        # Already rejected
        elif accept_response == 2 or accept_response == 3:
            await interaction.response.send_message(content="You cannot accept a call that you "
                + "have already rejected.", ephemeral=True)

    async def reject_button_callback(interaction: Interaction):
        reject_response = valorant_call.respond(interaction.user.id, 2)
        # User not in call
        if reject_response == -1:
            await interaction.response.send_message(content="You are unable to reject a call " 
                + "that you are not a part of.", ephemeral=True)
        # Valid acceptance
        elif reject_response == 0:
            await interaction.response.edit_message(embed=await generate_embed(bot, valorant_call))
            followup_embed = Embed(description="Reason yet to be provided.")
            followup_embed.set_author(name=interaction.user.display_name 
                + " has rejected the call.", icon_url=VALORANT_ICON)
            await interaction.followup.send(embed=followup_embed)
        # Already accepted
        elif reject_response == 1:
            await interaction.response.send_message(content="You cannot reject a call that you "
                + "have already accepted.\nYou must wait until the acception timer runs out, "
                + "suffer the penalty, and then reject it.", ephemeral=True)
        # Already rejected
        elif reject_response == 2 or reject_response == 3:
            await interaction.response.send_message(content="You have already rejected this call.",
                ephemeral=True)

    async def cancel_button_callback(interaction: Interaction):
        if interaction.user.id != valorant_call.creator \
                and interaction.user.id not in ADMINS:
            await interaction.response.send_message(content="You cannot cancel a call " 
                + "that you did not create.", ephemeral=True)
            return
        valorant_call.deactivate()
        cancelled_embed = Embed()
        cancelled_embed.set_author(name="Valorant call cancelled.", icon_url=VALORANT_ICON)
        await interaction.response.edit_message(embed=cancelled_embed, view=None)

    accept_button = Button(label="Accept", style=ButtonStyle.green, emoji="✅")
    reject_button = Button(label="Reject", style=ButtonStyle.red, emoji="⛔")
    cancel_button = Button(label="Cancel", style=ButtonStyle.blurple)

    accept_button.callback = accept_button_callback
    reject_button.callback = reject_button_callback
    cancel_button.callback = cancel_button_callback
    
    view.add_item(accept_button)
    view.add_item(reject_button)
    view.add_item(cancel_button)

    return view