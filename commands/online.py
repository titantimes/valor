from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed
import random
import requests

async def _register_online(valor: Valor):
    desc = "Online: shows who's online in a guild"
    @valor.command()
    async def online(ctx: Context, *args, guild="Titans Valor"):
        guild = ' '.join(args) if len(args) else guild
        res = requests.get(valor.endpoints["guild"].format(guild)).json()
        if res.get("error"):
            return await ctx.send(embed=ErrorEmbed("Guild doesn't exist."))
        members = {m["name"] for m in res["members"]}
        all_players = requests.get(valor.endpoints["online"]).json()
        del all_players["request"]
        online_rn = [(p, k) for k in all_players for p in all_players[k] if p in members]
        if not len(online_rn):
            return await LongTextEmbed.send_message(valor, ctx, f"{guild} Members Online", "There are no members online.", color = 0xFF)
        await LongFieldEmbed.send_message(valor, ctx, f"{guild} Members Online", online_rn)
        # await ctx.send("```"+'\n'.join("%16s | %8s" % (p, k) for p, k in online_rn) + "```")
    
    @online.error
    async def cmd_error(ctx, error):
        await ctx.send(embed=ErrorEmbed())
        print(error)
    
    @valor.help_override.command()
    async def online(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Online", desc, color=0xFF00)
    
    
    