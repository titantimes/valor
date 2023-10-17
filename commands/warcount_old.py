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
from commands.common import get_uuid, get_left_right
import argparse

load_dotenv()
async def _register_warcount_old(valor: Valor):
    desc = "Gets you the war count leaderboard. (old version)"
    clone_map = {"Hunter": "Archer", "Knight": "Warrior", "Dark Wizard": "Mage", "Ninja": "Assassin", "Skyseer": "Shaman"}
    real_classes = clone_map.values()
    # season_times={8:[1663016400,1666569600],9:[1666983600,1672462800]} # ! idk the end time for season 9 so i put a big number
    parser = argparse.ArgumentParser(description='Warcount Command')
    parser.add_argument('-n', '--names', nargs='+', default=[])
    parser.add_argument('-c', '--classes', nargs='+', default=[])
    parser.add_argument('-r', '--range', nargs='+', default=[2e9, 0])

    @valor.command()
    async def warcount_old(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "warcount_old", parser.format_help().replace("main.py", "-warcount_old"), color=0xFF00)
    
        counts = []
        collection = mongo.client.valor.war_entries
        listed_classes = real_classes if not opt.classes else opt.classes
        listed_classes_enumerated = {v.lower(): i+1 for i, v in enumerate(listed_classes)}

        names = {n.lower(): 0 for n in opt.names} if opt.names else "Anything"
        uuid_to_name = {}
        uuid_to_wars = {}

        start = time.time()
        valid_range = await get_left_right(opt, start)
        if valid_range == "N/A":
            return await ctx.send(embed=ErrorEmbed("Invalid season name input"))
        left, right = valid_range

        res = await ValorSQL._execute(f"SELECT time, name, uuid, class FROM war_attempts WHERE time>={left} and time<={right}")
        for row in res:
            if names != "Anything" and not row[1].lower() in names: continue
            elif names != "Anything":
                names[row[1].lower()] = 1
            uuid_to_name[row[2]] = row[1]
            if not row[2] in uuid_to_wars:
                uuid_to_wars[row[2]] = [0]*(len(listed_classes)+2)
                uuid_to_wars[row[2]][0] = "name"

            doc_class = row[3]
            if not doc_class: continue

            real_class = clone_map.get(doc_class, doc_class).lower()
            count_idx = listed_classes_enumerated.get(real_class, -1)
            if count_idx == -1: # because bear keeps entering garbage values into fields
                continue

            uuid_to_wars[row[2]][count_idx] += 1

        delta_time = time.time()-start

        for uuid in uuid_to_wars:
            record = uuid_to_wars[uuid]
            record[0] = uuid_to_name[uuid]
            record[-1] = sum(record[1:-1])
            counts.append(record)
        
        counts.sort(reverse=True, key=lambda x: x[-1])

        unidentified = [x for x in names if not names[x]] if isinstance(names, dict) else []
        unid_prefix = f"The following players are unidentified: {unidentified}\n" if unidentified else ""

        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}"

        header, unid_pref, rows, = [' '*14+"Name", *listed_classes, "Total"], unid_prefix, counts

        await LongTextTable.send_message(valor, ctx, header, rows, opt_after)

    @valor.help_override.command()
    async def warcount_old(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Warcount old", desc, color=0xFF00)
