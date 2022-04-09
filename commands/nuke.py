"""
Author: classAndrew
Description: Removes all the roles from members except for a few members. Do not ever use command
"""
from pyrsistent import discard
from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed, guild_name_from_tag
import random
from datetime import datetime
import requests

async def _register_nuke(valor: Valor):
    desc = "Entire guild changes"
    
    @valor.command()
    async def nuke(ctx: Context):
        if not ctx.author.guild_permissions.administrator and ctx.author.id != 146483065223512064:
            await LongTextEmbed(valor, ctx, "Nuke", "you probably want to stay away from this function...", color=0XFF0000)
        
        for member in ctx.guild.members:
            rls = {x.id for x in member.roles}
            name = member.display_name.split(" ")
            print(name)
            if 892886015017103360 in rls:
                await member.edit(nick="Sorcerer "+name[1])
            elif 702996152982962197 in rls:
                await member.edit(nick="Magi "+name[1])


    @nuke.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def nuke(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Nuke", desc, color=0xFF00)
    
    
    