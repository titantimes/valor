import discord
import os
import json
from discord.ext.commands import Bot, Context
import valor

valor = valor.Valor('-')


@valor.command()
async def echo(ctx: Context):
    await ctx.send("echo")

valor.run()
