import discord


class VistaExploracion(discord.ui.View):

    def __init__(self, manager):

        super().__init__(timeout=None)

        self.manager = manager

    @discord.ui.button(
        label="🎯 Capturar",
        style=discord.ButtonStyle.green
    )
    async def capturar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            "🚧 Sistema de captura próximamente.",
            ephemeral=True
        )

    @discord.ui.button(
        label="🚪 Salir",
        style=discord.ButtonStyle.red
    )
    async def salir(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.manager.world.finalizar_exploracion()

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="👋 Has salido del Mundo Pokémon.",
            view=self
        )