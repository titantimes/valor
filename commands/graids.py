import time, discord, os, asyncio, aiohttp, math
from valor import Valor
from sql import ValorSQL
from util import ErrorEmbed, HelpEmbed, LongFieldEmbed, LongTextEmbed, LongTextTable
from discord.ext.commands import Context
from PIL import Image, ImageFont, ImageDraw
from discord import File
from discord.ui import View
from datetime import datetime
from dotenv import load_dotenv
from .common import get_left_right, guild_names_from_tags
import argparse
from datetime import datetime, timedelta

load_dotenv()
async def _register_graids(valor: Valor):
    desc = "Gets you the guild raid count leaderboard"
    parser = argparse.ArgumentParser(description='Warcount Command')
    parser.add_argument('-r', '--range', nargs='+', default=None)
    parser.add_argument('-g', '--guild', nargs='+', default=None)
    parser.add_argument('-w', '--guild_wise', action="store_true", default=False)
    parser.add_argument('-n', '--name', nargs='+', type=str, default=None)

    class GRaidView(View):
        def __init__(self, ctx, header, rows, footer, timeout=60):
            super().__init__(timeout=timeout)
            self.ctx = ctx
            self.is_fancy = False
 
            self.page = 0
            self.header = header
            self.data = rows
            self.footer = footer
            
            self.max_pages = math.ceil(len(rows) / 10)

        async def update_message(self, interaction: discord.Interaction):
            if self.is_fancy:
                await interaction.response.defer()
                content = await fancy_table(self.data, self.page)
                await interaction.edit_original_response(content="", view=self, attachments=[content])
            else:
                content = basic_table(self.header, self.data, self.page, self.footer)
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
        model_base = "https://visage.surgeplay.com/bust/"
        tasks = []
        now = time.time()
        async with aiohttp.ClientSession() as session:
            for row in rows:
                if row[1]:
                    filename = f"/tmp/{row[1]}_model.png"
                    url = model_base + row[1] + '.png'
                    if not os.path.exists(filename) or now - os.path.getmtime(filename) > 24 * 3600:
                        tasks.append(download_model(session, url, filename))
            await asyncio.gather(*tasks)  # Run all downloads in parallel

    def basic_table(header: list[str], data: list[tuple], page: int, footer: str) -> str:
        start = page * 10
        end = start + 10
        sliced = data[start:end]

        col_widths = [len(h) for h in header]
        lines = []

        fmt = ' ┃ '.join(f"%{len(x)}s" for x in header)
        header_line = fmt % tuple(header)
        lines.append(header_line)

        separator = ''.join('╋' if x == '┃' else '━' for x in header_line)
        lines.append(separator)

        for row in sliced:
            line = ""
            for i, cell in enumerate(row):
                line += str(cell).rjust(col_widths[i])
                if i != len(row) - 1:
                    line += " ┃ "
            lines.append(line)

        lines.append(separator)
        lines.append(footer)

        return "```" + "\n".join(lines) + "```"
    
    async def fancy_table(stats, page):
        start = page * 10
        end = start + 10
        sliced = stats[start:end]

            
        rank_margin = 40
        model_margin = 110
        name_margin = 200
        value_margin = 680

        font = ImageFont.truetype("MinecraftRegular.ttf", 20)
        board = Image.new("RGBA", (720, 730), (255, 0, 0, 0))
        overlay = Image.open("assets/overlay.png")
        draw = ImageDraw.Draw(board)

        await fetch_all_models(stats)

        i = 1
        for row in sliced:
            height = (i*74)-74
            board.paste(overlay, (0, height))
            match row[0]:
                case 1:
                    color = "yellow"
                case 2:
                    color = (170,169,173,255)
                case 3:
                    color = (169,113,66,255)
                case _:
                    color = "white"
            try:
                model_img = Image.open(f"/tmp/{row[1]}_model.png", 'r')
                model_img = model_img.resize((64, 64))
            except Exception as e:
                model_img = Image.open(f"assets/unknown_model.png", 'r')
                model_img = model_img.resize((64, 64))
                print(f"Error loading image: {e}")

            board.paste(model_img, (model_margin, height), model_img)
            draw.text((rank_margin, height+22), "#"+str(row[0]), fill=color, font=font)
            draw.text((name_margin, height+22), str(row[1]), font=font)
            draw.text((value_margin, height+22), str(row[2]), font=font, anchor="rt")

            i += 1

        board.save("/tmp/graids.png")
        return File("/tmp/graids.png", filename="graids.png")

    @valor.command()
    async def graids(ctx: Context, *options):
        try:
            opt = parser.parse_args(options)
        except:
            return await LongTextEmbed.send_message(valor, ctx, "Guild Raids", parser.format_help().replace("main.py", "-graids"), color=0xFF00)

        start = time.time()

        if opt.name:
            names = opt.name
            uuiddd = await ValorSQL.exec_param("SELECT uuid, name FROM uuid_name WHERE name IN (" + ",".join(["%s"] * len(names)) + ")", names)
            if not uuiddd:
                return await ctx.send(embed=ErrorEmbed(f"No UUIDs found for names {', '.join(names)}"))
            uuidtoname = {name: uuid for uuid, name in uuiddd}
            uuids = [uuidtoname[name] for name in names if name in uuidtoname]
            if not uuids:
                return await ctx.send(embed=ErrorEmbed(f"No valid UUIDs found for names {', '.join(names)}"))
            template_query = '''
SELECT ROW_NUMBER() OVER(ORDER BY raid_cnt DESC) AS `raid_cnt`, name, guild, raid_cnt
FROM
    (SELECT B.name, A.guild, SUM(A.num_raids) AS raid_cnt
    FROM
        guild_raid_records A LEFT JOIN uuid_name B ON A.uuid=B.uuid
    WHERE 
        {TIME_CLAUSE}
        AND A.uuid IN ({UUIDS})
    GROUP BY A.uuid, A.guild
    ORDER BY raid_cnt DESC) C;
'''
            template_query_params = { "TIME_CLAUSE": "", "UUIDS": ",".join(["%s"] * len(uuids)) }
            prepared_params = uuids
        elif not opt.guild_wise:
            template_query = '''
SELECT ROW_NUMBER() OVER(ORDER BY raid_cnt DESC) AS `raid_cnt`, name, raid_cnt
FROM
    (SELECT B.name, SUM(A.num_raids) AS raid_cnt
    FROM
        guild_raid_records A LEFT JOIN uuid_name B ON A.uuid=B.uuid
    WHERE 
        {TIME_CLAUSE}
        {GUILD_CLAUSE}
    GROUP BY A.uuid
    ORDER BY raid_cnt DESC) C;
''' 
            template_query_params = { "TIME_CLAUSE": "", "GUILD_CLAUSE": "" }
            prepared_params = []
        else:
            template_query = '''
SELECT ROW_NUMBER() OVER(ORDER BY raid_cnt DESC), guild, raid_cnt
FROM
    (SELECT guild, SUM(num_raids) AS raid_cnt
    FROM
        guild_raid_records A
    WHERE
        {TIME_CLAUSE}
        {GUILD_CLAUSE}
    GROUP BY guild
    ORDER BY raid_cnt DESC) C;
'''
            template_query_params = { "TIME_CLAUSE": "", "GUILD_CLAUSE": "" }
            prepared_params = []

        if not opt.range:
            opt.range = ["7", "0"]

        valid_range = await get_left_right(opt, start)
        if valid_range == "N/A":
            return await ctx.send(embed=ErrorEmbed("Invalid season name input"))

        left, right = valid_range
        template_query_params["TIME_CLAUSE"] = "A.`time` > %s AND A.`time` <= %s"
        prepared_params.insert(0, left)
        prepared_params.insert(1, right)

        if opt.guild:
            opt.guild, _ = await guild_names_from_tags(opt.guild)
            template_query_params["GUILD_CLAUSE"] = "AND A.guild IN (" + ("%s,"*len(opt.guild))[:-1] + ")"
            prepared_params.extend(opt.guild)

        query = template_query.format(**template_query_params)

        res = await ValorSQL.exec_param(query, prepared_params)

        if not res:
            return await ctx.send(embed=ErrorEmbed("No raids recorded in the specified time period"))
