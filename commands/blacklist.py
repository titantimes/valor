from sql import ValorSQL
from valor import Valor
from discord import Embed
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, tables
import commands.common
from datetime import datetime
import time
import os
import argparse
from dotenv import load_dotenv
from .common import from_uuid, get_uuid, guild_tag_from_name, current_guild_from_uuid
import requests

load_dotenv()
TEST = os.getenv("TEST")=="TRUE"

async def _register_blacklist(valor: Valor):
    desc = "A list that shows untrustworthy/bad behaving players."
    parser = argparse.ArgumentParser(description='Blacklist command')
    parser.add_argument('-l', '--list', action="store_true") # list all blacklisted players and their UUID
    parser.add_argument('-a', '--add', type=str)  # player name
    parser.add_argument('-r', '--reason', type=str)
    parser.add_argument('-d', '--delete', type=str)  # player name
    parser.add_argument('-s', '--search', type=str)  # player name

    @valor.command()
    async def blacklist(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Blacklist Command", parser.format_help().replace("main.py", "-blacklist"), color=0xFF00)

        if opt.list:
            blacklist_query = f"SELECT uuid, timestamp FROM player_blacklist"
            result = await ValorSQL._execute(blacklist_query)

            blacklist_rows = [
                (
                    await from_uuid(uuid), 
                    await guild_tag_from_name(await current_guild_from_uuid(uuid)),
                    datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y")
                )
                for uuid, timestamp in result
            ]

            content = tables.fmt(["Name", "Guild", "Time added"], blacklist_rows)
            return await LongTextEmbed.send_message(valor, ctx, title=f"Blacklist", content=content, color=0xFF10, code_block=True, footer="Ask any Titan+ with proof to add someone to the blacklist")

        elif opt.add:
            if not commands.common.role1(ctx.author) and not TEST:
                return await ctx.send(embed=ErrorEmbed("No Permissions"))
            
            if "-" in opt.add:
                return await ctx.send(embed=ErrorEmbed("Invalid input")) # lazy sanitation
            
            reason = opt.reason if opt.reason else "No reason given"
            timestamp = int(time.time())
            
            try:
                add_query = f"""REPLACE INTO player_blacklist VALUES ("{await get_uuid(opt.add)}", "{reason}", {timestamp})"""
            except:
                return await ctx.send(embed=ErrorEmbed("Can't add player (Player doesn't exist?)"))
            
            time_str = f"<t:{timestamp}:F>"

            result = await ValorSQL._execute(add_query)

            content = f"Reason: {reason}\nTime added: {time_str}"
            return await LongTextEmbed.send_message(valor, ctx, title=f"Added {opt.add} to the blacklist", content=content, color=0xFF10)
        
        elif opt.delete:
            if not commands.common.role1(ctx.author) and not TEST:
                return await ctx.send(embed=ErrorEmbed("No Permissions"))
            
            if "-" in opt.delete:
                return await ctx.send(embed=ErrorEmbed("Invalid input")) # lazy sanitation
        
            delete_query = f"DELETE FROM player_blacklist WHERE uuid='{await get_uuid(opt.delete)}'"
            result = await ValorSQL._execute(delete_query)

            return await LongTextEmbed.send_message(valor, ctx, title=f"Deleted {opt.delete}", content="Removed player from the blacklist", color=0xFF10)
        
        elif opt.search:           
            uuid = await get_uuid(opt.search) if '-' not in opt.search else opt.search
            username = await from_uuid(uuid)
            
            search_query = f"SELECT reason, timestamp FROM player_blacklist WHERE uuid='{uuid}'"
            result = await ValorSQL._execute(search_query)
            
            if result:
                db_guild = await current_guild_from_uuid(uuid)
                guild = db_guild if db_guild != "N/A" else requests.get(f"https://api.wynncraft.com/v3/player/{uuid}").json()
                
                if type(guild) == dict:
                    if "Error" in guild:
                        guild = "No Wynncraft data"
                    else:
                        guild = guild["guild"]["name"]
                
                embed = Embed(color=0xFF10,title="Blacklist search result",description=username)
                embed.set_footer(text="Ask any Titan+ with proof to add someone to the blacklist")
                embed.set_thumbnail(url=f"https://visage.surgeplay.com/bust/512/{uuid}.png?y=-40")
                embed.add_field(name="Reason",value=result[0][0],inline=False)
                embed.add_field(name="Current guild",value=guild)
                embed.add_field(name="Time added",value=f"<t:{result[0][1]}:F>")
                embed.add_field(name="UUID",value=uuid,inline=False)
                
                return await ctx.send(embed=embed)
            else:
                return await ctx.send(embed=ErrorEmbed("No results found"))

        await LongTextEmbed.send_message(valor, ctx, "Blacklist command", desc, color=0xFF00)
            
    @valor.help_override.command()
    async def blacklist(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Blacklist command", desc, color=0xFF00)
    
    
    
