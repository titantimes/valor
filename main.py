import discord
import os
import json
from discord.ext.commands import Bot, Context
import valor
import commands
import asyncio

valor = valor.Valor('-')

loop = asyncio.get_event_loop()
loop.run_until_complete(commands.register_all(valor))

valor.run()
