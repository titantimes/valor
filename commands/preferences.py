from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed
from sql import ValorSQL

pref_list = ["wynnbuilder"]
pref_set = set(pref_list)

async def _register_preferences(valor: Valor):
    desc = """
    Enables / Disables a feature
    To use, do -preferences <disable/enable> <preference name>
    """

    @valor.group()
    async def preferences(ctx: Context):
        if not ctx.invoked_subcommand:
            await LongTextEmbed.send_message(valor, ctx, "Preferences", "Please refer to **-help preferences** \
                The following preferences are available to modify:\n" + '\n'.join(pref_list))

    @preferences.command()
    async def enable(ctx: Context, preference_name: str):
        if not preference_name in pref_set:
            return await ctx.send(embed=ErrorEmbed("Preference not found. -preference for a list of preferences"))
        ValorSQL.set_user_wynnbuilder(ctx.author.id, preference_name, True)
        await LongTextEmbed.send_message(valor, ctx, "Enabled preference")
    
    @preferences.command()
    async def disable(ctx: Context, preference_name: str):
        if not preference_name in pref_set:
            return await ctx.send(embed=ErrorEmbed("Preference not found. -preference for a list of preferences"))
        ValorSQL.set_user_wynnbuilder(ctx.author.id, preference_name, False)
        await LongTextEmbed.send_message(valor, ctx, "Disabled preference")
    
    @preferences.error
    async def cmd_error(ctx, error):
        await ctx.send(embed=ErrorEmbed())
        print(error)
    
    @valor.help_override.command()
    async def preferences(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Preferences", desc, color=0xFF00)