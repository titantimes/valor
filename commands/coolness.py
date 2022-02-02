from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed, guild_name_from_tag
import random
from datetime import datetime
import requests
from sql import ValorSQL
from commands.common import get_uuid, from_uuid
import time
import argparse

async def _register_coolness(valor: Valor):
    desc = "The leaderboard (but for coolness)"
    parser = argparse.ArgumentParser(description='Coolness command')
    parser.add_argument('-r', '--range', nargs=2)
    parser.add_argument('-g', '--guild', nargs='+')

    @valor.command()
    async def coolness(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "coolness", parser.format_help().replace("main.py", "-coolness"), color=0xFF00)
        
        start = time.time()
        query = "SELECT name, guild FROM activity_members WHERE "
        if opt.range:
            query += f" timestamp >= {start-3600*24*int(opt.range[0])} AND timestamp <= {start-3600*24*int(opt.range[1])}"
        else:
            query += f"  timestamp >= {start-3600*24*7}"

        res = await ValorSQL._execute(query)
        end = time.time()
        
        count = {}
        name_to_guild = {}
        guild_names = set(guild_name_from_tag(x) for x in opt.guild)
        for row in res:
            g_name = row[1]
            if not g_name in guild_names:
                continue
            if not row[0] in count:
                count[row[0]] = 0
                name_to_guild[row[0]] = g_name
            count[row[0]] += 1

        board = sorted([*count.items()], key=lambda x: x[1], reverse=True)
        table = '\n'.join("[%24s] %18s %5d%%" % (name_to_guild[name], name, count*2) for name, count in board)
        await LongTextEmbed.send_message(valor, ctx, "Leaderboard of Coolness", content=table, code_block=True, color=0x11FFBB,
            footer=f"Query took {end-start:.5}s - {len(res):,} rows"
        )

    @coolness.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def coolness(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Coolness", desc, color=0xFF00)
    
    
    