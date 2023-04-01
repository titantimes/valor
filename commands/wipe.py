from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed, discord_ansicolor
from .common import guild_name_from_tag
from datetime import datetime
from sql import ValorSQL
import requests
import commands.common
import re
import argparse
import time
import os
import random
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv()
TEST = os.getenv("TEST")=="TRUE"

async def _register_wipe(valor: Valor):
    desc = "Read or Update the alliance."

    wipe_parser = argparse.ArgumentParser(description='Wipe Time Command')
    wipe_parser.add_argument('-g', '--guild', nargs='+', default=["ANO"])
    wipe_parser.add_argument('-r', '--range', nargs='+', default=[7*24, 0])
    wipe_parser.add_argument('-t', '--threshold', nargs='+', default=[1, -10])
    wipe_parser.add_argument('-m', '--minsec', type=float, default=120)

    @valor.command()
    async def wipe(ctx: Context, *options):
        try:
            opt = wipe_parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Wipe Time command", wipe_parser.format_help().replace("main.py", "-wipe"), color=0xFF00)

        start = time.time()
        g_names = {await guild_name_from_tag(tag) for tag in opt.guild}
        g_names_paren = [f"'{n}'" for n in g_names]
        left, right = start - float(opt.range[0])*24*3600, start - float(opt.range[1])*24*3600
        left_count = int(opt.threshold[0])
        right_count = int(opt.threshold[1])
        left_count, right_count = (left_count, right_count) if left_count < right_count else (right_count, left_count)
        
        res = await ValorSQL._execute(f"SELECT * FROM terr_count WHERE guild IN ({','.join(g_names_paren)}) AND time >= {left} AND time <= {right} ORDER BY time") # time, guild, count

        wipe_time = {}
        last_time = {}
        last_count = {}
        wiped_count = {} # number of times wiped

        for t_time, guild, count in res:
            if not guild in last_count:
                wipe_time[guild] = 0
                last_count[guild] = count
                last_time[guild] = t_time
                wipe_time[guild] += (t_time - left) / 3600 # left end of the data

            if left_count <= count <= right_count and (t_time - last_time[guild]) >= opt.minsec+0.5:
                wipe_time[guild] += (t_time - last_time[guild]) / 3600
                if not guild in wiped_count:
                    wiped_count[guild] = 0
                wiped_count[guild] += 1
                
            last_count[guild] = count
            last_time[guild] = t_time
                
        upper_time = res[-1][0]
        if upper_time < right - 300: # if no guilds have terrs for the last 5 mins, use bigger bound (solves -r 1 0 issue with small data)
            upper_time = right

        not_wiped_guilds = set()
        i = len(res)-1
        while i >= 0:
            if res[i][0] <= upper_time - opt.minsec:
                break
            not_wiped_guilds.add(res[i][1])
            i -= 1

        for guild in (g_names - not_wiped_guilds) | (g_names - wipe_time.keys()):
            if not guild in wipe_time:
                wipe_time[guild] = 0
                wiped_count[guild] = 0

            wipe_time[guild] += (right- last_time.get(guild, left)) / 3600
            wiped_count[guild] += 1
        
        table_rows = []
        for guild in g_names:
            wiped_total_time = wipe_time.get(guild, 0)
            wiped_total_count = wiped_count.get(guild, 0)
            wiped_avg = wiped_total_time/wiped_total_count if wiped_total_count > 0 else "N/A"
            table_rows.append((guild, wiped_total_time, wiped_total_count, wiped_avg))
        
        table_rows.sort(key=lambda x: x[1], reverse=True)
            
        pre_header = "Wipe times given by HOURS\n"
        header = "Guild                   | Wiped Time | Wiped # | Avg. \n"\
                 "------------------------+------------+---------+------\n"
        footer = "------------------------+------------+---------+------\n"

        delta_time = time.time()-start
        post_footer = f"Query took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}\n"

        formatted_rows = []
        for r in table_rows:
            if r[3] == "N/A":
                formatted_rows.append("%24s|%12.3f|%9d|%6s" % r)
            else:
                formatted_rows.append("%24s|%12.3f|%9d|%6.2f" % r)
        
        table_body = '\n'.join(formatted_rows)

        content = '```\n'+pre_header+header+table_body+'\n'+footer+'\n'+post_footer+'\n```'
        await ctx.send(content)
        
    @wipe.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def wipe(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Wipe Time", desc, color=0xFF00)
    
    
    