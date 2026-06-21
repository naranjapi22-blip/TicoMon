import discord

from vistas_selector import SelectorPokemon
from incursiones.combate_incursion import iniciar_incursion


class SelectorIncursion(SelectorPokemon):

    def __init__(
        self,
        user,
        datos_equipo,
        session,
        raid
    ):

        self.raid = raid

        super().__init__(
            user,
            datos_equipo["valores"],
            session,
            max_seleccion=1,
            titulo="🎯 Selecciona tu Pokémon",
            descripcion_extra=(
                "Elige el Pokémon que participará "
                "en la incursión."
            ),
            placeholder_select="Elegir Pokémon",
            etiqueta_campo="Pokémon elegido",
            auto_confirmar_uno=True,
            etiquetas=datos_equipo.get(
                "etiquetas"
            ),
            nombre_por_valor=datos_equipo.get(
                "nombres"
            ),
        )

    async def _finalizar_seleccion(
        self,
        interaction: discord.Interaction,
        vista_previa=None
    ):


        captura_id = int(
            self.seleccionados[0]
        )

        self.raid.seleccionar_pokemon(
            interaction.user.id,
            captura_id
        )

        cantidad = len(
            self.raid.selecciones
        )

        self.stop()

        embed = await self.crear_embed(
            vista_previa=vista_previa
        )

        embed.title = "✅ Pokémon seleccionado"
        embed.color = discord.Color.green()

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

        if self.raid.selecciones_completas:

            await interaction.channel.send(
                "⚔️ Iniciando incursión..."
            )

            resultado = await iniciar_incursion(
                self.raid,
                interaction.client.session
            )

            await interaction.channel.send(
                resultado
            )