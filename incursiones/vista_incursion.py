import discord

from incursiones.incursion_manager import obtener_por_mensaje


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

        if not raid:
            await interaction.response.send_message(
                "Incursión no encontrada.",
                ephemeral=True
            )
            return

        agregado = raid.agregar_jugador(
            interaction.user.id
        )

        if not agregado:
            await interaction.response.send_message(
                "Ya estás dentro de esta incursión.",
                ephemeral=True
            )
            return

        cantidad = len(raid.jugadores)

        await interaction.response.defer()

        await interaction.message.edit(
            content=
            f"🦖 Alpha {raid.alpha} apareció\n\n"
            f"Participantes: {cantidad}/3",
            view=self
        )

        await interaction.followup.send(
            "Te uniste a la incursión.",
            ephemeral=True
        )