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
from util import ErrorEmbed, LongTextEmbed, LongTextTable
from commands.common import get_uuid, role1



async def get_tickets():
        embed = discord.Embed(title=f"Titans Valor: Weekly Tickets", color=0xFFFF00)
        res = await ValorSQL._execute(f"""
SELECT A.name, 
    SUM(CASE WHEN C.label = 'gu_gxp' THEN C.delta ELSE 0 END) AS gxp_gain, 
    SUM(CASE WHEN C.label IN ('g_The Canyon Colossus', "g_Orphion's Nexus of Light", 'Nest of the Grootslangs') THEN C.delta ELSE 0 END) AS raids_gain, 
    SUM(CASE WHEN C.label = 'g_wars' THEN C.delta ELSE 0 END) AS wars_gain, 
    COALESCE(MAX(T.ticket_bonus), 0) AS ticket_bonus 
FROM 
    guild_member_cache A NATURAL JOIN uuid_name B 
    NATURAL JOIN player_delta_record C 
    LEFT JOIN ticket_bonuses T ON B.uuid = T.uuid 
WHERE A.guild = "Titans Valor" 
AND YEARWEEK(FROM_UNIXTIME(C.time)) = YEARWEEK(NOW()) 
GROUP BY A.name;
""")
        data = []
        for player in res:
            t = [player[0], do_ticket_math(player[3], 10), do_ticket_math(player[1], 100000000), do_ticket_math(player[2], 35), player[4]]
            if int(t[1])+int(t[2])+int(t[3])+int(t[4]) != 0:
                t.append(int(t[1])+int(t[2])+int(t[3]))
                data.append(t)
        data = sorted(data, key=lambda x: x[5], reverse=True)
        
        header = [" Name            ", "  War  ", "  GXP  ", " Raid  ", " Bonus ", "   Total   "]
        return [header, data]

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
            if not role1(ctx.author):
                return await ctx.send(embed=ErrorEmbed("No Permissions"))
            print(opt.add)
            try:
                uuid = await get_uuid(opt.add[0])
                value = opt.add[1]
            except: 
                return await ctx.send(embed=ErrorEmbed("Invalid input"))
            
                        #res = await ValorSQL._execute(f"""
#INSERT INTO ticket_bonuses (uuid, ticket_bonus, timestamp) VALUES ('your_uuid_here', your_ticket_bonus_value, your_timestamp);
#""")       
            embed = discord.Embed(title="Operation successful", description="Successfully added " + value + " tickets to " + uuid, color=0xFF00)
            return await ctx.send(embed=embed)
        else:
            ticket_data = await get_tickets()
            table = LongTextTable(ticket_data[0], ticket_data[1])
            await ctx.send(table.description)

    @tickets.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def tickets(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Tickets", desc, color=0xFF00)
