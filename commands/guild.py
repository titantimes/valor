from valor import Valor
from discord.ext.commands import Context
from discord.ui import View
from discord import File
from datetime import datetime
import discord
import requests
from sql import ValorSQL
from util import ErrorEmbed, LongTextEmbed
from commands.common import from_uuid


class GuildView(View):
    def __init__(self, guild):
        super().__init__()
        self.page = 0
        self.guild = guild

        self.max_page = 2

    
    @discord.ui.button(emoji="⬅️", row=1)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        if self.page < 0:
            self.page = 0
            await interaction.response.send_message("You are at the first page!", ephemeral=True)
        else:
            await self.update(interaction)
    
    @discord.ui.button(emoji="➡️", row=1)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        if self.page > self.max_page:
            self.page = self.max_page
            await interaction.response.send_message("You are at the last page!", ephemeral=True)
        else:
            await self.update(interaction)

    async def update(self, interaction: discord.Interaction):
        embed = await get_guild(self.guild, self.page)
        self.embed = embed

        await interaction.response.edit_message(embed=self.embed, view=self)
        
async def get_guild_page_one(data):
    desc = f"""```properties
Name: {data["name"]} [{data["prefix"]}]
Level: {data["level"]} ({data["xpPercent"]}%)
Owner: {list(data["members"]["owner"])[0]}
Members: {data["members"]["total"]}
Territories: {data["territories"]}
War Count: {data["wars"]}
Created: {datetime.fromisoformat(data["created"][:-1]).strftime("%m/%d/%Y  %H:%M")}
```"""

    online = []

    for rank in data["members"]:
        if rank != "total":
            for member in data["members"][rank]:
                if data["members"][rank][member]["server"]:
                    online.append([member, rank, data["members"][rank][member]["server"]])

    rank_dict = {
        "recruit": "",
        "recruiter": "*",
        "captain": "**",
        "strategist": "***",
        "chief": "****",
        "owner": "*****"
    }

    if online:
        online_desc = "```isbl\n"
        online_desc += "Name            ┃ Rank  ┃ World\n"
        online_desc += "━━━━━━━━━━━━━━━━╋━━━━━━━╋━━━━━━\n"
        for player in online:
            t = player[0]
            t += (16 - len(player[0])) * " "
            t += "┃ " + rank_dict[player[1]]
            t += (5 - len(rank_dict[player[1]])) * " "
            t += " ┃ " + player[2] + "\n"
            
            online_desc += t
        online_desc += "```"
    else:
        online_desc = "```There are no members currently online```"

    embed = discord.Embed(title=f"{data['name']}: Overview", description=desc, color=0x7785cc)
    embed.add_field(name="Online Members", value=online_desc)

    
    return embed


async def get_guild_page_two(data):
    res = await ValorSQL._execute(f"""
SELECT A.name, SUM(C.warcount) AS wars
FROM
  uuid_name A NATURAL JOIN guild_member_cache B
  LEFT JOIN cumu_warcounts C ON A.uuid=C.uuid
GROUP BY B.guild, A.name
HAVING B.guild IN ("{data["name"]}")
ORDER BY wars DESC;""")
    warcounts = {}
    for pair in res:
        warcounts[pair[0]] = str(pair[1])  

    embed = discord.Embed(title=f"{data['name']}: Members", color=0x7785cc)

    for rank in data["members"]:
        if rank != "total":
            rank_desc = "Name            ┃   Joined   ┃  Wars \n"
            rank_desc += "━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━\n"
            for player in data["members"][rank]:
                try:
                    warcount = warcounts[player]
                except KeyError:
                    warcount = "0"

                t = player
                t += (16 - len(player)) * " "
                t += "┃ " + datetime.fromisoformat(data["members"][rank][player]["joined"][:-1]).strftime("%m/%d/%Y")
                t += " ┃ " + warcount + ((5 - len(warcount)) * " ") + "\n"
                
                rank_desc += t

            rank_name = f"{rank.capitalize()} ({len(data['members'][rank])})"
            if len(rank_desc) > 926:
                descriptions = [rank_desc[i:i+926] for i in range(0, len(rank_desc), 926)]
                embed.add_field(name=rank_name, value="```isbl\n" + descriptions[0] + "```")
                descriptions.pop(0)

                for desc in descriptions:
                    embed.add_field(name ="", value="```isbl\n" + desc + "```", inline=False)
            else:
                embed.add_field(name=rank_name, value="```isbl\n" + rank_desc + "```", inline=False)
    
    return embed


async def get_guild_page_three(data):
    embed = discord.Embed(title=f"{data['name']}: XP Contributions", color=0x7785cc)

    xp_table = []
    for rank in data["members"]:
        if rank != "total":
            for player in data["members"][rank]:
                xp_table.append([player, rank, data["members"][rank][player]["contributed"]])

    xp_table = sorted(xp_table, key=lambda x: x[2], reverse=True)

    i = 1

    gxp_desc = "     ┃Name             ┃ XP                 \n"
    gxp_desc += "━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━\n"
    for player in xp_table:

        t = str(i) + ")" + ((4 - len(str(i))) * " ") + "┃ "

        t += player[0]
        t += ((16 - len(player[0])) * " ")
        xp = "{:,}".format(data["members"][player[1]][player[0]]["contributed"])
        t += "┃ " + xp + " xp"
        t += ((16 - len(xp)) * " ") + "\n"
        
        gxp_desc += t
        i += 1

    descriptions = [gxp_desc[i:i+990] for i in range(0, len(gxp_desc), 990)]

    for desc in descriptions:
        embed.add_field(name ="", value="```isbl\n" + desc + "```", inline=False)
    
    return embed


async def get_guild(guild, page):
    res = requests.get("https://api.wynncraft.com/v3/guild/prefix/" + guild)

    if res.status_code != 200:
        return ErrorEmbed()
    
    data = res.json()

    if page == 0:
        embed = await get_guild_page_one(data)
    elif page == 1:
        embed = await get_guild_page_two(data)
    elif page == 2:
        embed = await get_guild_page_three(data)

    
    embed.set_footer(text=f"Page {page+1} | Use arrows keys to switch between pages.")
    return embed


async def _register_guild(valor: Valor):
    desc = "Provides an overview of a guild"

    @valor.command(aliases=["g"])
    async def guild(ctx: Context, guild="ANO"):

        view = GuildView(guild)

        embed = await get_guild(guild, 0)
        
        view.embed = embed

        await ctx.send(embed=view.embed, view=view)

    @guild.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def guild(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "guild", desc, color=0xFF00)
