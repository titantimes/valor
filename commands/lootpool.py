from valor import Valor
from discord.ext.commands import Context
from discord.ui import Select, View
import discord, requests
from util import ErrorEmbed, LongTextEmbed, EMOJIS, ITEM_TO_EMOJI_MAP


async def _register_lootpool(valor: Valor):
    desc = "Item lootpool for lootrun camps"

    POOL_NAME_MAP = {
        "silent_expanse": "Silent Expanse",
        "canyon_of_the_lost": "Canyon of the Lost",
        "corkus": "Corkus",
        "sky_islands": "Sky Islands",
        "molten_heights": "Molten Heights"
    }

    POOL_NAME_TO_API_MAP = {
        "silent_expanse": "SE",
        "canyon_of_the_lost": "Canyon",
        "corkus": "Corkus",
        "sky_islands": "Sky",
        "molten_heights": "Molten"
    }

    LOOTRUN_ICON_URL = "https://static.wikia.nocookie.net/wynncraft_gamepedia_en/images/f/f0/LootrunUpdateIcon.png/revision/latest"
    BASE_URL = "https://nori.fish"
    TOKEN_URL = f"{BASE_URL}/api/tokens"
    LOOTPOOL_URL = f"{BASE_URL}/api/lootpool"

    class LootpoolSelect(Select):
        def __init__(self):
            super().__init__(
                placeholder="Choose a loot pool...",
                options=[discord.SelectOption(label=v, value=k) for k, v in POOL_NAME_MAP.items()]
            )
        async def callback(self, interaction: discord.Interaction):
            embed = await get_pool(self.values[0])
            await interaction.response.edit_message(embed=embed, view=self.view)


    class LootpoolView(View):
        def __init__(self):
            super().__init__()

            self.select = LootpoolSelect()
            self.add_item(self.select)



    async def get_pool(pool):
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
        response = session.get(LOOTPOOL_URL, headers=headers)

        if response.status_code != 200:
            raise Exception("Failed to retrieve Lootpool data.")

        loot_data = response.json()
        all_loot = loot_data["Loot"]


        if pool is None:
            embed = discord.Embed(
                title="Loot Pool Overview",
                color=discord.Colour.from_rgb(74, 86, 219)
            )

            for pool_key, display_name in POOL_NAME_MAP.items():
                pool_name = POOL_NAME_TO_API_MAP[pool_key]
                pool_info = all_loot.get(pool_name)
                if not pool_info:
                    continue

                shiny = pool_info.get("Shiny")
                mythics = pool_info.get("Mythic", [])

                if not mythics and not shiny:
                    continue

                field_text = ""
                if shiny:
                    icon = EMOJIS[ITEM_TO_EMOJI_MAP[shiny['Item']]]
                    field_text += f"- {EMOJIS['shiny']}{icon} **Shiny** {shiny['Item']} (Tracker: {shiny['Tracker']})\n"
                if mythics:
                    for item in mythics:
                        icon = EMOJIS[ITEM_TO_EMOJI_MAP[item]]
                        field_text += f"- {icon} {item}\n"

                embed.add_field(name=f"{display_name} Mythics", value=field_text, inline=False)
                embed.set_thumbnail(url=LOOTRUN_ICON_URL)
            return embed


        pool_name = POOL_NAME_TO_API_MAP[pool]
        pool_info = all_loot[pool_name]

        if not pool_info:
            return ErrorEmbed(f"Loot pool data for {pool_name} not found.")
        
        embed = discord.Embed(title=f"Loot Pool: {pool_name}", color=discord.Colour.from_rgb(74, 86, 219))

        shiny = pool_info.pop("Shiny")
        mythics = pool_info.pop("Mythic")

        field_text = ""
        if shiny:
            icon = EMOJIS[ITEM_TO_EMOJI_MAP[shiny['Item']]]
            field_text += f"- {EMOJIS['shiny']}{icon} **Shiny** {shiny['Item']} (Tracker: {shiny['Tracker']})\n"
        if mythics:
            for item in mythics:
                icon = EMOJIS[ITEM_TO_EMOJI_MAP[item]]
                field_text += f"- {icon} {item}\n"

        embed.add_field(name="Mythics", value=field_text, inline=False)

        for rarity, items in pool_info.items():
            t = "\n".join(f"- {item}" for item in items)
            embed.add_field(name=rarity, value=t, inline=False)
        
        embed.set_thumbnail(url=LOOTRUN_ICON_URL)
        return embed


    @valor.command(aliases=["lp"])
    async def lootpool(ctx: Context): 
        view = LootpoolView()
        embed = await get_pool(None)
        await ctx.send(embed=embed, view=view)

    @lootpool.error
    async def cmd_error(ctx, error: Exception):
        await ctx.send(embed=ErrorEmbed())
        raise error
    
    @valor.help_override.command()
    async def lootpool(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "Lootpool", desc, color=0xFF00)
