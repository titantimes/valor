import websockets
import asyncio
from valor import Valor
from sql import ValorSQL
from dotenv import load_dotenv
import json
import os
import time
import requests
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed

load_dotenv()
async def _register_terr_track(valor: Valor):
    terrs = {
        "Volcano Upper",
        "Lost Atoll",
        "Pirate Town",
        "Zhight Island",
        "The Bear Zoo",
        "Rooster Island",
        "Durum Isles Lower",
        "Durum Isles Center",
        "Durum Isles East",
        "Durum Isles Upper",
        "Mage Island",
        "Half Moon Island",
        "Santa's Hideout",
        "Icy Island",
        "Dujgon Nation",
        "Nodguj Nation",
        "Regular Island",
        "Dead Island South East",
        "Dead Island North East",
        "Dead Island North West",
        "Dead Island South West",
        "Maro Peaks",
        "Tree Island",
        "Skiens Island",
        "Selchar",
        "Jofash Docks",
        "Jofash Tunnel"
    }

    async def task():
        await valor.wait_until_ready()
        chn_ids = [m[0] for m in await ValorSQL.get_all_configs()]
        last_pinged = 0

        while not valor.is_closed():
            c = await websockets.connect("ws://localhost"+os.environ["RMPORT"]) # await websockets.connect("ws://"+os.environ["REMOTE"]+os.environ["RMPORT"]+"/ws")
            try:
                async for msg in c:
                    msg = json.loads(msg)
                    for action in msg:
                        if action.get("defender") == "Titans Valor" and action.get("territory") in terrs:
                            for cid in chn_ids:
                                chn = valor.get_channel(cid)
                                if chn and time.time()-last_pinged >= 3600:
                                    ping_msg = "4+ Strat+ online. Ping voided"
                                    dat = requests.get("https://api.wynncraft.com/public_api.php?action=guildStats&command=Titans%20Valor").json()["members"]
                                    online_all = requests.get("https://api.wynncraft.com/public_api.php?action=onlinePlayers").json()
                                    
                                    online_guild = []
                                    for k in online_all:
                                        if k[:2] != "WC":
                                            continue
                                        online_guild += online_all[k]

                                    online_guild = set(online_guild)
                                    
                                    if sum(m["rank"] in {"STRATEGIST", "CHIEF", "OWNER"} for m in dat if m["name"] in online_guild) < 4:
                                        ping_msg = "<@&683785435117256939>"
                                    await chn.send(ping_msg, embed=LongTextEmbed("We're under attack!", 
                                    f"Attacker: **{action['attacker']}**\nTerritory: **{action['territory']}**",
                                    color=0xFF2222, footer="I'm sorry if this pings a billion times. Its cooldown is set to 1 hour now."))
                                    last_pinged = time.time()
            except Exception as e:
                await asyncio.sleep(30)
                await c.close()
                print("Reconnecting websocket")
                
    valor.loop.create_task(task())