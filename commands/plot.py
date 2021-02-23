import requests
from valor import Valor
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed
from discord.ext.commands import Context
from datetime import datetime
from discord import File
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import time
import math

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
    async def guild(ctx: Context, guild_name = "Avicia", start=int(time.time())-7*24*3600, end=int(time.time())):
        fig: plt.Figure = plt.figure()
        ax: plt.Axes = fig.add_subplot(5,1,(1,4))
        ax.set_ylabel("Player Online Count")
        ax.set_xlabel("Date (by the hour)")
        # plt.ylabel = "Player Count"
        schema = "https://" if os.getenv("USESSL") == "true" else "http://"
        print(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/activity/guild/{guild_name}/{start}/{end}")
        res = requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/activity/guild/{guild_name}/{start}/{end}").json()
        old_xvalues = list(res["data"])
        xvalues = [datetime.fromtimestamp(int(old_xvalues[0])).strftime("%-d/%m/%y-%H")]
        yvalues = [res["data"][old_xvalues[0]]]
        for i in range(1, len(old_xvalues)):
            # fill in the gaps in time
            old_xvalues[i] = int(old_xvalues[i])
            old_xvalues[i-1] = int(old_xvalues[i-1]) 
            xvalues.append(datetime.fromtimestamp(old_xvalues[i]).strftime("%-d/%m/%y-%H"))
            yvalues.append(res["data"][str(old_xvalues[i])])
            if int(old_xvalues[i])-int(old_xvalues[i-1]) > 60*61:
                fill = int((old_xvalues[i]-old_xvalues[i-1])/3600)
                xvalues.extend(
                    [datetime.fromtimestamp(old_xvalues[i]+j*3600).strftime("%-d/%m/%y-%H")
                        for j in range(1, fill)]
                )
                yvalues.extend([0 for _ in range(1, fill)])
        ax.plot(xvalues, yvalues)
        ax.tick_params("x",rotation=97)
        # ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
        for i, label in enumerate(ax.get_xticklabels()):
            if i % math.ceil(math.log(len(xvalues), 4)):
                label.set_visible(False)
        # plt.plot(res["data"].keys(), [res["data"][k] for k in res["data"]])
        fig.savefig("/tmp/valor_guild_plot.png")
        file = File("/tmp/valor_guild_plot.png", filename="plot.png")
        await LongTextEmbed.send_message(valor, ctx, f"Guild Activity of {guild_name}", "", color=0xFF0000, 
            file=file, 
            url="attachment://plot.png"
        )

    @guild.error
    async def guild_error(ctx, error):
        await ctx.send(embed=ErrorEmbed("Command failed :/. Make sure to surround guild names with quotes"))
        print(error)

    @plot.error
    async def plot_error(ctx, error):
        await ctx.send(embed=ErrorEmbed("Command failed :/. Make sure to surround guild names with quotes"))
        print(error)
    
    @valor.help_override.command()
    async def plot(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Plot", desc, color=0xFF00)