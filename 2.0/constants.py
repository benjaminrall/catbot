# Bot token should be in separate file 'token.txt' containing the bot's token on a single line
BOT_TOKEN = ""
with open("token.txt", "r") as f:
    BOT_TOKEN = f.readline()

# Link to a valorant icon
VALORANT_ICON = "https://cdn.iconscout.com/icon/free/png-256/valorant-3251602-2724649.png"
# List of admin user IDs - admins can cancel other people's votes, valorant calls etc and can adjust points manually
ADMINS = [312250768038297600]
# Channel to send valorant pings to
PINGS_CHANNEL = 1034961307381805107
# List of all users to be pinged with an empty /valorant call
#ALL_USERS = [312250768038297600, 204316473882181633, 354758457167052811, 707654215849345057, 221264723512000512, 867176767022301204]
ALL_USERS = [312250768038297600, 867176767022301204, 1036313168412155984]
# Penalty for rejecting without a reason
REJECTION_PENALTY = 90
# Penalty for rejecting with a reason
REASON_PENALTY = 30
# Time limit for joining a call after accepting
JOINING_TIME_LIMIT = 900
# Penalty for not joining within the time limit after accepting
NO_JOINING_PENALTY = 30
# Time multiplier for rejecting without a reason
NO_REASON_TIME_MULTIPLIER = 2

TEMPLATE_DATA = {
    "score": 0,
    "ping_time": 0,
    "penalties": 0,
    "acceptances": 0,
    "acceptance_time": 0,
    "acceptances_missed": 0,
    "no_reasons": 0,
    "reasons": 0,
    "votes_started": 0,
    "valid_votes": 0,
    "invalid_votes": 0,
    "voted_against": 0,
    "vote_penalties": 0
}