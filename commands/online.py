from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed, guild_name_from_tag
import random
import requests

async def _register_online(valor: Valor):
    desc = "Online: shows who's online in a guild"
    rank_order = dict(zip(["RECRUIT", "RECRUITER", "CAPTAIN", "STRATEGIST", "CHIEF", "OWNER"], range(5, -1, -1)))
    @valor.command()
    async def online(ctx: Context, *args, guild="Titans Valor"):
        group = False
        if args and args[0] == 'g':
            args = args[1:]
            group = True
        guild = ' '.join(args) if len(args) else guild
        res = requests.get(valor.endpoints["guild"].format(guild)).json()

        if res.get("error"):
            # try using the tag instead
            guild = guild_name_from_tag(guild)

        res = requests.get(valor.endpoints["guild"].format(guild)).json()

        if res.get("error"):
            return await ctx.send(embed=ErrorEmbed("Guild doesn't exist."))

        members = {m["name"]: m["rank"] for m in res["members"]}
        all_players = requests.get(valor.endpoints["online"]).json()

        del all_players["request"]

        # add the rank name along with wc
        online_rn = [(p, k, members[p]) for k in all_players for p in all_players[k] if p in members]
        
        if not len(online_rn):
            return await LongTextEmbed.send_message(valor, ctx, f"{guild} Members Online", "There are no members online.", color = 0xFF)
        if group:
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
        online_rn.sort(key = lambda x: rank_order[x[2]])
        # escape any underscores and concat rank with world number
        online_rn = [(p.replace("_", "\_"), f"{k}\n{rank}") for p, k, rank in online_rn]

        await LongFieldEmbed.send_message(valor, ctx, f"{guild} Members Online ({len(online_rn)})", online_rn)
        # await ctx.send("```"+'\n'.join("%16s | %8s" % (p, k) for p, k in online_rn) + "```")
    
    @online.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        print(error.with_traceback())
    
    @valor.help_override.command()
    async def online(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Online", desc, color=0xFF00)
    
    
    