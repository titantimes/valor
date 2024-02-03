from valor import Valor
from discord.ext.commands import Context
from discord.ui import Select, View
import discord
from util import ErrorEmbed, LongTextEmbed
from sql import ValorSQL
from commands.common import get_uuid, from_uuid

class LeaderboardOldSelect(Select):
    def __init__(self, options):
        super().__init__(options=options, placeholder="Select a stat to view its leaderboard.", row=0)
    
    async def callback(self, interaction: discord.Interaction):     
        table = await get_leaderboard_old(self.values[0])

        self.embed.title = f"Leaderboard for {self.values[0]}"
        self.embed.description = table

        await interaction.response.edit_message(embed=self.embed, view=self.view)

class LeaderboardOldView(View):
    def __init__(self, default, stat_set):
        super().__init__()
        self.page = 0

        self.stats = [stat_set[i:i + 25] for i in range(0, len(stat_set), 25)] # split into pages of 25 because discord limits select menus to 25 options
        self.max_page = len(self.stats) - 1

        for sublist in self.stats:
            if default in sublist:
                self.page = self.stats.index(sublist)
                break
        select_options = [discord.SelectOption(label=stat) for stat in self.stats[self.page]]
        self.select = LeaderboardOldSelect(options=select_options)
        self.add_item(self.select)

    
    @discord.ui.button(emoji="⬅️", row=1)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        if self.page < 0:
            self.page = 0
            await interaction.response.send_message("You are at the first page!", ephemeral=True)
        else:
            await self.update(interaction)
    
    @discord.ui.button(emoji="➡️", row=1)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        if self.page > self.max_page:
            self.page = self.max_page
            await interaction.response.send_message("You are at the last page!", ephemeral=True)
        else:
            await self.update(interaction)

    async def update(self, interaction: discord.Interaction):
        self.select.options = [discord.SelectOption(label=stat) for stat in self.stats[self.page]]
        self.select.embed.set_footer(text=f"Selection page {self.page+1} | Use arrows keys to switch between pages.")
        await interaction.response.edit_message(embed=self.select.embed, view=self)

async def get_leaderboard_old(stat):
    if stat == "raids":
        res = await ValorSQL._execute("SELECT uuid_name.name, uuid_name.uuid, player_stats.the_canyon_colossus + player_stats.nexus_of_light + player_stats.the_nameless_anomaly + player_stats.nest_of_the_grootslangs FROM player_stats LEFT JOIN uuid_name ON uuid_name.uuid=player_stats.uuid ORDER BY player_stats.the_canyon_colossus + player_stats.nexus_of_light + player_stats.the_nameless_anomaly + player_stats.nest_of_the_grootslangs DESC LIMIT 50")
    elif stat == "dungeons":
        res = await ValorSQL._execute("SELECT uuid_name.name, uuid_name.uuid, player_stats.decrepit_sewers + player_stats.corrupted_decrepit_sewers + player_stats.infested_pit + player_stats.corrupted_infested_pit + player_stats.corrupted_underworld_crypt + player_stats.underworld_crypt + player_stats.lost_sanctuary + player_stats.corrupted_lost_sanctuary + player_stats.ice_barrows + player_stats.corrupted_ice_barrows + player_stats.corrupted_undergrowth_ruins + player_stats.undergrowth_ruins + player_stats.corrupted_galleons_graveyard + player_stats.galleons_graveyard + player_stats.fallen_factory + player_stats.eldritch_outlook + player_stats.corrupted_sand_swept_tomb + player_stats.sand_swept_tomb + player_stats.timelost_sanctum FROM player_stats LEFT JOIN uuid_name ON uuid_name.uuid=player_stats.uuid ORDER BY player_stats.decrepit_sewers + player_stats.corrupted_decrepit_sewers + player_stats.infested_pit + player_stats.corrupted_infested_pit + player_stats.corrupted_underworld_crypt + player_stats.underworld_crypt + player_stats.lost_sanctuary + player_stats.corrupted_lost_sanctuary + player_stats.ice_barrows + player_stats.corrupted_ice_barrows + player_stats.corrupted_undergrowth_ruins + player_stats.undergrowth_ruins + player_stats.corrupted_galleons_graveyard + player_stats.galleons_graveyard + player_stats.fallen_factory + player_stats.eldritch_outlook + player_stats.corrupted_sand_swept_tomb + player_stats.sand_swept_tomb + player_stats.timelost_sanctum DESC LIMIT 50")
    else:
        res = await ValorSQL._execute(f"SELECT uuid_name.name, uuid_name.uuid, player_stats.{stat} FROM player_stats LEFT JOIN uuid_name ON uuid_name.uuid=player_stats.uuid ORDER BY {stat} DESC LIMIT 50")
    stats = []
    for m in res:
        if not m[0] and m[1]:
            stats.append((await from_uuid(m[1]), m[2]))
        else:
            stats.append((m[0] if m[0] else "can't find name", m[2]))

    return "```\n"+'\n'.join("%3d. %24s %5d" % (i+1, stats[i][0], stats[i][1]) for i in range(len(stats)))+"\n```"


