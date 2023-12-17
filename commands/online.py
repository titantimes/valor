from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed
from .common import guild_name_from_tag
import random
import argparse
import requests

async def _register_online(valor: Valor):
    desc = "Online: shows who's online in a guild\nThe new command is formatted like this: -online -g <guild_TAG>.\n For example: -online -g ano"
    rank_order = dict(zip(["recruit", "recruiter", "captain", "strategist", "chief", "owner"], range(5, -1, -1)))

    parser = argparse.ArgumentParser(description='Online command')
    parser.add_argument('-g', '--guild', type=str)
    
    @valor.command()
    async def online(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Online", parser.format_help().replace("main.py", "-online"), color=0xFF00)
        
        guild = await guild_name_from_tag(opt.guild)

        res = requests.get(valor.endpoints["guild"].format(guild)).json()

        if "members" not in res:
            return await ctx.send(embed=ErrorEmbed("Guild doesn't exist."))

        # add the rank name along with wc
        # online_rn = [(p, k, members[p]) for k in all_players for p in all_players[k] if p in members]
        online_rn = [(name, member["server"], rank) for rank, v in res["members"].items() if rank != "total" for name, member in v.items() if member["online"]]
        
        if not len(online_rn):
            return await LongTextEmbed.send_message(valor, ctx, f"{guild} Members Online", "There are no members online.", color = 0xFF)

        grouped = {}
        for p, k, rank in online_rn:
            if not k in grouped:
                grouped[k] = []
            grouped[k].append((p, k, rank))
            grouped[k].sort(key=lambda x: rank_order[x[2]])
        grouped = [x[1] for x in sorted(grouped.items(), key=lambda v: len(v[1]), reverse=True)]
        return await LongTextEmbed.send_message(valor, ctx, f"Members of {guild} online ({len(online_rn)})", '```' +
            '-'*17+'+'+'-'*7+'+'+'-'*12+'\n'+
            '\n'.join('\n'.join(('%16s | %5s | %10s' % x) for x in y)+'\n' for y in grouped) + '```',
            color=0xa1ffe1    
        )
    
    
    @online.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed("The new command is formatted like this: -online -g <guild_TAG>.\n For example: -online -g ano"))
        print(error.with_traceback())
    
    @valor.help_override.command()
    async def online(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Online", desc, color=0xFF00)
    
    
    