from sql import ValorSQL
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
    if "-" in uuid: return False
    exist = await ValorSQL._execute(f"SELECT * FROM uuid_name WHERE uuid='{uuid}' LIMIT 1")
    if not exist:
        name = requests.get(f"https://api.mojang.com/user/profiles/{uuid.replace('-', '')}/names")[-1]["name"]
        await ValorSQL._execute(f"INSERT INTO uuid_name VALUES ('{uuid}', '{name}')")
    else:
        name = exist[0][1]
    return name

async def guild_name_from_tag(tag: str) -> str:
    guilds = await ValorSQL._execute(f"SELECT * FROM guild_tag_name WHERE LOWER(tag)='{tag.lower()}' ORDER BY priority DESC")
    
    if not len(guilds):
        return "N/A"
    
    if guilds[0][2] == guilds[1][2]:
        revisions = []

        for g, tag, _ in guilds:
            res = requests.get("https://api.wynncraft.com/public_api.php?action=guildStats&command="+g).json()
            n_members = len(res["members"])
            revisions.append(f"('{g}','{tag}',{n_members})")

        await ValorSQL._execute(f"REPLACE INTO guild_tag_name VALUES " + ','.join(revisions))
        revisions.sort(key=lambda x: x[2], reverse=True)
        
        return revisions[0][0]
    
    return guilds[0][0]
    
async def g_tag(tag: str) -> str:
    return await guild_name_from_tag(tag)
    