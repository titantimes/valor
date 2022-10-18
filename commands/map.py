import requests
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, sinusoid_regress
from discord.ext.commands import Context
from datetime import datetime
from discord import File
from dotenv import load_dotenv
import os
import numpy as np
import argparse
from PIL import Image, ImageDraw, ImageFont
import time
import zlib
from .common import guild_name_from_tag


load_dotenv()
async def _register_map(valor: Valor):
    desc = "100 percent an Athena knockoff"
    parser = argparse.ArgumentParser(description='Map command')
    parser.add_argument('-g', '--guild', nargs='+')
    parser.add_argument('-r', '--routes', action='store_true')
    main_map = Image.open("assets/main-map.png") # like 10MB ish
    font = ImageFont.truetype("Ubuntu-R.ttf", 16)
    map_width, map_height = main_map.size

    avo_terr_res = None
    last_avo_terr_res = 0

    def to_full_map_coord(x_ingame, y_ingame):
        # (-1614 -2923) (x,y) center of corkus -> (192 913) (x, canvas y)
        # (-1609 -2943) (x,y) center of corkus balloon -> (193 908) (x, canvas y)
        x_canvas = (x_ingame+2382)*map_width/4034 # do linalg.solve to compute the weights
        y_canvas = (y_ingame+6572)*map_height/6414

        return x_canvas, y_canvas
    
    def get_col_tuple(x, alpha):
        return ((x >> 16) & 0xFF, (x >> 8) & 0xFF, x & 0xFF, alpha)
    
    @valor.command()
    async def map(ctx: Context, *options):
        # closure capture reference
        nonlocal avo_terr_res, last_avo_terr_res # I really didn't know about this feature. Better than static class var
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Map", parser.format_help().replace("main.py", "-map"), color=0xFF00)
        
        if time.time() - last_avo_terr_res > 3600*4: # refresh it every 4 hours or something
            avo_terr_res = requests.get("https://www.avicia.ml/map/terralldata.json").json()
            last_avo_terr_res = time.time()

        athena_terr_res = requests.get("https://athena.wynntils.com/cache/get/territoryList").json() 
        interested_guild_tags = set(opt.guild)
        
        interest_guild_names = set([await guild_name_from_tag(x) for x in interested_guild_tags])

        res = await ValorSQL._execute("SELECT * FROM ally_claims")
        claim_owner = {}
        for guild, terr in res:
            claim_owner[terr] = guild

        terr_details = {}
        x_lo = y_lo = float("inf")
        x_hi = y_hi = float("-inf")

        edge_list = []
        edge_list_done = set()

        for terr in athena_terr_res["territories"]:
            x0 = athena_terr_res["territories"][terr]["location"]["startX"]
            y0 = athena_terr_res["territories"][terr]["location"]["startZ"]
            x1 = athena_terr_res["territories"][terr]["location"]["endX"]
            y1 = athena_terr_res["territories"][terr]["location"]["endZ"]
            terr_details[terr] = {
                "holder": athena_terr_res["territories"][terr]["guild"],
                "holder_color": athena_terr_res["territories"][terr]["guildColor"],
                "holder_prefix": athena_terr_res["territories"][terr]["guildPrefix"],
                "adj": avo_terr_res[terr]["Trading Routes"],
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1
            }

            if opt.routes:
                neighbors = avo_terr_res[terr]["Trading Routes"]
                for n in neighbors:
                    if (terr, n) in edge_list_done or (n, terr) in edge_list_done: continue
                    edge_list_done.add((n, terr))
                    n_x0 = athena_terr_res["territories"][n]["location"]["startX"]
                    n_y0 = athena_terr_res["territories"][n]["location"]["startZ"]
                    n_x1 = athena_terr_res["territories"][n]["location"]["endX"]
                    n_y1 = athena_terr_res["territories"][n]["location"]["endZ"]
                    edge_list.append(((x0+x1)/2, (y0+y1)/2, (n_x0+n_x1)/2, (n_y0+n_y1)/2))

            if not terr_details[terr]["holder"] in interest_guild_names: continue
            x_lo = min(x_lo, min(x0, x1))
            x_hi = max(x_hi, max(x0, x1))
            y_lo = min(y_lo, min(y0, y1))
            y_hi = max(y_hi, max(y0, y1))

        # map goes from left upper to right lower world coordinates
        # following vars are 
        x_lo_full, y_lo_full = to_full_map_coord(x_lo, y_lo)
        x_hi_full, y_hi_full = to_full_map_coord(x_hi, y_hi)

        x_lo_full = max(0, x_lo_full-50) # extend the boundaries
        y_lo_full = max(0, y_lo_full-50) # extend the boundaries
        x_hi_full = min(map_width, x_hi_full+50) # extend the boundaries
        y_hi_full = min(map_height, y_hi_full+50) # extend the boundaries

        section = main_map.crop((x_lo_full, y_lo_full, x_hi_full, y_hi_full))
        section_layer = Image.new("RGBA", section.size, (255, 255, 255, 0))
        section_draw = ImageDraw.Draw(section_layer, "RGBA")
        # draw route lines
        for edge in edge_list:
            x0, y0 = to_full_map_coord(*edge[:2])
            x1, y1 = to_full_map_coord(*edge[2:])
            x0 -= x_lo_full
            y0 -= y_lo_full
            x1 -= x_lo_full
            y1 -= y_lo_full
            section_draw.line((x0, y0, x1, y1), width=3, fill=get_col_tuple(0xFFFFFF, 255))
        section = Image.alpha_composite(section, section_layer)

        # draw boxes around terrs and stuff
        for guild, claim in res:
            x0, y0 = to_full_map_coord(terr_details[claim]["x0"], terr_details[claim]["y0"])
            x1, y1 = to_full_map_coord(terr_details[claim]["x1"], terr_details[claim]["y1"])
            x0 -= x_lo_full
            y0 -= y_lo_full
            x1 -= x_lo_full
            y1 -= y_lo_full
            col_str = terr_details[claim]["holder_color"][1:]
            if not col_str:
                gu_color = zlib.crc32(guild.encode("utf8")) & 0xFFFFFF
            else:
                gu_color = int(col_str if col_str else "0", 16)

            holder_pfx = terr_details[claim]["holder_prefix"]

            section_draw.rectangle((x0, y0, x1, y1), fill=get_col_tuple(gu_color, 64), outline=get_col_tuple(gu_color, 200), width=2)
            if terr_details[claim]["holder"] != claim_owner[claim]: # disputed terr
                y_i = min(y0, y1)
                i = 0
                while y_i < max(y0, y1):
                    if i % 2 == 0:
                        section_draw.rectangle((x0, y_i, x1, min(max(y0, y1), y_i+5)), fill=get_col_tuple(0xFFFFFF, 64), outline=get_col_tuple(gu_color, 200), width=1)
                    i += 1
                    y_i += 5
                
            section_draw.text(((x0+x1-16*len(holder_pfx)/2)/2-1, (y0+y1-18)/2-1), holder_pfx, fill=get_col_tuple(0x00, 255), font=font)
            section_draw.text(((x0+x1-16*len(holder_pfx)/2)/2+1, (y0+y1-18)/2+1), holder_pfx, fill=get_col_tuple(0x00, 255), font=font)
            section_draw.text(((x0+x1-16*len(holder_pfx)/2)/2, (y0+y1-18)/2), holder_pfx, fill=get_col_tuple(0xFFFFFF, 255), font=font)

        section = Image.alpha_composite(section, section_layer)
        section.convert("RGB").save("/tmp/map_output.png")
        file = File("/tmp/map_output.png", filename="map.png")

        await LongTextEmbed.send_message(valor, ctx, f"Map", "It's out of embed because discord confines img previews in embeds.\n Striped lines means enemy holds ally (includes FFAs)", color=0xFF0000, 
            file=file, 
            # url="attachment://map.jpg",
        )

        # main_map.close() don't actually close it

    @valor.help_override.command()
    async def map(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Map", desc, color=0xFF00)