from sql import ValorSQL
from valor import Valor
from discord.ext.commands import Context
import discord
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed
import random
from datetime import datetime
import requests
import commands.common
import os
from dotenv import load_dotenv

load_dotenv()
TEST = os.getenv("TEST")=="TRUE"

async def _register_glist(valor: Valor):
    desc = "Adds or Removes Guild from Guild List"
    
    @valor.group()
    async def glist(ctx: Context):
        if ctx.invoked_subcommand: return
        exist = await ValorSQL._execute(f"SELECT * FROM guild_list")
        content = '\n'.join(x[0] for x in exist)
        await LongTextEmbed.send_message(valor, ctx, title="Guild List", content=content, color=0xFF10, code_block=True)
    
    @glist.command()
    async def add(ctx: Context, guild: str):
        if "-" in guild:
            return await ctx.send(embed=ErrorEmbed("Invalid guild name")) # lazy sanitation 
        if not commands.common.role1(ctx.author) and not TEST:
            return await ctx.send(embed=ErrorEmbed("No Permissions"))

        exist = await ValorSQL._execute(f"SELECT * FROM guild_list WHERE guild=\"{guild}\" LIMIT 1")
        if exist:
            return await LongTextEmbed.send_message(valor, ctx, f"'{guild}' is already in the list", color=0xFF10)
        
        await ValorSQL._execute(f"INSERT INTO guild_list VALUES (\"{guild}\")")

        await LongTextEmbed.send_message(valor, ctx, f"Added '{guild}' to list.", color=0xFF10)
    
    @glist.command()
    async def remove(ctx: Context, guild: str):
        if "-" in guild:
            return await ctx.send(embed=ErrorEmbed("Invalid guild name")) # lazy sanitation 
        if not TEST and not commands.common.role1(ctx.author):
            return await ctx.send(embed=ErrorEmbed("No Permissions"))
        
        exist = await ValorSQL._execute(f"SELECT * FROM guild_list WHERE guild=\"{guild}\" LIMIT 1")
        if exist:
            await ValorSQL._execute(f"DELETE FROM guild_list WHERE guild=\"{guild}\" LIMIT 1")
            return await LongTextEmbed.send_message(valor, ctx, f"Removed '{guild}' from list", color=0xFF10)

        await LongTextEmbed.send_message(valor, ctx, f"'{guild}' is not in list.", color=0xFF10)
    
    @valor.help_override.command()
    async def glist(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "glist", desc, color=0xFF00)
    
    
    