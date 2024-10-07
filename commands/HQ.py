import discord
import discord.ext
from discord.ext import commands
from discord.ext.commands import Context
from valor import Valor



#error embed
class ErrorEmbed(discord.Embed):
    def __init__(self):
        super().__init__(title="Error", description="Try the command as -HQ CONNECTIONS EXTERNALS, so -HQ 6 18", color=discord.Color.red())


async def _register_HQ(valor: Valor):
    desc = "Displays stats of an HQ at specified conns/exts"
    #HQ conn calculator
    @valor.command(name='HQ', aliases=['hq', 'Hq', 'hQ'])
    async def HQ(ctx: Context, conns: str = None, externals: str = None):
        if conns is None or externals is None:
            await ctx.send(embed=ErrorEmbed())
            return
        try:
            conns = int(conns)
            externals = int(externals)
            HP = round(int(3300000 * (1.5 + (0.25 * (conns + externals)))) * (1.0 +(0.3*conns)))
            Damage_low = round(int(5400 * (1.5 + (0.25 * (conns + externals)))) * (1.0 +(0.3*conns)))
            Damage_high = round(int(Damage_low*1.5))
            DPS = ((2*Damage_low)*4.7)
            ehp = HP*10

            embed = discord.Embed(title=f"""HQ with {conns} connections and {externals} externals\n""", description=None, color=0x11FFBB)
            embed.add_field(name="", value=f"HP: {HP:,}\n Damage: {Damage_low:,}-{Damage_high:,}\n Defence 90% \n Attack Speed 4.7x \n \n EHP: {ehp:,}\n DPS: {DPS:,}", inline=False,)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=ErrorEmbed())
            print(f"Error: {e}")

    # 3.3mil base hp? (HP or Damange*(100+25*26+50)*(1.3*6), base damage 5400

