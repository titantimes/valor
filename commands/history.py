from valor import Valor
from sql import ValorSQL
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed, guild_name_from_tag
from commands.common import get_uuid, from_uuid
from datetime import datetime
import time

async def _register_history(valor: Valor):
    desc = "Gets you the guild membership history of a player."
    
    @valor.command()
    async def history(ctx: Context, username: str):
        uuid = await get_uuid(username)
        now = time.time()

        content = "```ml\nGuild History of %s since April 2022\n---------------------------\n" % username
        join_guilds = await ValorSQL._execute(f"SELECT * FROM guild_join_log WHERE uuid='{uuid}' ORDER BY date DESC")
        if join_guilds:
            len_g_name = max([len(x[3]) for x in join_guilds])
            content += f'%{len_g_name+2}s\n' % join_guilds[0][3]
            for i in range(1, len(join_guilds)):
                _, _, _, joined, date = join_guilds[i]
                if joined == "None": continue

                old_rank = join_guilds[i-1][2]
                
                friendly_date = datetime.fromtimestamp(date).strftime("%d %b %Y %H:%M:%S.%f UTC")
                content +=  f'%{len_g_name+2}s %12s  %s\n' % (joined, old_rank, friendly_date) 
        
        content += f"Query took {(time.time()-now):.5}s\n"
                
        content += "\nCoolness Data (fewer guilds indexed) Since April 2021\n---------------------------\n"

        now = time.time()
        already_counted = set()
        join_guilds = await ValorSQL._execute(f"SELECT guild, timestamp FROM activity_members WHERE uuid='{uuid}' ORDER BY timestamp DESC")
        filtered = []
        for guild, timestamp in join_guilds:
            if guild in already_counted: continue
            already_counted.add(guild)
            friendly_date = datetime.fromtimestamp(timestamp).strftime("%d %b %Y %H:%M:%S.%f UTC")

            filtered.append((guild, friendly_date))

        if filtered: 
            len_g_name = max([len(x[0]) for x in filtered])

            for guild, date in filtered:
                content += f'%{len_g_name+2}s  %s\n' % (guild, date) 
        
        content += f"Query took {(time.time()-now):.5}s"

        content += '```'

        await ctx.send(content)

    @history.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed("How did an error even happen (player doesn't exist?"))
        raise error
    
    @valor.help_override.command()
    async def history(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "History", desc, color=0xFF00)
    
    
    