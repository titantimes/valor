from valor import Valor
from util.valor_message import LongTextEmbed
from discord.ext.commands import Context
import argparse
import requests
import time

async def _register_up(valor: Valor):
    desc = "Shows the uptime of Wynncraft worlds along with multiple sorting options."
    parser = argparse.ArgumentParser(description='Up command')
    parser.add_argument("-s", "--sort", choices=["uptime"], default="uptime")

    @valor.command()
    async def up(ctx: Context, *args):

        try:
            opt = parser.parse_args(args)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Up", parser.format_help().replace("main.py", "-up"), color=0xFF00)

        res = requests.get("https://athena.wynntils.com/cache/get/serverList")
        server_list = res.json()["servers"]

        for server in server_list:
            server_list[server]["uptime"] = round((time.time() - (server_list[server]["firstSeen"] / 1000)) / 60)
            del server_list[server]["firstSeen"]
        
        sorted_server_list = sorted(server_list, key=lambda x: server_list[x][f"{opt.sort}"])

        # very stupid line
        table = "%5s %12s %7s\n" % ("World", "Uptime", "Players") +'\n'.join("%5s %12s %7s" % 
            (server, 
                f"{server_list[server]['uptime'] // 60} h {server_list[server]['uptime'] % 60} m", 
                f"{len(server_list[server]['players'])}/45") for server in sorted_server_list)

        await LongTextEmbed.send_message(valor, ctx, "Server List", content=table, code_block=True, color=0x03A9F4)      
    
    @valor.help_override.command()
    async def up(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Up", desc, color=0xFF00)
