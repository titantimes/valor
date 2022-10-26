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
    async with valor:
        ValorSQL.pool = valor.loop.run_until_complete(await aiomysql.create_pool(**ValorSQL._info, loop=valor.loop))

        loop.run_until_complete(commands.register_all(valor))
        loop.run_until_complete(listeners.register_all(valor))
        loop.run_until_complete(ws.register_all(valor))
        # loop.run_until_complete(cron._smp_loop(valor))

        await valor.run()

asyncio.run(main())