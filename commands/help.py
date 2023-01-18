from valor import Valor
from util import ErrorEmbed, HelpEmbed
from discord.ext.commands import Context

async def _register_help(valor: Valor):
    # Remove default help command
    valor.help_command = None
    @valor.hybrid_command()
    async def help2(ctx: Context):
        await ctx.send("working on help2 with fancy interactions")

    @valor.group()
    async def help(ctx: Context):
        if not ctx.invoked_subcommand:
            await HelpEmbed.send_message(valor, ctx)
    valor.help_override = help