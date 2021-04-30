import requests
from valor import Valor
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, ReactionEmbed
from discord.ext.commands import Context
from datetime import datetime
from dotenv import load_dotenv
from sql import ValorSQL
import os
import time

load_dotenv()
async def _register_ticket(valor: Valor):
    desc = "Ticket command family. See (all expire parameters are optional. The default will be 50 years):\n`-ticket create \"<title>\" \"<message>\" \"<emoji1>, <emoji2>, ...\" <seconds until expire>`\n"\
        "\n`-ticket app \"<title>\" \"<message>\" \"<emoji>\" <expire>`\n"\
        "Ping Andrew if you need help."
    
    @valor.group()
    async def ticket(ctx: Context):
        if not ctx.invoked_subcommand:
            return await LongTextEmbed.send_message(valor, ctx, "Ticket System", desc, color=0xFF00)
    
    @ticket.command()
    async def create(ctx: Context, title: str, message: str, emotes: str, expire_sec: int = 1576800000):
        reactions = []
        for c in emotes.strip().replace(", ", ",").split(","):
            if len(c) == 1:
                reactions.append(c)
            else:
                reactions.append(c.split(":")[-1][:-1])

        await ReactionEmbed.send_message(valor, ctx, title, message, color=0xBBBBFF, reactions=reactions)
        expire = int(time.time()+expire_sec)
        valor.reaction_msg_ids[ctx.message.id] = expire
        ValorSQL.create_react_msg(ctx.message.id, expire)

        for emoji in reactions:
            if len(emoji) == 1:
                emoji = ord(emoji)

            ValorSQL.create_react_reaction(ctx.message.id, int(emoji))

    @ticket.error
    async def err(ctx, error):
        await ctx.send(embed=ErrorEmbed("Command failed :/ (Use quotes around the guild name if you haven't)"))
        raise error
    
    @valor.help_override.command()
    async def ticket(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Ticket System", desc, color=0xFF00)