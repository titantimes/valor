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

class LongTextTable:
    def __init__(self, header: Tuple[str], content: List[Tuple[str]], opt_after="", limit=1000): # code blocks always true for tables content should all be strings
        self.fmt = ' | '.join(f"%{len(x)}s" for x in header)
        self.header_str = self.fmt % tuple(header)
        self.opt_after = opt_after

        self.content = [self.fmt % tuple(line) for line in content]
        self.table_bar = ''.join('+' if x == '|' else '-' for x in self.header_str)

        self.page = 1
        line_idx = 0
        lp = LongTextEmbed.find_linepair(self.content, line_idx, limit)
        self.total_pages = int(math.ceil(len(self.content)/(lp[1]-lp[0])))
        self.line_pairs = []
        for i in range(self.total_pages):
            lp = LongTextEmbed.find_linepair(self.content, line_idx, limit)
            self.line_pairs.append(lp)
            line_idx = lp[1]

        self.description = '\n'.join(self.content[self.line_pairs[0][0]:self.line_pairs[0][1]])
        self.description = '```'+self.header_str+'\n'+self.table_bar+'\n'+self.description+'\n'+self.table_bar+'\n'+self.opt_after+'```'

    def forward_page(self):
        if self.page == self.total_pages:
            return
        lp = self.line_pairs[self.page]
        self.page += 1
        self.description = '\n'.join(self.content[lp[0]:lp[1]])
        self.description = '```'+self.header_str+'\n'+self.table_bar+'\n'+self.description+'\n'+self.table_bar+'\n'+self.opt_after+'```'

    def back_page(self):
        if self.page == 1:
            return
        self.page -= 1
        lp = self.line_pairs[self.page-1]
        self.description = '\n'.join(self.content[lp[0]:lp[1]])
        self.description = '```'+self.header_str+'\n'+self.table_bar+'\n'+self.description+'\n'+self.table_bar+'```'

    @classmethod
    async def send_message(cls, valor: Valor, ctx: Context, header, content="", opt_after=""):
        msg_txt: cls = cls(header, content, opt_after)

        msg: discord.Message = await ctx.send(msg_txt.description)

        if msg_txt.total_pages <= 1:
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
                    msg_txt.back_page()
                    await msg.remove_reaction(LEFT_PAGE_EMOJI, usr)
                else:
                    msg_txt.forward_page()
                    await msg.remove_reaction(RIGHT_PAGE_EMOJI, usr)
                await msg.edit(content=msg_txt.description)

class LongTextMessage:
    def __init__(self, title: str, content, limit=1700, code_block=False, code_type=""):
        if isinstance(content, str):
            self.content = content.split('\n')
        self.page = 1
        self.code_block = code_block
        self.code_type = code_type

        line_idx = 0
        lp = LongTextEmbed.find_linepair(self.content, line_idx)
        self.total_pages = int(math.ceil(len(self.content)/(lp[1]-lp[0])))
        self.line_pairs = []
        for i in range(self.total_pages):
            lp = LongTextEmbed.find_linepair(self.content, line_idx, limit)
            self.line_pairs.append(lp)
            line_idx = lp[1]

        self.description = '\n'.join(self.content[self.line_pairs[0][0]:self.line_pairs[0][1]])
        if code_block:
            self.description = f'```{self.code_type}\n'+self.description+'```'

    def forward_page(self):
        if self.page == self.total_pages:
            return
        lp = self.line_pairs[self.page]
        self.page += 1
        self.description = '\n'.join(self.content[lp[0]:lp[1]])
        if self.code_block:
            self.description = f'```{self.code_type}\n'+self.description+'```'

    def back_page(self):
        if self.page == 1:
            return
        self.page -= 1
        lp = self.line_pairs[self.page-1]
        self.description = '\n'.join(self.content[lp[0]:lp[1]])
        if self.code_block:
            self.description = f'```{self.code_type}\n'+self.description+'```'

    @classmethod
    async def send_message(cls, valor: Valor, ctx: Context, title: str, content="", **kwargs):
        msg_txt: cls = cls(title, content, **kwargs)

        msg: discord.Message = await ctx.send(msg_txt.description)

        if msg_txt.total_pages <= 1:
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
                    msg_txt.back_page()
                    await msg.remove_reaction(LEFT_PAGE_EMOJI, usr)
                else:
                    msg_txt.forward_page()
                    await msg.remove_reaction(RIGHT_PAGE_EMOJI, usr)
                await msg.edit(content=repr(msg_txt))

    def __repr__(self):
        return self.description

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

class LongTextEmbed(discord.Embed):
    def __init__(self, title: str, content, limit=3000, code_block=False, footer=None, code_type="", **kwargs):
        if isinstance(content, str):
            self.content = content.split('\n')
        self.page = 1
        self.code_block = code_block
        self.code_type = code_type

        line_idx = 0
        lp = LongTextEmbed.find_linepair(self.content, line_idx)
        self.total_pages = int(math.ceil(len(self.content)/(lp[1]-lp[0])))
        self.line_pairs = []
        for i in range(self.total_pages):
            lp = LongTextEmbed.find_linepair(self.content, line_idx, limit)
            self.line_pairs.append(lp)
            line_idx = lp[1]

        description = '\n'.join(self.content[self.line_pairs[0][0]:self.line_pairs[0][1]])
        if code_block:
            description = f'```{code_type}'+description+'```'

        super(LongTextEmbed, self).__init__(
            title = title,
            description = description,
            **kwargs
        )
        if not footer:
            self.set_footer(text="Page 1 of {}".format(self.total_pages))
        else:
            self.set_footer(text=footer)

    def forward_page(self):
        if self.page == self.total_pages:
            return
        lp = self.line_pairs[self.page]
        self.page += 1
        self.description = '\n'.join(self.content[lp[0]:lp[1]])
        if self.code_block:
            self.description = f'```{self.code_type}\n'+self.description+'```'
        self.set_footer(text="Page {} of {}".format(self.page, self.total_pages))
    
    def back_page(self):
        if self.page == 1:
            return
        self.page -= 1
        lp = self.line_pairs[self.page-1]
        self.description = '\n'.join(self.content[lp[0]:lp[1]])
        if self.code_block:
            self.description = f'```{self.code_type}\n'+self.description+'```'
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
    async def send_message(cls, valor: Valor, ctx: Context, title: str, content="", color=0x000000, file="", url="", reply=False, **kwargs):
        em: cls = cls(title, content, **kwargs)
        if url:
            em.set_image(url=url)
        em.color = color
        msg: discord.Message
        if file:
            if reply:
                msg = await ctx.message.reply(file=file, embed=em)
            else:
                msg = await ctx.send(file=file, embed=em)
        else:
            if reply:
                msg =await ctx.message.reply(embed=em)
            else:
                msg = await ctx.send(embed=em)
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
    def __init__(self, title: str, content: List[Tuple[str, str]], **kwargs):
        discord.Embed.__init__(self, **kwargs)
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
        if self.page == 1:
            return
        self.clear_fields()
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
    async def send_message(cls, valor: Valor, ctx: Context, title: str, content, color=0xa1ffe1, file="", **kwargs):
        await super(LongFieldEmbed, cls).send_message(valor, ctx, title, content, color, file, kwargs)

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