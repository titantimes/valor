from valor import Valor
from discord.ext.commands import Context
from util import LongTextEmbed
from discord import ui, Interaction, File
import os, discord
from dotenv import load_dotenv

load_dotenv()
TEST = os.getenv("TEST")=="TRUE"

async def _register_ffa(valor: Valor):
    desc = "FFA maps"
    FFA_MAPS_DIR = "assets/ffa_maps"

    def format_label(filename: str) -> str:
        name, _ = os.path.splitext(filename)
        return name.replace("_", " ").title()

    class FFAMapSelect(ui.Select):
        def __init__(self, ctx: Context, options: list[discord.SelectOption], message: discord.Message):
            super().__init__(
                placeholder="Select an FFA map to view...",
                options=options
            )
            self.ctx = ctx
            self.message = message

        async def callback(self, interaction: Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("Only the original user can use this menu.", ephemeral=True)

            selected_file = self.values[0]
            file_path = os.path.join(FFA_MAPS_DIR, selected_file)

            if not os.path.isfile(file_path):
                return await interaction.response.send_message("Map not found.", ephemeral=True)

            label = format_label(selected_file)
            with open(file_path, "rb") as f:
                file = File(f, filename=selected_file)

            embed = discord.Embed(
                title=f"{label} FFA Map",
                color=0x0000FF
            )
            embed.set_image(url=f"attachment://{selected_file}")

            await interaction.response.edit_message(
                embed=embed,
                attachments=[file],
                view=self.view
            )

    class FFAMapView(ui.View):
        def __init__(self, ctx: Context, message: discord.Message):
            super().__init__(timeout=60)
            self.ctx = ctx
            self.message = message
            self.populate_select()

        def populate_select(self):
            files = [f for f in os.listdir(FFA_MAPS_DIR)]
            options = [discord.SelectOption(label=format_label(f), value=f) for f in files]
            self.add_item(FFAMapSelect(self.ctx, options, self.message))

    @valor.command()
    async def ffa(ctx: Context):
        embed = discord.Embed(
            title="Select a map",
            description="Select an FFA map to view",
            color=0x0022FF
        )
        msg = await ctx.send(embed=embed, view=FFAMapView(ctx, None))
        view = FFAMapView(ctx, msg)
        view.message = msg
        await msg.edit(view=view)

    @valor.help_override.command()
    async def ffa(ctx: Context):
        await LongTextEmbed.send_message(valor, ctx, "ffa", desc, color=0xFF00)

