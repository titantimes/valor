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
from commands.common import get_uuid, get_left_right, guild_names_from_tags, guild_tags_from_names, get_guild_members
import argparse

load_dotenv()
async def _register_inactivity(valor: Valor):
    desc = "Gives you inactivity details of a given guild"
    parser = argparse.ArgumentParser(description='Inactivity Command')
    parser.add_argument('-n', '--name', type=str)
    parser.add_argument('-g', '--guild', nargs='+', default=[]) # this one is filter players only in guilds, Callum: 100

    @valor.command()
    async def inactivity(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Inactivity", parser.format_help().replace("main.py", "-inactivity"), color=0xFF00)

        if opt.name: # detailed search takes precedence
            return await handle_get_inactivity_details(valor, ctx, opt.name)
        
        guild_names, unidentified_guilds = await guild_names_from_tags(opt.guild)

        query = '''
SELECT F.tag, guild_rank, B.name, Round((%s-lastjoin)/3600/24, 2) AS days_inactive, Round((%s-E.notify_timestamp)/3600/24, 2), CONCAT(IFNULL(G.coolness,0), "%%") 
FROM 
    player_stats A 
    NATURAL JOIN uuid_name B 
    NATURAL JOIN guild_member_cache C 
    LEFT JOIN id_uuid D ON B.uuid = D.uuid 
    LEFT JOIN (SELECT * FROM inactivity_alerts ORDER BY notify_timestamp DESC LIMIT 1) E
        ON E.discord_id=D.discord_id
    LEFT JOIN guild_tag_name F ON F.guild=C.guild
    LEFT JOIN (
        SELECT uuid, COUNT(*) AS coolness 
        FROM activity_members
        WHERE timestamp >= %s-3600*24*7
        GROUP BY uuid
    ) G ON G.uuid=D.uuid
WHERE C.guild IN ''' + f"({','.join('%s' for _ in range(len(guild_names)))})\n" + \
"ORDER BY days_inactive DESC;"
        now = time.time()
        results = await ValorSQL.exec_param(query, (now, now, now, *guild_names))

        header = ['Guild', "   Rank   ", "       Name       ", "Days Inactive", "Days Since Notice", "Coolness"]
        opt_after = f"\nQuery took {time.time()-now:.3}s. Requested at {datetime.utcnow().ctime()}"
        await LongTextTable.send_message(valor, ctx, header, results, opt_after)
    
    async def handle_get_inactivity_details(valor, ctx, name):
        query = '''
SELECT B.name, B.uuid, C.msg, C.message_id
FROM
    player_stats A
    NATURAL JOIN uuid_name B
    NATURAL JOIN inactivity_alerts C
WHERE B.name=%s
LIMIT 1;
'''     
        results = await ValorSQL.exec_param(query, (name, ))
        if not results:
            await LongTextEmbed.send_message(valor, ctx, f"Inactivity Details for {name}", "Player not found", color=0xFF0000)
        results = results[0]

        content = f"""
Name: `{name}`
UUID: {results[1]}
MSG: 
```
{results[2]}
```
Message Link: https://discord.com/channels/535603929598394389/679724389184569364/{results[3]}

        """

        await LongTextEmbed.send_message(valor, ctx, f"Inactivity Details for {name}", content, color=0xAA)

    @valor.help_override.command()
    async def inactivity(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "inactivity", desc, color=0xFF00)
