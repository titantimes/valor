from valor import Valor
from discord import Embed
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed
import argparse
import asyncio
import time
import re
import json
import os

async def _register_annihilation(valor: Valor):
    desc = "Tracks and informs of the next Annihilation world event"
    parser = argparse.ArgumentParser(description='Annihilation tracker command')
    parser.add_argument('-s', '--set', help='Time until next Annihilation (e.g., 2h30m or 1h 45m)', type=str)

    ANNI_EMBED_COLOR = 0x7A1507
    ANNI_FILE = "assets/annihilation_tracker.json"

    def load_annihilation():
        if not os.path.exists(ANNI_FILE):
            return None
        with open(ANNI_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None

    def save_annihilation(timestamp: int):
        with open(ANNI_FILE, "w") as f:
            json.dump({"timestamp": timestamp}, f)

    @valor.command(aliases=["annie", "anni"])
    async def annihilation(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(
                valor, ctx, "Annihilation", parser.format_help().replace("main.py", "-annihilation"), color=ANNI_EMBED_COLOR
            )

        if opt.set:
            # Permission check
            allowed_roles = [940392136610840606, 892879299881869352, 702991927318020138] # Economiser, Titan and Sage Council roles respectively
            has_permission = False
            for role in ctx.author.roles:
                if role.id in allowed_roles:
                    has_permission = True
            if not has_permission:
                return await ctx.send(embed=ErrorEmbed("You do not have permission to report an Annihilation time."))

            # Crazy regex function that parses time like "2h30m" or "2h 30m"
            match = re.match(r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?", opt.set.replace(" ", ""), re.IGNORECASE)
            if not match:
                return await ctx.send(embed=ErrorEmbed("Invalid format. Use one of the following formats: \n`2h30m`, `1h 45m`, `1h`, `30m`"))

            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2)) if match.group(2) else 0

            if hours == 0 and minutes == 0:
                return await ctx.send(embed=ErrorEmbed("Duration must be greater than zero."))

            new_timestamp = int(time.time()) + (hours * 3600) + (minutes * 60)

            existing = load_annihilation()

            if existing and existing["timestamp"] > int(time.time()):
                existing_ts = existing["timestamp"]
                overwrite_embed = Embed(
                    title="Annihilation Time Already Reported",
                    description=(
                        f"Annihilation is already set for <t:{existing_ts}:f> (<t:{existing_ts}:R>).\n"
                        f"Confirm within 30 seconds to overwrite it with `{opt.set}`."
                    ),
                    color=ANNI_EMBED_COLOR
                )
                msg = await ctx.send(embed=overwrite_embed)
                await msg.add_reaction("✅")

                def check(reaction, user):
                    return (
                        str(reaction.emoji) == "✅"
                        and user == ctx.author
                        and reaction.message.id == msg.id
                    )

                try:
                    await valor.wait_for('reaction_add', timeout=30.0, check=check)
                except asyncio.TimeoutError:
                    return
                else:
                    save_annihilation(new_timestamp)
                    return await msg.edit(embed=Embed(
                        title="Annihilation Time Overwritten",
                        description=f"Annihilation time has been updated to <t:{new_timestamp}:f> (<t:{new_timestamp}:R>)",
                        color=ANNI_EMBED_COLOR
                    ))
            
            save_annihilation(new_timestamp)
            return await ctx.send(embed=Embed(
                title="Annihilation Time Reported",
                description=f"Next Annihilation is set for <t:{new_timestamp}:f> (<t:{new_timestamp}:R>)",
                color=ANNI_EMBED_COLOR
            ))
        else:
            data = load_annihilation()
            if not data or data.get("timestamp", 0) < int(time.time()):
                return await ctx.send(embed=Embed(
                    title="Annihilation Tracker",
                    description="There is currently no Annihilation reported.",
                    color=ANNI_EMBED_COLOR
                ))

            timestamp = data["timestamp"]
            return await ctx.send(embed=Embed(
                title="Annihilation Tracker",
                description=f"Next Annihilation is at <t:{timestamp}:f> (<t:{timestamp}:R>)",
                color=ANNI_EMBED_COLOR
            ))

    @valor.help_override.command()
    async def annihilation(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Annihilation", desc, color=0xFF00)
