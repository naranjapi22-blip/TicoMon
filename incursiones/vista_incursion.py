import discord

from incursiones.incursion_manager import obtener_por_mensaje
from incursiones.selector_incursion import SelectorIncursion
from database import obtener_equipo_selector


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

        # DESARROLLO: usar >= 1
        sala_llena = cantidad >= 3

        if sala_llena:

            raid.estado = "seleccion"

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

        if sala_llena:

            for jugador in raid.jugadores:

                miembro = interaction.guild.get_member(
                    jugador["id"]
                )

                if not miembro:
                    continue

                datos_equipo = obtener_equipo_selector(
                    jugador["id"]
                )

                if not datos_equipo["valores"]:
                    continue

                await interaction.channel.send(
                    f"🎯 {jugador['nombre']} selecciona tu Pokémon",
                    view=SelectorIncursion(
                        miembro,
                        datos_equipo,
                        interaction.client.session,
                        raid
                    )
                )