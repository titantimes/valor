import requests
from valor import Valor
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed
from discord.ext.commands import Context
from datetime import datetime
from dotenv import load_dotenv
from typing import Tuple
import os
import aiohttp
import asyncio
import argparse
import time
from sql import ValorSQL
from .common import guild_name_from_tag

load_dotenv()
uri = "https://api.wynncraft.com/v3/guild/"
player_uri = "https://api.wynncraft.com/v3/player/"

async def query_task(session: aiohttp.ClientSession, uuid: str) -> Tuple[str, datetime, str]:
    async with session.get(player_uri + uuid) as res:
        res = await res.json()

    # skip player if wynnapi errors.
    if "username" not in res:
        return None, None, None
    user = res["username"]
    last = res["lastJoin"][:-1]
    uuid = res["uuid"]

    return user, datetime.fromisoformat(last).timestamp(), uuid

async def _register_activity(valor: Valor):
    desc = "Gets you the player last logins sorted"

    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-g', '--guild', type=str)

    @valor.command()
    async def activity(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "activity", parser.format_help().replace("main.py", "-activity"), color=0xFF00)
        
        if not opt.guild:
            return await LongTextEmbed.send_message(valor, ctx, "activity", parser.format_help().replace("main.py", "-activity"), color=0xFF00)
        
        guild_name = await guild_name_from_tag(opt.guild)

        guild_members_data = requests.get(uri+guild_name).json()["members"]
        members = set()
        for rank in guild_members_data:
            if type(guild_members_data[rank]) != dict: continue

            members |= {guild_members_data[rank][x]["uuid"] for x in guild_members_data[rank]}

        members = list(members)
        # res = await ValorSQL.exec_param("SELECT uuid_name.name, player_stats.lastJoin, player_stats.uuid FROM player_stats LEFT JOIN uuid_name ON player_stats.uuid=uuid_name.uuid WHERE player_stats.guild=%s", [guild_name])
        content = []

        # checkup_on = []
        # checkup_on.extend(set(members) - set(uuid for _, _, uuid in res)) # by default get anyone who isn't in player_stats

        res = []
        async with aiohttp.ClientSession() as sess:
            res.extend(await asyncio.gather(*[query_task(sess, uuid) for uuid in members[:64]]))
            await asyncio.sleep(1)
            res.extend(await asyncio.gather(*[query_task(sess, uuid) for uuid in members[64:]]))
        
        for name, last_join, uuid in res:
            if not uuid in members: continue
            if not name: continue # name is none type should almost never happen (initially messed up uuid_name table or when wynnapi returns error)
            
            time_delta = datetime.utcnow() - datetime.fromtimestamp(last_join)
            if last_join:
                content.append((time_delta, name.replace('_', '\\_'), f'{time_delta.days}d{time_delta.seconds // 3600}h'))
            else:
                content.append((time_delta, name.replace('_', '\\_'), '30d+'))
                # checkup_on.append(uuid)
        
        content.sort(reverse=True)
        content = [(x[1], x[2]) for x in content]

        # push the player into the queue to check on
        # now = time.time()
        # pairs = [(uuid, now) for uuid in checkup_on]
        # if pairs:
        #     await ValorSQL.exec_param("REPLACE INTO player_stats_queue VALUES " + ("(%s,%s),"*len(pairs))[:-1], [y for x in pairs for y in x])

        # quickly respond to the command
        await LongFieldEmbed.send_message(valor, ctx, f"Player Last Join of {guild_name} ({len(members)})", content)
        
    @activity.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed(err=error))
        raise error
    
    @valor.help_override.command()
    async def activity(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Activity", desc, color=0xFF00)