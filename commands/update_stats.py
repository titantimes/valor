from valor import Valor
from discord.ext.commands import Context
from sql import ValorSQL
from util import LongTextEmbed
import os
import argparse
import time
from dotenv import load_dotenv
from .common import guild_name_from_tag

from protos import player_stats_update_pb2
from protos import player_stats_update_pb2_grpc
import grpc

load_dotenv()
TEST = os.getenv("TEST")=="TRUE"

async def _register_update_stats(valor: Valor):
    desc = "Force a player stats update"
    cmd_warning = "\n-g option is not meant to be frequently used. If you want faster updates, please consider updating players specifically or adjusting -a or -b options"+\
        "\nAdditionally, all guild players must have been 'sufficiently active' in the last 7 days."+\
        "\nAsk Andrew for specifics."
    parser = argparse.ArgumentParser(description='Update stats command')

    parser.add_argument('-g', '--guild', nargs='+')
    parser.add_argument('-a', '--above_threshold', type=int, default=8)
    parser.add_argument('-b', '--below_threshold', type=int, default=None)
    parser.add_argument('-z', '--no_threshold', action="store_true")
    parser.add_argument('-u', '--username', nargs='+')

    @valor.command()
    async def update_stats(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Update stats command", parser.format_help().replace("main.py", "-update_stats"), color=0xFF00)

        update_players = []
        if opt.guild:
            guild_clause = " guild IN (" + ("%s,"*len(opt.guild))[:-1] + ") "
            query = """
SELECT uuid, COUNT(*) AS records
FROM player_delta_record
WHERE 
""" + guild_clause + "  AND `time` >= %s " + " GROUP BY uuid"
            query_params = [await guild_name_from_tag(x) for x in opt.guild]
            query_params.append(time.time() - 3600 * 24 * 7)
            if not opt.no_threshold:
                op = '>' if not opt.below_threshold else '<'
                val = opt.above_threshold if not opt.below_threshold else opt.below_threshold
                query += " HAVING records " + op + " %s ;"
                query_params.append(val)
            
            res = [uuid for uuid, _ in await ValorSQL.exec_param(query, query_params)]
            expected_time = len(res) * 1.5 # give or take

            await LongTextEmbed.send_message(valor, ctx, title=f"Player Stats Update", 
                                             content=f"Your query will complete in about {expected_time:.4}s." + cmd_warning, color=0xFF10, code_block=True)

            # for guild_tag in opt.guild:
            #     guild_name = await guild_name_from_tag(guild_tag)
            #     guild_members_data = (await valor.ahttp.get_json("https://api.wynncraft.com/v3/guild/"+guild_name))["members"]
            #     for rank in guild_members_data:
            #         if type(guild_members_data[rank]) != dict: continue

            #         update_players.extend([guild_members_data[rank][x]["uuid"] for x in guild_members_data[rank]])
            update_players.extend(res)

        if opt.username:
            update_players.extend(opt.username)

        async with grpc.aio.insecure_channel("localhost:50051") as channel:
            stub = player_stats_update_pb2_grpc.PlayerStatsUpdaterStub(channel)
            start = time.time()
            response = await stub.UpdatePlayerStats(player_stats_update_pb2.Request(player_uuid=update_players))
            end = time.time()

        requested_players = set(update_players)
        failed_players = set(response.failures)

        content = "Updated Players:\n" + '\n'.join(requested_players - failed_players)
        if failed_players:
            content += "\n\nFailed to Update:\n" + '\n'.join(failed_players)
        return await LongTextEmbed.send_message(valor, ctx, title=f"Player Stats Update", content=content, color=0xFF10, code_block=True, footer=f"RPC took {end-start:.3}s.")

    @valor.help_override.command()
    async def update_stats(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Update stats command", desc, color=0xFF00)
    
    
    