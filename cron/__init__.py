import asyncio
from valor import Valor
from dotenv import load_dotenv
import json
import os
import requests
import time
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed

load_dotenv()
async def _smp_loop(valor: Valor):
    plyrs = set(os.environ["PLAYERS"].split(','))
    checked = set()
    async def task():
        await valor.wait_until_ready()

        while not valor.is_closed():
            online = requests.get("https://api.mcsrvstat.us/2/157.90.65.205:25565").json()["players"]["uuid"]
            online_rev = {uuid: v for v, uuid in online.items()}
            intersect = set(online.values()) & plyrs
            for m in checked:
                if not m in intersect:
                    checked.remove(m)
            res = [m for m in intersect if not m in checked]
            if res:
                await (await valor.fetch_user(int(os.environ["SENDTO"]))).send(repr([online_rev[x] for x in res]) + "\n joined Hestia SMP")
            for m in intersect:
                checked.add(m)

            await asyncio.sleep(60)
    # valor.loop.create_task(task())