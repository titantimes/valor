import time
from typing import NamedTuple, List, Optional, Tuple
from valor import Valor
from sql import ValorSQL
import discord
from util import ErrorEmbed
from discord.ext.commands import Context
from discord.ui import View
from commands.common import get_left_right, guild_names_from_tags
from datetime import datetime
import argparse
import math

class Milestone(NamedTuple):
    threshold: int
    reward: int

MILESTONES: List[Milestone] = [
    Milestone(50, 5),
    Milestone(100, 5),
    Milestone(150, 5),
    Milestone(200, 5),
    Milestone(250, 5),
    Milestone(300, 10),
    Milestone(400, 10),
    Milestone(500, 10),
    Milestone(600, 10),
    Milestone(700, 10),
    Milestone(800, 10),
    Milestone(900, 10),
    Milestone(1000, 15),
]

INVALID_RANGE = "N/A"

def le_for_wars(wars: int) -> int:
    le = sum(milestone.reward for milestone in MILESTONES if wars >= milestone.threshold)
    le += wars // 10
    return le

def next_milestone(wars: int) -> Optional[Tuple[int, int]]:
    for milestone in MILESTONES:
        if wars < milestone.threshold:
            return milestone.threshold, milestone.reward
    return None

def get_sql_value(rows, default: int = 0) -> int:
    try:
        return int(rows[0][0]) if rows and rows[0][0] is not None else default
    except Exception:
        return default

class OceanTrialsView(View):
    def __init__(self, ctx, data, tags, embed, time_range_str, extra_warning, titan_disclaimer, per_page=20, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.data = data
        self.tags = tags
        self.embed = embed
        self.time_range_str = time_range_str
        self.extra_warning = extra_warning
        self.titan_disclaimer = titan_disclaimer
        self.per_page = per_page
        self.page = 0
        self.max_pages = max(1, math.ceil(len(data) / per_page))

    def get_footer(self):
        return f"Page {self.page + 1} out of {self.max_pages}"


    def build_page_description(self):
        start = self.page * self.per_page
        end = start + self.per_page
        lines = [
            f"{'Name':<18} {'Wars':>6} {'LE':>6}",
            "-" * 32
        ]
        for name, wars in self.data[start:end]:
            lines.append(f"{name:<18} {wars:>6} {le_for_wars(wars):>6}")
        table = "```" + "\n".join(lines) + "```"
        return (self.titan_disclaimer + table).strip()

    async def update_message(self, interaction: discord.Interaction):
        self.embed.description = self.build_page_description()
        self.embed.set_footer(text=self.get_footer())
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="⬅️")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="➡️")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.max_pages - 1:
            self.page += 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

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
            return await ctx.send(embed=ErrorEmbed("You must provide a valid season (like `-r season24`) for Ocean Trials payouts."))

        # Add payout warning for old seasons
        season_num = int(season[6:])
        extra_warning = "\n\n*The payouts of older seasons used to be different.*" if season_num < 20 else ""

        valid_range = await get_left_right(opt, time.time())
        if valid_range == INVALID_RANGE:
            return await ctx.send(embed=ErrorEmbed("Invalid season name input.\n\nContact support if you believe this is an error."))

        left, right = valid_range
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
            next_m = next_milestone(wars)

            embed = discord.Embed(
                title=f"Ocean Trials | {opt.name}",
                color=discord.Color.green(),
                description=f"Wars in range: **{wars}**\nLE from milestones: **{total_le} LE**"
            )
            if next_m:
                embed.add_field(name="Next milestone", value=f"{next_m[0]} wars ({next_m[1]} LE)", inline=True)
                embed.add_field(name="Wars to next milestone", value=f"{max(0, next_m[0] - wars)}", inline=True)
            else:
                embed.add_field(name="Milestones", value="All milestones reached.", inline=False)
            embed.set_footer(text=f"Range: {time_range_str}{extra_warning}")
            return await ctx.send(embed=embed)

        # Guild payout summary table
        if opt.guild:
            tags = [tag.upper() for tag in opt.guild]
            guild_names, _ = await guild_names_from_tags(tags)
            if not guild_names:
                return await ctx.send(embed=ErrorEmbed(f"Could not find guild(s) for tag(s): {', '.join(tags)}"))
            guild_names_str = ",".join(f"'{name}'" for name in guild_names)

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
            filtered_res = [(name, int(wars)) for name, wars in res if le_for_wars(int(wars)) > 0]

            if not filtered_res:
                return await ctx.send(embed=ErrorEmbed("No results. No eligible wars for this guild in the given period."))

            # Add Titans valor disclaimer if not ANO
            titan_disclaimer = ""
            if not all(tag == "ANO" for tag in tags):
                titan_disclaimer = "Ocean Trials is based on Titans valor payout system.\n\n"

            embed = discord.Embed(
                title=f"Ocean Trials | Guild: {', '.join(tags)}",
                color=discord.Color.green()
            )
            view = OceanTrialsView(ctx, filtered_res, tags, embed, time_range_str, extra_warning, titan_disclaimer)
            embed.description = view.build_page_description()
            embed.set_footer(text=view.get_footer())
            await ctx.send(embed=embed, view=view)
            return

        # No name or guild
        return await ctx.send(embed=ErrorEmbed("You must provide either `-n <IGN>` or `-g <TAG>` to use Ocean Trials."))
