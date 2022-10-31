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
    season_times={8:[1663016400,1666569600],9:[1666983600,1672462800]} # ! idk the end time for season 9 so i put a big number
    current_season = 9
    parser = argparse.ArgumentParser(description='Warcount Command')
    parser.add_argument('-n', '--names', nargs='+', default=[])
    parser.add_argument('-c', '--classes', nargs='+', default=[])
    parser.add_argument('-r', '--range', nargs='+', default=[])
    parser.add_argument('-s', '--season', nargs='+', default=[])
    
    @valor.command()
    async def warcount(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "warcount", parser.format_help().replace("main.py", "-warcount"), color=0xFF00)
    

        if opt.season:
            await ctx.send(warcount_season(opt))
        elif not opt.range:
            await ctx.send(warcount_nonrange(opt))
        else:
            await ctx.send(warcount_range(opt))
    
    def warcount_season(opt):
        counts = []
        collection = mongo.client.valor.war_entries
        listed_classes = real_classes if not opt.classes else opt.classes
        listed_classes_enumerated = {v.lower(): i+1 for i, v in enumerate(listed_classes)}

        names = {n.lower(): 0 for n in opt.names} if opt.names else "Anything"
        uuid_to_name = {}
        uuid_to_wars = {}


        t0,t1 = season_times[opt.season]
        # t0 = time.time()*1000-1000*3600*24*int(opt.range[0])
        # t1 = time.time()*1000-1000*3600*24*int(opt.range[1])
        start = time.time()
        for doc in collection.find({"_id": {"$gt": t0, "$lt": t1}}):
            if names != "Anything" and not doc["sender"].lower() in names: continue
            elif names != "Anything":
                names[doc["sender"].lower()] = 1
            uuid_to_name[doc["uuid"]] = doc["sender"]
            if not doc["uuid"] in uuid_to_wars:
                uuid_to_wars[doc["uuid"]] = [0]*(len(listed_classes)+2)
                uuid_to_wars[doc["uuid"]][0] = "name"

            doc_class = doc.get("class_")
            if not doc_class: continue

            real_class = clone_map.get(doc_class, doc_class).lower()
            count_idx = listed_classes_enumerated.get(real_class, -1)
            if count_idx == -1: # because bear keeps entering garbage values into fields - watafak
                continue

            uuid_to_wars[doc["uuid"]][count_idx] += 1


        delta_time = time.time()-start

        for uuid in uuid_to_wars:
            record = uuid_to_wars[uuid]
            record[0] = uuid_to_name[uuid]
            record[-1] = sum(record[1:-1])
            counts.append(record)
        
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

        content = "```\n"+header+'\n'+sep+'\n'+'\n'.join(format % tuple(map(str, count)) for count in counts[:15])+\
            '\n'+footer+"```"
        
        return f"{unid_prefix}\n{content}"
    
    def warcount_range(opt):
        counts = []
        collection = mongo.client.valor.war_entries
        listed_classes = real_classes if not opt.classes else opt.classes
        listed_classes_enumerated = {v.lower(): i+1 for i, v in enumerate(listed_classes)}

        names = {n.lower(): 0 for n in opt.names} if opt.names else "Anything"
        uuid_to_name = {}
        uuid_to_wars = {}

        t0 = time.time()*1000-1000*3600*24*int(opt.range[0])
        t1 = time.time()*1000-1000*3600*24*int(opt.range[1])
        start = time.time()
        for doc in collection.find({"_id": {"$gt": t0, "$lt": t1}}):
            if names != "Anything" and not doc["sender"].lower() in names: continue
            elif names != "Anything":
                names[doc["sender"].lower()] = 1
            uuid_to_name[doc["uuid"]] = doc["sender"]
            if not doc["uuid"] in uuid_to_wars:
                uuid_to_wars[doc["uuid"]] = [0]*(len(listed_classes)+2)
                uuid_to_wars[doc["uuid"]][0] = "name"

            doc_class = doc.get("class_")
            if not doc_class: continue

            real_class = clone_map.get(doc_class, doc_class).lower()
            count_idx = listed_classes_enumerated.get(real_class, -1)
            if count_idx == -1: # because bear keeps entering garbage values into fields - watafak
                continue

            uuid_to_wars[doc["uuid"]][count_idx] += 1


        delta_time = time.time()-start

        for uuid in uuid_to_wars:
            record = uuid_to_wars[uuid]
            record[0] = uuid_to_name[uuid]
            record[-1] = sum(record[1:-1])
            counts.append(record)
        
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

        content = "```\n"+header+'\n'+sep+'\n'+'\n'.join(format % tuple(map(str, count)) for count in counts[:15])+\
            '\n'+footer+"```"
        
        return f"{unid_prefix}\n{content}"
    
    def warcount_nonrange(opt):
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

        content = "```\n"+header+'\n'+sep+'\n'+'\n'.join(format % tuple(map(str, count)) for count in counts[:15])+\
            '\n'+footer+"```"
        
        return f"{unid_prefix}\n{content}"

    @valor.help_override.command()
    async def warcount(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Warcount", desc, color=0xFF00)