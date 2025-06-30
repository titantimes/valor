from valor import Valor
from discord.ext.commands import Context
import discord
from util import ErrorEmbed, LongTextEmbed
import commands.common, os
from dotenv import load_dotenv

load_dotenv()
TEST = os.getenv("TEST")=="TRUE"

async def _register_pings(valor: Valor):
    desc = "Pings menu for pinging roles"

    PING_ROLES = {
        "ffa": {
            "name": "FFA",
            "description": "FFA run",
            "emoji": "⚔️",
            "role_id": 892884695199666187
        },
        "dps": {
            "name": "DPS",
            "description": "DPS players needed",
            "emoji": "💥",
            "role_id": 892885182300954624
        },
        "guardian": {
            "name": "Guardian",
            "description": "Guardian needed",
            "emoji": "🛡️",
            "role_id": 892884953996591164
        },
        "healer": {
            "name": "Healer",
            "description": "Healer needed",
            "emoji": "❤️",
            "role_id": 892885381744320532
        },
        "trg": {
            "name": "Royal Guard",
            "description": "Royal Guard Ping",
            "emoji": "👑",
            "role_id": 683785435117256939
        },
    }

    class PingsButtonView(discord.ui.View):
        def __init__(self, ctx: Context):
            super().__init__(timeout=60)
            self.ctx = ctx
            for key, data in PING_ROLES.items():
                self.add_item(PingsButton(key))

    class PingsButton(discord.ui.Button):
        def __init__(self, ping_id: str):
            self.ping_id = ping_id
            data = PING_ROLES[ping_id]
            super().__init__(emoji=data["emoji"])

        async def callback(self, interaction: discord.Interaction):
            if not commands.common.role1(interaction.user, allow={536068288606896128}) and not TEST:
                return await interaction.response.send_message(embed=ErrorEmbed("No Permissions. (you need military role)"), ephemeral=True)

            data = PING_ROLES[self.ping_id]
            await interaction.response.send_message(
                f"<@&{data['role_id']}>",
            )


    
    @valor.command()
    async def pings(ctx: Context, *msg):
        if not commands.common.role1(ctx.author, allow={536068288606896128}) and not TEST:
            return await ctx.send(embed=ErrorEmbed("No Permissions. (you need military role)"))
    
        embed = LongTextEmbed(
            title="Available Role Pings",
            content="\n".join(
                f"{data['emoji']} **{data['name']}** — {data['description']}"
                for data in PING_ROLES.values()
            ),
            color=0x00FFFF
        )
        await ctx.send(embed=embed, view=PingsButtonView(ctx))
    
    
    
