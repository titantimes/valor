from sql import ValorSQL

def avg_process(lock, query):
    guilds = {}
    content = "```"

    with lock:
        res = ValorSQL.execute_sync(query)

    data_pts = len(res)
    for x in res:
        if not x[0] in guilds:
            guilds[x[0]] = [0, 0]
        guilds[x[0]][0] += x[1]
        guilds[x[0]][1] += 1
    
    guild_name_spacing = len(max(guilds, key=len)) + 1
    sorted_rank = [(guilds[g][0]/guilds[g][1], g) for g in guilds]
    sorted_rank.sort(reverse=True)
    content += '\n'.join(f"%{guild_name_spacing}s %6.3f" % (g, v) for v, g in sorted_rank)
    content += "\n```"

    return data_pts, content
