import requests
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, sinusoid_regress, guild_name_from_tag
from discord.ext.commands import Context
from datetime import datetime
from discord import File
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import matplotlib.dates as md
from scipy.interpolate import make_interp_spline
import numpy as np
import time
import math
import random
import argparse
from matplotlib.ticker import MaxNLocator

load_dotenv()
async def _register_plot2(valor: Valor):
    desc = "Plots data for you!"
    opts = ["tag"]
    choice_em = ErrorEmbed(f"Your options are `{repr(opts)}`")
    rnklut = {"RECRUIT": 0, "RECRUITER": 1, "CAPTAIN": 2, "STRATEGIST": 3, "CHIEF": 4, "OWNER": 5}
    parser = argparse.ArgumentParser(description='Plot2 command')
    parser.add_argument('-r', '--range', nargs=2)
    parser.add_argument('-g', '--guild', nargs='+')
    parser.add_argument('-s', '--split', action='store_true')
    parser.add_argument('-sm', '--smooth', action='store_true')
    parser.add_argument('-rs', '--resolution')
    parser.add_argument('-mv', '--moving_average', type=int, default=1)
    
    @valor.command()
    async def plot2(ctx: Context, *options):
        roles = {x.id for x in ctx.author.roles}
        if not 703018636301828246 in roles and not 733841716855046205 in roles and ctx.author.id != 146483065223512064:
            return await ctx.send(embed=ErrorEmbed("Skill Issue"))
        
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Plot", parser.format_help().replace("main.py", "-plot2"), color=0xFF00)
        
        a = []
        b = []
        xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')

        fig = plt.figure()
        fig.set_figwidth(20)
        fig.set_figheight(10)

        ax = plt.gca()
        ax.xaxis.set_major_formatter(xfmt)
        plt.xticks(rotation=25)

        start = time.time()
        data_pts = 0

        query = f"SELECT * FROM `guild_member_count` WHERE guild=\"%s\""
        if opt.resolution:
            query += f" AND time%%{3600} >= {int(opt.resolution)*60}"
        if opt.range:
            query += f" AND time >= {start-3600*24*int(opt.range[0])} AND time <= {start-3600*24*int(opt.range[1])}"

        for tag in opt.guild:
            guild = guild_name_from_tag(tag)
            res = await ValorSQL._execute(query % guild)

            if opt.split:
                b = np.array([x[2] for x in res])
                a = np.array([x[1] for x in res])

                if opt.moving_average > 1:
                    a = np.convolve(a, np.ones(opt.moving_average)/opt.moving_average, mode="valid")
                    b = b[:len(b)-opt.moving_average+1]

                if opt.smooth:
                    spline = make_interp_spline(b, a)

                    b = np.linspace(b.min(), b.max(), 500)
                    a = spline(b)

                plt.plot([datetime.fromtimestamp(x) for x in b], a, label=guild)
                plt.legend(loc="upper left")

            else:
                for i in range(len(res)):
                    if i >= len(a):
                        a.append(0)
                        b.append(res[i][2])
                    a[i] += res[i][1]

                a = np.array(a)
                b = np.array(b)

            data_pts += len(res)

        end = time.time()

        content = "Plot"

        if opt.split:
            content = "Split graph"
        else:
            content =f"""```
Mean: {sum(a)/len(a):.7}
Max: {max(a)}
Min: {min(a)}```"""
            if opt.moving_average > 1:
                a = np.convolve(a, np.ones(opt.moving_average)/opt.moving_average, mode="valid")
                b = b[:len(b)-opt.moving_average+1]
                
            if opt.smooth:
                spline = make_interp_spline(b, a)

                b = np.linspace(b.min(), b.max(), 500)
                a = spline(b)

            plt.plot([datetime.fromtimestamp(x) for x in b], a) 

        ax.xaxis.set_major_locator(MaxNLocator(30))

        plt.title("Online Player Activity")
        plt.ylabel("Player Count")
        plt.xlabel("Date Y-m-d H:M:S")

        fig.savefig("/tmp/valor_guild_plot.png")
        file = File("/tmp/valor_guild_plot.png", filename="plot.png")
        
        await LongTextEmbed.send_message(valor, ctx, f"Guild Activity of {opt.guild}", content, color=0xFF0000, 
            file=file, 
            url="attachment://plot.png",
            footer = f"Query Took {end-start:.5}s - {data_pts:,} rows"
        )

        fig.clear()
        plt.close(fig)

    @valor.help_override.command()
    async def plot2(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Plot", desc, color=0xFF00)