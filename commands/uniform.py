import re
from util.valor_message import LongTextEmbed
from valor import Valor
from discord.ext.commands import Context
from discord import File
from util import ErrorEmbed
from PIL import Image, ImageColor
import argparse
import requests
import base64
import ast

async def _register_uniform(valor: Valor):
    desc = "Generates skin with ANO uniform based on the inserted username."
    parser = argparse.ArgumentParser(description='Uniform command')
    parser.add_argument("-u", "--username", type=str)
    parser.add_argument("-c", "--skincolour", type=str) # colour smh
    parser.add_argument("-v", "--variant", type=str.lower, default="male", choices=["male", "female"])
#    parser.add_argument("-at", "-autodetect", action='store_true') # to implement (autodetect skin colour)
#    parser.add_argument("-o", "-overlay", action='store_true') # to implement (Ignores the skin colour section and overlays the template on your skin)

    @valor.command()
    async def uniform(ctx: Context, *args):
        roles = {x.id for x in ctx.author.roles}
        if not 535609000193163274 in roles:
            return await ctx.send(embed=ErrorEmbed("Skill Issue"))
        
        try:
            opt = parser.parse_args(args)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Uniform", parser.format_help().replace("main.py", "-uniform"), color=0xFF00)

        try:
            skincolour = ImageColor.getrgb(opt.skincolour)
        except:
            return await ctx.send(embed=ErrorEmbed("Enter a proper hexadecimal colour that starts with #"))
        
        uuid = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{opt.username}").json()["id"]
        data = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}").json()
        skindata = ast.literal_eval(base64.b64decode(data["properties"][0]["value"]).decode("UTF-8"))

        player_skin = Image.open(requests.get(skindata["textures"]["SKIN"]["url"], stream=True).raw)

        if opt.variant == "male":
            uniform_skin = Image.open("assets/male-uniform.png").convert("RGBA")
        elif opt.variant == "female":
            uniform_skin = Image.open("assets/female-uniform.png").convert("RGBA")

        player_head = player_skin.crop((0,0,64,16)).convert("RGBA")

        final_skin = Image.new("RGBA", uniform_skin.size)
        final_skin.paste(uniform_skin, (0,0), uniform_skin)
        final_skin.paste(player_head, (0,0), player_head)

        skin_data = final_skin.getdata()

        new_skin_data = [skincolour if item == (255, 0, 0, 255) else item for item in skin_data]

        final_skin.putdata(new_skin_data)
        final_skin.save("/tmp/uniform_skin.png")

        file = File("/tmp/uniform_skin.png", filename="uniform_skin.png")

        await LongTextEmbed.send_message(valor, ctx, f"{opt.username}'s uniform", "", color=0xFF0000, 
            file=file, 
            url="attachment://uniform_skin.png"
        )
   
    @valor.help_override.command()
    async def uniform(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Uniform", desc, color=0xFF00)
        