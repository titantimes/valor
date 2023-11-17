import json
from valor import Valor
import discord
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed
from sql import ValorSQL
import time
import os
from dotenv import load_dotenv

load_dotenv()
async def _register_msg_listiner(valor: Valor):
    cooldown = {}
    with open("assets/strat.json") as f:
        strat_stages = json.load(f)
    @valor.event
    async def on_message(message: discord.Message):
        # if "https://wynnbuilder.github.io/#" in message.content or \
        #     "https://hppeng-wynn.github.io/#" in message.content:
        #     # Disable this feature. It's no longer wanted
        #     return

        #     usr_conf = ValorSQL.get_user_config(message.author.id)
        #     if not usr_conf.get("wynnbuilder"):
        #         return
        #     link = message.content
        #     pos = link.find(".github.io/#")+len(".github.io/#")-1
        #     ending = link[pos:].find(' ')
        #     # make sure to also handle newlines
        #     a = link[pos:].find('\n')
        #     if a != -1 and a < ending:
        #         ending = a
        #     link = link[pos:][:ending]
        #     build = info(link)
        #     ctx = await valor.get_context(message)
        #     return await LongFieldEmbed.send_message(valor, ctx, "WynnBuilder build", build)
        # if len(message.content) and message.content[0] == '-':
        #     now = time.time()
        #     ctx = await valor.get_context(message)
        #     if now-cooldown.get(message.author.id, 0) <= 2:
        #         await ctx.send(embed=ErrorEmbed("Please don't spam commands :). The cooldown is 2 seconds"))
        #     else:
        #         cooldown[message.author.id] = now

        # for application processing
        apps = {"app", "cpt", "spir", "bril", "fury"}
        if message.author.id != int(os.environ["SELFID"]) and (message.channel.name.split('-')[0] in apps):
            config = (await ValorSQL.get_server_config(message.guild.id))[0]
            if message.channel.category_id == config[1] and message.author.id == int(message.channel.topic):
                ctx = await valor.get_context(message)
                msg = await ctx.send(embed=LongTextEmbed("Click the green checkmark below to submit", "Send your application again if you messed up.\n**Your most recent message will be submitted**", color=0xFFFF, footer=f"Valor - {message.id}"))
                await msg.add_reaction('✅')
            
        if message.author.id != int(os.environ["SELFID"]) and (message.channel.name.split('-')[0] == "strat"):
            # chn topic should be usr_id,stage
            config = (await ValorSQL.get_server_config(message.guild.id))[0]
            taker_id, stage = message.channel.topic.split(',')
            taker_id = int(taker_id)

            if message.author.id != taker_id: return
            
            ctx = await valor.get_context(message)

            if stage == "3":
                msg = await ctx.send(embed=LongTextEmbed("Click the checkmark to finish (3/3)", "**Your most recent message will be used for this section**", color=0xFFFF, footer=f"Valor - {message.id}"))
                await msg.add_reaction('✅')
            else:
                ctx = await valor.get_context(message)
                msg = await ctx.send(embed=LongTextEmbed(f"Click the checkmark to proceed ({stage}/3)", "**Your most recent message will be used for this section**", color=0xFFFF, footer=f"Valor - {message.id}"))
                await msg.add_reaction('✅')
            
 
        # server specific
        if message.channel.id == 679447964665774101:
            # sloppy heuristics
            if message.content.count("\n") > 3:
                await message.add_reaction(valor.get_emoji(849394540057985134))
                await message.add_reaction('❌')

        # slash commands need to be considered separately
        if message.content.startswith('-') and (os.getenv("TEST") != "TRUE"):
            await valor.update_cmd_counts(message.channel.guild.id, 
                                          message.channel.guild.name, message.author.id, message.author.name, message.content) # let the bot class handle non commands

        await valor.process_commands(message)
