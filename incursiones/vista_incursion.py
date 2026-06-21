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
            interaction.user.id,
            interaction.user.display_name
        )

        if not agregado:
            await interaction.response.send_message(
                "Ya estás dentro de esta incursión.",
                ephemeral=True
            )
            return

        cantidad = len(raid.jugadores)

        lista_jugadores = "\n".join(
            f"• {j['nombre']}"
            for j in raid.jugadores
        )

        sala_llena = cantidad >= 1   # cambiar luego a >= 3

        if sala_llena:

            raid.estado = "llena"

            for child in self.children:
                child.disabled = True

        texto = (
            f"🦖 Alpha {raid.alpha} apareció\n\n"
            f"Participantes ({cantidad}/3)\n\n"
            f"{lista_jugadores}"
        )

        if sala_llena:
            texto += "\n\n✅ Sala completa"

        await interaction.response.defer()

        await interaction.message.edit(
            content=texto,
            view=self
        )

        await interaction.followup.send(
            "Te uniste a la incursión.",
            ephemeral=True
        )