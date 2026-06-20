import discord


class VistaIncursion(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Unirse",
        style=discord.ButtonStyle.green
    )
    async def unirse(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        raid = obtener_por_mensaje(
            interaction.message.id
        )
        raid.agregar_jugador(
            interaction.user.id
        )