import time
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, LongTextTable
from discord.ext.commands import Context
from datetime import datetime
from dotenv import load_dotenv
from .common import get_left_right, guild_names_from_tags
import argparse
from datetime import datetime, timedelta

load_dotenv()
async def _register_graids(valor: Valor):
    desc = "Gets you the guild raid count leaderboard"
    parser = argparse.ArgumentParser(description='Warcount Command')
    parser.add_argument('-r', '--range', nargs='+', default=None)
    parser.add_argument('-g', '--guild', nargs='+', default=None)
    parser.add_argument('-w', '--guild_wise', action="store_true", default=False)

    @valor.command()
    async def graids(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Guild Raids", parser.format_help().replace("main.py", "-graids"), color=0xFF00)
    
        start = time.time()

        if not opt.guild_wise:
            template_query = '''
SELECT ROW_NUMBER() OVER(ORDER BY raid_cnt DESC) AS `raid_cnt`, name, raid_cnt
FROM
    (SELECT B.name, SUM(A.num_raids) AS raid_cnt
    FROM
        guild_raid_records A LEFT JOIN uuid_name B ON A.uuid=B.uuid
    WHERE 
        {TIME_CLAUSE}
        {GUILD_CLAUSE}
    GROUP BY A.uuid
    ORDER BY raid_cnt DESC) C;
''' 
        else:
            template_query = '''
SELECT ROW_NUMBER() OVER(ORDER BY raid_cnt DESC), guild, raid_cnt
FROM
    (SELECT guild, SUM(num_raids) AS raid_cnt
    FROM
        guild_raid_records A
    WHERE
        {TIME_CLAUSE}
        {GUILD_CLAUSE}
    GROUP BY guild
    ORDER BY raid_cnt DESC) C;
'''

        template_query_params = { "TIME_CLAUSE": "", "GUILD_CLAUSE": "" }
        prepared_params = []

        if not opt.range:
            opt.range = ["7", "0"]
        
        valid_range = await get_left_right(opt, start)
        if valid_range == "N/A":
            return await ctx.send(embed=ErrorEmbed("Invalid season name input"))
        
        left, right = valid_range
        template_query_params["TIME_CLAUSE"] = "A.`time` > %s AND A.`time` <= %s"
        prepared_params.append(left)
        prepared_params.append(right)

        if not opt.guild_wise and not opt.guild:
            opt.guild = ["ANO"]
        
        if opt.guild:
            opt.guild, _ = await guild_names_from_tags(opt.guild) # second arg for errors. do later
            template_query_params["GUILD_CLAUSE"] = "AND A.guild IN (" + ("%s,"*len(opt.guild))[:-1] + ")"
            prepared_params.extend(opt.guild)
        
        query = template_query.format(**template_query_params)
        
        res = await ValorSQL.exec_param(query, prepared_params)

        delta_time = time.time()-start
        
        header = [' Rank ', ' '*14+"Name", "  Total  "]
        
        # rows = [(name_to_ranking[name], name, guild_to_tag.get(player_to_guild[name], ("None", -1))[0], *player_warcounts[name], sum(player_warcounts[name])) for name in player_warcounts]
        # rows.sort(key=lambda x: x[-1], reverse=True)

        now = datetime.now()
        start_date = now - timedelta(days=float(opt.range[0]))
        end_date = now - timedelta(days=float(opt.range[1]))

        time_range_str = f"{start_date.strftime('%d/%m/%Y %H:%M')} until {end_date.strftime('%d/%m/%Y %H:%M')}"

        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}\nRange: {time_range_str}"
        await LongTextTable.send_message(valor, ctx, header, res, opt_after)

    @valor.help_override.command()
    async def graids(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Guild Raids", desc, color=0xFF00)
