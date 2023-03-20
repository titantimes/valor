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
    if os.environ["TEST"] == "TRUE":
        return
    
    await valor.wait_until_ready()

    guild = valor.get_guild(535603929598394389)
    # guild = valor.get_guild(886035924461432893) # test server

    roles = [0,guild.get_role(1049771610950869044), guild.get_role(1049771738076041306), guild.get_role(1049771820301176832), guild.get_role(1049772313551319110), guild.get_role(1049772376893689927), guild.get_role(1049772389573070939), guild.get_role(1049772521664286841), guild.get_role(1049772658784485446), guild.get_role(1049772867107176548), guild.get_role(1049772907640926269)]
    # test server roles 
    # roles = [0, guild.get_role(1085380592620818564), guild.get_role(1085380626552729640), guild.get_role(1085380658391691284), guild.get_role(1085380670152527922), guild.get_role(1085380671268208710), guild.get_role(1085380672685879336), guild.get_role(1085380673407295569), guild.get_role(1085380674330050740), guild.get_role(1085380768039174154), guild.get_role(1085380768978718771)]

    while not valor.is_closed():
        user_xps_table = await ValorSQL._execute(f"SELECT * FROM user_total_xps")
        user_ids = await ValorSQL._execute(f"SELECT * FROM id_uuid")

        user_xps= {}
        for row in user_xps_table: # * make a dictionary of uuid:xp
            if row[4]:
                user_xps[row[4]] = row[1]

        for row in user_ids:
            discord_id, uuid = row
            xp = user_xps[uuid]
            member = guild.get_member(discord_id)

            if not member: # skip if member is not in discord anymore.
                continue

            member_roles = set(member.roles)
            intersect = set(roles) & member_roles
            if not intersect: continue

            intersect = [*intersect][0]

            xp_role=roles[profile_calc.get_xp_rank_index(xp)]

            if intersect and intersect != xp_role:
                await member.remove_roles(intersect)

            await member.add_roles(xp_role)
    
        await asyncio.sleep(600)
