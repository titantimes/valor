from valor import Valor
from discord.ext.commands import Context
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
    parser = argparse.ArgumentParser(description='Update stats command')

    parser.add_argument('-g', '--guild', nargs='+')
    parser.add_argument('-u', '--username', nargs='+')

    @valor.command()
    async def update_stats(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Update stats command", parser.format_help().replace("main.py", "-update_stats"), color=0xFF00)

        update_players = []
        if opt.guild:
            for guild_tag in opt.guild:
                guild_name = await guild_name_from_tag(guild_tag)
                guild_members_data = (await valor.ahttp.get_json("https://api.wynncraft.com/v3/guild/"+guild_name))["members"]
                for rank in guild_members_data:
                    if type(guild_members_data[rank]) != dict: continue

                    update_players.extend([guild_members_data[rank][x]["uuid"] for x in guild_members_data[rank]])

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
            content += "\nFailed to Update:\n" + '\n'.join(failed_players)
        return await LongTextEmbed.send_message(valor, ctx, title=f"Player Stats Update", content=content, color=0xFF10, code_block=True, footer=f"RPC took {end-start:.3}s.")

    @valor.help_override.command()
    async def update_stats(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Update stats command", desc, color=0xFF00)
    
    
    