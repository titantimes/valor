from valor import Valor
from discord.ext.commands import Context
from discord.ui import Select, View
import discord, requests
from util import ErrorEmbed, LongTextEmbed, EMOJIS, ASPECT_TO_EMOJI_MAP


async def _register_aspectpool(valor: Valor):
    desc = "Aspect lootpool for raids"

    POOL_NAME_MAP = {
        "tna": "The Nameless Anomaly",
        "tcc": "The Canyon Colossus",
        "nol": "Nexus of Light",
        "notg": "Nest of The Grootslangs"
    }

    POOL_NAME_TO_API_MAP = {
        "tna": "TNA",
        "tcc": "TCC",
        "nol": "NOL",
        "notg": "NOTG"
    }
    ASPECT_ICON_URL = "https://nori.fish/resources/aspect.gif"
    BASE_URL = "https://nori.fish"
    TOKEN_URL = f"{BASE_URL}/api/tokens"
    ASPECTPOOL_URL = f"{BASE_URL}/api/aspects"

    class AspectPoolSelect(Select):
        def __init__(self):
            super().__init__(
                placeholder="Choose an aspect pool...",
                options=[discord.SelectOption(label=v, value=k) for k, v in POOL_NAME_MAP.items()]
            )
        async def callback(self, interaction: discord.Interaction):
            embed = await get_pool(self.values[0])
            await interaction.response.edit_message(embed=embed, view=self.view)


    class AspectPoolView(View):
        def __init__(self):
            super().__init__()

            self.select = AspectPoolSelect()
            self.add_item(self.select)



    async def get_pool(raid):
        session = requests.Session()

        token_response = session.get(TOKEN_URL)
        if token_response.status_code != 200:
            raise Exception("Failed to retrieve authentication tokens.")
        csrf_token = session.cookies.get("csrf_token")
        if not csrf_token:
            raise Exception("CSRF token not found in cookies.")

        headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf_token
        }
        response = session.get(ASPECTPOOL_URL, headers=headers)

        if response.status_code != 200:
            raise Exception("Failed to retrieve aspectpool data.")

        aspect_data = response.json()
        all_loot = aspect_data["Loot"]

        if raid is None:
            embed = discord.Embed(
                title="Aspect Pool Overview",
                color=discord.Colour.from_rgb(74, 86, 219)
            )
            for pool_key, display_name in POOL_NAME_MAP.items():
                pool_name = POOL_NAME_TO_API_MAP[pool_key]
                raid_loot = all_loot[pool_name]

                text = ""
                for item in raid_loot["Mythic"]:
                    icon = EMOJIS[ASPECT_TO_EMOJI_MAP[aspect_data["Icon"][item]]]
                    text += f"- {icon} {item}\n"

                if text:
                    embed.add_field(name=f"{display_name} Mythic Aspects", value=text, inline=False)

            embed.set_thumbnail(url=ASPECT_ICON_URL)
            return embed

        # Detailed view for a specific raid
        pool_name = POOL_NAME_TO_API_MAP[raid]
        pool_data = all_loot.get(pool_name)
        if not pool_data:
            return ErrorEmbed(f"Aspect lootpool data for {pool_name} not found.")

        embed = discord.Embed(
            title=f"Aspect Pool: {POOL_NAME_MAP[raid]}",
            color=discord.Colour.from_rgb(74, 86, 219)
        )

        for rarity in ("Mythic", "Fabled", "Legendary"):
            items = pool_data[rarity]

            field_text = ""
            for item in items:
                icon = EMOJIS[ASPECT_TO_EMOJI_MAP[aspect_data["Icon"][item]]]
                field_text += f"- {icon} {item}\n"
            embed.add_field(name=f"{rarity} Aspects", value=field_text, inline=False)

        embed.set_thumbnail(url=ASPECT_ICON_URL)
        return embed
        




    @valor.command(aliases=["ap"])
    async def aspectpool(ctx: Context): 
        view = AspectPoolView()
        embed = await get_pool(None)
        await ctx.send(embed=embed, view=view)

    @aspectpool.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def aspectpool(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Aspect lootpool", desc, color=0xFF00)
