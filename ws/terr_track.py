import websockets
import asyncio
from valor import Valor
from sql import ValorSQL
from dotenv import load_dotenv
import json
import os
import time
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
        "Twain Mansion"
    }

    async def task():
        await valor.wait_until_ready()
        chn_ids = [m[0] for m in ValorSQL.get_all_configs()]
        last_pinged = 0

        while not valor.is_closed():
            c = await websockets.connect("ws://"+os.environ["REMOTE"]+os.environ["RMPORT"]+"/ws")
            try:
                async for msg in c:
                    parsed = json.loads(msg)
                    if msg.get("defender") == "Titans Valor" and msg.get("territory") in terrs:
                        for cid in chn_ids:
                            chn = valor.get_channel(cid)
                            if chn and time.time()-last_pinged >= 3600*2:
                                await chn.send_message(embed=LongTextEmbed("Ping! We're under attack!", 
                                f"Attacker: **{msg['attacker']}**\nTerritory: **{msg['territory']}**",
                                color=0xFF2222))
                                last_pinged = time.time()
            except Exception as e:
                await asyncio.sleep(30)
                await c.close()
                print("Reconnecting websocket")
                raise e
                
    valor.loop.create_task(task())