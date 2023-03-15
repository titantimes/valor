import asyncio
from valor import Valor
from dotenv import load_dotenv
import json
import os
import requests
import time
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed
from sql import ValorSQL
from util import profile_calc

load_dotenv()
async def _smp_loop(valor: Valor):
    plyrs = set(os.environ["PLAYERS"].split(','))
    checked = set()
    async def task():
        await valor.wait_until_ready()

        while not valor.is_closed():
            online = requests.get("https://api.mcsrvstat.us/2/157.90.65.205:25565").json()["players"]["uuid"]
            online_rev = {uuid: v for v, uuid in online.items()}
            intersect = set(online.values()) & plyrs
            for m in checked:
                if not m in intersect: # * remove offline players
                    checked.remove(m)
            res = [m for m in intersect if not m in checked] # * new player
            if res:
                await (await valor.fetch_user(int(os.environ["SENDTO"]))).send(repr([online_rev[x] for x in res]) + "\n joined Hestia SMP")
            for m in intersect:
                checked.add(m)

            await asyncio.sleep(60)
    # valor.loop.create_task(task())



async def gxp_roles(valor: Valor):
    guild = valor.get_guild(535603929598394389)
    roles = [0,guild.get_role(1049771610950869044), guild.get_role(1049771738076041306), guild.get_role(1049771820301176832), guild.get_role(1049772313551319110), guild.get_role(1049772376893689927), guild.get_role(1049772389573070939), guild.get_role(1049772521664286841), guild.get_role(1049772658784485446), guild.get_role(1049772867107176548), guild.get_role(1049772907640926269)] 
    # * this is so scuffed but idk how else to do it

    async def task():
        await valor.wait_until_ready()

        while not valor.is_closed():
            user_xps_table = await ValorSQL._execute(f"SELECT * FROM user_total_xps")
            user_ids = await ValorSQL._execute(f"SELECT * FROM id_uuid")
            # * i decided to make these variables cus i figured it would be faster than querying the server a bunch and the tables arent that long

            user_xps= {}
            for row in user_xps_table: # * make a dictionary of uuid:xp
                if row[4]:
                    user_xps[row[4]] = row[1]
    

            for row in user_ids:
                discord_id, uuid = row
                xp = user_xps[uuid]
                member = guild.get_member(discord_id)
                member_roles = set(member.roles)
                intersect = member_roles.intersection(set(roles))
                xp_role=roles[profile_calc.get_xp_rank_index(xp)]
                if intersect:
                    await member.remove_roles(intersect)
                await member.add_roles(xp_role)
        
            await asyncio.sleep(600)
                
                
    # task1 = asyncio.create_task(task())
    # await task1

    
