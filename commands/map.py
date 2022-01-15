import requests
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, sinusoid_regress, guild_name_from_tag
from discord.ext.commands import Context
from datetime import datetime
from discord import File
from dotenv import load_dotenv
import os
import numpy as np
import argparse
from PIL import Image

load_dotenv()
async def _register_map(valor: Valor):
    desc = "100 percent an Athena knockoff"
    parser = argparse.ArgumentParser(description='Map command')
    parser.add_argument('-g', '--guild', nargs='+')
    parser.add_argument('-r', '--routes', action='store_true')
    main_map = Image.open("assets/main-map.png")
    map_width, map_height = main_map.size
    
    @valor.command()
    async def map(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Map", parser.format_help().replace("main.py", "-map"), color=0xFF00)
        
        requests.get("https://athena.wynntils.com/cache/get/territoryList")

        section = main_map.crop((0, map_height-1-500, 500, map_height-1))
        section.convert("RGB").save("/tmp/map_output.jpg")
        file = File("/tmp/map_output.jpg", filename="map.jpg")

        await LongTextEmbed.send_message(valor, ctx, f"Map", "It's a map", color=0xFF0000, 
            file=file, 
            url="attachment://map.jpg",
        )

        main_map.close()

    @valor.help_override.command()
    async def map(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Map", desc, color=0xFF00)