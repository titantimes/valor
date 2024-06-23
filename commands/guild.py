from valor import Valor
from discord.ext.commands import Context
from discord.ui import View
from discord import File
from datetime import datetime
import discord
import requests
from sql import ValorSQL
from util import ErrorEmbed, LongTextEmbed, LongTextTable
from commands.common import get_left_right
import time
import argparse

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

def break_description(desc, length):
    lines = desc.split("\n")
    descriptions = []
    current_field = ""
    for line in lines:
        if len(current_field) + len(line) + 1 > length:
            descriptions.append(current_field)
            current_field = line
        else:
            current_field += "\n" + line
    if current_field:
        descriptions.append(current_field)

    return descriptions
        
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

    gxp_desc = "     ┃Name             ┃ XP            \n"
    gxp_desc += "━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━\n"
    for player in xp_table:

        t = str(i) + ")" + ((4 - len(str(i))) * " ") + "┃ "

        t += player[0]
        t += ((16 - len(player[0])) * " ")
        xp = str(data["members"][player[1]][player[0]]["contributed"])
        t += "┃ " + xp
        t += ((16 - len(xp)) * " ") + "\n"
        
        gxp_desc += t
        i += 1

    descriptions = break_description(gxp_desc, 990)

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

    embed.set_footer(text=f"Page {page+1} | Use arrow buttons to switch between pages.")

    # 500x1 transparent image for embed width
    embed.set_image(url="https://cdn.discordapp.com/attachments/703019604968210482/1254483589362618518/placeholder.png")
    return embed


async def _register_guild(valor: Valor):
    desc = "Provides an overview of a guild"
    parser = argparse.ArgumentParser(description='Guild command')
    parser.add_argument('-f', '--feature', type=str, default=None)
    parser.add_argument('-r', '--range', nargs='+', default=None)

    @valor.command(aliases=["g"])
    async def guild(ctx: Context, *options):
        if len(options) < 2:
            # default to c0rupted's feature otherwise start argparsing 
            options = "ANO" if not options else options[0]
            view = GuildView(options)
            embed = await get_guild(options, 0)
            view.embed = embed
            return await ctx.send(embed=view.embed, view=view)
        
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Guild", parser.format_help().replace("main.py", "-guild"), color=0xFF00)
        
        template_query = """
        SELECT 
            ROW_NUMBER() OVER(ORDER BY %s DESC),
            tag,
            guild, 
            `level`,
            CASE 
                WHEN ABS(delta_gxp) >= 1e12 THEN CONCAT(ROUND(delta_gxp / 1e12, 1), 'T') 
                WHEN ABS(delta_gxp) >= 1e9 THEN CONCAT(ROUND(delta_gxp / 1e9, 1), 'B')
                WHEN ABS(delta_gxp) >= 1e6 THEN CONCAT(ROUND(delta_gxp / 1e6, 1), 'M') 
                WHEN ABS(delta_gxp) >= 1e3 THEN CONCAT(ROUND(delta_gxp / 1e3, 1), 'K')
                ELSE gxp
            END AS delta_gxp_s,  
            CASE 
                WHEN ABS(gxp) >= 1e12 THEN CONCAT(ROUND(gxp / 1e12, 1), 'T') 
                WHEN ABS(gxp) >= 1e9 THEN CONCAT(ROUND(gxp / 1e9, 1), 'B')
                WHEN ABS(gxp) >= 1e6 THEN CONCAT(ROUND(gxp / 1e6, 1), 'M') 
                WHEN ABS(gxp) >= 1e3 THEN CONCAT(ROUND(gxp / 1e3, 1), 'K')
                ELSE gxp
            END AS gxp_s
        FROM
            (SELECT D.tag, C.guild, delta_gxp, `level`, gxp
            FROM
                (SELECT A.guild, A.delta_gxp, CAST(TRUNCATE(B.level, 0) AS UNSIGNED) AS `level`, 885689*EXP(0.139808*`level`) AS gxp
                FROM
                    (SELECT guild, SUM(delta) delta_gxp
                    FROM
                        player_delta_record
                    WHERE `time` >= %%s AND `time` <= %%s AND label="gu_gxp" 
                    GROUP BY guild
                    ORDER BY delta_gxp DESC LIMIT 100) A
                    LEFT JOIN
                    guild_autotrack_active B ON A.guild=B.guild) C
                LEFT JOIN guild_tag_name D ON C.guild=D.guild) E
        ORDER BY %s DESC;
        """

        t_start = time.time()
        if opt.range:
            # opt.range = [2e9, 0]
            valid_range = await get_left_right(opt, t_start)
            if valid_range == "N/A":
                return await ctx.send(embed=ErrorEmbed("Invalid season name input"))
            t_left, t_right = valid_range
        else:
            t_left, t_right = t_start - 3600*24, t_start

        query = None

        if opt.feature == "xp":
            # past 24 hour gained per guild see >g xp
            query = template_query % ('delta_gxp', 'delta_gxp') 
        elif opt.feature == "levelrank":
            # see >g levelrank
            query = template_query % ('`level`', '`level`') 
        elif opt.feature == "globalxp":
            query = template_query % ('`gxp`', '`gxp`') 
        else:
            return ctx.send(ErrorEmbed("-f options are xp, levelrank, and globalxp"))
        
        rows = await ValorSQL.exec_param(query, (t_left, t_right))
        delta_time = time.time() - t_start
        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}"
        header = ['   ',  " Tag ", " "*16+"Guild ", " Level ", " XP Gain ", " Total XP "]

        return await LongTextTable.send_message(valor, ctx, header, rows, opt_after)

    @guild.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def guild(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "guild", desc, color=0xFF00)
