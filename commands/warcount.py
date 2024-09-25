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
    clone_map = {"HUNTER": "ARCHER", "KNIGHT": "WARRIOR", "DARKWIZARD": "MAGE", "NINJA": "ASSASSIN", "SKYSEER": "SHAMAN"}
    clone_map_inv = {clone_map[k]: k for k in clone_map}
    real_classes = clone_map.values()
    parser = argparse.ArgumentParser(description='Warcount Command')
    parser.add_argument('-n', '--names', nargs='+', default=[])
    parser.add_argument('-a', '--guild_aggregate', action="store_true", default=False)
    parser.add_argument('-t', '--territory_captures', action="store_true", default=False)
    parser.add_argument('-g', '--guild', nargs='+', default=[]) # this one is filter players only in guilds, Callum: 100
    parser.add_argument('-c', '--classes', nargs='+', default=[])
    parser.add_argument('-r', '--range', nargs='+', default=None)
    parser.add_argument('-rk', '--rank', type=str, default="global")

    async def do_guild_aggregate_warcount(ctx: Context, opt):
        query = """
SELECT ROW_NUMBER() OVER(ORDER BY wars DESC) AS `rank`, B.tag, A.guild, CAST(A.wars AS UNSIGNED)
FROM
    (SELECT guild, SUM(delta) wars
    FROM
        player_delta_record
    WHERE label="g_wars" AND time >= %s AND time <= %s
    GROUP BY guild
    ORDER BY wars DESC LIMIT 100) A
    LEFT JOIN guild_tag_name B ON A.guild=B.guild;
"""
        start = time.time()
        if opt.range:
            # opt.range = [2e9, 0]
            valid_range = await get_left_right(opt, start)
            if valid_range == "N/A":
                return await ctx.send(embed=ErrorEmbed("Invalid season name input"))
            left, right = valid_range
        else:
            left, right = start - 3600*24*7, start

        rows = await ValorSQL.exec_param(query, (left, right))

        delta_time = time.time() - start
        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}"
        header = ['   ',  " Tag ", " "*16+"Guild ", "  Wars  "]

        return await LongTextTable.send_message(valor, ctx, header, rows, opt_after)
    
    async def do_guild_aggregate_captures(ctx: Context, opt):
        query = """
SELECT ROW_NUMBER() OVER(ORDER BY captures DESC) AS `rank`,B .tag, A.guild, CAST(A.captures AS UNSIGNED)
FROM
    (SELECT terr_exchange.attacker AS guild, COUNT(terr_exchange.attacker) AS captures
    FROM
        terr_exchange
    WHERE time >= %s AND time <= %s
    GROUP BY terr_exchange.attacker
    ORDER BY captures DESC LIMIT 100) A
    LEFT JOIN guild_tag_name B ON A.guild=B.guild;
"""
        start = time.time()
        if opt.range:
            # opt.range = [2e9, 0]
            valid_range = await get_left_right(opt, start)
            if valid_range == "N/A":
                return await ctx.send(embed=ErrorEmbed("Invalid season name input"))
            left, right = valid_range
        else:
            left, right = start - 3600*24*7, start

        rows = await ValorSQL.exec_param(query, (left, right))

        delta_time = time.time() - start
        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}"
        header = ['   ',  " Tag ", " "*16+"Guild ", "  Captures  "]

        return await LongTextTable.send_message(valor, ctx, header, rows, opt_after)

    @valor.command()
    async def warcount(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "warcount", parser.format_help().replace("main.py", "-warcount"), color=0xFF00)
    
        if opt.guild_aggregate:
            return await do_guild_aggregate_warcount(ctx, opt)
        elif opt.territory_captures:
            return await do_guild_aggregate_captures(ctx, opt)
        
        listed_classes = real_classes if not opt.classes else opt.classes
        listed_classes = [x.upper() for x in listed_classes]
        listed_classes_enumerated = {v.upper(): i for i, v in enumerate(listed_classes)} # {classname: 0, classname: 1, ...}

        names = {n.upper() for n in opt.names} if opt.names else None

        start = time.time()

        table_type = "cumu_warcounts" if not opt.range else "delta_warcounts"
        table_count_column = "warcount" if not opt.range else "warcount_diff"

        warcount_query = f'''SELECT uuid_name.name, 
    %s,
	SUM({table_type}.{table_count_column}) as all_wars, 
	player_stats.guild
FROM {table_type} 
LEFT JOIN uuid_name ON uuid_name.uuid={table_type}.uuid 
LEFT JOIN player_stats ON player_stats.uuid={table_type}.uuid 
WHERE UPPER({table_type}.class_type) IN (%s) %%s 
GROUP BY uuid_name.uuid, player_stats.guild
ORDER BY all_wars DESC;'''
        
        class_column_count_parts = []
        select_class_in_parts = []
        for real_class in listed_classes:
            class_column_count_parts.append( # lol the dict lookup will fail if user tries some tricky sql input
                f"SUM(CASE WHEN UPPER({table_type}.class_type)='{real_class}' OR UPPER({table_type}.class_type)='{clone_map_inv[real_class]}' THEN {table_type}.{table_count_column} ELSE 0 END) AS {real_class}_count")
            select_class_in_parts.append(f"'{real_class}', '{clone_map_inv[real_class]}'")
        
        warcount_query = warcount_query % (','.join(class_column_count_parts), ','.join(select_class_in_parts))

        if opt.range:
            # opt.range = [2e9, 0]
            valid_range = await get_left_right(opt, start)
            if valid_range == "N/A":
                return await ctx.send(embed=ErrorEmbed("Invalid season name input"))
            left, right = valid_range

            res = await ValorSQL._execute(warcount_query % f' AND delta_warcounts.time >= {left} AND delta_warcounts.time <= {right}')
        else:
            res = await ValorSQL._execute(warcount_query % '')

        delta_time = time.time()-start
        
        guild_names, unidentified = await guild_names_from_tags(opt.guild)

        header = ['  Rank  ', ' '*14+"Name", "Guild", *[f"  {x}  " for x in listed_classes], "  Total  "]

        player_to_guild = {}
        guilds_seen = set()
        player_warcounts = {}

        name_to_ranking = {}

        for rank_0, row in enumerate(res):
            name, total, guild = row[0], row[-2], row[-1]
            name_to_ranking[name] = rank_0+1
            classes_count = row[1:-2]

            if opt.guild and not guild in guild_names: continue
            if not name or (opt.names and not name.upper() in names): continue
            if not name in player_warcounts:
                player_warcounts[name] = [0]*len(listed_classes_enumerated)

            for i, real_class in enumerate(listed_classes):
                player_warcounts[name][listed_classes_enumerated[real_class]] += classes_count[i]

            player_to_guild[name] = guild
            guilds_seen.add(guild)
        
        guild_to_tag = {}
        if guilds_seen:
            expanded_guilds_str = ','.join(f"'{x}'" for x in guilds_seen) # TODO: batch req size 50
            res = await ValorSQL._execute(f'SELECT guild, tag, priority FROM guild_tag_name WHERE guild IN ({expanded_guilds_str})')
            for guild, tag, priority in res:
                if priority > guild_to_tag.get(guild, ("N/A", -1))[1]:
                    guild_to_tag[guild] = (tag, priority)


        if opt.rank != "global":
            rows_total_count = [(name, sum(player_warcounts[name])) for name in player_warcounts]
            rows_total_count.sort(key=lambda x: x[-1], reverse=True) 
            name_to_ranking = {}
            for i, rest in enumerate(rows_total_count):
                name_to_ranking[rest[0]] = i+1
        
        rows = [(name_to_ranking[name], name, guild_to_tag.get(player_to_guild[name], ("None", -1))[0], *player_warcounts[name], sum(player_warcounts[name])) for name in player_warcounts]
        rows.sort(key=lambda x: x[-1], reverse=True)

        if not rows:
            return await ctx.send(embed=ErrorEmbed("No results, wrong username? have they done no wars?"))

        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}"
        await LongTextTable.send_message(valor, ctx, header, rows, opt_after)

    @valor.help_override.command()
    async def warcount(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Warcount", desc, color=0xFF00)
