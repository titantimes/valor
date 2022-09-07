from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed
import random
from datetime import datetime
import requests
from sql import ValorSQL
from commands.common import get_uuid, from_uuid

async def _register_leaderboard(valor: Valor):
    desc = "The leaderboard"
    stat_set = {'sand_swept_tomb', 'galleons_graveyard', 'firstjoin', 'scribing', 'chests_found', 'woodcutting', 'tailoring', 'fishing', 'eldritch_outlook', 'alchemism', 'logins', 'deaths', 'corrupted_decrepit_sewers', 'armouring', 'corrupted_undergrowth_ruins', 'items_identified', 'nest_of_the_grootslangs', 'blocks_walked', 'lost_sanctuary', 'mining', 'the_canyon_colossus', 'undergrowth_ruins', 'corrupted_ice_barrows', 'jeweling', 'woodworking', 'uuid', 'underworld_crypt', 'fallen_factory', 'mobs_killed', 'infested_pit', 'decrepit_sewers', 'corrupted_sand_swept_tomb', 'corrupted_infested_pit', 'farming', 'corrupted_lost_sanctuary', 'cooking', 'guild', 'combat', 'weaponsmithing', 'playtime', 'corrupted_underworld_crypt', 'ice_barrows', 'nexus_of_light', "guild_rank"}
    @valor.command()
    async def leaderboard(ctx: Context, stat="galleons_graveyard"):
        if not stat in stat_set:
            return await LongTextEmbed.send_message(valor, ctx, "Invalid Stat, choose from the following: ", content='\n'.join(stat_set), code_block=True, color=0x1111AA)
        
        res = await ValorSQL._execute(f"SELECT uuid_name.name, uuid_name.uuid, player_stats.{stat} FROM player_stats LEFT JOIN uuid_name ON uuid_name.uuid=player_stats.uuid ORDER BY {stat} DESC LIMIT 50")
        stats = []
        for m in res:
            if not m[0] and m[1]:
                stats.append((await from_uuid(m[1]), m[2]))
            else:
                stats.append((m[0] if m[0] else "can't find name", m[2]))

        table = "```\n"+'\n'.join("%3d. %24s %5d" % (i+1, stats[i][0], stats[i][1]) for i in range(len(stats)))+"\n```"
        

        await LongTextEmbed.send_message(valor, ctx, stat, content=table, color=0x11FFBB)

    @leaderboard.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def leaderboard(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Leaderboard", desc, color=0xFF00)
    
    
    