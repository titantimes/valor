from valor import Valor
from discord.ext.commands import Context
from discord.ui import View
from discord import File
from datetime import datetime
import discord
import requests
from util import ErrorEmbed, LongTextEmbed
from commands.common import from_uuid


class GuildView(View):
    def __init__(self, guild):
        super().__init__()
        self.page = 0
        self.guild = guild

        self.max_page = 4

    
    @discord.ui.button(emoji="⬅️", row=1)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        if self.page <= 0:
            self.page = 0
            await interaction.response.send_message("You are at the first page!", ephemeral=True)
        else:
            await self.update(interaction)
    
    @discord.ui.button(emoji="➡️", row=1)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        if self.page >= self.max_page:
            self.page = self.max_page
            await interaction.response.send_message("You are at the last page!", ephemeral=True)
        else:
            await self.update(interaction)

    async def update(self, interaction: discord.Interaction):
        embed = await get_guild(self.guild, self.page)
        self.embed = embed

        await interaction.response.edit_message(embed=self.embed, view=self)
        
async def get_guild_page_one(guild, page, data):
    desc = f"""```
Name: {data["name"]} [{data["prefix"]}]
Level: {data["level"]} ({data["xpPercent"]}%)
Owner: {list(data["members"]["owner"])[0]}
Members: {data["members"]["total"]}
Territories: needs work
War Count: needs work
Created: {datetime.fromisoformat(data["created"]).strftime("%m/%d/%Y  %H:%M")}
```"""

    online = []

    for rank in data["members"]:
        if rank != "total":
            for member in data["members"][rank]:
                if data["members"][rank][member]["server"]:
                    online.append([member, data["members"][rank][member]["server"], rank])

    

    print(online)




    embed = discord.Embed(title=f"{data['name']}: Overview", description=desc, color=0x7785cc)
    embed.add_field(name="Online Members", value="salutations!")

    
    return embed



async def get_guild(valor, guild, page):
    res = requests.get("https://api.wynncraft.com/v3/guild/prefix/" + guild)

    if res.status_code != 200:
        return ErrorEmbed()
    
    data = res.json()

    if page == 0:
        embed = await get_guild_page_one(guild, page, data)

    


    embed.set_footer(text=f"Page {page+1} | Use arrows keys to switch between pages.")
    return embed


async def _register_guild(valor: Valor):
    desc = "Provides an overview of a guild"

    @valor.command()
    async def guild(ctx: Context, guild="ANO"):

        view = GuildView(guild)

        embed = await get_guild(valor, guild, 0)
        
        view.embed = embed

        await ctx.send(embed=view.embed, view=view)

    @guild.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def guild(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "guild", desc, color=0xFF00)
