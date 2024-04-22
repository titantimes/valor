from sql import ValorSQL
import time
from typing import List, Tuple, MutableSet
import requests

def role1(usr, allow={892879299881869352, 702992600835031082, 702991927318020138}): # for setting uuid to id
    roles = {x.id for x in usr.roles}
    return len(allow & roles) > 0

async def get_discord_id(uuid):
    res = ValorSQL._execute(f"SELECT * FROM id_uuid WHERE uuid='{uuid}' LIMIT 1")
    if not res:
        return False
    return res[0][0]

async def get_uuid(player: str):
    if "-" in player: return False
    exist = await ValorSQL._execute(f"SELECT * FROM uuid_name WHERE name='{player}' LIMIT 1")
    if not exist:
        uuid = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}").json()["id"]
        await ValorSQL._execute(f"INSERT INTO uuid_name VALUES ('{uuid}', '{player}')")
    else:
        return exist[0][0]
    return uuid[:8]+'-'+uuid[8:12]+'-'+uuid[12:16]+'-'+uuid[16:20]+'-'+uuid[20:]

async def from_uuid(uuid: str):
    exist = await ValorSQL._execute(f"SELECT * FROM uuid_name WHERE uuid='{uuid}' LIMIT 1")
    if not exist:
        name = requests.get(f"https://api.mojang.com/user/profile/{uuid.replace('-', '')}").json()["name"]
        await ValorSQL._execute(f"INSERT INTO uuid_name VALUES ('{uuid}', '{name}')")
    else:
        name = exist[0][1]
    return name

async def get_range_from_season(season_name: str) -> Tuple[float, float]:
    if '-' in season_name: return "N/A"

    season_query = f"SELECT start_time, end_time FROM season_list WHERE season_name='{season_name}' LIMIT 1"
    res = await ValorSQL._execute(season_query)
    if not res:
        return "N/A"
    start_int, end_int = res[0]
    dt_now = time.time()
    
    start_diff = dt_now - start_int
    end_diff = dt_now - end_int
    return start_diff/3600/24, end_diff/3600/24

async def get_left_right(opt, start):
    if (opt.range[0].isdecimal() or "." in opt.range[0]) and len(opt.range) == 1:
        opt.range.append(0)
    # get left and right using season range
    elif isinstance(opt.range[0], str) and len(opt.range) == 1:
        res = await get_range_from_season(opt.range[0])
        if res == "N/A":
            return "N/A"
        
        opt.range[0] = res[0]
        opt.range.append(res[1])

    left, right = start - float(opt.range[0])*24*3600, start - float(opt.range[1])*24*3600
    return left, right

async def get_guild_names_from_group(guild_group: str) -> List[str]:
    if '-' in guild_group: return "N/A"

    guild_group_query = f"SELECT guild FROM guild_group WHERE guild_group='{guild_group}'"
    res = await ValorSQL._execute(guild_group_query)
    g_names = {x[0] for x in res}

    return g_names

async def guild_name_from_tag(tag: str) -> str:
    if "--" in tag or ";" in tag: return "N/A"
    
    guilds = await ValorSQL._execute(f"SELECT * FROM guild_tag_name WHERE LOWER(tag)='{tag.lower()}' ORDER BY priority DESC")
    
    if not len(guilds):
        return "N/A"
    
    if len(guilds) >= 2 and guilds[0][2] == guilds[1][2]:
        revisions = []

        for g, tag, _ in guilds:
            res = requests.get("https://api.wynncraft.com/v3/guild/"+g).json()
            n_members = res["members"]["total"]
            revisions.append(f"('{g}','{tag}',{n_members})")

        await ValorSQL._execute(f"REPLACE INTO guild_tag_name VALUES " + ','.join(revisions))
        revisions.sort(key=lambda x: x[2], reverse=True)
        
        return revisions[0][0]
    
    return guilds[0][0]

async def guild_tag_from_name(name: str) -> str:
    if "--" in name or ";" in name: return "N/A"
    
    guilds = await ValorSQL._execute(f"SELECT * FROM guild_tag_name WHERE LOWER(guild)='{name.lower()}' ORDER BY priority DESC")
    
    if not len(guilds):
        return "N/A"
    
    if len(guilds) >= 2 and guilds[0][2] == guilds[1][2]:
        revisions = []

        for g, tag, _ in guilds:
            res = requests.get("https://api.wynncraft.com/v3/guild/"+g).json()
            n_members = res["members"]["total"]
            revisions.append(f"('{g}','{tag}',{n_members})")

        await ValorSQL._execute(f"REPLACE INTO guild_tag_name VALUES " + ','.join(revisions))
        revisions.sort(key=lambda x: x[2], reverse=True)
        
        return revisions[0][1]
    
    return guilds[0][1]

# plural!
async def guild_names_from_tags(tags: List[str]) -> Tuple[MutableSet[str], List[str]]:
    unidentified = []
    guild_names = []
    guild_names_list = [await guild_name_from_tag(x) for x in tags]
    for i in range(len(tags)):
        if guild_names_list[i] == "N/A": unidentified.append(tags[i])
        else: guild_names.append(guild_names_list[i])
    
    return guild_names, unidentified

async def guild_tags_from_names(names: List[str]) -> Tuple[MutableSet[str], List[str]]:
    unidentified = []
    guild_tags = []
    guild_tags_list = [await guild_tag_from_name(x) for x in names]
    for i in range(len(names)):
        if guild_tags_list[i] == "N/A": unidentified.append(names[i])
        else: guild_tags.append(guild_tags_list[i])
    
    return guild_tags, unidentified

async def current_guild_from_uuid(uuid: str) -> str:
    result = await ValorSQL._execute(f"SELECT joined FROM guild_join_log WHERE uuid='{uuid}' ORDER BY date DESC LIMIT 1")
    guild = "N/A" if not result else result[0][0]
    return guild
    
async def g_tag(tag: str) -> str:
    return await guild_name_from_tag(tag)

async def get_guild_members(ahttp_ctx, guild_name: str) -> List[str]:
    members = []
    guild_members_data = (await ahttp_ctx.get_json("https://api.wynncraft.com/v3/guild/"+guild_name))["members"]
    for rank in guild_members_data:
        if type(guild_members_data[rank]) != dict: continue

        members.extend([guild_members_data[rank][x]["uuid"] for x in guild_members_data[rank]]) 
    
    return members