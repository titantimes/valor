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
async def _register_graids(valor: Valor):
    desc = "Gets you the guild raid count leaderboard"
    parser = argparse.ArgumentParser(description='Warcount Command')
    parser.add_argument('-r', '--range', nargs='+', default=None)
    parser.add_argument('-g', '--guild', nargs='+', default=None)


    @valor.command()
    async def graids(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Guild Raids", parser.format_help().replace("main.py", "-graids"), color=0xFF00)
    
        start = time.time()

        template_query = '''
SELECT B.name, SUM(A.num_raids) AS raid_cnt
FROM
	guild_raid_records A LEFT JOIN uuid_name B ON A.uuid=B.uuid
WHERE 
    {TIME_CLAUSE}
    AND A.guild IN ("Titans Valor")
GROUP BY A.uuid
ORDER BY raid_cnt DESC;
'''

        template_query_params = { "TIME_CLAUSE": "" }
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
        
        query = template_query.format(**template_query_params)
        
        res = await ValorSQL.exec_param(query, prepared_params)

        delta_time = time.time()-start
        
        header = [' '*14+"Name", "  Total  "]
        
        # rows = [(name_to_ranking[name], name, guild_to_tag.get(player_to_guild[name], ("None", -1))[0], *player_warcounts[name], sum(player_warcounts[name])) for name in player_warcounts]
        # rows.sort(key=lambda x: x[-1], reverse=True)

        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}"
        await LongTextTable.send_message(valor, ctx, header, res, opt_after)

    @valor.help_override.command()
    async def graids(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Guild Raids", desc, color=0xFF00)
