import requests
import time
from valor import Valor
from sql import ValorSQL
import mongo
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, get_war_rank, get_xp_rank
from discord.ext.commands import Context
from datetime import datetime
from dotenv import load_dotenv
import os
from commands.common import get_uuid
import argparse

load_dotenv()
async def _register_warcount(valor: Valor):
    desc = "Gets you the war count leaderboard."
    parser = argparse.ArgumentParser(description='Warcount Command')
    parser.add_argument('-n', '--names', nargs='+', default=[])
    parser.add_argument('-c', '--classes', nargs='+', default=[])
    
    @valor.command()
    async def warcount(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "warcount", parser.format_help().replace("main.py", "-warcount"), color=0xFF00)
        
        unidentified = []
        counts = []
        collection = mongo.client.valor.war_count
        player_data = {}
        listed_classes = set() if not opt.classes else opt.classes

        if opt.names:
            for name in opt.names:
                uuid = await get_uuid(name)
                cursor = collection.find_one({"_id": uuid})
                if not cursor: 
                    unidentified.append(cursor)
                    continue
                player_data[name] = cursor["classes"]

                if not opt.classes: 
                    listed_classes |= cursor["classes"].keys()
        else:
            cursor = collection.find({})
            for doc in cursor:
                name = doc["name"]
                opt.names.append(name)
                player_data[name] = doc["classes"]
                if not opt.classes: 
                    listed_classes |= doc["classes"].keys()
        
        listed_classes = list(listed_classes)
        for name in opt.names:
            record = []
            for c in listed_classes:
                record.append(player_data[name].get(c, 0))
            counts.append([sum(record), *record, name])
        
        counts.sort(reverse=True)
        unid_prefix = f"The following players are unidentified: {unidentified}\n" if unidentified else ""
        len_name = max([len(x[-1]) for x in counts])
        len_class = max([len(x) for x in listed_classes])
        # name       |   c1   |   c2   |  total  
        format = f"%{len_name}s" + f" | %{len_class+1}s"*len(listed_classes) + " |  %s  "
        sep = "-"*len_name + ("-+-"+'-'*(len_class+1))*len(listed_classes) + "-+---------"
        header = format % ("Name", *listed_classes, "Total")
        counts = [[x[-1], *x[1:-1], x[0]] for x in counts]
        content = "```"+header+'\n'+sep+'\n'+'\n'.join(format % tuple(map(str, count)) for count in counts[:25])+"```"
    
        await ctx.send(f"{unid_prefix}\n{content}")

    @valor.help_override.command()
    async def warcount(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Warcount", desc, color=0xFF00)