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
    clone_map = {"Hunter": "Archer", "Knight": "Warrior", "Dark Wizard": "Mage", "Ninja": "Assassin", "Skyseer": "Shaman"}
    real_classes = clone_map.values()
    parser = argparse.ArgumentParser(description='Warcount Command')
    parser.add_argument('-n', '--names', nargs='+', default=[])
    parser.add_argument('-c', '--classes', nargs='+', default=[])
    
    @valor.command()
    async def warcount(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "warcount", parser.format_help().replace("main.py", "-warcount"), color=0xFF00)
        
        counts = []
        collection = mongo.client.valor.war_count
        listed_classes = real_classes if not opt.classes else opt.classes
        listed_classes_enumerated = {v.lower(): i+1 for i, v in enumerate(listed_classes)}

        names = {n: 0 for n in opt.names} if opt.names else "Anything"

        start = time.time()
        for doc in collection.find():
            if names != "Anything" and not doc.get("name") in names: continue
            
            if isinstance(names, dict): names[doc["name"]] = True # mark as identified
            
            classes = doc.get("classes")
            if not classes: continue

            # name #stuff... #total
            record = [0]*(len(listed_classes)+2)
            record[0] = doc["name"]

            for c in classes:
                real_c = clone_map.get(c, c).lower()
                if real_c in listed_classes_enumerated:
                    record[listed_classes_enumerated[real_c]] += classes[c]
            
            record[-1] = sum(record[1:-1])

            counts.append(record)
        delta_time = time.time()-start

        counts.sort(reverse=True, key=lambda x: x[-1])
        unidentified = [x for x in names if not names[x]] if isinstance(names, dict) else []

        unid_prefix = f"The following players are unidentified: {unidentified}\n" if unidentified else ""
        len_name = max([len(x[0]) for x in counts])
        len_class = max([len(x) for x in listed_classes])
        # name       |   c1   |   c2   |  total  
        format = f"%{len_name}s" + f" | %{len_class+1}s"*len(listed_classes) + " |  %s  "
        sep = "-"*len_name + ("-+-"+'-'*(len_class+1))*len(listed_classes) + "-+---------"
        header = format % ("Name", *listed_classes, "Total")
        footer = f"{sep}\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}"

        content = "```\n"+header+'\n'+sep+'\n'+'\n'.join(format % tuple(map(str, count)) for count in counts[:25])+\
            '\n'+footer+"```"
    
        await ctx.send(f"{unid_prefix}\n{content}")

    @valor.help_override.command()
    async def warcount(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Warcount", desc, color=0xFF00)