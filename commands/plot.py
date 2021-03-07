import requests
from valor import Valor
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, sinusoid_regress, guild_name_from_tag
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
    @valor.group()
    async def plot(ctx: Context):
        if not ctx.invoked_subcommand:
            await ctx.send(embed=choice_em)
    
    @plot.command()
    async def guild(ctx: Context, guild_name = "Avicia", options = ""):
        options = options.split(' ')
        print(options)
        end = int(time.time())
        start = int(time.time()) - 3600*24*7
        ignore_regression = False
        if options[0] != '':
            if len(options) > 0:
                if options[0] == "start":
                    start = 0
                else:
                    start = int(datetime.strptime(options[0], "%d/%m/%y").timestamp())
            if len(options) > 1 and options[1] != "now":
                end = int(datetime.strptime(options[1], "%d/%m/%y").timestamp())
            if len(options) > 2:
                ignore_regression = options[2] == 'no'
        fig: plt.Figure = plt.figure()
        ax: plt.Axes = fig.add_subplot(7,1,(1,6))
        ax.set_ylabel("Player Online Count")
        ax.set_xlabel("Hour (24 hour-format GMT/BST)")
        # plt.ylabel = "Player Count"
        schema = "https://" if os.getenv("USESSL") == "true" else "http://"
        # print(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/activity/guild/{guild_name}/{start}/{end}")
        res = requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/activity/guild/{guild_name}/{start}/{end}").json()
        old_xvalues = [*map(int, res["data"])]
        # old_xvalues = sorted(old_xvalues)
        xvalues = [datetime.fromtimestamp(old_xvalues[0]).strftime("%-d/%m/%y-%H")]
        xtimes = [int(old_xvalues[0])]
        yvalues = [res["data"][str(old_xvalues[0])]]
        for i in range(1, len(old_xvalues)):
            # fill in the gaps in time
            fill = (old_xvalues[i]-old_xvalues[i-1])//3600
            if fill > 2:
                xvalues.extend(
                    [datetime.fromtimestamp(old_xvalues[i-1]+j*3600).strftime("%-d/%m/%y-%H")
                        for j in range(1, fill)]
                )
                xtimes.extend([old_xvalues[i-1]+j*3600
                        for j in range(1, fill)])
                yvalues.extend([0]*(fill-1))
            xtimes.append(old_xvalues[i])
            xvalues.append(datetime.fromtimestamp(old_xvalues[i]).strftime("%-d/%m/%y-%H"))
            yvalues.append(res["data"][str(old_xvalues[i])])

        ax.plot(xtimes, yvalues)
        try:
            solved = sinusoid_regress([x-xtimes[0] for x in xtimes], yvalues)
        # runtime errors with numpy. This really never happens unless the guild was recently added
        except:
            solved = [0,0,0,0]
        content = f"```Min: {min(yvalues)}\nMax: {max(yvalues)}\nMean: {solved[3]}"
        if not ignore_regression:

            freq = 1/solved[1]*2*3.1415
            model = lambda t: solved[0]*math.sin(freq*t-solved[2])+solved[3]
            model_x = range(xtimes[0], xtimes[-1], 3600)
            model_values = [model(x) for x in model_x]
            model_x_date = [datetime.fromtimestamp(x).strftime("%-d/%m/%y-%H") for x in model_x]
            template = f"\n{solved[0]}*sin({freq}*t-{solved[2]})+{solved[3]}"
            content += template
            # print(model_x_date)
            ax.plot(model_x, model_values, 'g--')
        content += '```'
        # print(model_x_date)
        # ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
        # skip = len(xvalues)//10
        
        # ax.xaxis.set_major_formatter(mticker.FuncFormatter(tick_rename))
        
        # ax.tick_params(axis='x', rotation=40)
        # plt.plot(res["data"].keys(), [res["data"][k] for k in res["data"]])
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
        
        await LongTextEmbed.send_message(valor, ctx, f"Guild Activity of {guild_name}", content, color=0xFF0000, 
            file=file, 
            url="attachment://plot.png"
        )

    # @guild.error
    # async def guild_error(ctx, error):
    #     await ctx.send(embed=ErrorEmbed("Command failed :/. Make sure to surround guild names with quotes"))
    #     print(error)

    # @plot.error
    # async def plot_error(ctx, error):
    #     await ctx.send(embed=ErrorEmbed("Command failed :/. Make sure to surround guild names with quotes"))
    #     print(error)
    
    @plot.command()
    async def tag(ctx: Context, guild_name = "AVO", options = ""):
        return await guild(ctx, guild_name_from_tag(guild_name), options) 

    @valor.help_override.command()
    async def plot(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Plot", desc, color=0xFF00)