from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed, discord_ansicolor
from .common import guild_name_from_tag
from datetime import datetime
from sql import ValorSQL
import requests
import commands.common
import re
import argparse
import time
import os
import random
from dotenv import load_dotenv

load_dotenv()
TEST = os.getenv("TEST")=="TRUE"

async def _register_alliance(valor: Valor):
    desc = "Read or Update the alliance."
    avo_macro = "https://script.google.com/macros/s/AKfycbwZIgGTJe_y-GBui-45XaJuNa5eH1_B60wnOkN-6k99uDMLV-C5/exec"
    list_parser = argparse.ArgumentParser(description='Alliance List Command')
    list_parser.add_argument('-g', '--guild', nargs='+')

    stats_parser = argparse.ArgumentParser(description='Alliance Stats Command')
    stats_parser.add_argument('-g', '--guild', nargs='+')
    stats_parser.add_argument('-s', '--sort', choices=["ffa", "reclaim", "help", "other", "total"], default="total")

    sort_choice_map = { "ffa": 1, "reclaim": 2, "help": 4, "other": 3 }

    with open("assets/all_I_want_for_xmas.txt", 'r') as f:
        xmas = [x.split('\n') for x in f.read().split('\n\n')]

    @valor.group()
    async def alliance(ctx: Context):
        if ctx.invoked_subcommand: return
        res = await ValorSQL._execute(f"SELECT * FROM ally_claims")

        guild_claims = {}
        for guild, claim in res:
            if not guild in guild_claims: guild_claims[guild] = []
            guild_claims[guild].append(claim)
        
        content = '\n\n'.join(guild+f" ({len(guild_claims[guild])})\n"+', '.join(claim[:24] for claim in guild_claims[guild]) for guild in guild_claims)

        await LongTextEmbed.send_message(valor, ctx, title="Alliance Claim List", content=content, 
            color=0xFF30, code_block=True)
    
    @alliance.command()
    async def list(ctx: Context, *options):
        try:
            opt = list_parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Alliance List", list_parser.format_help().replace("main.py", "-alliance list"), color=0xFF00)
        
        res = await ValorSQL._execute(f"SELECT * FROM ally_claims")
        interested = set([await guild_name_from_tag(x) for x in opt.guild]) if opt.guild else None

        guild_claims = {}
        for guild, claim in res:
            if interested and not guild in interested: continue
            if not guild in guild_claims: guild_claims[guild] = []
            guild_claims[guild].append(claim)
        
        content = '\n\n'.join(guild+f" ({len(guild_claims[guild])})\n"+', '.join(claim[:24] for claim in guild_claims[guild]) for guild in guild_claims)

        await LongTextEmbed.send_message(valor, ctx, title="Alliance Claim List", content=content, 
            color=0xFF30, code_block=True)

    @alliance.command()
    async def stats(ctx: Context, *options):
        try:
            opt = stats_parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Alliance", stats_parser.format_help().replace("main.py", "-alliance stats"), color=0xFF00)

        start = time.time()
        res = await ValorSQL._execute(f"SELECT * FROM ally_claims")
        ally_guilds = {record[0] for record in res}
        
        if opt.guild:
            ally_guilds = set([await guild_name_from_tag(x) for x in opt.guild]) & ally_guilds

        res = await ValorSQL._execute(f"SELECT guild,ffa,reclaim,other,help FROM ally_stats")
        totals = {x[0]: sum(x[1:]) for x in res}

        if opt.sort == "total":
            res = sorted(res, key=lambda x: totals[x[0]], reverse=True)
        else:
            res = sorted(res, key=lambda x: x[sort_choice_map[opt.sort]], reverse=True)
        
        delta_time = time.time()-start
        
        title, ending = random.choice(xmas)
        title += '\n'
        # 24 7 7 11 6 7
        header = "Guild                   |   FFA   | Reclaim |  Other  |  Nom. Help  |  Total  \n"+\
                 "------------------------+---------+---------+---------+-------------+-------------\n"
        footer = "------------------------+---------+---------+---------+-------------+-------------\n"+\
                ending + '\n' +\
                f"Query took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}\n"
        
        table_line = "%24s| %7d | %7d | %7d | %11d | %7d "
        body = '\n'.join(table_line % (*x, totals[x[0]]) for x in res if x[0] in ally_guilds)

        # content = '```ml\n'+title+header+body+'\n'+footer+'\n```'
        content_body = title+header+body+'\n'+footer
        new_content_body = []
        cols = [discord_ansicolor.green, discord_ansicolor.red, discord_ansicolor.white]
        i = 0
        last_match = 0
        for m in re.finditer(r'(.+?)\n', content_body):
            w = m.group()
            pos, end = m.span()
            if last_match:
                new_content_body.append(content_body[last_match:pos])
            new_content_body.append(str(cols[i%3](w)))
            last_match = end
            i += 1
        new_content_body.append(content_body[last_match:])
        new_content_body = ''.join(new_content_body)

        content = '```ansi\n'+new_content_body+'\n```'
        await ctx.send(content)

    @alliance.command()
    async def update(ctx: Context, url: str):
        if not commands.common.role1(ctx.author) and not TEST:
            return await ctx.send(embed=ErrorEmbed("No Permissions"))

        avo = requests.get("https://www.avicia.ml/map-maker/main.js").text
        t_list = re.search('(?<=Compression = \[)((.+?)(?=\]))', avo)[0].replace('"', '')
        t_id = re.search('(?<=IdForCompression = \[)((.+?)(?=\]))', avo)[0].replace('"', '').replace(' ', '')
        # google sheets has some non ascii compliant ordering for column names :(
        t_lookup = dict(zip(t_id.split(','), t_list.split(',')))
        macro_key = url.split("#")[1]
        encoded_t = requests.get(f"{avo_macro}?key={macro_key}").text[1:-1]

        insert_values = []
        for guild_dat in encoded_t.split('+')[1:]:
            tag = guild_dat.split('-')[0]
            encoded_list = guild_dat.split('=')[1]
            claims = [t_lookup[encoded_list[i:i+2]].lstrip() for i in range(0, len(encoded_list), 2)]
            g_name = await guild_name_from_tag(tag)
            insert_values.extend(f"(\"{g_name if g_name else 'null'}\", \"{claim}\")" for claim in claims)
        
        await ValorSQL._execute(f"DELETE FROM ally_claims")
        await ValorSQL._execute(f"INSERT INTO ally_claims VALUES {','.join(insert_values)}")
        await LongTextEmbed.send_message(valor, ctx, title="Alliance Update", content=f"Refreshed Alliance Claim List to Match {macro_key}", 
            color=0xFF30, code_block=True)

    @alliance.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def alliance(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Alliance", desc, color=0xFF00)
    
    
    