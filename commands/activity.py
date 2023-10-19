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

load_dotenv()
uri = "https://api.wynncraft.com/v3/guild/"
player_uri = "https://api.wynncraft.com/v3/player/"

async def query_task(session: aiohttp.ClientSession, uuid: str) -> Tuple[str, datetime]:
    async with session.get(player_uri + uuid) as res:
        res = await res.json()
    user = res["username"]
    last = res["lastJoin"]
    return user, datetime.utcnow() - datetime.strptime(last, "%Y-%m-%dT%H:%M:%S.%f")

async def _register_activity(valor: Valor):
    desc = "Gets you the player last logins sorted"
    @valor.command()
    async def activity(ctx: Context, guild="Titans Valor"):
        # members = [x["uuid"] for x in requests.get(uri + guild).json()["members"]]
        members = [x["uuid"] for k, v in requests.get(uri + guild).json()["members"].items() if k != "total" for _, x in v.items()]
        async with aiohttp.ClientSession() as sess:
            data = await asyncio.gather(*[query_task(sess, uuid) for uuid in members])
        content = sorted([[pair[0], pair[1].days*24*3600 + pair[1].seconds] for pair in data], key = lambda x: -x[1])
        content = [(pair[0].replace('_', '\_'), f"{round(pair[1]/3600/24, 2)} days") for pair in content]
        await LongFieldEmbed.send_message(valor, ctx, f"Player Last Join of {guild} ({len(members)})", content)
    @valor.help_override.command()
    async def activity(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Activity", desc, color=0xFF00)