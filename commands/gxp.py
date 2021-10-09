import requests
from valor import Valor
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, to_seconds
from sql import ValorSQL
from discord.ext.commands import Context
from datetime import datetime
from dotenv import load_dotenv
import os
import time

load_dotenv()
async def _register_gxp(valor: Valor):
    desc = "Gets you GXP of a member. `-gxp h` to get the xp contributions of a player with time slices"

    @valor.group()
    async def gxp(ctx: Context, guild="Titans Valor", player="", arg2 = "", arg3 = ""):
        schema = "https://" if os.getenv("USESSL") == "true" else "http://"
        if guild == "h":
            # player is arg1
            t1 = int(time.time()) if not arg3 else int(datetime.strptime(arg3, "%d/%m/%y").timestamp())
            t0 = int(datetime.strptime(arg2, "%d/%m/%y").timestamp()) if arg2 else 0
            uuid = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}").json()["id"]
            # add hyphens
            uuid = '-'.join([uuid[:8],uuid[8:12],uuid[12:16],uuid[16:20],uuid[20:]])
            res = requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/incxp/{uuid}/{t0}/{t1}").json()["data"]
            # print(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/incxp/{uuid}/{t0}/{t1}")
            total = sum(x[0] for x in res["values"])
            content = f"From {arg2 if arg2 else '17/04/2021'} to {arg3 if arg3 else 'Now'}\nContributed: {total:,} GXP"
            return await LongTextEmbed.send_message(valor, ctx, f"{player}'s XP Contributions Over Time", content, color=0xF5b642)
        
        elif guild == "frame":
            now = int(time.time())
            t0 = now-to_seconds(player)
            t1 = now-to_seconds(arg2)
            res = ValorSQL._execute(f"SELECT * FROM member_record_xps WHERE timestamp > {t0} AND timestamp < {t1}")
            membermap = {}
            for m in res:
                if not m[1] in membermap:
                    membermap[m[1]] = 0
                membermap[m[1]] += m[3]

            pair_data = [[x[0], f"{x[1]:,}"] for x in sorted(membermap.items(), key = lambda x: x[1], reverse=True)]
            
            return await LongFieldEmbed.send_message(valor, ctx, f"GXP Contribs Over Specified Time", pair_data, color=0xF5b642)
            

        # res = requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/usertotalxp/{guild}/{player}").json()["data"]
        res = ValorSQL._execute(f"SELECT * FROM user_total_xps")
        if isinstance(res, list):
            mesg = [[k[0], k[1]] for k in res]
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
        raise error
    
    @valor.help_override.command()
    async def gxp(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Gxp", desc, color=0xFF00)