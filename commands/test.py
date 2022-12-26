from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, HelpEmbed, LongFieldEmbed
import random
import requests

async def _register_test(valor: Valor):
    desc =  "Spooky test command. Used to quickly test various different things"
    @valor.group()
    async def test(ctx: Context):
        if not ctx.invoked_subcommand:
            await LongTextEmbed.send_message(valor, ctx, "test", "it's just a normal command. What else can I say?")
    
    @test.command()
    async def fields(ctx: Context):
        content = [("this", "no longer does anything funny")]

        await LongFieldEmbed.send_message(valor, ctx, "Field Test", content)

    @valor.help_override.command()
    async def test(ctx: Context):
        await ctx.send(desc)

