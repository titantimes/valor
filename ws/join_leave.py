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
async def _register_join_leave(valor: Valor):
    async def task():
        await valor.wait_until_ready()
        chn_id = 717490202909737101
        while not valor.is_closed():
            c = await websockets.connect("ws://localhost"+os.environ["RMPORT"]) # await websockets.connect("ws://"+os.environ["REMOTE"]+os.environ["RMPORT"]+"/ws")
            try:
                async for msg in c:
                    msg = json.loads(msg)

                    if msg.get("type", -1) != 'join':
                        continue
                    
                    await valor.get_channel(chn_id).send("<-"+str(msg["leave"]))
                    await valor.get_channel(chn_id).send("->"+str(msg["join"]))
            except Exception as e:
                print(e)
                await asyncio.sleep(30)
                await c.close()
                print("Reconnecting websocket")
                
    valor.loop.create_task(task())