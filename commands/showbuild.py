from valor import Valor
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed

async def _register_showbuild(valor: Valor):
    desc = "Reveals wynnbuilder links as an embed... because wynnbuilder doesn't have meta tags for em."
    @valor.command()
    async def showbuild(ctx: Context, link: str):
        if not link.startswith("https://wynnbuilder.github.io/") and not link.startswith("https://hppeng-wynn.github.io/"):
            raise Exception("Invalid Wynnbuilder link.")
        link = link[link.find('#'):]
        build = info(link)
        await LongFieldEmbed.send_message(valor, ctx, "WynnBuilder build", build)
    
    @valor.help_override.command()
    async def showbuild(ctx: Context):
        await ctx.send(desc)