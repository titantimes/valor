from valor import Valor
import discord
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed
from sql import ValorSQL

async def _register_msg_listiner(valor: Valor):
    @valor.event
    async def on_message(message: discord.Message):
        if "https://wynnbuilder.github.io/#" in message.content or \
            "https://hppeng-wynn.github.io/#" in message.content:
            usr_conf = ValorSQL.get_user_config(message.author.id)
            if not usr_conf.get("wynnbuilder"):
                return
            link = message.content
            pos = link.find(".github.io/#")+len(".github.io/#")-1
            link = link[pos:link[pos:].find(' ')]
            build = info(link)
            ctx = await valor.get_context(message)
            return await LongFieldEmbed.send_message(valor, ctx, "WynnBuilder build", build)
        await valor.process_commands(message)
