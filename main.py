import discord
import os
import json
from discord.ext.commands import Bot, Context
import valor
import commands
import listeners
import asyncio
import logging
import time
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='%(asctime)s %(message)s')
logging.getLogger().setLevel(logging.INFO)
logging.warning("Starting")
valor = valor.Valor('-')

loop = asyncio.get_event_loop()
loop.run_until_complete(commands.register_all(valor))
loop.run_until_complete(listeners.register_all(valor))

async def check():
    while True:
        logging.info("Ping")
        await asyncio.sleep(60)
loop.create_task(check())

valor.run()
