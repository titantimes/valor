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
    parser.add_argument('-n', '--name', nargs='+', type=str, default=None)

    @valor.command()
    async def graids(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Guild Raids", parser.format_help().replace("main.py", "-graids"), color=0xFF00)

        start = time.time()

        if opt.name:
            names = opt.name
            uuiddd = await ValorSQL.exec_param("SELECT uuid, name FROM uuid_name WHERE name IN (" + ",".join(["%s"] * len(names)) + ")", names)
            if not uuiddd:
                return await ctx.send(embed=ErrorEmbed(f"No UUIDs found for names {', '.join(names)}"))
            uuidtoname = {name: uuid for uuid, name in uuiddd}
            uuids = [uuidtoname[name] for name in names if name in uuidtoname]
            if not uuids:
                return await ctx.send(embed=ErrorEmbed(f"No valid UUIDs found for names {', '.join(names)}"))
            template_query = '''
SELECT ROW_NUMBER() OVER(ORDER BY raid_cnt DESC) AS `raid_cnt`, name, guild, raid_cnt
FROM
    (SELECT B.name, A.guild, SUM(A.num_raids) AS raid_cnt
    FROM
        guild_raid_records A LEFT JOIN uuid_name B ON A.uuid=B.uuid
    WHERE 
        {TIME_CLAUSE}
        AND A.uuid IN ({UUIDS})
    GROUP BY A.uuid, A.guild
    ORDER BY raid_cnt DESC) C;
'''
            template_query_params = { "TIME_CLAUSE": "", "UUIDS": ",".join(["%s"] * len(uuids)) }
            prepared_params = uuids
        elif not opt.guild_wise:
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
            template_query_params = { "TIME_CLAUSE": "", "GUILD_CLAUSE": "" }
            prepared_params = []
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
        prepared_params.insert(0, left)
        prepared_params.insert(1, right)

        if opt.guild:
            opt.guild, _ = await guild_names_from_tags(opt.guild)
            template_query_params["GUILD_CLAUSE"] = "AND A.guild IN (" + ("%s,"*len(opt.guild))[:-1] + ")"
            prepared_params.extend(opt.guild)

        query = template_query.format(**template_query_params)

        res = await ValorSQL.exec_param(query, prepared_params)

        if not res:
            return await ctx.send(embed=ErrorEmbed("No raids recorded in the specified time period"))
#This can easily pop up if queries fail just a note if someone is debugging in the future and keeps getting this.
        delta_time = time.time() - start

        if opt.name:
            header = [' Rank ', ' '*14+"Name", ' '*14+"Guild", "  Total  "] #this looks abit jank with 14 buffer on each but i was too lazy to make something dynamic
            res = list(res)
            for name in names:
                uuid = uuidtoname.get(name)
                if uuid:
                    raidsall = sum(row[3] for row in res if row[1] == name)
                    res.append((None, name, 'Total', raidsall)) #with multiple names there is no "rank" to totals which could be fixed here later fine for now
        else:
            header = [' Rank ', ' '*14+"Name", "  Total  "]

        now = datetime.now()
        start_date = now - timedelta(days=float(opt.range[0]))
        end_date = now - timedelta(days=float(opt.range[1]))

        time_range_str = f"{start_date.strftime('%d/%m/%Y %H:%M')} until {end_date.strftime('%d/%m/%Y %H:%M')}"

        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}\nRange: {time_range_str}"
        await LongTextTable.send_message(valor, ctx, header, res, opt_after)

    @valor.help_override.command()
    async def graids(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Guild Raids", desc, color=0xFF00)
