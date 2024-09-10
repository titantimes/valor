import requests
import time
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, get_war_rank, get_xp_rank
from discord.ext.commands import Context
from datetime import datetime
from discord import File
from dotenv import load_dotenv
import os
import re
import math
import textwrap
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from util import strhash
from commands.common import get_uuid

load_dotenv()
async def _register_profile(valor: Valor):
    desc = "Gives you a profile bio card"

    def human_format(number):
        units = ['', 'K', 'M', 'B', 'T']
        k = 1000.0

        if not number:
            number = 0

        try:
            magnitude = int(math.floor(math.log(number + 1e-8, k)))
            x = number / k**magnitude
            if int(x) == x:
                v = int(x)
            else:
                v = round(x, 3)
            return f"{v}{units[magnitude]}"
        except ValueError:
            return 0
    

    white = (255, 255, 255)
    red = (229, 83, 107)
    green = (87, 234, 128)
    blue = (47, 63, 210)

    name_fontsize = 32
    rank_fontsize = 28
    text_fontsize = 15
    stat_text_fontsize = 12
    name_font = ImageFont.truetype("assets/MinecraftRegular.ttf", name_fontsize)
    rank_font = ImageFont.truetype("assets/MinecraftRegular.ttf", rank_fontsize)
    text_font = ImageFont.truetype("assets/MinecraftRegular.ttf", text_fontsize)
    stat_text_font = ImageFont.truetype("assets/MinecraftRegular.ttf", stat_text_fontsize)
    model_base = "https://visage.surgeplay.com/bust/"

    @valor.command(aliases=["p"])
    async def profile(ctx: Context, username):
        uuid = await get_uuid(username)

        res = requests.get("https://api.wynncraft.com/v3/player/"+uuid)
        if res.status_code != 200:
            return await ctx.send(embed=ErrorEmbed())
        data = res.json()

        warcount = valor.warcount119.get(username.lower(), 0)
        res = await ValorSQL.exec_param("SELECT SUM(warcount) FROM cumu_warcounts WHERE uuid=%s", uuid)
        warcount += (res[0][0] if res else 0)
        war_ranking = get_war_rank(warcount)
        
        res = await ValorSQL.exec_param("""
SELECT MAX(xp)
FROM
	((SELECT xp FROM user_total_xps WHERE uuid=%s)
    UNION ALL
    (SELECT SUM(delta) FROM player_delta_record WHERE guild="Titans Valor" AND uuid=%s AND label="gu_gxp")) A;""", (uuid, uuid))
        if res and res[0][0]:
            gxp_contrib = res[0][0]
        elif data["guild"]:
            res = requests.get("https://api.wynncraft.com/v3/guild/prefix/"+data["guild"]["prefix"])
            res = res.json()
            gxp_contrib = res["members"][data["guild"]["rank"].lower()][username]["contributed"]
        else:
            gxp_contrib = 0

        gxp_ranking = get_xp_rank(gxp_contrib)

        img: Image = Image.open("assets/profile_template.png")
        draw = ImageDraw.Draw(img)

        #if rank 
        offset = 0
        if data["supportRank"]:
            rank_badge = Image.open(f'assets/badges/{data["supportRank"]}.png')
            img.paste(rank_badge, (21, 25), rank_badge)
            # python < 3.10
            if data["supportRank"] == "vip":
                offset = 84
            elif data["supportRank"] == "vipplus":
                offset = 105
            elif data["supportRank"] == "hero":
                offset = 110
            elif data["supportRank"] == "champion":
                offset = 175
        draw.text((21+offset, 24), username, white, name_font)


        if not os.path.exists(f"/tmp/{username}_model.png") or time.time() - os.path.getmtime(f"/tmp/{username}_model.png") > (24 * 3600):
            user_agent = {'User-Agent': 'valor-bot/1.0'}
            model = requests.get(model_base+uuid+'.png', headers=user_agent).content
            with open(f"/tmp/{username}_model.png", "wb") as f:
                f.write(model)
        model_img = Image.open(f"/tmp/{username}_model.png", 'r')
        model_img = model_img.resize((203, 190))
        img.paste(model_img, (26, 79), model_img)
        

        draw.text((342, 161), war_ranking[0], red, rank_font, anchor="mm")
        draw.text((342, 230), f"{warcount} / {war_ranking[1]}", white, text_font,  anchor="ma")

        img.putpixel((268, 222), red)
        img.putpixel((268, 223), red)
        value = min(round((warcount/war_ranking[1])*142), 142)
        draw.rectangle([(269, 221), (value+269, 224)], red)
        if value == 142:
            img.putpixel((412, 222), red)
            img.putpixel((412, 223), red)


        draw.text((542, 161), gxp_ranking[0], green, rank_font, anchor="mm")
        draw.text((542, 230), f"{human_format(gxp_contrib)} / {human_format(gxp_ranking[1])}", white, text_font, anchor="ma")
        
        img.putpixel((468, 222), green)
        img.putpixel((468, 223), green)
        value = min(round((gxp_contrib/gxp_ranking[1])*142), 142)
        draw.rectangle([(469, 221), (value+469, 224)], green)
        if value == 142:
            img.putpixel((612, 222), green)
            img.putpixel((612, 223), green)


        cool = min(len(await ValorSQL._execute(f"SELECT * FROM activity_members WHERE uuid='{uuid}' AND timestamp>={time.time()-3600*24*7}"))/100, 1)
        cool_percent = round(cool*100)
        value = round(cool*142)

        img.putpixel((667, 125), blue)
        img.putpixel((667, 126), blue)
        draw.rectangle([(668, 124), (value+668, 127)], blue)
        draw.text((740, 140), f"{cool_percent}% Cool", white, text_font, anchor="ma")


        if data["online"]:
            draw.text((740, 209), 'Player Online:', green, text_font, anchor="ma")
            draw.text((740, 229), data["server"], white, text_font, anchor="ma")
        else:
            draw.text((740, 209), 'Player last seen:', white, text_font, anchor="ma")
            draw.text((740, 229), datetime.fromisoformat(data["lastJoin"][:-1]).strftime("%H:%M  %m/%d/%Y"), white, text_font, anchor="ma")

        rankings = data["ranking"]
        for rank in dict(rankings):
            if rank in {"hardcoreLegacyLevel"}:
                rankings.pop(rank)
        top_rank_keys = sorted(rankings, key=rankings.get)[:3]
        top_rankings = {}
        for key in top_rank_keys:
            top_rankings[key] = rankings[key]
        
        for i, key in enumerate(top_rank_keys):
            temp = [s for s in re.split("([A-Z][^A-Z]*)", key) if s]

            rank_badge_link = f"https://cdn.wynncraft.com/nextgen/leaderboard/icons/{temp[0]}.webp?height=50"
            rank_place = rankings[key]
            rank_word_list = []
            for word in temp:
                if word in {"tcc", "nol", "nog", "tna", "huic", "huich", "hic", "hich"}:
                    rank_word_list.append(word.upper())
                else:
                    rank_word_list.append(word.title())
            rank = " ".join(rank_word_list)
            wrapper = textwrap.TextWrapper(width=13, max_lines=2, placeholder="") 
            rank = wrapper.wrap(text=rank) 

            if temp[0] in {"craftsman", "hunted", "ironman", "hardcore", "ultimate", "huic", "huich", "hic", "hich"}:
                rank_badge = Image.open(f"assets/icons/gamemodes/{temp[0]}.png")
            else:
                rank_badge = Image.open(requests.get(rank_badge_link, stream=True).raw)

            for x, line in enumerate(rank):
                draw.text((91+(i*120), 335+(x*20)), line, white, text_font, anchor="ma")
            img.paste(rank_badge, (66+(i*120), 380), rank_badge)
            draw.text((91+(i*120), 445), f"#{rank_place}", white, text_font, anchor="ma")


        offset = 53
        if data["guild"]:
            try:
                guild_badge = Image.open(f'assets/icons/guilds/{data["guild"]["prefix"]}.png')
                img.paste(guild_badge, (414, 289), guild_badge)
            except FileNotFoundError:
                offset = 0

            draw.text((505, 380+offset), f'{data["guild"]["rank"]} of', white, text_font, anchor="ma")
            draw.text((505, 400+offset), data["guild"]["name"], white, text_font, anchor="ma")
        else:
            draw.text((505, 390), "No Guild", white, text_font, anchor="ma")


        stats = [f'{data["playtime"]} Hours', 
                 f'{data["globalData"]["totalLevel"]} Levels',
                 f'{data["globalData"]["killedMobs"]} Mobs',
                 f'{data["globalData"]["chestsFound"]} Chests',
                 f'{data["globalData"]["completedQuests"]} Quests']
        i = 0
        for stat in stats:
            draw.text((819, 333+(i*29)), stat, white, stat_text_font, anchor="ra")
            i += 1


        img.save("/tmp/out_profile.png")
        file = File("/tmp/out_profile.png", filename="out_profile.png")
    
        await ctx.send(file=file)


    @valor.help_override.command()
    async def profile(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Profile", desc, color=0xFF00)