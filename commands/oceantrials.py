import time
from valor import Valor
from sql import ValorSQL
import discord
from util import ErrorEmbed, LongTextEmbed
from discord.ext.commands import Context
from commands.common import get_left_right, guild_names_from_tags
from datetime import datetime
import argparse

MILESTONES = [
    (50, 5), (100, 5), (150, 5), (200, 5), (250, 5),
    (300, 10), (400, 10), (500, 10), (600, 10),
    (700, 10), (800, 10), (900, 10), (1000, 15)
]

def le_for_wars(wars: int) -> int:
    le = sum(reward for threshold, reward in MILESTONES if wars >= threshold)
    le += wars // 10
    return le

def next_milestone(wars: int):
    for threshold, reward in MILESTONES:
        if wars < threshold:
            return threshold, reward
    return None, None

def get_sql_value(rows, default=0):
    """Get a single value from a SQL result set safely."""
    try:
        return int(rows[0][0]) if rows and rows[0][0] is not None else default
    except Exception:
        return default

async def _register_oceantrials(valor: Valor):
    parser = argparse.ArgumentParser(description='OceanTrials Command', add_help=False)
    parser.add_argument('-n', '--name', type=str)
    parser.add_argument('-g', '--guild', nargs='+', default=[])
    parser.add_argument('-r', '--range', nargs='+', default=None)

    @valor.command()
    async def oceantrials(ctx: Context, *options):
        # Parse args but allow unknowns (so -h doesn't crash)
        opt, _ = parser.parse_known_args(options)

        # Require a season, like -r season24
        season = (opt.range or [None])[0]
        if not (season and season.lower().startswith("season") and season[6:].isdigit()):
            return await ctx.send(embed=ErrorEmbed("You must provide a valid season (like `-r season24`) for Ocean Trials payouts!"))

        # Add payout warning for old seasons
        extra_warning = ""
        season_num = int(season[6:])
        if season_num < 20:
            extra_warning = "\n\n*The payouts of older seasons used to be different*"

        # Get time bounds for the season using the existing helper
        valid_range = await get_left_right(opt, time.time())
        if valid_range == "N/A":
            return await ctx.send(embed=ErrorEmbed("Invalid season name input\n\nScream at Andrew or Cal if something should be working"))
        left, right = valid_range

        # Build footer
        start_date = datetime.fromtimestamp(left)
        end_date = datetime.fromtimestamp(right)
        time_range_str = f"{start_date.strftime('%d/%m/%Y %H:%M')} until {end_date.strftime('%d/%m/%Y %H:%M')}"

        # Player (single user) payout summary
        if opt.name:
            query = """
SELECT SUM(warcount_diff) FROM delta_warcounts
LEFT JOIN uuid_name ON uuid_name.uuid = delta_warcounts.uuid
WHERE UPPER(uuid_name.name) = UPPER(%s) AND delta_warcounts.time >= %s AND delta_warcounts.time <= %s
"""
            params = (opt.name, left, right)
            rows = await ValorSQL.exec_param(query, params)
            wars = get_sql_value(rows)
            total_le = le_for_wars(wars)
            next_ms, next_le = next_milestone(wars)

            embed = discord.Embed(
                title=f"Ocean Trials | {opt.name}",
                color=discord.Color.teal(),
                description=f"Wars this season: **{wars}**\nTotal LE: **{total_le} LE**"
            )
            if next_ms:
                embed.add_field(name="Next milestone", value=f"{next_ms} wars ({next_le} LE)", inline=True)
                embed.add_field(name="Wars to next milestone", value=f"{max(0, next_ms - wars)}", inline=True)
            else:
                embed.add_field(name="Milestones", value="All milestones reached!", inline=False)
            embed.set_footer(text=f"Range: {time_range_str}{extra_warning}")
            return await ctx.send(embed=embed)

        # Guild payout summary table
        if opt.guild:
            tags = [x.upper() for x in opt.guild]
            guild_names, _ = await guild_names_from_tags(tags)
            if not guild_names:
                return await ctx.send(embed=ErrorEmbed(f"Could not find guild(s) for tag(s): {', '.join(tags)}"))
            guild_names_str = ",".join(f"'{x}'" for x in guild_names)

            query = f"""
SELECT uuid_name.name, SUM(warcount_diff) as wars
FROM delta_warcounts
LEFT JOIN player_stats ON player_stats.uuid = delta_warcounts.uuid
LEFT JOIN uuid_name ON uuid_name.uuid = delta_warcounts.uuid
WHERE player_stats.guild IN ({guild_names_str}) AND delta_warcounts.time >= %s AND delta_warcounts.time <= %s
GROUP BY uuid_name.name
HAVING wars > 0
ORDER BY wars DESC
"""
            params = (left, right)
            res = await ValorSQL.exec_param(query, params)
            if not res:
                return await ctx.send(embed=ErrorEmbed("No results. No wars for this guild in the given period."))

            # Add Titans valor disclaimer if not ANO
            titan_disclaimer = ""
            if not all(tag == "ANO" for tag in tags):
                titan_disclaimer = "Ocean Trials is based on Titans valor payout system.\n\n"

            lines = [f"{'Name':<18} {'Wars':>6} {'LE':>6}", "-" * 32]
            for name, wars in res:
                wars = int(wars or 0)
                le = le_for_wars(wars)
                lines.append(f"{name:<18} {wars:>6} {le:>6}")

            table_str = "```" + "\n".join(lines) + "```"

            embed = discord.Embed(
                title=f"Ocean Trials | Guild: {', '.join(tags)}",
                color=discord.Color.gold(),
                description=f"{titan_disclaimer}Wars and LE payouts for each member\n\n{table_str}"
            )
            embed.set_footer(text=f"Range: {time_range_str}{extra_warning}")

            return await ctx.send(embed=embed)

        # No name or guild
        return await ctx.send(embed=ErrorEmbed("You must provide either `-n <IGN>` or `-g <TAG>` to use Ocean Trials!"))