async def _register_leaderboard_old(valor: Valor):
    desc = "The old leaderboard"
    stat_set = ['sand_swept_tomb', 'galleons_graveyard', 'firstjoin', 'scribing', 'chests_found', 'woodcutting', 'tailoring', 'fishing', 'eldritch_outlook', 'alchemism', 'logins', 'deaths', 'corrupted_decrepit_sewers', 'armouring', 'corrupted_undergrowth_ruins', 'items_identified', 'nest_of_the_grootslangs', 'blocks_walked', 'lost_sanctuary', 'mining', 'the_canyon_colossus', 'undergrowth_ruins', 'corrupted_ice_barrows', 'jeweling', 'woodworking', 'uuid', 'underworld_crypt', 'fallen_factory', 'mobs_killed', 'infested_pit', 'decrepit_sewers', 'corrupted_sand_swept_tomb', 'corrupted_infested_pit', 'farming', 'corrupted_lost_sanctuary', 'cooking', 'guild', 'combat', 'weaponsmithing', 'playtime', 'corrupted_underworld_crypt', 'ice_barrows', 'nexus_of_light', "guild_rank", "the_nameless_anomaly", "raids", "corrupted_galleons_graveyard", "timelost_sanctum", "dungeons"]
    stats_abbr = {'tna' : 'the_nameless_anomaly', 'notg' : 'nest_of_the_grootslangs', 'sst' : 'sand_swept_tomb', 'gg' : 'galleons_graveyard', 'cgg' : 'corrupted_galleons_graveyard', 'csst' : 'corrupted_sand_swept_tomb', 'cds' : 'corrupted_decrepit_sewers', 'ds' : 'decrepit_sewers', 'cur' :'corrupted_undergrowth_ruins', 'ur' : 'undergrowth_ruins', 'tcc' : 'the_canyon_colossus', 'ib' : 'ice_barrows', 'cib' : 'corrupted_ice_barrows', 'uc' : 'underworld_crypt', 'cuc' : 'corrupted_underworld_crypt', 'ff' : 'fallen_factory', 'ip' : 'infested_pit', 'cip' : 'corrupted_infested_pit', 'ls' : 'lost_sanctuary', 'cls' : 'corrupted_lost_sanctuary', 'nol' : 'nexus_of_light', }
    
    @valor.command()
    async def leaderboard_old(ctx: Context, stat="galleons_graveyard"): 

        if stat in stats_abbr:
            stat = stats_abbr[stat]
        
        if stat not in stat_set:
            return await LongTextEmbed.send_message(valor, ctx, "Invalid Stat, choose from the following: ", content='\n'.join(stat_set), code_block=True, color=0x1111AA)
        
        view = LeaderboardOldView(stat, stat_set)

        table = await get_leaderboard_old(stat)
        
        view.select.embed = discord.Embed(
            title=f"Leaderboard for {stat}",
            description=table,
            color=0x11FFBB,
        )
        view.select.embed.set_footer(text=f"Selection page {view.page+1} | Use arrows keys to switch between pages.")

        await ctx.send(embed=view.select.embed, view=view)

    @leaderboard_old.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def leaderboard_old(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Leaderboard", desc, color=0xFF00)