import time
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, LongTextTable
from discord.ext.commands import Context
from datetime import datetime
from dotenv import load_dotenv
from .common import get_left_right
import argparse

load_dotenv()
async def _register_raids(valor: Valor):
    desc = "Gets you the raid count leaderboard"
    parser = argparse.ArgumentParser(description='Warcount Command')
    parser.add_argument('-r', '--range', nargs='+', default=None)
    parser.add_argument('-g', '--guild', nargs='+', default=None)
    parser.add_argument('-u', '--user', nargs='+', default=None)

    async def get_cumu_guild_agg_table():
        pass

    async def get_range_guild_agg_table():
        pass

    async def get_cumu_player_table():
        pass

    async def get_range_player_table():
        pass

    @valor.command()
    async def raids(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "warcount", parser.format_help().replace("main.py", "-warcount"), color=0xFF00)
    
        start = time.time()

        template_query = '''
SELECT D.name, C.notg_count, C.nol_count, C.tcc_count, C.tna_count, C.notg_count + C.nol_count + C.tcc_count + C.tna_count AS total
FROM
    (SELECT uuid, 
        SUM(CASE WHEN UPPER(label)='G_NEST OF THE GROOTSLANGS' THEN delta ELSE 0 END) AS notg_count,
        SUM(CASE WHEN UPPER(label)='G_ORPHION\\'S NEXUS OF LIGHT' THEN delta ELSE 0 END) AS nol_count,
        SUM(CASE WHEN UPPER(label)='G_THE CANYON COLOSSUS' THEN delta ELSE 0 END) AS tcc_count,
        SUM(CASE WHEN UPPER(label)='G_THE NAMELESS ANOMALY' THEN delta ELSE 0 END) AS tna_count
    FROM 
        `player_delta_record`
    WHERE
        {TIME_CLAUSE}
        {GUILD_WHERE_CLAUSE}
    GROUP BY 
        uuid  
    ) C
    LEFT JOIN uuid_name D ON D.uuid=C.uuid
{NAME_FILTER_CLAUSE}
ORDER BY total DESC
LIMIT 100;
'''

        template_query_params = { "TIME_CLAUSE": "", "GUILD_WHERE_CLAUSE": "", "NAME_FILTER_CLAUSE": "" }
        prepared_params = []

        if not opt.range:
            opt.range = ["7", "0"]
        
        valid_range = await get_left_right(opt, start)
        if valid_range == "N/A":
            return await ctx.send(embed=ErrorEmbed("Invalid season name input"))
        
        left, right = valid_range
        template_query_params["TIME_CLAUSE"] = "`time` > %s AND `time` <= %s"
        prepared_params.append(left)
        prepared_params.append(right)

        if opt.guild:
            template_query_params["GUILD_WHERE_CLAUSE"] = "AND guild IN (" + "%s," * len(opt.guild) + ")"
            prepared_params.extend(opt.guild)
        
        if opt.user:
            template_query["NAME_FILTER_CLAUSE"] = "WHERE D.name IN (" + "%s," * len(opt.user) + ")"
            prepared_params.extend(opt.user)
        
        query = template_query.format(**template_query_params)
        
        res = await ValorSQL.exec_param(query, prepared_params)

        delta_time = time.time()-start
        
        header = ['  Rank  ', ' '*14+"Name", " NOTG ", "  NOL  ", "  TCC  ", "  TNA  ", "  Total  "]
        
        # rows = [(name_to_ranking[name], name, guild_to_tag.get(player_to_guild[name], ("None", -1))[0], *player_warcounts[name], sum(player_warcounts[name])) for name in player_warcounts]
        # rows.sort(key=lambda x: x[-1], reverse=True)

        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}"
        await LongTextTable.send_message(valor, ctx, header, res, opt_after)

    @valor.help_override.command()
    async def raids(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Raids", desc, color=0xFF00)
