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

async def _register_coolness(valor: Valor):
    desc = "The leaderboard (but for coolness)"
    parser = argparse.ArgumentParser(description='Coolness command')
    parser.add_argument('-r', '--range', nargs=2)
    parser.add_argument('-g', '--guild', nargs='+', default=["ANO"])
    parser.add_argument('-b', '--backwards', action='store_true')
    parser.add_argument('-t', '--threshold', type=float, default=-1)

    @valor.command()
    async def coolness(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "coolness", parser.format_help().replace("main.py", "-coolness"), color=0xFF00)
        
        start = time.time()
        query = "SELECT name, guild FROM activity_members WHERE "
        if opt.range:
            query += f" timestamp >= {start-3600*24*float(opt.range[0])} AND timestamp <= {start-3600*24*float(opt.range[1])}"
        else:
            query += f"  timestamp >= {start-3600*24*7}"

        res = await ValorSQL._execute(query)
        end = time.time()
        
        count = {}
        name_to_guild = {}

        guild_names, unidentified = await guild_names_from_tags(opt.guild)
        guild_names = set(guild_names)
        if not guild_names:
            return await LongTextEmbed.send_message(
                valor, ctx, f"Coolness Error", f"{unidentified} unknown", color=0xFF0000)

        guild_members = {g_name: {name 
            for k, v in requests.get(f"https://api.wynncraft.com/v3/guild/{g_name}")
                .json().get("members", {}).items() if k != "total" for name, _ in v.items()} for g_name in guild_names}

        for guild in guild_members:
            for member in guild_members[guild]:
                count[member] = 0
                name_to_guild[member] = guild

        for row in res:
            g_name = row[1]
            if not g_name in guild_names or not row[0] in guild_members[g_name]:
                continue
            if not row[0] in count:
                count[row[0]] = 0
                name_to_guild[row[0]] = g_name
            count[row[0]] += 1

        board = sorted([*count.items()], key=lambda x: x[1], reverse=not opt.backwards)

        # wow actually using a leetcode trick, let alone binary search in practice
        # will end up making a splice copy anyways which involves same complexity as a linear search
        # but leaving this here in case I think of an optimization
        if opt.threshold != -1:
            left = 0; mid = 0; right = len(board)-1
            while left <= right:
                mid = left + (right-left)//2
                if board[mid][1] > opt.threshold+.5: right = mid-1
                else: left = mid+1
            board = board[:mid]

        header = [" Guild" + ' '*(max(len(x) for x in name_to_guild.values())-5), "Username"+' '*(18-8), "Hours Online"]
        table = [(name_to_guild[name], name, count) for name, count in board] 

        if unidentified:
            unid_prefix = f"The following guilds are unidentified: {unidentified}\n" if unidentified else ""
            await LongTextEmbed.send_message(valor, ctx, "Unidentified Guilds", unid_prefix)

        await LongTextTable.send_message(valor, ctx, header, table, f"Query took {end-start:.5}s - {len(res):,} rows")
        # await LongTextEmbed.send_message(valor, ctx, "Leaderboard of Coolness", content=unid_prefix+table, code_block=True, color=0x11FFBB,
        #     footer=f"Query took {end-start:.5}s - {len(res):,} rows"
        # )

    @coolness.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def coolness(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Coolness", desc, color=0xFF00)
    
    
    