#This can easily pop up if queries fail just a note if someone is debugging in the future and keeps getting this.
        delta_time = time.time() - start

        if opt.name:
            header = [' Rank ', ' '*14+"Name", ' '*14+"Guild", "  Total  "] #this looks abit jank with 14 buffer on each but i was too lazy to make something dynamic
            res = list(res)
            for name in names:
                uuid = uuidtoname.get(name)
                if uuid:
                    raidsall = sum(row[3] for row in res if row[1] == name)
                    res.append((None, name, 'Total', raidsall)) #with multiple names there is no "rank" to totals which could be fixed here later fine for now
        else:
            header = [' Rank ', ' '*14+"Name", "  Total  "]

        now = datetime.now()
        start_date = now - timedelta(days=float(opt.range[0]))
        end_date = now - timedelta(days=float(opt.range[1]))

        time_range_str = f"{start_date.strftime('%d/%m/%Y %H:%M')} until {end_date.strftime('%d/%m/%Y %H:%M')}"

        opt_after = f"\nQuery took {delta_time:.3}s. Requested at {datetime.utcnow().ctime()}\nRange: {time_range_str}"

        view = GRaidView(ctx, header, res, opt_after)
        await ctx.send(content=basic_table(header, res, 0, opt_after), view=view)

    @valor.help_override.command()
    async def graids(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Guild Raids", desc, color=0xFF00)
