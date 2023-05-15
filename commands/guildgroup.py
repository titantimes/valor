from sql import ValorSQL
from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, LongFieldEmbed
import commands.common
import os
import argparse
from dotenv import load_dotenv
from .common import guild_name_from_tag

load_dotenv()
TEST = os.getenv("TEST")=="TRUE"

async def _register_guildgroup(valor: Valor):
    desc = "Manages guild groups (e.g. alliances)"
    parser = argparse.ArgumentParser(description='GuildGroup command')
    parser.add_argument('-l', '--list', type=str) # single argument

    parser.add_argument('-gr', '--groups', action="store_true") # no args
    parser.add_argument('-r', '--remove', type=str)  # delete entries with group name

    parser.add_argument('-s', '--set', type=str) # single name for group name
    parser.add_argument('-g', '--guild', nargs='+') # list of guild tags ["ano", "avo", "esi"] 

    @valor.command()
    async def guildgroup(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Guild Groups", parser.format_help().replace("main.py", "-guildgroup"), color=0xFF00)
        
        if not commands.common.role1(ctx.author) and not TEST:
            return await ctx.send(embed=ErrorEmbed("No Permissions"))

        if opt.list:
            if "-" in opt.list:
                return await ctx.send(embed=ErrorEmbed("Invalid input")) # lazy sanitation
            guild_group_query = f"SELECT guild FROM guild_group WHERE guild_group='{opt.list.lower()}'"
            result = await ValorSQL._execute(guild_group_query)
            if result:
                content = '\n'.join(x[0] for x in result)
                await LongTextEmbed.send_message(valor, ctx, title=f"Guild Group of {opt.list}", content=content, color=0xFF10, code_block=True)
            else:
                await LongTextEmbed.send_message(valor, ctx, title=f"Guild Group of {opt.list}", content="Unknown group name", color=0xFF0010, code_block=True)

        elif opt.groups:
            guild_group_query = f"SELECT DISTINCT guild_group FROM guild_group"
            result = await ValorSQL._execute(guild_group_query)
            content = '\n'.join(x[0] for x in result)
            await LongTextEmbed.send_message(valor, ctx, title=f"Guild Group List", content=content, color=0xFF10, code_block=True)
        
        elif opt.remove:
            if "-" in opt.remove:
                return await ctx.send(embed=ErrorEmbed("Invalid input")) # lazy sanitation
            
            guild_group_query = f"DELETE FROM guild_group WHERE guild_group='{opt.remove.lower()}'"
            result = await ValorSQL._execute(guild_group_query)
            
            await LongTextEmbed.send_message(valor, ctx, title=f"Guild Group Delete", content=f"Removed {opt.remove}", color=0xFF10, code_block=True)

        elif opt.set:
            if "-" in opt.set:
                return await ctx.send(embed=ErrorEmbed("Invalid input")) # lazy sanitation
        
            if not opt.guild:
                return await LongTextEmbed.send_message(valor, ctx, title=f"Needs list of guild names", content="See help prompt. ex: -guilgroup -s group_name -g ano esi avo", color=0xFF0010, code_block=True)

            # remove old guild group
            guild_group_remove_query = f"DELETE FROM guild_group WHERE guild_group='{opt.set.lower()}'"
            result = await ValorSQL._execute(guild_group_remove_query)

            guild_names = [await guild_name_from_tag(x) for x in opt.guild]

            guild_group_query = f"INSERT INTO guild_group VALUES " + ','.join(f"('{opt.set.lower()}', '{x}')" for x in guild_names)
            result = await ValorSQL._execute(guild_group_query)
    
    @valor.help_override.command()
    async def guildgroup(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Guild Group", desc, color=0xFF00)
    
    
    