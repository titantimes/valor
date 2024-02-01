import discord
import os
import json
from discord.ext.commands import Bot, Context
import valor
import commands
import listeners
import ws
import cron
import logging
import time
from sql import ValorSQL
import asyncio
import aiomysql
from dotenv import load_dotenv
import multiprocessing
import platform

# this is supposedly "unsafe" on macos, but is the default on unix.
# alternatively use forkserver (or spawn, which breaks because it's unfreezable) instead of fork
if platform.mac_ver()[0]:
    multiprocessing.set_start_method("fork")

load_dotenv()
# set to GMT time
os.environ["TZ"] = "Europe/London"
time.tzset()

logging.basicConfig(format='%(asctime)s %(message)s')
logging.getLogger().setLevel(logging.INFO)
logging.warning("Starting")

loop = asyncio.get_event_loop()
valor = valor.Valor('-', intents=discord.Intents.all())

async def main():
    @valor.event
    async def on_ready():
        await valor.tree.sync()

    async with valor:
        ValorSQL.pool = await aiomysql.create_pool(**ValorSQL._info, loop=valor.loop)
        
        await commands.register_all(valor)
        await listeners.register_all(valor)
        await ws.register_all(valor)
        # loop.run_until_complete(cron._smp_loop(valor))
        # loop.run_until_complete(cron.gxp_roles(valor))
        
        await asyncio.gather(
            asyncio.ensure_future(valor.run()),
            asyncio.ensure_future(cron.gxp_roles(valor)),
            asyncio.ensure_future(cron.warcount_roles(valor))      
        )
        

asyncio.run(main())