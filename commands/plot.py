import requests
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, sinusoid_regress
from .common import  guild_name_from_tag
from discord.ext.commands import Context
from datetime import datetime
from discord import File
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import time
import math
import random
from matplotlib.ticker import MaxNLocator

load_dotenv()
async def _register_plot(valor: Valor):
    desc = "Plots data for you!"
    opts = ["guild", "player"]
    choice_em = ErrorEmbed(f"Your options are `{repr(opts)}`")
    # rnklut = {"RECRUIT": 0, "RECRUITER": 1, "CAPTAIN": 2, "STRATEGIST": 3, "CHIEF": 4, "OWNER": 5}
    rnklut = {"recruit": 0, "recruiter": 1, "captain": 2, "strategist": 3, "chief": 4, "owner": 5}
    @valor.group()
    async def plot(ctx: Context):
        if not ctx.invoked_subcommand:
            await ctx.send(embed=choice_em)

    # helper function
    async def fake_req(captains, name, start, end):
        # raw sql query
        res = await ValorSQL._execute(f"SELECT * FROM activity_members WHERE guild = \"{name}\" AND timestamp >= {start} AND timestamp <= {end};")
        ret = {}
        # members = requests.get("https://api.wynncraft.com/public_api.php?action=guildStats&command="+name).json()["members"]
        # cpts = {m["name"] for m in members if rnklut[m["rank"]] >= rnklut["CAPTAIN"]}
        members = requests.get("https://api.wynncraft.com/v3/guild/"+name).json()["members"]
        cpts = {name for k, v in members.items() if rnklut.get(k, 0) >= rnklut["captain"] for name, _ in v.items()}
        for row in res:
            if not row[2] in ret:
                ret[row[2]] = 0
            ret[row[2]] += (not captains or row[0] in cpts)
        return ret
    
    # allows for multiple guilds delimited by commas
    @plot.command()
    async def guild(ctx: Context, unparsed_guild_names = "Avicia", options = ""):
        roles = {x.id for x in ctx.author.roles}
        if not 703018636301828246 in roles and not 733841716855046205 in roles and ctx.author.id != 146483065223512064 and os.getenv("TEST") != "TRUE":
            return await ctx.send(embed=ErrorEmbed("Skill Issue"))
        guild_names = unparsed_guild_names.replace(', ', ',').split(',')
        options = options.split(' ')
        # print(options)
        end = int(time.time())
        start = int(time.time()) - 3600*24*7
        ignore_regression = False

        # the horizontal lines that cal asked for
        use_tm = False

        if options != ['']:
            if len(options) > 0:
                if options[0] == "start":
                    start = 0
                else:
                    start = int(time.time()) - int(options[0][:-1])*3600*24
            if len(options) > 1 and options[1] != "end":
                end -= int(options[1][:-1])*3600*24 # int(datetime.strptime(options[1], "%d/%m/%y").timestamp())
            if len(options) > 2:
                if options[2] == "yes" or options[2] == "no":
                    ignore_regression = options[2] == 'no'
                else:
                    use_tm = True

        fig: plt.Figure = plt.figure()
        ax: plt.Axes = fig.add_subplot(7,1,(1,6))
        ax.set_ylabel("Player Online Count")
        ax.set_xlabel("Hour (24 hour-format GMT/BST)")
        # plt.ylabel = "Player Count"
        schema = "https://" if os.getenv("USESSL") == "true" else "http://"
        # print(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/activity/guild/{guild_name}/{start}/{end}")

        cumulative_xvalues = []
        cumulative_yvalues = []
        cumulative_xtimes = []
        # loop through each guild and get cumulative sum 
        all_or_captains = "captains" in options
        for name in guild_names:

            res = await fake_req(all_or_captains, name, start, end) # requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/activity/{all_or_captains}/{name}/{start}/{end}").json()
            
            for k in [*res.keys()]:
                # replace all keys in res with the floor'd values to nearest hour in seconds
                res[int(k)//3600*3600] = res[k]
                del res[k]

            old_xvalues = [*res.keys()]

            # old_xvalues = sorted(old_xvalues)
            xvalues = [datetime.fromtimestamp(old_xvalues[0]).strftime("%-d/%m/%y-%H")]
            xtimes = [int(old_xvalues[0])]
            yvalues = [res[old_xvalues[0]]]
            for i in range(1, len(old_xvalues)):
                # fill in the gaps in time
                fill_float = (old_xvalues[i]-old_xvalues[i-1])
                fill = fill_float//3600
                if fill_float > 3600:
                    xvalues.extend(
                        [datetime.fromtimestamp(old_xvalues[i-1]+(j+1)*3600).strftime("%-d/%m/%y-%H")
                            for j in range(0, fill)]
                    )
                    xtimes.extend([old_xvalues[i-1]+(j+1)*3600
                            for j in range(0, fill)])
                    yvalues.extend([0]*(fill))
                xtimes.append(old_xvalues[i])
                xvalues.append(datetime.fromtimestamp(old_xvalues[i]).strftime("%-d/%m/%y-%H"))
                yvalues.append(res[old_xvalues[i]])

            cumulative_yvalues.append(yvalues)
            cumulative_xvalues = xvalues
            cumulative_xtimes.append(xtimes)
        
        sortable_timeseries = [(cumulative_xtimes[i], cumulative_yvalues[i]) for i in range(len(cumulative_xtimes))]
        sortable_timeseries.sort(key = lambda n: len(n[0]))
        
        
        # do average values if specified
        if "avg" in options or "average" in options:
            cumulative_yvalues = [sum(x[1][i] for x in sortable_timeseries)/len(sortable_timeseries) for i in range(len(sortable_timeseries[0][0]))]
        else:
            cumulative_yvalues = [sum(x[1][i] for x in sortable_timeseries) for i in range(len(sortable_timeseries[0][0]))]
        cumulative_xtimes = sortable_timeseries[0][0]

        ax.plot(cumulative_xtimes, cumulative_yvalues)
        if use_tm:
            ax.vlines(x=cumulative_xtimes[::24], ymin=0, ymax=max(cumulative_yvalues), ls=':', color='b')
        try:
            solved = sinusoid_regress([x-cumulative_xtimes[0] for x in cumulative_xtimes], cumulative_yvalues)
        # runtime errors with numpy. This really never happens unless the guild was recently added
        except:
            solved = [0,0,0,0]
        content = f"```Min: {min(cumulative_yvalues)}\nMax: {max(cumulative_yvalues)}\nMean: {solved[3]}"

        if not ignore_regression:

            freq = 1/solved[1]*2*3.1415
            model = lambda t: solved[0]*math.sin(freq*t-solved[2])+solved[3]
            model_x = range(cumulative_xtimes[0], cumulative_xtimes[-1], 3600)
            model_values = [model(x) for x in model_x]
            model_x_date = [datetime.fromtimestamp(x).strftime("%-d/%m/%y-%H") for x in model_x]
            template = f"\n{round(solved[0], 3)}*sin({round(freq, 7)}*t-{round(solved[2], 3)})+{round(solved[3], 3)}"
            content += template
            # print(model_x_date)
            ax.plot(model_x, model_values, 'g--')
        content += '```'
        # print(model_x_date)
        # ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
        # skip = len(xvalues)//10
        
        # ax.xaxis.set_major_formatter(mticker.FuncFormatter(tick_rename))
        
        # ax.tick_params(axis='x', rotation=40)
        # plt.plot(res.keys(), [res[k] for k in res])
        # https://stackoverflow.com/questions/7761778/matplotlib-adding-second-axes-with-transparent-background
        # this is to just get it sorted with day
        newax = ax.twiny()
        fig.subplots_adjust(bottom=0.20)
        newax.set_frame_on(True)
        newax.patch.set_visible(False)
        newax.xaxis.set_ticks_position('bottom')
        newax.xaxis.set_label_position('bottom')
        newax.set_xlabel('Day (d/m/y)')
        newax.spines['bottom'].set_position(('outward', 40))
        # hacky way to do this
        newax.plot([x[:x.find('-')] for x in xvalues], [1]*len(xvalues), alpha=0)
        # newax.tick_params(axis='x', rotation=90)
        ax.xaxis.set_major_locator(MaxNLocator(min(len(xvalues), 20))) 
        skip = 1
        # for i, label in enumerate(ax.get_xticklabels()):
        #     if not i % skip:
        #         label.set_visible(False)
        labels = [item.get_text() for item in ax.get_xticklabels()]
        for i in range(len(labels)-1):
            labels[i+1] = int(xvalues[i][xvalues[i].find('-')+1:])
        ax.set_xticklabels(labels)

        for tick in ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(8)

        # .label.set_fontsize(14) 
        # old = ax.xaxis.get_major_formatter()
        # tick_rename = lambda x, pos: int(xvalues[pos-1][xvalues[pos-1].find('-')+1:]) if not (pos-1) % skip else ""
        # ax.xaxis.set_major_formatter(mticker.FuncFormatter(tick_rename))
        # ax.tick_params("x",rotation=20)

        fig.savefig("/tmp/valor_guild_plot.png")
        file = File("/tmp/valor_guild_plot.png", filename="plot.png")
        
        await LongTextEmbed.send_message(valor, ctx, f"Guild Activity of {unparsed_guild_names}", content, color=0xFF0000, 
            file=file, 
            url="attachment://plot.png"
        )

        fig.clear()
        plt.close(fig)

    # @guild.error
    # async def guild_error(ctx, error):
    #     await ctx.send(embed=ErrorEmbed("Command failed :/. Make sure to surround guild names with quotes"))
    #     print(error)

    # @plot.error
    # async def plot_error(ctx, error):
    #     await ctx.send(embed=ErrorEmbed("Command failed :/. Make sure to surround guild names with quotes"))
    #     print(error)
    
    @plot.command()
    async def tag(ctx: Context, guild_names = "AVO", options = ""):
        guild_names = guild_names.replace(', ', ',').split(',')
        return await guild(ctx, ', '.join(await guild_name_from_tag(x) for x in guild_names), options) 

    @valor.help_override.command()
    async def plot(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Plot", desc, color=0xFF00)