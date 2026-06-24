import asyncio
import discord

from incursiones.incursion_manager import (
    obtener_por_mensaje,
    eliminar_incursion
)
from incursiones.selector_incursion import SelectorIncursion
from database import obtener_equipo_selector


async def timeout_seleccion(
    raid,
    canal
):

    await asyncio.sleep(60)

    if raid.estado != "seleccion":
        return

    if raid.selecciones_completas:
        return

    raid.cerrar()

    eliminar_incursion(
        raid.canal_id
    )

    await canal.send(
        "❌ La incursión fue cancelada porque no todos seleccionaron su Pokémon a tiempo."
    )


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

        sala_llena = cantidad >= 3

        texto = (
            f"🦖 Alpha {raid.alpha} apareció\n\n"
            f"Participantes ({cantidad}/3)\n\n"
            f"{lista_jugadores}"
        )

        if sala_llena:

            raid.estado = "lista"

            texto += (
                "\n\n✅ Sala completa"
                "\n⚔️ Pulsa 'Iniciar Incursión'"
            )

            for child in self.children:

                if child.label == "Unirse":
                    child.disabled = True

                if child.label == "Iniciar Incursión":
                    child.disabled = False

        await interaction.response.defer()

        await interaction.message.edit(
            content=texto,
            view=self
        )

    @discord.ui.button(
        label="Iniciar Incursión",
        style=discord.ButtonStyle.red,
        disabled=True
    )
    async def iniciar_incursion(
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

        if len(raid.jugadores) < 3:

            await interaction.response.send_message(
                "Aún faltan jugadores.",
                ephemeral=True
            )
            return

        if raid.estado != "lista":

            await interaction.response.send_message(
                "La incursión ya fue iniciada.",
                ephemeral=True
            )
            return

        raid.estado = "seleccion"

        # Timeout de selección
        asyncio.create_task(
            timeout_seleccion(
                raid,
                interaction.channel
            )
        )

        await interaction.response.defer()

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(
            view=self
        )

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