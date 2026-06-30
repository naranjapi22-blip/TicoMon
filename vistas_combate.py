import discord
import asyncio
import random
import os
from combate_v2.orquestador import CombateV2
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
        self.imagen_actual = None
        self.historial = []
        self.msg_imagen = None
        self.msg_ui = None
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

        await interaction.response.edit_message(
            content="⚔️ ¡El combate ha comenzado!",
            view=None
        )

        buffer = await imagencomb.generar_escena_combate(
            ...
        )

        self.msg_imagen = await interaction.followup.send(
            file=discord.File(
                buffer,
                filename="combate.png"
            ),
            wait=True
        )

        self.msg_ui = await interaction.followup.send(
            embed=discord.Embed(
                title="⚔️ Preparando combate..."
            ),
            wait=True
        )

        self.msg_ui = await interaction.followup.send(

            embed=discord.Embed(
                title="⚔️ Preparando combate..."
            ),

            wait=True

        )
        self.interaction = interaction

        eventos = self.combate.simular()

        snapshots = self.combate.obtener_snapshots()

        orquestador = CombateV2()

        await orquestador.reproducir(
            eventos,
            snapshots,
            callback=self.actualizar_discord
        )

        ganador = self.combate.es_fin_del_juego()

        await interaction.followup.send(
            f"🏆 **¡El combate ha finalizado!**\n"
            f"El ganador es: "
            f"**{self.p1.display_name if ganador == 'Jugador 1' else self.p2.display_name}**"
        )
    def on_timeout(self):
        self.stop()
    async def actualizar_discord(
        self,
        paso,
        historial,
    ):
        try:

            print("ACTUALIZANDO DISCORD")
            evento = paso["evento"]

            estado = paso["estado"]

            e1 = estado["Jugador 1"]
            e2 = estado["Jugador 2"]

            p1_actual = e1["pokes"][e1["activo"]]
            p2_actual = e2["pokes"][e2["activo"]]

            hp1 = e1["hp"][e1["activo"]]
            hp_max1 = e1["hp_max"][e1["activo"]]

            hp2 = e2["hp"][e2["activo"]]
            hp_max2 = e2["hp_max"][e2["activo"]]

            turno_atacante = 1

            if (
                evento.tipo == "ataque"
                and evento.atacante == p2_actual["nombre"]
            ):
                turno_atacante = 2

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


            barra1 = self.barra_hp(
                hp1,
                hp_max1
            )

            barra2 = self.barra_hp(
                hp2,
                hp_max2
            )
            embed = discord.Embed(
                title="⚔️ Duelo Épico",
                color=discord.Color.red()
            )

            embed.add_field(
                name=f"👤 {self.p1.display_name}",
                value=(
                    f"**{p1_actual['nombre']}**\n"
                    f"❤️ `{barra1}`\n"
                    f"**{hp1}/{hp_max1} HP**"
                ),
                inline=True
            )

            embed.add_field(
                name="🆚",
                value=" ",
                inline=True
            )

            embed.add_field(
                name=f"👤 {self.p2.display_name}",
                value=(
                    f"**{p2_actual['nombre']}**\n"
                    f"❤️ `{barra2}`\n"
                    f"**{hp2}/{hp_max2} HP**"
                ),
                inline=True
            )

            embed.add_field(
                name="📜 Últimas acciones",
                value="\n\n".join(historial),
                inline=False
            )
            embed.set_footer(
                text=f"Turno {evento.turno}"
            )
            actualizar_imagen = evento.tipo in (
                "inicio",
                "cambio",
                "victoria",
            )     
            if actualizar_imagen:

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

                self.imagen_actual = discord.File(
                    buffer,
                    filename="combate.png"
                )

                embed.set_image(
                    url="attachment://combate.png"
                )

                await self.msg_imagen.edit(

                    attachments=[self.imagen_actual]

                )

            await self.msg_ui.edit(
                embed=embed
            )


        except Exception:

            import traceback
            traceback.print_exc()
    def necesita_actualizar_imagen(self, escena):

        for evento in escena["eventos"]:

            if evento.tipo in (
                "inicio",
                "cambio",
                "victoria",
            ):
                return True

        return False
    def barra_hp(self, actual, maximo, largo=10):

        if maximo <= 0:
            return "░" * largo

        porcentaje = max(0, actual / maximo)

        llenos = round(
            porcentaje * largo
        )

        vacios = largo - llenos

        return (
            "█" * llenos +
            "░" * vacios
        )


    def agregar_historial(self, texto):

        self.historial.append(
            texto
        )

        self.historial = self.historial[-5:]    