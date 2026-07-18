import time
import discord
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, LongTextEmbed
from discord.ext.commands import Context
from .common import get_uuid


async def _register_eco(valor: Valor):
    desc = "-eco NAME"
    allowed_roles = {892881748646559754, 892879299881869352, 702991927318020138}

    @valor.command()
    async def eco(ctx: Context, name: str = ""):
        user_roles = {x.id for x in ctx.author.roles}
        if not (allowed_roles & user_roles):
            return await ctx.send(embed=ErrorEmbed("No Permissions"))

        if not name:
            return await LongTextEmbed.send_message(valor, ctx, "Eco", desc, color=0xFF00)

        try:
            uuid = await get_uuid(name)
            if not uuid:
                return await ctx.send(embed=ErrorEmbed("Invalid player name"))
        except Exception:
            return await ctx.send(embed=ErrorEmbed("Invalid player name"))

        timestamp = int(time.time())
        await ValorSQL.exec_param(
            """
INSERT INTO ano_reclaim_records (uuid, contribution, time, raid_type)
VALUES (%s, %s, %s, %s)
""",
            (uuid, 0, timestamp, "eco"),
        )

        embed = discord.Embed(
            title="great success",
            description=f"added eco reclaim for {name}",
            color=0x00FF00,
        )
        await ctx.send(embed=embed)

    @eco.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error

    @valor.help_override.command()
    async def eco(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Eco", desc, color=0xFF00)
