from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed, guild_name_from_tag
import random
from datetime import datetime
import requests
from sql import ValorSQL
from commands.common import get_uuid, from_uuid

async def _register_leaderboard(valor: Valor):
    desc = "The leaderboard"
    
    @valor.command()
    async def leaderboard(ctx: Context):
        res = await ValorSQL._execute("SELECT uuid_name.name, uuid_name.uuid, player_stats.galleons_graveyard FROM player_stats LEFT JOIN uuid_name ON uuid_name.uuid=player_stats.uuid ORDER BY galleons_graveyard DESC LIMIT 50")
        stats = []
        for m in res:
            if not m[0] and m[1]:
                stats.append((await from_uuid(m[1]), m[2]))
            else:
                stats.append((m[0] if m[0] else "can't find name", m[2]))

        table = "```\n"+'\n'.join("%3d. %24s %5d" % (i+1, stats[i][0], stats[i][1]) for i in range(len(stats)))+"\n```"
        

        await LongTextEmbed.send_message(valor, ctx, "Galleon's Graveyard", content=table, color=0x11FFBB)

    @leaderboard.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def leaderboard(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Leaderboard", desc, color=0xFF00)
    
    
    