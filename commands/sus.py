from valor import Valor
from discord import Embed, File
from discord.ext.commands import Context
from util import ErrorEmbed, LongTextEmbed, HelpEmbed, LongFieldEmbed
import requests
import datetime
import time
import uuid
import os
from sql import ValorSQL


async def _register_sus(valor: Valor):
    desc = "Determines if a user is sus by checking factors from various minecraft servers."

    @valor.command()
    async def sus(ctx: Context, username):
        res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
        if res.status_code != 200:
            return await ctx.send(embed=ErrorEmbed("Mojang API Issue"))
        id = res.json()["id"]
        name = res.json()["name"]
        dashed_uuid = str(uuid.UUID(hex=id))

        headers = {'user-agent': 'ano_valor/0.0.0',"API-Key":os.environ["HYPIXEL_API_KEY"]}
        hypixel_data = requests.get(f"https://api.hypixel.net/player?uuid={id}", headers=headers).json()
        hypixel_join = None
        if hypixel_data["success"] and "player" in hypixel_data and "firstLogin" in hypixel_data["player"]:
            hypixel_join = float(int(hypixel_data["player"]["firstLogin"] / 1000))

        wynn_data = requests.get(f"https://api.wynncraft.com/v3/player/{dashed_uuid}?fullResult").json()
        if "username" not in wynn_data:
            return await ctx.send(embed=ErrorEmbed("Wynn API Issue"))
        wynn_join = wynn_data["firstJoin"].split("T")[0]
        wynn_join_timestamp = time.mktime(datetime.datetime.strptime(wynn_join, "%Y-%m-%d").timetuple())
        # wynn_rank = "VETERAN" if wynn_data["meta"]["veteran"] else wynn_data["meta"]["tag"]["value"]
        wynn_rank = wynn_data["supportRank"]
        wynn_level = sum([character["level"] for _, character in wynn_data["characters"].items()])
        wynn_playtime = wynn_data["playtime"]
        wynn_quest = wynn_data["globalData"]["completedQuests"]

        first_seen = min(hypixel_join, wynn_join_timestamp) if hypixel_join else wynn_join_timestamp
        first_seen_time = datetime.date.fromtimestamp(first_seen).strftime("%Y-%m-%d")
        first_seen_sus = round(max(0, (time.time() - first_seen - 94672800) * -1) * 100 / 94672800, 1)
        

        wynn_join_sus = round(max(0, (time.time() - wynn_join_timestamp - 63072000) * -1) * 100 / 63072000, 1)
        wynn_level_sus = round(max(0, (wynn_level - 210) * -1) * 100 / 210, 1)
        wynn_playtime_sus = round(max(0, (wynn_playtime - 800) * -1) * 100 / 800, 1)
        wynn_quest_sus = round(max(0, (wynn_quest - 150) * -1) * 100 / 150, 1)

        # tweedle dum blacklist check
        query = f"SELECT * FROM player_blacklist WHERE uuid='{dashed_uuid}'"
        blacklisted = await ValorSQL._execute(query)
        if blacklisted:
            blacklisted = "**BLACKLISTED**"
            blacklisted_sus = 100.0
        else:
            blacklisted = "False"
            blacklisted_sus = 0
        
        if wynn_rank == "veteran" or wynn_rank == "champion" or wynn_rank == "hero" or wynn_rank == "vipplus":
            wynn_rank_sus = 0.0
        elif wynn_rank == "vip":
            wynn_rank_sus = 25.0
        else:
            wynn_rank_sus = 50.0

        overall_sus = round((first_seen_sus + wynn_join_sus + wynn_level_sus + wynn_playtime_sus + wynn_quest_sus + wynn_rank_sus) / 6, 2)

        embed=Embed(title=f"Suspiciousness of {name}: {overall_sus}%", description="The rating is based on the following components:", color=0x00ff2a)
        embed.set_thumbnail(url=f"https://visage.surgeplay.com/bust/512/{id}.png?y=-40")
        embed.add_field(name="Wynncraft Join Date", value=f"{wynn_join}\n{wynn_join_sus}%", inline=True)
        embed.add_field(name="Wynncraft Playtime", value=f"{wynn_playtime} hours\n{wynn_playtime_sus}%", inline=True)
        embed.add_field(name="Wynncraft Level", value=f"{wynn_level}\n{wynn_level_sus}%", inline=True)
        embed.add_field(name="Wynncraft Quests", value=f"{wynn_quest}\n{wynn_quest_sus}%", inline=True)
        embed.add_field(name="Wynncraft Rank", value=f"{wynn_rank}\n{wynn_rank_sus}%", inline=True)
        embed.add_field(name="Minecraft First Seen", value=f"""{first_seen_time}\n{first_seen_sus}%""", inline=True)
        if blacklisted != "False":
            overall_sus = 100.0
            embed.color = discord.Color.red()
            embed.title = f"Suspicousness of {name}: {overall_sus}% \n ⚠ Player is blacklisted ⚠"
            embed.add_field(name="Blacklisted?", value=f"{blacklisted}\n{blacklisted_sus}%", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)



    @valor.help_override.command()
    async def sus(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Sus", desc, color=0xFF00)
