import discord
import os
import json

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

    def run(self):
        super(Valor, self).run(self.BOT_TOKEN)
