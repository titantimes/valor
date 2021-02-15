import requests
from valor import Valor
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed
from discord.ext.commands import Context
from dotenv import load_dotenv
import os

load_dotenv()
async def _register_gxp(valor: Valor):
    desc = "Gets you GXP of a member"
    @valor.command()
    async def gxp(ctx: Context, guild="Titans Valor", player=""):
        if not ctx.invoked_subcommand:
            schema = "https://" if os.getenv("USESSL") == "true" else "http://"
            res = requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/usertotalxp/{guild}/{player}").json()["data"]
            if isinstance(res, list):
                mesg = [[k["name"], k["xp"]] for k in res]
                mesg = sorted(mesg, key=lambda x: x[1], reverse=True)
                total = sum(x[1] for x in mesg)
                for x in mesg:
                    x[1] = f"{x[1]:,}"
                await LongFieldEmbed.send_message(valor, ctx, f"{guild} XP Breakdown (Total: {total:,})", mesg)
            else:
                mesg = f"**{int(res['xp']):,}**\nUpdates Every 30 Minutes"
                await LongTextEmbed.send_message(valor, ctx, f"{player}'s XP Gain for {guild}", mesg, color=0xF5b642)
    @gxp.error
    async def gxp_error(ctx, error):
        await ctx.send(embed=ErrorEmbed("Command failed :/ (Use quotes around the guild name if you haven't)"))
        print(error)
    
    @valor.help_override.command()
    async def gxp(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Gxp", desc, color=0xFF00)