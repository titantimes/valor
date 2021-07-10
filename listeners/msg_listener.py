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
        if message.author.id != int(os.environ["SELFID"]) and (message.channel.name.startswith("app") or message.channel.name.startswith("cpt") or
            message.channel.name.startswith("strat")):
            config = ValorSQL.get_server_config(message.guild.id)[0]
            if message.channel.category_id == config[1]:
                ctx = await valor.get_context(message)
                msg = await ctx.send(embed=LongTextEmbed("Click the green checkmark below to submit", "Send your application again if you messed up.\n**Your most recent message will be submitted**", color=0xFFFF, footer=f"Valor - {message.id}"))
                await msg.add_reaction('✅')
                
        # server specific
        if message.channel.id == 679447964665774101:
            # sloppy heuristics
            if message.content.count("\n") > 3:
                await message.add_reaction(valor.get_emoji(849394540057985134))
                await message.add_reaction('❌')
        await valor.process_commands(message)
