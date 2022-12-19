from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed
from .common import guild_name_from_tag, guild_names_from_tags
import random
from datetime import datetime
import requests
from sql import ValorSQL
import commands
from commands.common import get_uuid, from_uuid, role1
import time
import argparse
from dotenv import load_dotenv
import discord
import os

load_dotenv()
TEST = os.getenv("TEST")=="TRUE"

async def _register_rank(valor: Valor):
    desc = """Like the old -roles but
-roles @discord IGN (optional -m)
This should link their @ to the ign
rename them to Magi <ign>
give them titans valor, magi, then all the divider roles 
then military too if -m is applied"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-u', '--user', nargs=2)
    parser.add_argument('-m', '--military', action='store_true')

    @valor.command()
    async def rank(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "rank", parser.format_help().replace("main.py", "-rank"), color=0xFF00)
        
        if not opt.user:
            return await LongTextEmbed.send_message(valor, ctx, "rank", parser.format_help().replace("main.py", "-rank"), color=0xFF00)
        
        base_roles = [ctx.guild.get_role(535609000193163274), ctx.guild.get_role(892878784380956712)] # Guild Role, Military Separator
        if opt.military:
            base_roles.append(ctx.guild.get_role(536068288606896128)) # military role
        base_roles.extend([ctx.guild.get_role(702775389751345182), ctx.guild.get_role(702774404492296253), ctx.guild.get_role(702766346416423013)]) # medals, reaction, extras separators

        mention, username = opt.user
        target_id = int(mention[2:-1])
        if "-" in username:
             return await ctx.send(embed=ErrorEmbed("Invalid user name")) # lazy sanitation 
        if not commands.common.role1(ctx.author) and not TEST:
             return await ctx.send(embed=ErrorEmbed("No Permissions"))

        exist = await ValorSQL._execute(f"SELECT * FROM id_uuid WHERE discord_id={target_id} LIMIT 1")
        uuid = await commands.common.get_uuid(username)
        if exist:
            await ValorSQL._execute(f"UPDATE id_uuid SET uuid='{uuid}' WHERE discord_id={target_id}")
        else:
            await ValorSQL._execute(f"INSERT INTO id_uuid VALUES ({target_id}, '{uuid}')")

        await ctx.guild.get_member(target_id).add_roles(base_roles)
        resp_msg = f"Linking UUID for {username}", f"{target_id} to {uuid} and added roles."

        await LongTextEmbed.send_message(valor, ctx, resp_msg, color=0xFF10)

    @rank.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def rank(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Rank", desc, color=0xFF00)
    
    
    