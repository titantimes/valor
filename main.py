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

async def main():
    async with valor:
        loop = asyncio.get_event_loop()

        valor = valor.Valor('-', intents=discord.Intents.all())

        ValorSQL.pool = valor.loop.run_until_complete(aiomysql.create_pool(**ValorSQL._info, loop=valor.loop))

        loop.run_until_complete(commands.register_all(valor))
        loop.run_until_complete(listeners.register_all(valor))
        loop.run_until_complete(ws.register_all(valor))
        # loop.run_until_complete(cron._smp_loop(valor))

        valor.run()

asyncio.run(main())