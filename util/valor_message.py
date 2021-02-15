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

class ErrorEmbed(discord.Embed):
    def __init__(self, err = "The command failed!"):
        super(ErrorEmbed, self).__init__(
            title = "Error!",
            description = err,
            color = 0xFF0000
        )
        self.set_footer(text="Scream at Andrew or Cal if something should be working")

class LongTextEmbed(discord.Embed):
    def __init__(self, title: str, content):
        if isinstance(content, str):
            self.content = content.split('\n')
        self.page = 1

        line_idx = 0
        lp = LongTextEmbed.find_linepair(self.content, line_idx)
        self.total_pages = int(math.ceil(len(self.content)/(lp[1]-lp[0])))
        self.line_pairs = []
        for i in range(self.total_pages):
            lp = LongTextEmbed.find_linepair(self.content, line_idx)
            self.line_pairs.append(lp)
            line_idx = lp[1]

        super(LongTextEmbed, self).__init__(
            title = title,
            description = '\n'.join(self.content[self.line_pairs[0][0]:self.line_pairs[0][1]])
        )
        self.set_footer(text="Page 1 of {}".format(self.total_pages))

    def forward_page(self):
        if self.page == self.total_pages:
            return
        lp = self.line_pairs[self.page]
        self.page += 1
        self.description = '\n'.join(self.content[lp[0]:lp[1]])
        self.set_footer(text="Page {} of {}".format(self.page, self.total_pages))
    
    def back_page(self):
        if self.page == 1:
            return
        self.page -= 1
        lp = self.line_pairs[self.page-1]
        self.description = '\n'.join(self.content[lp[0]:lp[1]])
        self.set_footer(text="Page {} of {}".format(self.page, self.total_pages))

    @staticmethod
    def find_linepair(content: List[str], start_line = 0, limit=1500) -> Tuple[int, int]:
        """
        Find the beginning line and ending line (not included) under maxlimit. This is due to
        discord's max char limit of 2000, so this is used to split messages into pages.
        returns indices [start_line, i)
        """
        cnt = 0
        i = start_line
        while i < len(content) and cnt < limit:
            cnt += len(content[i])
            i += 1

        return start_line, i

    @staticmethod
    def check(rxn: discord.Reaction, usr: discord.User) -> bool:
        return usr.id != SELF_ID and (str(rxn.emoji) == LEFT_PAGE_EMOJI or str(rxn.emoji) == RIGHT_PAGE_EMOJI)

    @abstractclassmethod
    async def send_message(cls, valor: Valor, ctx: Context, title: str, content="", color=0x000000):
        em: cls = cls(title, content)
        em.color = color
        msg: discord.Message = await ctx.send(embed=em)
        if em.total_pages <= 1:
            return
        await msg.add_reaction(LEFT_PAGE_EMOJI)
        await msg.add_reaction(RIGHT_PAGE_EMOJI)
        while True:
            try:
                rxn, usr = await valor.wait_for('reaction_add', timeout=60., check = LongTextEmbed.check)
            except:
                break
            else:
                if rxn.message.id != msg.id:
                    continue
                if str(rxn.emoji) == LEFT_PAGE_EMOJI:
                    em.back_page()
                    await msg.remove_reaction(LEFT_PAGE_EMOJI, usr)
                else:
                    em.forward_page()
                    await msg.remove_reaction(RIGHT_PAGE_EMOJI, usr)
                await msg.edit(embed=em)

class LongFieldEmbed(LongTextEmbed):
    # CONTENT MUST BE TUPLE LIST
    def __init__(self, title: str, content: List[Tuple[str, str]]):
        discord.Embed.__init__(self)
        self.page = 1
        self.content = content
        line_idx = 0
        lp = LongFieldEmbed.find_linepair(self.content, line_idx)
        self.total_pages = int(math.ceil(len(content)/(lp[1]-lp[0])))
        self.line_pairs = []
        for i in range(self.total_pages):
            lp = LongFieldEmbed.find_linepair(self.content, line_idx)
            self.line_pairs.append(lp)
            line_idx = lp[1]
        self.title = title
        for line in self.content[self.line_pairs[0][0]:self.line_pairs[0][1]]:
            self.add_field(name=line[0], value=line[1])
            
        self.set_footer(text="Page 1 of {}".format(self.total_pages))

    def forward_page(self):
        if self.page == self.total_pages:
            return
        self.clear_fields()
        lp = self.line_pairs[self.page]
        self.page += 1
        for line in self.content[lp[0]:lp[1]]:
            self.add_field(name=line[0], value=line[1])
        self.set_footer(text="Page {} of {}".format(self.page, self.total_pages))
    
    def back_page(self):
        self.clear_fields()
        if self.page == 1:
            return
        self.page -= 1
        lp = self.line_pairs[self.page-1]
        for line in self.content[lp[0]:lp[1]]:
            self.add_field(name=line[0], value=line[1])
        self.set_footer(text="Page {} of {}".format(self.page, self.total_pages))

    @classmethod
    def find_linepair(cls, content: List[Tuple[str, str]], start_line = 0, limit=1500, field_limit=24) -> Tuple[int, int]:
        """
        Find the beginning line and ending line (not included) under maxlimit. This is due to
        discord's max char limit of 2000, so this is used to split messages into pages.
        returns indices [start_line, i)
        """
        cnt = 0
        lcnt = 0
        i = start_line
        while i < len(content) and (cnt < limit and lcnt < field_limit):
            # update cnt with length of key and value
            # a single line counts as a lot more. so 50 lines of 'a' will take up tons of space
            lcnt += 1
            cnt += 0 if not content[i][0] else len(content[i][0]) + 0 if not content[i][1] else len(content[i][1]) 
            i += 1

        return start_line, i

    @classmethod
    async def send_message(cls, valor: Valor, ctx: Context, title: str, content, color=0xa1ffe1):
        await super(LongFieldEmbed, cls).send_message(valor, ctx, title, content, color)

    @staticmethod
    def check(rxn: discord.Reaction, usr: discord.User) -> bool:
        return usr.id != SELF_ID and (str(rxn.emoji) == LEFT_PAGE_EMOJI or str(rxn.emoji) == RIGHT_PAGE_EMOJI)
                
class HelpEmbed(LongTextEmbed):
    # singleton instance
    single_info: 'HelpEmbed' = None
    def __init__(self, content: str):
        super(HelpEmbed, self).__init__("Help Command", content)

    @classmethod
    def _help(cls, valor: Valor):
        """
        Sets static field to generated command information
        -online <guild>
        -test <this>
        """
        if not cls.single_info:
            cls.single_info = cls('\n'.join('-'+c.name+' '+c.signature for c in valor.commands))
        return cls.single_info
    
    @classmethod
    async def send_message(cls, valor: Valor, ctx: Context):
        em: HelpEmbed = cls._help(valor)
        msg: discord.Message = await ctx.send(embed=em)
        if em.total_pages <= 1:
            return
        await msg.add_reaction(LEFT_PAGE_EMOJI)
        await msg.add_reaction(RIGHT_PAGE_EMOJI)
        while True:
            try:
                rxn, usr = await valor.wait_for('reaction_add', timeout=60., check = LongTextEmbed.check)
            except:
                break
            else:
                if rxn.message.id != msg.id:
                    continue
                if str(rxn.emoji) == LEFT_PAGE_EMOJI:
                    em.back_page()
                    await msg.remove_reaction(LEFT_PAGE_EMOJI, usr)
                else:
                    em.forward_page()
                    await msg.remove_reaction(RIGHT_PAGE_EMOJI, usr)
                await msg.edit(embed=em)