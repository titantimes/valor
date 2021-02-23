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
# set to GMT time
os.environ["TZ"] = "Europe/London"
time.tzset()

logging.basicConfig(format='%(asctime)s %(message)s')
logging.getLogger().setLevel(logging.INFO)
logging.warning("Starting")
valor = valor.Valor('-')

loop = asyncio.get_event_loop()
loop.run_until_complete(commands.register_all(valor))
loop.run_until_complete(listeners.register_all(valor))

valor.run()
