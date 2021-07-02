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
        "Desolate Valley",
        "Nesaak Transition",
        "Nesaak Village",
        "Nesaak Plains Upper North West",
        "Nesaak Plains Mid North West",
        "Nesaak Plains Lower North West",
        "Nesaak Plains North East",
        "Nesaak Plains South West",
        "Nesaak Plains South East",
        "Nesaak Bridge Transition",
        "Great Bridge Nesaak",
        "Icy Descent",
        "Lusuco",
        "Twain Lake",
        "Twain Mansion",
        "Sanctuary Bridge",
        "Nether Plains Lower"
    }

    async def task():
        await valor.wait_until_ready()
        chn_ids = [m[0] for m in ValorSQL.get_all_configs()]
        last_pinged = 0

        while not valor.is_closed():
            c = await websockets.connect("ws://"+os.environ["REMOTE"]+os.environ["RMPORT"]+"/ws")
            try:
                async for msg in c:
                    msg = json.loads(msg)
                    for action in msg:
                        if action.get("defender") == "Titans Valor" and action.get("territory") in terrs:
                            for cid in chn_ids:
                                chn = valor.get_channel(cid)
                                if chn and time.time()-last_pinged >= 3600:
                                    ping_msg = "3+ Strat+ online. Ping voided"
                                    dat = requests.get("https://api.wynncraft.com/public_api.php?action=guildStats&command=Titans%20Valor").json()["members"]
                                    if sum(m["rank"] in {"STRATEGIST", "CHIEF", "OWNER"} for m in dat) < 3:
                                        ping_msg = "<@&683785435117256939>"
                                    await chn.send(ping_msg, embed=LongTextEmbed("We're under attack!", 
                                    f"Attacker: **{action['attacker']}**\nTerritory: **{action['territory']}**",
                                    color=0xFF2222, footer="I'm sorry if this pings a billion times. Its cooldown is set to 1 hour now."))
                                    last_pinged = time.time()
            except Exception as e:
                await asyncio.sleep(30)
                await c.close()
                print("Reconnecting websocket")
                raise e
                
    valor.loop.create_task(task())