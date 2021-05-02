import discord
from discord.ext.commands import Context
from typing import List, Tuple
from .constants import LEFT_PAGE_EMOJI, RIGHT_PAGE_EMOJI
from valor import Valor
from abc import abstractclassmethod
import math
import os
from dotenv import load_dotenv

load_dotenv()
SELF_ID = int(os.environ["SELFID"])

class ReactionEmbed(discord.Embed):
    def __init__(self, title: str, content: str, reactions: List[str], **kwargs):
        super(ReactionEmbed, self).__init__(
            title = title,
            description = content,
            **kwargs
        )

        self.set_footer(text="Valor")
        self.reactions= reactions

    @classmethod
    async def send_message(cls, valor: Valor, ctx: Context, title: str, content="", color=0x000000, file="", url="", reactions=[], **kwargs):
        em: cls = cls(title, content, reactions, **kwargs)

        if url:
            em.set_image(url=url)

        em.color = color
        msg: discord.Message

        if file:
            msg = await ctx.send(file=file, embed=em)
        else:

            msg = await ctx.send(embed=em)

        for react_id in em.reactions:
            await msg.add_reaction(react_id if len(react_id) == 1 else valor.get_emoji(int(react_id)))

        return msg

