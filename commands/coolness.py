from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed, LongTextTable
from .common import guild_name_from_tag, guild_names_from_tags
import random
from datetime import datetime
import requests
from sql import ValorSQL
from commands.common import get_uuid, from_uuid
import time
import argparse
import os
from dotenv import load_dotenv  
load_dotenv()

async def _register_coolness(valor: Valor):
    desc = "The leaderboard (but for coolness)"
    parser = argparse.ArgumentParser(description='Coolness command')
    parser.add_argument('-r', '--range', nargs=2)
    parser.add_argument('-g', '--guild', nargs='+', default=["ANO"])
    parser.add_argument('-b', '--backwards', action='store_true')
    parser.add_argument('-t', '--threshold', type=float, default=-1)

    @valor.command()
    async def coolness(ctx: Context, *options):
        roles = {x.id for x in ctx.author.roles}
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "coolness", parser.format_help().replace("main.py", "-coolness"), color=0xFF00)
        
        COUNCILID = 702991927318020138
        if opt.range:
            t_range = float(opt.range[0]) - float(opt.range[1])
            if not os.environ["TEST"] and t_range > 100 and COUNCILID not in roles:
                return await LongTextEmbed.send_message(valor, ctx, "coolness Error", f" Maximum time range exceeded (100 days), ask an ANO chief if you need a longer timeframe.", color=0xFF0000)

        guild_names, unidentified = await guild_names_from_tags(opt.guild)
        guild_names = set(guild_names)
        if not guild_names:
            return await LongTextEmbed.send_message(
                valor, ctx, f"Coolness Error", f"{unidentified} unknown", color=0xFF0000)

        start = time.time()
        sql_time_range_condition = "AND "
        if opt.range:
            sql_time_range_condition += f" timestamp >= {start-3600*24*float(opt.range[0])} AND timestamp <= {start-3600*24*float(opt.range[1])}"
        else:
            sql_time_range_condition += f" timestamp >= {start-3600*24*7}"

        query = '''
SELECT A.guild, B.name, A.coolness
FROM
  (SELECT guild, uuid, COUNT(*) as coolness 
  FROM 
    activity_members
    WHERE guild IN %s
    %s
    GROUP BY uuid, guild) A
  JOIN uuid_name B ON A.uuid=B.uuid  
ORDER BY A.coolness DESC;
''' % ("(" + ('%s,'*len(guild_names))[:-1] + ")", sql_time_range_condition)
        
        board = await ValorSQL.exec_param(query, guild_names)
        end = time.time()

        header = [" Guild" + ' '*(max(len(x[0]) for x in board)-5), "Username"+' '*(18-8), "Hours Online"]

        if unidentified:
            unid_prefix = f"The following guilds are unidentified: {unidentified}\n" if unidentified else ""
            await LongTextEmbed.send_message(valor, ctx, "Unidentified Guilds", unid_prefix)

        await LongTextTable.send_message(valor, ctx, header, board, f"Query took {end-start:.5}s - {len(board):,} rows")

    @coolness.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def coolness(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Coolness", desc, color=0xFF00)
    
    
    
