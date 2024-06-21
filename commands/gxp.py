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
        # schema = "https://" if os.getenv("USESSL") == "true" else "http://"
        # if guild == "h":
        #     # player is arg1
        #     t1 = int(time.time()) if not arg3 else int(datetime.strptime(arg3, "%d/%m/%y").timestamp())
        #     t0 = int(datetime.strptime(arg2, "%d/%m/%y").timestamp()) if arg2 else 0
        #     uuid = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}").json()["id"]
        #     # add hyphens
        #     uuid = '-'.join([uuid[:8],uuid[8:12],uuid[12:16],uuid[16:20],uuid[20:]])
        #     res = requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/incxp/{uuid}/{t0}/{t1}").json()["data"]
        #     # print(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/incxp/{uuid}/{t0}/{t1}")
        #     total = sum(x[0] for x in res["values"])
        #     content = f"From {arg2 if arg2 else '17/04/2021'} to {arg3 if arg3 else 'Now'}\nContributed: {total:,} GXP"
        #     return await LongTextEmbed.send_message(valor, ctx, f"{player}'s XP Contributions Over Time", content, color=0xF5b642)
        
        if guild == "frame":
            now = int(time.time())
            t0 = now-to_seconds(player)
            t1 = now-to_seconds(arg2)
            res = await ValorSQL.exec_param("""
SELECT C.name, SUM(B.delta) AS delta_gxp
FROM 
    (SELECT * FROM player_delta_record WHERE guild="Titans Valor" AND label="gu_gxp" AND time >= %s AND time <= %s) B 
    JOIN uuid_name C ON B.uuid=C.uuid
GROUP BY B.uuid
ORDER BY delta_gxp  DESC;
""", (t0, t1))
            pair_data = [[x[0], f"{x[1]:,}"] for x in sorted(res, key = lambda x: x[1], reverse=True)]
            
            return await LongFieldEmbed.send_message(valor, ctx, f"GXP Contribs Over Specified Time", pair_data, color=0xF5b642)
            

        # res = requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/usertotalxp/{guild}/{player}").json()["data"]
        if guild == "Titans Valor":
            res = await ValorSQL._execute("""
SELECT IFNULL(B2.name, C2.name), A2.gxp
FROM
    (SELECT uuid, MAX(xp) AS gxp
    FROM
        ((SELECT uuid, xp FROM user_total_xps)
        UNION ALL
        (SELECT B.uuid, B.value AS xp
        FROM 
            player_stats A JOIN player_global_stats B ON A.uuid=B.uuid
        WHERE A.guild="Titans Valor" AND B.label="gu_gxp")) A1
    GROUP BY uuid) A2 
    LEFT JOIN uuid_name B2 ON A2.uuid=B2.uuid
    LEFT JOIN (SELECT uuid, name FROM user_total_xps) C2 ON C2.uuid=A2.uuid
ORDER BY A2.gxp DESC;
""")
        else:
            res = await ValorSQL.exec_param("""
SELECT C.name, B.value
FROM 
    player_stats A JOIN player_global_stats B ON A.uuid=B.uuid
    JOIN uuid_name C ON B.uuid=C.uuid
WHERE A.guild=(%s) AND B.label="gu_gxp"  
ORDER BY `B`.`value`  DESC
""", (guild))
            
        # if isinstance(res, tuple):
        mesg = [[k[0], k[1]] for k in res]
        mesg = sorted(mesg, key=lambda x: x[1], reverse=True)
        total = sum(x[1] for x in mesg)
        for x in mesg:
            x[1] = f"{x[1]:,}"
        await LongFieldEmbed.send_message(valor, ctx, f"{guild} XP Breakdown (Total: {total:,})", mesg)
        # else:
        #     uuid = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}").json()["id"]
        #     # add hyphens
        #     uuid = '-'.join([uuid[:8],uuid[8:12],uuid[12:16],uuid[16:20],uuid[20:]])
        #     for x in res:
        #         if x[4] == uuid:
        #             res = x
        #             break

        #     mesg = f"**{int(res[1]):,}**\nUpdates Every 30 Minutes"
        #     await LongTextEmbed.send_message(valor, ctx, f"{player}'s XP Gain for {guild}", mesg, color=0xF5b642)

    @gxp.error
    async def gxp_error(ctx, error):
        await ctx.send(embed=ErrorEmbed("Command failed :/ (Use quotes around the guild name if you haven't)"))
        raise error
    
    @valor.help_override.command()
    async def gxp(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Gxp", desc, color=0xFF00)