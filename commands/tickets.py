from valor import Valor
from discord.ext.commands import Context
from discord.ui import View
from discord import File
from datetime import datetime
import discord
import argparse
import time
import math
import numpy as np
from sql import ValorSQL
from util import ErrorEmbed, LongTextEmbed, LongTextTable
from commands.common import get_uuid, role1



async def get_tickets():
        res = await ValorSQL._execute(f"""
SELECT 
    GMC.name,
    SUM(CASE WHEN PDR.label = 'g_wars' THEN PDR.delta ELSE 0 END) AS wars_gain,
    SUM(CASE WHEN PDR.label = 'gu_gxp' THEN PDR.delta ELSE 0 END) AS gxp_gain,
    SUM(CASE WHEN PDR.label IN ('g_The Canyon Colossus', "g_Orphion's Nexus of Light", 'g_Nest of the Grootslangs', "g_The Nameless Anomaly") THEN PDR.delta ELSE 0 END) AS raids_gain,
    COALESCE(MAX(TB.ticket_bonus), 0) AS ticket_bonus
FROM 
    guild_member_cache GMC
JOIN 
    uuid_name UN ON GMC.name = UN.name
JOIN 
    player_delta_record PDR ON UN.uuid = PDR.uuid
LEFT JOIN 
    (SELECT uuid, SUM(ticket_bonus) AS ticket_bonus
     FROM ticket_bonuses
     WHERE YEARWEEK(FROM_UNIXTIME(timestamp), 1) = YEARWEEK(CURDATE(), 1)
     GROUP BY uuid) TB ON UN.uuid = TB.uuid
WHERE 
    GMC.guild = "Titans Valor" 
    AND YEARWEEK(FROM_UNIXTIME(PDR.time), 1) = YEARWEEK(CURDATE(), 1)
GROUP BY 
    GMC.name;
""")
        data = []
        for player in res:
            t = [player[0], do_ticket_math(player[1], 10), do_ticket_math(player[2], 100000000), do_ticket_math(player[3], 35), int(player[4])]
            _sum = t[1]+t[2]+t[3]+t[4]
            if _sum != 0:
                t.append(_sum)
                data.append(t)
        data = sorted(data, key=lambda x: x[5], reverse=True)
        
        i = 0
        for player in data:
            data[i].insert(0, f"{str(i+1)})")
            i += 1
        
        header = ["    ", " Name            ", "  War  ", "  GXP  ", " Raid  ", " Bonus ", "   Total   "]
        return [header, data]

def do_ticket_math(value, b):
    return math.floor(math.log((math.floor(float(value) + 0.5) / b) + 1, 1.05) + 0.5)



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
            if not role1(ctx.author):
                return await ctx.send(embed=ErrorEmbed("No Permissions"))
            try:
                uuid = await get_uuid(opt.add[0])
                value = opt.add[1]
            except: 
                return await ctx.send(embed=ErrorEmbed("Invalid input"))
            res = await ValorSQL._execute(f"""
INSERT INTO ticket_bonuses (uuid, ticket_bonus, timestamp) VALUES ('{uuid}', {value}, {str(time.time())});
""")        
            embed = discord.Embed(title="Operation successful", description=f"Successfully added {value} tickets to {opt.add[0]} ({uuid})", color=0xFF00)
            return await ctx.send(embed=embed)
        else:
            ticket_data = await get_tickets()
            await LongTextTable.send_message(valor, ctx, ticket_data[0], ticket_data[1])

    @tickets.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def tickets(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Tickets", desc, color=0xFF00)
