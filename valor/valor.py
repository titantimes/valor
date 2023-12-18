import discord
import os
import json
from sql import ValorSQL
import multiprocessing as mp
import time
from valor import aiohttp_handler
from dotenv import load_dotenv

load_dotenv()

class Valor(discord.ext.commands.Bot):
    """
    Subclass of discord.ext.commands.Bot class holding additional information
    """

    def __init__(self, *args, **kwargs):
        self.BOT_TOKEN = os.environ["BOT_TOKEN"]
        # this is used to override the help command and then register the help subcommands for other commands
        self.help_override = None

        self.config = {
            "description": "A bot to help out with guild tasks."
        }

        self.endpoints = {

        }

        self.last_cmd_counts = []

        self.http = aiohttp_handler.HTTPHandler()

        manager = mp.Manager()
        self.db_lock = manager.Lock()

        # default configuration file is not found
        if not os.path.exists('config.json'):
            with open("config.json", 'w') as f:
                json.dump(self.config, f)
        else:
            with open("config.json", 'r') as f:
                self.config = json.load(f)

        # get all wynncraft endpoints
        with open("endpoints.json", 'r') as f:
            self.endpoints = json.load(f)

        with open('assets/warcount119.json', 'r') as f:
            self.warcount119 = json.load(f)

        super(Valor, self).__init__(*args, **kwargs, description=self.config["description"])

    async def run(self):
        self.reaction_msg_ids = dict(await ValorSQL.get_all_react_msg())
        await super(Valor, self).start(self.BOT_TOKEN)
    
    async def update_cmd_counts(self, server_id, server_name, discord_id, discord_name, full_command: str):
        cmd_str = full_command.split(' ')[0][1:]
        save_N = 10 # how many to buffer until db write
        valid_cmd_names = set(cmd.name for cmd in self.commands)
        if not cmd_str in valid_cmd_names: return
        
        now = time.time()
        self.last_cmd_counts.append((server_id, server_name, discord_id, discord_name, cmd_str, full_command, now))

        if len(self.last_cmd_counts) < save_N: return

        query = "INSERT INTO command_queries (server_id, server_name, discord_id, discord_name, command, full_command, time) VALUES "+\
            ("(%s, %s, %s, %s, %s, %s, %s),"*len(self.last_cmd_counts))[:-1]

        async with ValorSQL.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, [y for x in self.last_cmd_counts for y in x])
                await conn.commit()

        self.last_cmd_counts.clear()

