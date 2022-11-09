from discord.ext import commands
import os
import json
from sql import ValorSQL
import asyncio
import aiomysql
import multiprocessing as mp
from dotenv import load_dotenv

load_dotenv()

class Valor(commands.Bot):
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
        
        async with super(Valor, self):
            self.reaction_msg_ids = dict(await ValorSQL.get_all_react_msg())
            super(Valor, self).start(self.BOT_TOKEN)
