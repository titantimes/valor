from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, HelpEmbed, LongFieldEmbed
import random
import requests

async def _register_info(valor: Valor):
    desc =  "All macro-like, static commands"
    
    @valor.command()
    async def medals(ctx: Context):
        await ctx.send('https://docs.google.com/document/d/1vTrHIM91574Vb3Mi4vF99XNP3eJueGynMBW0qgyKLl8')


