from valor import Valor
from discord.ext.commands import Context
from discord.ui import View
from discord import File
from datetime import datetime
import discord
import argparse
import time
import numpy as np
from sql import ValorSQL
from util import ErrorEmbed, LongTextEmbed
from commands.common import from_uuid



async def get_tickets():
        embed = discord.Embed(title=f"Titans Valor: Weekly Tickets", color=0xFFFF00)
        res = await ValorSQL._execute(f"""
SELECT A.name, 
    SUM(CASE WHEN C.label = 'gu_gxp' THEN C.delta ELSE 0 END) AS gxp_gain,
    SUM(CASE WHEN C.label IN ('g_The Canyon Colossus', "g_Orphion's Nexus of Light", 'Nest of the Grootslangs') THEN C.delta ELSE 0 END) AS raids_gain,
    SUM(CASE WHEN C.label = 'g_wars' THEN C.delta ELSE 0 END) AS wars_gain
FROM 
    guild_member_cache A NATURAL JOIN uuid_name B
    NATURAL JOIN player_delta_record C
WHERE A.guild="Titans Valor" AND C.time >= {time.time()-3600*24*7}
GROUP BY A.name  
""")
        data = []
        for player in res:
            t = [player[0], do_ticket_math(player[3], 10), do_ticket_math(player[1], 100000000), do_ticket_math(player[2], 35)]
            if int(t[1])+int(t[2])+int(t[3]) != 0:
                t.append(int(t[1])+int(t[2])+int(t[3]))
                data.append(t)
        data = sorted(data, key=lambda x: x[4], reverse=True)

        i = 1
        desc = "     ┃ Name            ┃  War  ┃  GXP  ┃ Raid  ┃   Total   \n"
        desc += "━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━╋━━━━━━━╋━━━━━━━╋━━━━━━━━━━━\n"
        for player in data:
                t = str(i) + ")" + ((4 - len(str(i))) * " ") + "┃ "

                t += player[0]
                t += ((16 - len(player[0])) * " ")
                t += "┃ " + player[1]
                t += ((6 - len(player[1])) * " ")
                t += "┃ " + player[2]
                t += ((6 - len(player[2])) * " ")
                t += "┃ " + player[3]
                t += ((6 - len(player[3])) * " ")
                t += "┃ " + str(player[4])
                t += ((10 - len(str(player[4]))) * " ") + "\n"
                
                desc += t
                i += 1

        if len(desc) > 960:
            descriptions = [desc[i:i+960] for i in range(0, len(desc), 960)]
            for desc in descriptions:
                embed.add_field(name ="", value="```isbl\n" + desc + "```", inline=False)
        else:
            embed.add_field(name="", value="```isbl\n" + desc + "```", inline=False)
        
        return embed

def do_ticket_math(value, b):
    return str(round(np.log(((int(value)/b)+1))/np.log(1.05)))



async def _register_tickets(valor: Valor):
    desc = "Provides ticket leaderboard"
    parser = argparse.ArgumentParser(description='Tickets Command')
    parser.add_argument('-a', '--add', nargs='*', default=[])

    @valor.command(aliases=["t"])
    async def tickets(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "tickets", parser.format_help().replace("main.py", "-tickets"), color=0xFF00)
        
        if opt.add:
            res = await ValorSQL._execute(f"""
SELECT * FROM ticket_bonuses;  
""")    
            print(res)
            await ctx.send("done")
        else:
            embed = await get_tickets()
            await ctx.send(embed=embed)

    @tickets.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def tickets(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Tickets", desc, color=0xFF00)
