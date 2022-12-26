import requests
from valor import Valor
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, ReactionEmbed
from discord.ext.commands import Context
from datetime import datetime
from dotenv import load_dotenv
from sql import ValorSQL
import os
import discord
import time
from discord.utils import get

load_dotenv()
async def _register_pm(valor: Valor):
    desc = "PMs people by opening a channel"
    
    @valor.command()
    async def pm(ctx: Context, user: discord.Member):
        guild = ctx.guild
        config = await ValorSQL.get_server_config(guild.id)[0]
        category_id = config[1]
        category = get(guild.categories, id=category_id)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True),
            # payload.member: discord.PermissionOverwrite(view_channel=True),
            # payload.member: discord.PermissionOverwrite(send_messages=True),
        }

        chn = await guild.create_text_channel(f"pm-{user.name}-{id(user)}", overwrites=overwrites, category=category)
        await chn.send(f"<@{user.id}>")

    @pm.error
    async def err(ctx, error):
        await ctx.send(embed=ErrorEmbed("Command failed :/ (Use quotes around the guild name if you haven't)"))
        raise error
    
    @valor.help_override.command()
    async def pm(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "PM Channel System", desc, color=0xFF00)