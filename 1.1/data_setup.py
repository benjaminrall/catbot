import json

DEFAULT_DATA = {
    "CAT_API": "",
    "BOT_TOKEN": "",
    "VALORANT_ID": 0,
    "ADMIN_ID": 0,
    "DISAPPOINTMENT_ROLE_ID": 0,
    "GUILD_ID": 0
}

def setup():
    with open("data.json", "w") as f:
        json.dump(DEFAULT_DATA, f)