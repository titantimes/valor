import requests
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, sinusoid_regress
from discord.ext.commands import Context
from datetime import datetime
from discord import File
from collections import defaultdict
import logging
from dotenv import load_dotenv
import argparse
from PIL import Image, ImageDraw, ImageFont
from .common import guild_name_from_tag, guild_tag_from_name
import json, math, json, discord, time

load_dotenv()
with open("assets/map_regions.json") as f:
    map_regions = json.load(f)

async def _register_map(valor: Valor):
    desc = "100 percent an Athena knockoff"
    parser = argparse.ArgumentParser(description='Map command')
    main_map = Image.open("assets/main-map.png") # like 10MB ish
    font = ImageFont.truetype("MinecraftRegular.ttf", 16)
    map_width, map_height = main_map.size

    def to_full_map_coord(x_ingame, y_ingame):
        # (-1614 -2923) (x,y) center of corkus -> (192 913) (x, canvas y)
        # (-1609 -2943) (x,y) center of corkus balloon -> (193 908) (x, canvas y)
        x_canvas = (x_ingame+2382)*map_width/4034 # do linalg.solve to compute the weights
        y_canvas = (y_ingame+6572)*map_height/6414

        return x_canvas, y_canvas
    

    def draw_text_with_outline(draw, position, text, font, fill, outline_color=(0, 0, 0), outline_width=1):
        x, y = position
        y_pad = -2
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy + y_pad), text, font=font, fill=outline_color)
        draw.text((x, y + y_pad), text, font=font, fill=fill)


    def hex_to_rgb(hex_color, fallback=(136, 136, 136)):
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                # Default conversion
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            elif len(hex_color) == 3:
                # Shorthand RGB, like #f0a -> #ff00aa
                return tuple(int(hex_color[i]*2, 16) for i in range(3))
            elif len(hex_color) < 6:
                # Pad short values like "ff00" -> "ff0000"
                padded = (hex_color + "0"*6)[:6]
                return tuple(int(padded[i:i+2], 16) for i in (0, 2, 4))
            else:
                raise ValueError("Too long to be valid RGB")
        except Exception:
            logging.warning(f"Invalid color code: #{hex_color}")
            return fallback

    
    
    @valor.command(aliases=["m"])
    async def map(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Map", parser.format_help().replace("main.py", "-map"), color=0xFF00)

        try:
            terr_res = requests.get("https://athena.wynntils.com/cache/get/territoryList").json()

            guild_colors_res = requests.get("https://athena.wynntils.com/cache/get/guildListWithColors").json()
            guild_color_lookup = {entry["_id"]: entry["color"] for entry in guild_colors_res.values()}
        except:
            logging.error("Athena is down")
            return await ErrorEmbed.send_message(valor, ctx, "Athena is down")

        with open("assets/terr_conns.json") as f:
            terr_conns = json.load(f)

        # Layers: base (connections), territory (fills), labels (text/outlines)
        base = Image.new("RGBA", main_map.size, (0, 0, 0, 0))
        territory_layer = Image.new("RGBA", main_map.size, (0, 0, 0, 0))
        label_layer = Image.new("RGBA", main_map.size, (0, 0, 0, 0))

        draw_base = ImageDraw.Draw(base)
        draw_territory = ImageDraw.Draw(territory_layer)
        draw_label = ImageDraw.Draw(label_layer)

        centers = {}

        # First pass: determine centers of each terr
        for terr_name, data in terr_res["territories"].items():
            loc = data["location"]
            x1, y1 = to_full_map_coord(loc["startX"], loc["startZ"])
            x2, y2 = to_full_map_coord(loc["endX"], loc["endZ"])
            left, right = sorted([x1, x2])
            top, bottom = sorted([y1, y2])
            cx = (left + right) / 2
            cy = (top + bottom) / 2
            centers[terr_name] = (cx, cy)

        # Draw the connections first, on base layer
        for terr_name, conn in terr_conns.items():
            center_start = centers.get(terr_name)
            if not center_start:
                continue
            for target_name in conn.get("Trading Routes", []):
                center_end = centers.get(target_name)
                if not center_end:
                    continue
                draw_base.line([center_start, center_end], fill=(20, 20, 20), width=2)

        # Draw territory fills and labels
        for terr_name, data in terr_res["territories"].items():
            loc = data["location"]
            guild_name = data["guild"]
            prefix = data["guildPrefix"]
            if prefix == "None":
                rgb = (255, 255, 255)
            else:
                color = data.get("guildColor") or guild_color_lookup.get(guild_name, "#888888")
                rgb = hex_to_rgb(color)
            fill_color = rgb + (90,)
            border_color = rgb + (255,)

            x1, y1 = to_full_map_coord(loc["startX"], loc["startZ"])
            x2, y2 = to_full_map_coord(loc["endX"], loc["endZ"])
            left, right = sorted([x1, x2])
            top, bottom = sorted([y1, y2])
            cx = (left + right) / 2
            cy = (top + bottom) / 2

            # Fill on territory layer
            draw_territory.rectangle([left, top, right, bottom], fill=fill_color)

            # Outline and text on label layer
            draw_label.rectangle([left-1, top-1, right+1, bottom+1], outline=(0, 0, 0), width=3)
            draw_label.rectangle([left, top, right, bottom], outline=border_color, width=2)

            bbox = draw_label.textbbox((0, 0), prefix, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw_text_with_outline(draw_label, (cx - text_width / 2, cy - text_height / 2), prefix, font, fill=border_color)

        # Composite in correct order
        composed = Image.alpha_composite(main_map.convert("RGBA"), base)
        composed = Image.alpha_composite(composed, territory_layer)
        final = Image.alpha_composite(composed, label_layer)

        final.save("/tmp/map.png")
        await ctx.send(file=discord.File("/tmp/map.png"))



    @valor.help_override.command()
    async def map(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Map", desc, color=0xFF00)
