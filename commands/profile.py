import requests
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, get_war_rank, get_xp_rank
from discord.ext.commands import Context
from datetime import datetime
from discord import File
from dotenv import load_dotenv
import os
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from util import strhash, get_uuid

load_dotenv()
async def _register_profile(valor: Valor):
    desc = "Gives you a profile bio card"
    
    fontsize = 50
    bar_fontsize = 20
    bar_length = 348
    circle_fontsize = 20
    rank_fontsize = 30
    font = ImageFont.truetype("Ubuntu-R.ttf", fontsize)
    bar_font = ImageFont.truetype("Ubuntu-R.ttf", bar_fontsize)
    circle_font = ImageFont.truetype("Ubuntu-R.ttf", circle_fontsize)
    rank_font = ImageFont.truetype("Ubuntu-B.ttf", rank_fontsize)
    model_base = "https://visage.surgeplay.com/bust/"
    @valor.command()
    async def profile(ctx: Context, username):
        # guild_data = requests.get("https://api.wynncraft.com/public_api.php?action=guildStats&command=Titans%20Valor").json()

        # uuid = ""
        # not_replaced_uuid = ""
        # for m in guild_data["members"]:
        #     if m["name"] == username:
        #         uuid = m["uuid"].replace('-', '')
        #         not_replaced_uuid = m["uuid"]
        #         break
        # if not uuid:
        #     await ctx.send(embed=ErrorEmbed(f"{username} isn't even in the guild."))

        uuid = get_uuid(username)

        warcount = valor.warcount119.get(username, 0)
        wranking = get_war_rank(warcount)
        # schema = "https://" if os.getenv("USESSL") == "true" else "http://"
        # res = requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/usertotalxp/Titans Valor/{username}").json().get("data", {"xp": 0})
        res = await ValorSQL._execute(f"SELECT * FROM user_total_xps WHERE uuid='{uuid}'")
        gxp_contrib = res[0][1] if res else 0
        xpranking = get_xp_rank(gxp_contrib)

        img: Image = Image.open("assets/profile.png")
        draw = ImageDraw.Draw(img)
        draw.text((14, 75-fontsize), username, (0, 0, 0), font=font)
        # bar 1
        draw.text((235, 96-bar_fontsize), "1.19 War Count", (0, 0, 0), font=bar_font)
        draw.text((450, 96-bar_fontsize), f"{warcount}/{wranking[1]} Wars", (0, 0, 0), font=bar_font)
        bar1_percent = min(warcount/wranking[1], 1)
        draw.rectangle([241, 113, 241+bar_length*bar1_percent, 96], fill=(200, 40, 40))
        # bar 2
        draw.text((235, 149-bar_fontsize), "Guild XP Contribution", (0, 0, 0), font=bar_font)
        bar2_percent = min(gxp_contrib/xpranking[1], 1)
        draw.text((450, 149-bar_fontsize), f"{gxp_contrib} XP", (0, 0, 0), font=bar_font)
        draw.rectangle([241, 168, 241+bar_length*bar2_percent, 151], fill=(40, 200, 40))
        # bar 3
        draw.text((235, 200-bar_fontsize), "Coolness", (0, 0, 0), font=bar_font)
        bar3_percent = 1-abs(strhash(username))/(0xFFFFFFFF)
        
        draw.text((450, 200-bar_fontsize), f"{round(bar3_percent*100)}% Cool", (0, 0, 0), font=bar_font)
        draw.rectangle([241, 217, 241+bar_length*bar3_percent, 201], fill=(40, 40, 200))
        # circle 1
        draw.text((267, 270-circle_fontsize), "Wars", (180, 20, 20), font=circle_font)
        draw.text((267, 290-circle_fontsize), wranking[0], (120, 20, 20), font=rank_font)
        # circle 2
        draw.text((395, 270-circle_fontsize), "GXP", (20, 180, 20), font=circle_font)
        draw.text((395, 290-circle_fontsize), xpranking[0], (20, 120, 20), font=rank_font)
        # circle 3
        draw.text((520, 270-circle_fontsize), "Cool", (20, 20, 180), font=circle_font)
        draw.text((520, 290-circle_fontsize), "X", (20, 20, 120), font=rank_font)
        # medals
        draw.text((244, 364-circle_fontsize), "No medals lul", (0, 50, 80), font=circle_font)
        # get model
        if not os.path.exists(f"/tmp/{username}_model.png"):
            model = requests.get(model_base+uuid).content 
            with open(f"/tmp/{username}_model.png", "wb") as f:
                f.write(model)
        model_img = Image.open(f"/tmp/{username}_model.png", 'r')
        img.paste(model_img, (1, 104), model_img)
        img.save("/tmp/out_profile.png")
        file = File("/tmp/out_profile.png", filename="out_profile.png")
    
        await LongTextEmbed.send_message(valor, ctx, f"Profile of {username}", "", color=0xFF0000, 
            file=file, 
            url="attachment://out_profile.png"
        )


    @valor.help_override.command()
    async def profile(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Profile", desc, color=0xFF00)