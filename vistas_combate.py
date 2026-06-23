import discord
import asyncio
import random
import os

import imagencomb
import servicios
import combate_servicios
import database

from combate import CombateSim


class VistaCombate(discord.ui.View):
    def __init__(
        self,
        p1,
        p2,
        equipo1,
        equipo2,
        session,
        *,
        modo="nombres",
        owner1_id=None,
        owner2_id=None,
    ):
        super().__init__(timeout=300)

        self.p1 = p1
        self.p2 = p2
        self.equipo1 = equipo1
        self.equipo2 = equipo2
        self.session = session
        self.modo = modo
        self.owner1_id = owner1_id
        self.owner2_id = owner2_id
        self.combate = None
        self.fondo_seleccionado = None

    async def preparar_combate(self):

        if self.modo == "capturas":

            equipo1 = await combate_servicios.preparar_equipo_desde_capturas(
                self.session,
                self.owner1_id,
                self.equipo1
            )

            equipo2 = await combate_servicios.preparar_equipo_desde_capturas(
                self.session,
                self.owner2_id,
                self.equipo2
            )

        else:

            equipo1 = await combate_servicios.preparar_equipos_completos(
                self.session,
                self.equipo1
            )

            equipo2 = await combate_servicios.preparar_equipos_completos(
                self.session,
                self.equipo2
            )

        self.combate = CombateSim(
            equipo1,
            equipo2
        )

    @discord.ui.button(
        label="¡Iniciar Combate Épico!",
        style=discord.ButtonStyle.danger
    )
    async def iniciar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        button.disabled = True

        await interaction.response.edit_message(
            content="⚔️ **¡El combate ha comenzado!**",
            view=self
        )

        msg = await interaction.original_response()

        carpeta_fondos = "fondos"

        lista_fondos = [
            f
            for f in os.listdir(carpeta_fondos)
            if f.endswith((".jpg", ".png"))
        ]

        self.fondo_seleccionado = random.choice(
            lista_fondos
        )

        while not self.combate.es_fin_del_juego():

            resumen_ronda = self.combate.ejecutar_ronda()

            e1 = self.combate.equipos["Jugador 1"]
            e2 = self.combate.equipos["Jugador 2"]

            p1_actual = e1["pokes"][e1["activo"]]
            p2_actual = e2["pokes"][e2["activo"]]

            hp1 = e1["hp"][e1["activo"]]
            hp_max1 = e1["hp_max"][e1["activo"]]

            hp2 = e2["hp"][e2["activo"]]
            hp_max2 = e2["hp_max"][e2["activo"]]

            turno_atacante = (
                1
                if resumen_ronda.startswith(
                    p1_actual["nombre"]
                )
                else 2
            )

            # ==================================================
            # IDs visuales (compatibles con formas regionales)
            # ==================================================

            id1 = p1_actual.get("id")

            if not id1:

                pokemon1 = database.obtener_pokemon_local_nombre(
                    p1_actual["nombre"]
                )

                if pokemon1:
                    id1 = pokemon1.get(
                        "pokeapi_id",
                        pokemon1["id"]
                    )
                else:
                    id1 = 25

            id2 = p2_actual.get("id")

            if not id2:

                pokemon2 = database.obtener_pokemon_local_nombre(
                    p2_actual["nombre"]
                )

                if pokemon2:
                    id2 = pokemon2.get(
                        "pokeapi_id",
                        pokemon2["id"]
                    )
                else:
                    id2 = 25

            buffer = await imagencomb.generar_escena_combate(
                self.session,
                id1,
                id2,
                nombre1=p1_actual["nombre"],
                nombre2=p2_actual["nombre"],
                hp1=hp1,
                hp2=hp2,
                hp_max1=hp_max1,
                hp_max2=hp_max2,
                turno_jugador=turno_atacante,
                es_shiny1=p1_actual.get(
                    "shiny",
                    False
                ),
                es_shiny2=p2_actual.get(
                    "shiny",
                    False
                ),
                fondo_nombre=self.fondo_seleccionado
            )

            file = discord.File(
                buffer,
                filename="combate.png"
            )

            embed = discord.Embed(
                title="⚔️ Duelo Épico",
                color=discord.Color.red()
            )

            embed.set_image(
                url="attachment://combate.png"
            )

            embed.add_field(
                name=f"👤 {self.p1.display_name}",
                value=f"**{p1_actual['nombre']}**",
                inline=True
            )

            embed.add_field(
                name="VS",
                value="🆚",
                inline=True
            )

            embed.add_field(
                name=f"👤 {self.p2.display_name}",
                value=f"**{p2_actual['nombre']}**",
                inline=True
            )

            embed.add_field(
                name="📜 Resumen de la ronda",
                value=resumen_ronda,
                inline=False
            )

            await msg.edit(
                embed=embed,
                attachments=[file]
            )

            ganador = self.combate.es_fin_del_juego()

            if ganador:

                await interaction.followup.send(
                    f"🏆 **¡El combate ha finalizado!**\n"
                    f"El ganador es: "
                    f"**{self.p1.display_name if ganador == 'Jugador 1' else self.p2.display_name}**"
                )

                break

            await asyncio.sleep(6)

    def on_timeout(self):
        self.stop()