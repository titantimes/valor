from valor import Valor
import discord
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed
import time
from sql import ValorSQL
from dotenv import load_dotenv
import os

load_dotenv()

async def _register_react_listener(valor: Valor):
    @valor.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        # REQUIRES MEMBER INTENT TO BE ENABLED IN DISCORD SETTINGS
        msg_id = payload.message_id
        if payload.user_id != int(os.environ["SELFID"]) and valor.reaction_msg_ids.get(msg_id, 0) > int(time.time()):
            emoji = str(payload.emoji)
            if len(emoji) == 1:
                emoji = ord(emoji)
            else:
                emoji = int(emoji.split(":")[-1][:-1])
            res = ValorSQL.get_react_msg_reaction(msg_id,  emoji)
            print(res)