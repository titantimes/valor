from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed
import random
import requests

async def _register_online(valor: Valor):
    """
    Online: shows who's online in a guild
    """
    @valor.command()
    async def online(ctx: Context, guild="Titans Valor"):
        res = requests.get(valor.endpoints["guild"].format(guild)).json()
        if res.get("error"):
            return await ctx.send(embed=ErrorEmbed("Guild doesn't exist."))
        members = {m["name"] for m in res["members"]}
        all_players = requests.get(valor.endpoints["online"]).json()
        del all_players["request"]
        online_rn = [(p, k) for k in all_players for p in all_players[k] if p in members]
        await ctx.send("```"+'\n'.join("%16s | %8s" % (p, k) for p, k in online_rn) + "```")
    
    
    