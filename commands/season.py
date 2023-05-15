from sql import ValorSQL
from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed, tables
import commands.common
from datetime import datetime
import os
import argparse
from dotenv import load_dotenv
from .common import guild_name_from_tag

load_dotenv()
TEST = os.getenv("TEST")=="TRUE"

async def _register_season(valor: Valor):
    desc = "Manage season times"
    parser = argparse.ArgumentParser(description='Season command')
    parser.add_argument('-l', '--list', action="store_true") # list all seasons and their start / end times

    parser.add_argument('-e', '--edit', type=str)  # season name
    parser.add_argument('-t', '--times', nargs=2, type=int)  # start, end. ideally timestamps

    @valor.command()
    async def season(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Season Command", parser.format_help().replace("main.py", "-season"), color=0xFF00)
        
        if not commands.common.role1(ctx.author) and not TEST:
            return await ctx.send(embed=ErrorEmbed("No Permissions"))

        if opt.list:
            season_query = f"SELECT season_name, start_time, end_time FROM season_list"
            result = await ValorSQL._execute(season_query)
            season_rows = [
                (season_name, datetime.fromtimestamp(start_time).strftime("%d-%m-%Y"), 
                    datetime.fromtimestamp(end_time).strftime("%d-%m-%Y"))
                for season_name, start_time, end_time in result
            ]

            content = tables.fmt(["Season", "Start", "End"], season_rows)
            return await LongTextEmbed.send_message(valor, ctx, title=f"Guild Group of {opt.list}", content=content, color=0xFF10, code_block=True)

        elif opt.edit:
            if "-" in opt.times:
                return await ctx.send(embed=ErrorEmbed("Invalid input")) # lazy sanitation
            
            season_edit_query = f"REPLACE INTO season_list VALUES ('{opt.edit}', {opt.times[0]}, {opt.times[1]})"
            start_str = datetime.fromtimestamp(opt.times[0]).ctime()
            end_str = datetime.fromtimestamp(opt.times[1]).ctime()

            result = await ValorSQL._execute(season_edit_query)

            content = f"Beginning: {start_str}\nEnding: {end_str}"
            return await LongTextEmbed.send_message(valor, ctx, title=f"Set Season Time for {opt.edit}", content=content, color=0xFF10, code_block=True)
        
        await LongTextEmbed.send_message(valor, ctx, "Season command", desc, color=0xFF00)
            
    @valor.help_override.command()
    async def season(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Season command", desc, color=0xFF00)
    
    
    