from functools import lru_cache
import requests

dat = requests.get("https://api.wynncraft.com/public_api.php?action=statsLeaderboard&type=guild&timeframe=alltime").json()
@lru_cache(500)
def guild_name_from_tag_old(tag: str) -> str:
    tag = tag.lower()
    for k in dat["data"]:
        if k["prefix"].lower() == tag:
            return k["name"]
    return ''