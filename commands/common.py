from sql import ValorSQL

def role1(usr): # for setting uuid to id
    roles = {x.id for x in usr.roles}
    allow = {892879299881869352, 702992600835031082, 702991927318020138}
    return len(allow & roles) > 0

async def get_discord_id(uuid):
    res = ValorSQL._execute(f"SELECT * FROM id_uuid WHERE uuid='{uuid}' LIMIT 1")
    if not res:
        return False
    return res[0][0]