import requests

def get_uuid(player: str):
    uuid = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}").json()["id"]
    return uuid[:8]+'-'+uuid[8:12]+'-'+uuid[12:16]+'-'+uuid[16:20]+'-'+uuid[20:]
