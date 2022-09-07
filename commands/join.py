from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed
import random
from datetime import datetime
import requests

async def _register_join(valor: Valor):
    desc = "Gets you the join date of a player to the guild."
    
    @valor.command()
    async def join(ctx: Context, username: str):
        user_data = requests.get("https://api.wynncraft.com/public_api.php?action=guildStats&command=Titans%20Valor").json()
        for m in user_data["members"]:
            if m["name"] == username:
                ezjoin = datetime.fromisoformat(m["joined"][:-1])
                return await LongTextEmbed.send_message(valor, ctx, "Most Recent Join Date of %s" % username, ezjoin.strftime("%d %b %Y %H:%M:%S.%f UTC"), color=0xFF00)
        
        await ctx.send(embed=ErrorEmbed("%s isn't in the guild" % username))

    @join.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def join(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Join", desc, color=0xFF00)
    
    
    