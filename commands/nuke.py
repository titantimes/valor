"""
Author: classAndrew
Description: Removes all the roles from members except for a few members. Do not ever use command
"""
from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed, guild_name_from_tag
import random
from datetime import datetime
import requests

async def _register_nuke(valor: Valor):
    desc = "Removes the roles of certain players"
    
    @valor.command()
    async def nuke(ctx: Context):
        if not ctx.author.guild_permissions.administrator:
            await LongTextEmbed(valor, ctx, "Nuke", "you probably want to stay away from this function...", color=0XFF0000)
        

    @nuke.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def nuke(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Nuke", desc, color=0xFF00)
    
    
    