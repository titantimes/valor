from valor import Valor
from sql import ValorSQL
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongTextMessage
from commands.common import get_uuid, from_uuid
from datetime import datetime
import time
import requests

async def _register_history(valor: Valor):
    desc = "Gets you the guild membership history of a player."
    
    @valor.command()
    async def history(ctx: Context, username: str):
        uuid = await get_uuid(username)
        now = time.time()

        # Fetch data from the database
        join_guilds = await ValorSQL._execute(f"SELECT * FROM guild_join_log WHERE uuid='{uuid}' ORDER BY date DESC")
        activity_members = await ValorSQL._execute(f"SELECT * FROM activity_members WHERE uuid='{uuid}' ORDER BY timestamp DESC")

        # Combine data from both tables
        combined_data = []
        if join_guilds:
            for x in join_guilds:
                try:
                    combined_data.append((x[1], x[2], int(x[4]), x[3]))  # (guild, rank, date, joined)
                except ValueError as e:
                    print(f"Error converting join_guilds date to int: {x[4]} - {e}")

        if activity_members:
            for x in activity_members:
                try:
                    combined_data.append((x[1], '', int(x[2]), None))  # (guild, rank(not from) timestamp, joined(not from), timestamp repeat)
                except ValueError as e:
                    print(f"Error converting activity_members timestamp to int: {x[2]} - {e}")

        len_g_name = max(len(x[0]) for x in combined_data) if combined_data else 0
        len_rank = max(len(x[1]) for x in combined_data) if combined_data else 5

        # seperator line changes length innit
        separator_length = len_g_name + 4 + len_rank + 4 + 22 + 22 + 9
        separator_line = '-' * separator_length

        # Top Line
        content = "Guild History of %s since 2021, some guilds weren't indexed until 2022\n%s\n" % (username, separator_line) #i want to shorten this more idk how to

        combined_data.sort(key=lambda x: x[2], reverse=True) 

        filtered_data = []
        current_guild = None
        earliest_timestamp = None

        for entry in combined_data:
            guild, rank, timestamp, joined = entry
            if earliest_timestamp is None or timestamp < earliest_timestamp:
                earliest_timestamp = timestamp
            if current_guild is None:
                # First entry, consider it a join
                filtered_data.append((guild, rank, None, None))  # (guild, rank, join_date, leave_date)
                current_guild = guild
            elif guild != current_guild:
                # Silly transfer logic
                leave_date = timestamp
                filtered_data[-1] = (filtered_data[-1][0], filtered_data[-1][1], filtered_data[-1][2], leave_date)  # Update leave_date of the last (join date inverse)
                filtered_data.append((guild, rank, leave_date, None))  
                current_guild = guild

        # If the last entry is still in a guild make it a leave
        if current_guild is not None:
            filtered_data[-1] = (filtered_data[-1][0], filtered_data[-1][1], filtered_data[-1][2], earliest_timestamp)  # Update leave_date of the last entry

        # When only 1 entry in combined
        if len(combined_data) == 1:
            filtered_data[0] = (combined_data[0][0], combined_data[0][1], combined_data[0][2], None)  # Set join_date to None and leave_date to the timestamp

        # api call to update to most recent; its abit jank but works and is nice, not necessary though if u hate it
        def fetch_current_guild_info(username):
            api_url = f"https://api.wynncraft.com/v3/player/{username}?fullResult"
            response = requests.get(api_url)
            if response.status_code == 200:
                return response.json()
            return None

        current_guild_info = fetch_current_guild_info(username)
        if current_guild_info and 'guild' in current_guild_info:
            guild_info = current_guild_info['guild']
            if guild_info == 'null' or guild_info is None:
                current_guild_name = "None"
                current_guild_rank = "N/A"
            else:
                current_guild_name = guild_info.get("name", "N/A")
                current_guild_rank = guild_info.get("rank", "N/A")

            
            if filtered_data and filtered_data[0][0] != current_guild_name:
                filtered_data.insert(0, (current_guild_name, None, None, filtered_data[0][2])) #add joined date to match the leave date of last when nothing else is recorded
            
            if filtered_data and filtered_data[0][0] == current_guild_name:
                # dont touch the dates
                filtered_data[0] = (current_guild_name, current_guild_rank, filtered_data[0][2], filtered_data[0][3])
            else:
                filtered_data.insert(0, (current_guild_name, current_guild_rank, None, None)) #new one

        # table maker maker maker
        if filtered_data:
            len_g_name = max(len(x[0]) for x in filtered_data)
            len_rank = max(len(x[1]) for x in filtered_data)
            if len_rank == 0:
                len_rank == 5 #this literally doesnt work ill fix it one day 
            
            content += f'{"Guild":<{len_g_name+4}} | {"Rank":<{len_rank+4}} | {"Join Date":<22} | {"Leave Date":<22}\n'
            content += '-' * (separator_length) + '\n'

            for guild, rank, join_date, leave_date in filtered_data:
                rank = rank if rank else 'N/A'
                join_date_str = datetime.fromtimestamp(join_date).strftime("%d %b %Y %H:%M") if join_date else 'N/A'
                leave_date_str = datetime.fromtimestamp(leave_date).strftime("%d %b %Y %H:%M") if leave_date else 'N/A'
                content += f'{guild:<{len_g_name+4}} | {rank:<{len_rank+4}} | {leave_date_str:<22} | {join_date_str:<22}\n' #well aware these are inverted so sorry if anyone has to ever look back at this

        content += f"Query took {(time.time()-now):.5}s\n"

        await LongTextMessage.send_message(valor, ctx, title=f"Guild History of {username}", content=content, 
            code_block=True, code_type="ml")
        
    #copy of the old errors for -history
    @history.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed("How did an error even happen (player doesn't exist?"))
        raise error
    
    @valor.help_override.command()
    async def history(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "History", desc, color=0xFF00)
