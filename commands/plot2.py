from valor import Valor
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, sinusoid_regress
from .common import  guild_name_from_tag, guild_names_from_tags
from discord.ext.commands import Context
from discord import File
from dotenv import load_dotenv
from mp import plot_process
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import time
import argparse
import os

load_dotenv()
async def _register_plot2(valor: Valor):
    desc = "Plots data for you!"
    opts = ["tag"]
    choice_em = ErrorEmbed(f"Your options are `{repr(opts)}`")
    rnklut = {"RECRUIT": 0, "RECRUITER": 1, "CAPTAIN": 2, "STRATEGIST": 3, "CHIEF": 4, "OWNER": 5}
    parser = argparse.ArgumentParser(description='Plot2 command')
    parser.add_argument('-r', '--range', nargs=2)
    parser.add_argument('-g', '--guild', nargs='+')
    parser.add_argument('-n', '--name', nargs='+')
    parser.add_argument('-s', '--split', action='store_true')
    parser.add_argument('-sm', '--smooth', action='store_true')
    parser.add_argument('-rs', '--resolution')
    parser.add_argument('-mv', '--moving_average', type=int, default=1)
    
    @valor.command()
    async def plot2(ctx: Context, *options):
        roles = {x.id for x in ctx.author.roles}
        # if not 703018636301828246 in roles and not 733841716855046205 in roles and ctx.author.id != 146483065223512064:
        #     return await ctx.send(embed=ErrorEmbed("Skill Issue"))
        
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Plot", parser.format_help().replace("main.py", "-plot2"), color=0xFF00)
        
        guild_names, unidentified = await guild_names_from_tags(opt.guild)

        if not guild_names:
            return await LongTextEmbed.send_message(
                valor, ctx, f"Plot2 Error", f"{unidentified} unknown", color=0xFF0000)

        opt.guild = guild_names
        if opt.name:
            opt.guild.extend(opt.name)

        start = time.time()
        
        query = f"SELECT * FROM `guild_member_count` WHERE guild=\"%s\""
        if opt.resolution:
            query += f" AND time%%{3600} >= {int(opt.resolution)*60}"
        if opt.range:
            query += f" AND time >= {start-3600*24*float(opt.range[0])} AND time <= {start-3600*24*float(opt.range[1])}"
        else:
            query += f" AND time >= {start-3600*24*7}"
        query += " ORDER BY time ASC"

        start_time = start - 3600 * 24 * 7 #should mimic default values
        end_time = start
        
        if opt.range:
            start_time = int(start - 3600 * 24 * float(opt.range[0]))
            end_time = int(start - 3600 * 24 * float(opt.range[1]))

        COUNCILID = int(os.getenv('COUNCILID'))
        if (end_time - start_time) > (365 *24 * 3600) and COUNCILID not in roles:
            return await LongTextEmbed.send_message(valor, ctx, "Plot2 Error", f" Maximum time range exceeded (365 days), ask a council member if you need a longer timeframe.", color=0xFF0000)


        pool = ProcessPoolExecutor(max_workers=4)
        data_pts, content = await valor.loop.run_in_executor(pool, plot_process, valor.db_lock, opt, query)
        pool.shutdown()
        file = File("/tmp/valor_guild_plot.png", filename="plot.png")
        
        end = time.time()

        unid_prefix = f"The following guilds are unidentified: {unidentified}\n" if unidentified else ""

        await LongTextEmbed.send_message(valor, ctx, f"Guild Activity of {opt.guild}", unid_prefix+content, color=0xFF0000, 
            file=file, 
            url="attachment://plot.png",
            footer = f"Query Took {end-start:.5}s - {data_pts:,} rows"
        )

    @valor.help_override.command()
    async def plot2(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Plot2", desc, color=0xFF00)
