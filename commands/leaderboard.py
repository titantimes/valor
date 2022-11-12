from valor import Valor
from discord.ext.commands import Context
from discord.ui import Select, View
import discord
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed
import random
from datetime import datetime
import requests
from sql import ValorSQL
from commands.common import get_uuid, from_uuid

class LeaderboardSelect(Select):
    def __init__(self, options):
        super().__init__(options=options, row=0)
    
    async def callback(self, interaction: discord.Interaction):     
        table = await get_leaderboard(self.values[0])

        self.embed = discord.Embed(
            title=f"Leaderboard for {self.values[0]}",
            description=table
        )

        await interaction.response.edit_message(embed=self.embed, view=self.view)

class LeaderboardView(View):
    def __init__(self, default, stat_set):
        super().__init__()
        self.page = 0

        self.stats = [stat_set[i:i + 25] for i in range(0, len(stat_set), 25)] # split into pages of 25 because discord limits select menus to 25 options
        self.max_page = len(self.stats) - 1

        for sublist in self.stats:
            if default in sublist:
                self.page = self.stats.index(sublist)
                break
        select_options = [discord.SelectOption(label=stat) for stat in self.stats[self.page] if stat != default]
        select_options.append(discord.SelectOption(label=default, default=True))
        self.select = LeaderboardSelect(options=select_options)
        self.add_item(self.select)

    
    @discord.ui.button(emoji="⬅️", row=1)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        if self.page < 0:
            self.page = 0
        await self.update(interaction)
    
    @discord.ui.button(emoji="➡️", row=1)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        if self.page > self.max_page:
            self.page = self.max_page
        await self.update(interaction)

    async def update(self, interaction: discord.Interaction):
        self.select.options = [discord.SelectOption(label=stat) for stat in self.stats[self.page]]
        await interaction.response.edit_message(embed=self.select.embed, view=self)

async def get_leaderboard(stat):
    if stat == "raids":
        res = await ValorSQL._execute("SELECT uuid_name.name, uuid_name.uuid, player_stats.the_canyon_colossus + player_stats.nexus_of_light + player_stats.the_nameless_anomaly + player_stats.nest_of_the_grootslangs FROM player_stats LEFT JOIN uuid_name ON uuid_name.uuid=player_stats.uuid ORDER BY player_stats.the_canyon_colossus + player_stats.nexus_of_light + player_stats.the_nameless_anomaly + player_stats.nest_of_the_grootslangs DESC LIMIT 50")
    else:
        res = await ValorSQL._execute(f"SELECT uuid_name.name, uuid_name.uuid, player_stats.{stat} FROM player_stats LEFT JOIN uuid_name ON uuid_name.uuid=player_stats.uuid ORDER BY {stat} DESC LIMIT 50")
    stats = []
    for m in res:
        if not m[0] and m[1]:
            stats.append((await from_uuid(m[1]), m[2]))
        else:
            stats.append((m[0] if m[0] else "can't find name", m[2]))

    return "```\n"+'\n'.join("%3d. %24s %5d" % (i+1, stats[i][0], stats[i][1]) for i in range(len(stats)))+"\n```"


async def _register_leaderboard(valor: Valor):
    desc = "The leaderboard"
    stat_set = ['sand_swept_tomb', 'galleons_graveyard', 'firstjoin', 'scribing', 'chests_found', 'woodcutting', 'tailoring', 'fishing', 'eldritch_outlook', 'alchemism', 'logins', 'deaths', 'corrupted_decrepit_sewers', 'armouring', 'corrupted_undergrowth_ruins', 'items_identified', 'nest_of_the_grootslangs', 'blocks_walked', 'lost_sanctuary', 'mining', 'the_canyon_colossus', 'undergrowth_ruins', 'corrupted_ice_barrows', 'jeweling', 'woodworking', 'uuid', 'underworld_crypt', 'fallen_factory', 'mobs_killed', 'infested_pit', 'decrepit_sewers', 'corrupted_sand_swept_tomb', 'corrupted_infested_pit', 'farming', 'corrupted_lost_sanctuary', 'cooking', 'guild', 'combat', 'weaponsmithing', 'playtime', 'corrupted_underworld_crypt', 'ice_barrows', 'nexus_of_light', "guild_rank", "the_nameless_anomaly", "raids"]

    @valor.command()
    async def leaderboard(ctx: Context, stat="galleons_graveyard"): 

        if stat not in stat_set:
            return await LongTextEmbed.send_message(valor, ctx, "Invalid Stat, choose from the following: ", content='\n'.join(stat_set), code_block=True, color=0x1111AA)
        
        view = LeaderboardView(stat, stat_set)

        table = await get_leaderboard(stat)
        
        view.select.embed = discord.Embed(
            title=f"Leaderboard for {stat}",
            description=table
        )
        await ctx.send(embed=view.select.embed, view=view)

    @leaderboard.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def leaderboard(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Leaderboard", desc, color=0xFF00)