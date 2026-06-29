import discord


class VistaMundo(discord.ui.View):

    def __init__(self, manager):

        super().__init__(timeout=None)

        self.manager = manager

    @discord.ui.button(
        label="🌍 Interactuar",
        style=discord.ButtonStyle.green,
        custom_id="mundo_interactuar"
    )
    async def interactuar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.manager.world.iniciar_exploracion(
            interaction.user.id
        ):

            return await interaction.response.send_message(
                "🌍 Otro entrenador está explorando el mundo.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "📩 Revisa tus mensajes privados.",
            ephemeral=True
        )

        await self.manager.abrir_exploracion(
            interaction.user
        )