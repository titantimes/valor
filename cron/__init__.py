import asyncio
from valor import Valor
from dotenv import load_dotenv
import os
import requests
import datetime as dt
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed, LongTextTable
from discord.ext import tasks
from commands.tickets import get_tickets
from sql import ValorSQL
from util import profile_calc
from commands.common import from_uuid

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
        user_xps_table = await ValorSQL._execute("""
SELECT IFNULL(A2.uuid, C2.uuid), A2.gxp
FROM
    (SELECT uuid, MAX(xp) AS gxp
    FROM
        ((SELECT uuid, xp FROM user_total_xps)
        UNION ALL
        (SELECT B.uuid, B.value AS xp
        FROM 
            player_stats A JOIN player_global_stats B ON A.uuid=B.uuid
        WHERE A.guild="Titans Valor" AND B.label="gu_gxp")) A1
    GROUP BY uuid) A2 
    LEFT JOIN (SELECT uuid, name FROM user_total_xps) C2 ON C2.uuid=A2.uuid
ORDER BY A2.gxp DESC;
""")
        user_ids = await ValorSQL._execute(f"SELECT * FROM id_uuid")

        user_xps= {}
        for row in user_xps_table: # * make a dictionary of uuid:xp
            if row[0]:
                user_xps[row[0]] = row[1]

        for row in user_ids:
            discord_id, uuid = row
            xp = user_xps.get(uuid, 0)
            member = guild.get_member(discord_id)

            if not member: # skip if member is not in discord anymore.
                continue

            member_roles = set(member.roles)
            intersect = set(roles) & member_roles

            xp_role=roles[profile_calc.get_xp_rank_index(xp)-1]

            if not xp_role in member.roles:
                if intersect and intersect != xp_role:
                    await member.remove_roles([*intersect][0])

                if member.roles and xp_role: # snazz for whatever reason wants a 0 at the beginning of roles
                    await member.add_roles(xp_role)
        
        await asyncio.sleep(600)

async def seniority_roles(valor: Valor):
    if os.environ["TEST"] == "TRUE":
        return
    
    await valor.wait_until_ready()

    guild = valor.get_guild(713926223075475458)

    roles = [0,guild.get_role(1049771610950869044), ]

    while not valor.is_closed():
        user_xps_table = await ValorSQL._execute(f"SELECT * FROM user_total_xps")
        user_ids = await ValorSQL._execute(f"SELECT * FROM id_uuid")

        user_xps= {}
        for row in user_xps_table: # * make a dictionary of uuid:xp
            if row[4]:
                user_xps[row[4]] = row[1]

        for row in user_ids:
            discord_id, uuid = row
            xp = user_xps.get(uuid, 0)
            member = guild.get_member(discord_id)

            if not member: # skip if member is not in discord anymore.
                continue

            member_roles = set(member.roles)
            intersect = set(roles) & member_roles

            xp_role=roles[profile_calc.get_xp_rank_index(xp)-1]

            if intersect and intersect != xp_role:
                await member.remove_roles([*intersect][0])

            if xp_role: # snazz for whatever reason wants a 0 at the beginning of roles
                await member.add_roles(xp_role)
    
        await asyncio.sleep(3600)

async def warcount_roles(valor: Valor):
    if os.environ["TEST"] == "TRUE":
        return
    
    await valor.wait_until_ready()

    guild = valor.get_guild(535603929598394389)
    # guild = valor.get_guild(1088602008837169294) # test server

    roles = [0,guild.get_role(1054213859289878528), guild.get_role(1054214523717947423), guild.get_role(1054214514054271015), guild.get_role(1054214505766330408), guild.get_role(1054214486820663346), guild.get_role(1054214475231793172), guild.get_role(1054214464817336350), guild.get_role(1054214452712579142), guild.get_role(1054214410169765908), guild.get_role(1054214365278126110)]
    # test server roles 
    # roles = [0, guild.get_role(1088604270603026502), guild.get_role(1088604260935147580), guild.get_role(1088604253104378016), guild.get_role(1088604245474943148), guild.get_role(1088604237946179594), guild.get_role(1088604229830184980), guild.get_role(1088604222473383996), guild.get_role(1088604215049474161), guild.get_role(1088604206832824330), guild.get_role(1088603953786265652)]

    while not valor.is_closed():
        user_wars_table = await ValorSQL._execute(f"SELECT uuid, SUM(warcount) FROM cumu_warcounts GROUP BY uuid;")
        user_ids = await ValorSQL._execute(f"SELECT * FROM id_uuid")

        user_wars= {}
        for row in user_wars_table: # * make a dictionary of uuid:warcount
            user_wars[row[0]] = row[1]

        for row in user_ids:
            discord_id, uuid = row
            wars = user_wars.get(uuid, 0)
            member = guild.get_member(discord_id)

            if not member: # skip if member is not in discord anymore.
                continue

            username = await from_uuid(uuid)
            wars += valor.warcount119.get(username.lower(), 0) # 1.19 wars

            member_roles = set(member.roles)
            intersect = set(roles) & member_roles

            war_role=roles[profile_calc.get_war_rank_index(wars)-1]

            if not war_role in member.roles:
                if intersect and intersect != war_role:
                    await member.remove_roles([*intersect][0])

                if member.roles and war_role: # snazz for whatever reason wants a 0 at the beginning of roles
                    await member.add_roles(war_role)
        
        await asyncio.sleep(600)

@tasks.loop(seconds=55)
async def ticket_cron(valor: Valor):
    if dt.datetime.now(tz=dt.timezone.utc).strftime("%a %H:%M") == "Sun 17:00":
        message_channel = valor.get_channel(892878955323994132)
        ticket_data = await get_tickets()
        table = LongTextTable(ticket_data[0], ticket_data[1])
        await message_channel.send(table.description)
