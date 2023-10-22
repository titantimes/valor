import requests
import time
from valor import Valor
from sql import ValorSQL
import mongo
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, LongTextTable, get_war_rank, get_xp_rank
from discord.ext.commands import Context
from datetime import datetime
from dotenv import load_dotenv
import os
from commands.common import get_uuid, get_left_right, guild_names_from_tags, guild_tags_from_names
import argparse

load_dotenv()
async def _register_warcount(valor: Valor):
    desc = "Gets you the war count leaderboard. (old version)"
    clone_map = {"hunter": "Archer", "knight": "Warrior", "darkwizard": "Mage", "ninja": "Assassin", "skyseer": "Shaman"}
    real_classes = clone_map.values()
    # season_times={8:[1663016400,1666569600],9:[1666983600,1672462800]} # ! idk the end time for season 9 so i put a big number
    parser = argparse.ArgumentParser(description='Warcount Command')
    parser.add_argument('-n', '--names', nargs='+', default=[])
    parser.add_argument('-g', '--guild', nargs='+', default=[]) # this one is filter players only in guilds, Callum: 100
    parser.add_argument('-gs', '--guildsum', nargs='+', default=[]) # TODO: this one is for guild totals ANO: 100, ESI: 200 etc.
    parser.add_argument('-c', '--classes', nargs='+', default=[])
    parser.add_argument('-r', '--range', nargs='+', default=None)

    @valor.command()
    async def warcount(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "warcount", parser.format_help().replace("main.py", "-warcount"), color=0xFF00)
    
        listed_classes = real_classes if not opt.classes else opt.classes
        listed_classes_enumerated = {v.lower(): i for i, v in enumerate(listed_classes)} # {classname: 0, classname: 1, ...}

        names = {n.lower() for n in opt.names} if opt.names else None

        start = time.time()

        if opt.range:
            # opt.range = [2e9, 0]
            valid_range = await get_left_right(opt, start)
            if valid_range == "N/A":
                return await ctx.send(embed=ErrorEmbed("Invalid season name input"))
            left, right = valid_range

            res = await ValorSQL._execute(f'''SELECT uuid_name.name, delta_warcounts.warcount_diff, delta_warcounts.class_type, player_stats.guild
FROM delta_warcounts 
LEFT JOIN uuid_name ON uuid_name.uuid=delta_warcounts.uuid 
LEFT JOIN player_stats ON player_stats.uuid=delta_warcounts.uuid WHERE delta_warcounts.time >= {left} AND delta_warcounts.time <= {right} ORDER BY delta_warcounts.time ASC;''')
        else:
            res = await ValorSQL._execute(f'''SELECT uuid_name.name, cumu_warcounts.warcount, cumu_warcounts.class_type, player_stats.guild
FROM cumu_warcounts 
LEFT JOIN uuid_name ON uuid_name.uuid=cumu_warcounts.uuid 
LEFT JOIN player_stats ON player_stats.uuid=cumu_warcounts.uuid''')
        delta_time = time.time()-start
        
        guild_names, unidentified = await guild_names_from_tags(opt.guild)

        header = [' '*14+"Name", "Guild", *[f"  {x}  " for x in listed_classes], "  Total  "]
        player_to_guild = {}
        guilds_seen = set()
        player_warcounts = {}

        for name, wardiff, class_type, guild in res:
            if opt.guild and not guild in guild_names: continue
            if not name or (opt.names and not name.lower() in names): continue

            if not class_type: continue # skip. errors in early db insertions
            class_type = class_type.lower()
            real_class = clone_map.get(class_type, class_type).lower()

            if not name in player_warcounts:
                player_warcounts[name] = [0]*len(listed_classes_enumerated)

            player_warcounts[name][listed_classes_enumerated[real_class]] += wardiff
            player_to_guild[name] = guild
            guilds_seen.add(guild)
        
        guild_to_tag = {}
        if guilds_seen:
            expanded_guilds_str = ','.join(f"'{x}'" for x in guilds_seen) # TODO: batch req size 50
            res = await ValorSQL._execute(f'SELECT guild, tag, priority FROM guild_tag_name WHERE guild IN ({expanded_guilds_str})')
            for guild, tag, priority in res:
                if priority > guild_to_tag.get(guild, ("N/A", -1))[1]:
                    guild_to_tag[guild] = (tag, priority)

        rows = [(name, guild_to_tag.get(player_to_guild[name], ("None", -1))[0], *player_warcounts[name], sum(player_warcounts[name])) for name in player_warcounts]
        rows.sort(key=lambda x: x[-1], reverse=True) # Raw, you can add sortby option

        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}"
        await LongTextTable.send_message(valor, ctx, header, rows, opt_after)

    @valor.help_override.command()
    async def warcount(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Warcount", desc, color=0xFF00)
