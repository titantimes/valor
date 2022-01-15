import requests
from valor import Valor
from mp import avg_process
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, sinusoid_regress, guild_name_from_tag
from discord.ext.commands import Context
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from discord import File
from dotenv import load_dotenv
import numpy as np
import time
import argparse
import gc

load_dotenv()
async def _register_avg(valor: Valor):
    desc = "Averages online activity data"
    opts = ["tag"]
    choice_em = ErrorEmbed(f"Your options are `{repr(opts)}`")
    parser = argparse.ArgumentParser(description='Plot2 command')
    parser.add_argument('-r', '--range', nargs=2)
    parser.add_argument('-g', '--guild', nargs='+')
    
    @valor.command()
    async def avg(ctx: Context, *options):
        roles = {x.id for x in ctx.author.roles}
        # if not 703018636301828246 in roles and not 733841716855046205 in roles and ctx.author.id != 146483065223512064:
        #     return await ctx.send(embed=ErrorEmbed("Skill Issue"))
        
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Avg", parser.format_help().replace("main.py", "-avg"), color=0xFF00)

        start = time.time()

        query = f"SELECT * FROM `guild_member_count` WHERE "
        if opt.guild:
            query += "("+' OR '.join("guild="+'"'+guild_name_from_tag(n)+'"' for n in opt.guild)+")" + " AND "

        if opt.range:
            query += f"time >= {start-3600*24*int(opt.range[0])} AND time <= {start-3600*24*int(opt.range[1])}"
        else:
            query += f"time >= {start-3600*24*7}"

        pool = ProcessPoolExecutor(max_workers=4)
        data_pts, content = await valor.loop.run_in_executor(pool, avg_process, valor.db_lock, query)
        pool.shutdown()
        
        end = time.time()

        await LongTextEmbed.send_message(valor, ctx, f"Guild Averages {opt.guild if opt.guild else 'ALL'}", content, color=0xFF0000, 
            footer = f"Query Took {end-start:.5}s - {data_pts:,} rows"
        )

    @valor.help_override.command()
    async def avg(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Plot", desc, color=0xFF00)