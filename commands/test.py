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
            await LongTextEmbed.send_message(valor, ctx, "test", '\n'.join(
                ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for x in range(100)) for _ in range(random.randrange(100))))
    
    @test.command()
    async def fields(ctx: Context):
        content = [*zip(
            [''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for x in range(1, 50)) for _ in range(random.randrange(1, 200))],
            [''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for x in range(1, 50)) for _ in range(random.randrange(1, 200))]
        )]

        await LongFieldEmbed.send_message(valor, ctx, "Field Test", content)

    @valor.help_override.command()
    async def test(ctx: Context):
        await ctx.send(desc)

