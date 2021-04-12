import requests
from valor import Valor
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, CURRENCY_CODES
from discord.ext.commands import Context
from dotenv import load_dotenv
import os

load_dotenv()
async def _register_coin(valor: Valor):
    desc = "Performs a currency conversion. Example -coin usd eur 5. Do -coin list to list all supported currencies"
    @valor.command()
    async def coin(ctx: Context, coin1="", coin2="", amt = 1):
        coin1 = coin1.upper()
        coin2 = coin2.upper()
        if not coin1:
            return await LongTextEmbed.send_message(valor, ctx, "Coin Conversion", f"`{desc}`", 0xFF00)
        elif coin1 == "LIST":
            return await LongTextEmbed.send_message(valor, ctx, "Currency Exchange List", 
                '\n'.join("`%20s | %20s`" % (x[0], x[1]) for x in CURRENCY_CODES), 0xFF10)
        if not coin2:
            return await ctx.send(embed=ErrorEmbed("Please specify a target currency"))
        res = requests.get(f"https://api.ofx.com/PublicSite.ApiService/OFX/spotrate/Individual/{coin1}/{coin2}/1?format=json")
        if res.status_code != 200:
            return await ctx.send(embed=ErrorEmbed("Command failed. Do -coin to see what this is about"))
        res = res.json()
        if "do not" in res["Message"]:
             return await ctx.send(embed=ErrorEmbed("Currency code is incorrect. Check if you typed it in correctly"))
        content = f"**{amt}** {coin1} ➜ **{round(res['InterbankRate']*amt, 4)}** {coin2}" 
        await LongTextEmbed.send_message(valor, ctx, f"{coin1} **➜** {coin2}", content, color=0xFF10)
    
    @coin.error
    async def coin_error(ctx, error):
        await ctx.send(embed=ErrorEmbed("Command failed. Do -coin to see what this is about"))
        raise error
    
    @valor.help_override.command()
    async def coin(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Coin", desc, color=0xFF00)