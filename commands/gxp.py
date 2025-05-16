import requests
from valor import Valor
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, to_seconds
from sql import ValorSQL
from discord.ext.commands import Context
from datetime import datetime
from dotenv import load_dotenv
import discord, asyncio, time, os, aiohttp, math
from discord.ui import View
from discord import File
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

load_dotenv()
async def _register_gxp(valor: Valor):
    desc = "Gets you GXP of a member. `-gxp h` to get the xp contributions of a player with time slices"
    model_base = "https://visage.surgeplay.com/bust/"

    def basic_table(data: list[tuple], page: int, title: str) -> str:
        per_page = 20
        start = page * per_page
        end = start + per_page
        sliced = data[start:end]

        i = 1+(page*per_page)

        table = f"```isbl\n{title}\n\n"
        table += " Rank ┃ Name            ┃ XP             \n"
        table += "━━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━\n"

        for player in sliced:
            rank = f"{i})"
            rank_pad = " " * int((6 - len(rank)))
            name = player[0]
            name_pad = " " * int((16 - len(name)))
            xp = f"{int(player[1]):,}"
            xp_pad = " " * int((16 - len(xp)))

            t = f"{rank}{rank_pad}┃ {name}{name_pad}┃ {xp}{xp_pad}\n"
            table += t
            i += 1

        table += "━━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━\n```"

        return table


    async def download_model(session, url, filename):
        user_agent = {'User-Agent': 'valor-bot/1.0'}
        try:
            async with session.get(url, headers=user_agent) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(filename, "wb") as f:
                        f.write(content)
                else:
                    print(f"Failed to fetch {url}: {response.status}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    async def fetch_all_models(rows):
        tasks = []
        now = time.time()
        async with aiohttp.ClientSession() as session:
            for row in rows:
                if row[0]:
                    filename = f"/tmp/{row[0]}_model.png"
                    url = model_base + row[0] + '.png'

                    if not os.path.exists(filename) or now - os.path.getmtime(filename) > 24 * 3600:
                        tasks.append(download_model(session, url, filename))
            await asyncio.gather(*tasks)  # Run all downloads in parallel


    async def fancy_table(data: list[tuple], page: int):
        start = page * 10
        end = start + 10
        sliced = data[start:end]

        rank_margin = 45
        model_margin = 115
        name_margin = 205
        value_margin = 685

        font = ImageFont.truetype("MinecraftRegular.ttf", 20)
        board = Image.new("RGBA", (730, 695), (110, 110, 110))
        overlay = Image.open("assets/overlay.png")
        overlay2 = Image.open("assets/overlay2.png")
        overlay_toggle = True
        draw = ImageDraw.Draw(board)

        await fetch_all_models(sliced)

        i = 0
        rank = 1+(page*10)
        for stat in sliced:

            height = (i*69)+5
            board.paste(overlay if overlay_toggle else overlay2, (5, height), overlay)
            overlay_toggle = not overlay_toggle
            match rank:
                case 1:
                    color = "yellow"
                case 2:
                    color = (170,169,173,255)
                case 3:
                    color = (169,113,66,255)
                case _:
                    color = "white"
            try:
                model_img = Image.open(f"/tmp/{stat[0]}_model.png", 'r')
                model_img = model_img.resize((64, 64))
            except Exception as e:
                model_img = Image.open(f"assets/unknown_model.png", 'r')
                model_img = model_img.resize((64, 64))
                print(f"Error loading image: {e}")

            board.paste(model_img, (model_margin, height), model_img)
            draw.text((rank_margin, height+22), "#"+str(rank), fill=color, font=font)
            draw.text((name_margin, height+22), str(stat[0]), font=font)
            draw.text((value_margin, height+22), f"{int(stat[1]):,}", font=font, anchor="rt")

            rank += 1
            i += 1


        board.save("/tmp/gxp.png")

        return File("/tmp/gxp.png", filename="gxp.png")

    class GXPView(View):
        def __init__(self, ctx, rows, title, timeout=60):
            super().__init__(timeout=timeout)
            self.ctx = ctx
            self.is_fancy = False

            self.page = 0
            self.title = title
            self.data = rows
            
            self.max_pages = math.ceil(len(rows) / 10)

        async def update_message(self, interaction: discord.Interaction):
            if self.is_fancy:
                await interaction.response.defer()
                content = await fancy_table(self.data, self.page)
                await interaction.edit_original_response(content="", view=self, attachments=[content])
            else:
                content = basic_table(self.data, self.page, self.title)
                await interaction.response.edit_message(content=content, view=self, attachments=[])

        @discord.ui.button(label="⬅️")
        async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page > 0:
                self.page -= 1
                await self.update_message(interaction)
            else:
                await interaction.response.defer()

        @discord.ui.button(label="➡️")
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page < self.max_pages - 1:
                self.page += 1
                await self.update_message(interaction)
            else:
                await interaction.response.defer()
        
        @discord.ui.button(label="✨")
        async def fancy(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.is_fancy = not self.is_fancy
            await self.update_message(interaction)


    @valor.group()
    async def gxp(ctx: Context, guild="Titans Valor", player="", arg2 = "", arg3 = ""):
        # schema = "https://" if os.getenv("USESSL") == "true" else "http://"
        # if guild == "h":
        #     # player is arg1
        #     t1 = int(time.time()) if not arg3 else int(datetime.strptime(arg3, "%d/%m/%y").timestamp())
        #     t0 = int(datetime.strptime(arg2, "%d/%m/%y").timestamp()) if arg2 else 0
        #     uuid = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}").json()["id"]
        #     # add hyphens
        #     uuid = '-'.join([uuid[:8],uuid[8:12],uuid[12:16],uuid[16:20],uuid[20:]])
        #     res = requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/incxp/{uuid}/{t0}/{t1}").json()["data"]
        #     # print(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/incxp/{uuid}/{t0}/{t1}")
        #     total = sum(x[0] for x in res["values"])
        #     content = f"From {arg2 if arg2 else '17/04/2021'} to {arg3 if arg3 else 'Now'}\nContributed: {total:,} GXP"
        #     return await LongTextEmbed.send_message(valor, ctx, f"{player}'s XP Contributions Over Time", content, color=0xF5b642)
        
        if guild == "frame":
            now = int(time.time())
            t0 = now-to_seconds(player)
            t1 = now-to_seconds(arg2)
            res = await ValorSQL.exec_param("""
SELECT C.name, SUM(B.delta) AS delta_gxp
FROM 
    (SELECT * FROM player_delta_record WHERE guild="Titans Valor" AND label="gu_gxp" AND time >= %s AND time <= %s) B 
    JOIN uuid_name C ON B.uuid=C.uuid
GROUP BY B.uuid
ORDER BY delta_gxp  DESC;
""", (t0, t1))
            pair_data = [[x[0], f"{x[1]:,}"] for x in sorted(res, key = lambda x: x[1], reverse=True)]
            
            return await LongFieldEmbed.send_message(valor, ctx, f"GXP Contribs Over Specified Time", pair_data, color=0xF5b642)
            

        # res = requests.get(schema+os.getenv("REMOTE")+os.getenv("RMPORT")+f"/usertotalxp/{guild}/{player}").json()["data"]
        if guild == "Titans Valor":
            res = await ValorSQL._execute("""
SELECT IFNULL(B2.name, C2.name), A2.gxp
FROM
    (SELECT uuid, MAX(xp) AS gxp
    FROM
        ((SELECT uuid, xp FROM user_total_xps)
        UNION ALL
        (SELECT B.uuid, B.value AS xp
        FROM 
            player_stats A JOIN player_global_stats B ON A.uuid=B.uuid
        WHERE A.guild="Titans Valor" AND B.label="gu_gxp")) A1
    GROUP BY uuid) A2 
    LEFT JOIN uuid_name B2 ON A2.uuid=B2.uuid
    LEFT JOIN (SELECT uuid, name FROM user_total_xps) C2 ON C2.uuid=A2.uuid
ORDER BY A2.gxp DESC;
""")
        else:
            res = await ValorSQL.exec_param("""
SELECT C.name, B.value
FROM 
    player_stats A JOIN player_global_stats B ON A.uuid=B.uuid
    JOIN uuid_name C ON B.uuid=C.uuid
WHERE A.guild=(%s) AND B.label="gu_gxp"  
ORDER BY `B`.`value`  DESC
""", (guild))
            
        # if isinstance(res, tuple):
        total = 0
        for value in res:
            total += value[1]
        total = int(total)

        title = f"{guild} — XP Breakdown (Total: {total:,})"

        view = GXPView(ctx, res, title)

        await ctx.send(content=basic_table(res, 0, title), view=view)
        # else:
        #     uuid = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}").json()["id"]
        #     # add hyphens
        #     uuid = '-'.join([uuid[:8],uuid[8:12],uuid[12:16],uuid[16:20],uuid[20:]])
        #     for x in res:
        #         if x[4] == uuid:
        #             res = x
        #             break

        #     mesg = f"**{int(res[1]):,}**\nUpdates Every 30 Minutes"
        #     await LongTextEmbed.send_message(valor, ctx, f"{player}'s XP Gain for {guild}", mesg, color=0xF5b642)

    @gxp.error
    async def gxp_error(ctx, error):
        await ctx.send(embed=ErrorEmbed("Command failed :/ (Use quotes around the guild name if you haven't)"))
        raise error
    
    @valor.help_override.command()
    async def gxp(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Gxp", desc, color=0xFF00)