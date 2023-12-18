from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed
from dotenv import load_dotenv
import time

load_dotenv()

async def _register_inspire(valor: Valor):
    desc = "Inspire command.\nGenerates inspirational images from https://inspirobot.me/.\nAdded at Micah's request."
    http = valor.ahttp

    @valor.command()
    async def inspire(ctx: Context):
        start = time.time()
        inspiro_uri = await http.get_text("https://inspirobot.me/api?generate=true")
        duration = time.time()-start
        return await LongTextEmbed.send_message(valor, ctx, "Inspire", color=0xFF00, reply=True, footer=f"inspirobot.me took {duration:.3}s", url=inspiro_uri)

    @inspire.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed(f"{error}"))
    
    @valor.help_override.command()
    async def inspire(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Inspire", desc, color=0xFF00)
    