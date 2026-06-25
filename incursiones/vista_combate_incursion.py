import discord
import asyncio
from incursiones.imagen_raid import generar_escena_raid

from incursiones.combate_raid import CombateRaidSim


class VistaCombateIncursion:

    def __init__(
        self,
        canal,
        session,
        equipo_jugador,
        alpha
    ):
        self.canal = canal
        self.session = session
        self.equipo_jugador = equipo_jugador
        self.alpha = alpha

        self.combate = CombateRaidSim(
            equipo_jugador,
            alpha
        )

    def barra_hp(
        self,
        actual,
        maximo
    ):

        if maximo <= 0:
            return "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛"

        porcentaje = actual / maximo

        llenos = int(
            porcentaje * 10
        )

        if actual > 0 and llenos == 0:
            llenos = 1

        vacios = 10 - llenos

        if porcentaje >= 0.6:
            color = "🟩"

        elif porcentaje >= 0.3:
            color = "🟨"

        else:
            color = "🟥"

        return (
            color * llenos +
            "⬛" * vacios
        )

    def construir_estado(self):

        lineas_jugadores = []

        for i, pokemon in enumerate(
            self.combate.jugadores
        ):

            hp = self.combate.hp_jugadores[i]
            hp_max = pokemon["hp_max"]

            if hp <= 0:

                lineas_jugadores.append(
                    f"💀 {pokemon['nombre']}\n"
                    f"⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛\n"
                    f"0/{hp_max} HP"
                )

            else:

                lineas_jugadores.append(
                    f"❤️ {pokemon['nombre']}\n"
                    f"{self.barra_hp(hp, hp_max)}\n"
                    f"{hp}/{hp_max} HP"
                )

        return (
            f"{chr(10).join(lineas_jugadores)}\n\n"
            f"🐉 {self.combate.alpha['nombre']}\n"
            f"{self.barra_hp(self.combate.hp_alpha, self.combate.hp_alpha_max)}\n"
            f"{self.combate.hp_alpha}/{self.combate.hp_alpha_max} HP"
        )

    async def iniciar(self):

        mensaje = await self.canal.send(
            "⚔️ Comenzando incursión...\n"
            "🎨 Preparando escenario..."
        )

        # Imagen inicial

        buffer = await generar_escena_raid(
            self.session,
            self.combate.jugadores,
            self.combate.hp_jugadores,
            self.combate.alpha,
            self.combate.hp_alpha,
            self.combate.hp_alpha_max,
            "bosque.png"
        )

        file = discord.File(
            buffer,
            filename="raid.png"
        )

        await mensaje.edit(
            content=(
                "⚔️ ¡La incursión ha comenzado!\n\n"
                f"👹 {self.combate.alpha['nombre']} apareció."
            ),
            attachments=[file]
        )

        await asyncio.sleep(3)

        ronda = 1

        while not self.combate.es_fin_del_juego():

            estado_inicial = self.construir_estado()

            eventos = self.combate.ejecutar_ronda()

            historial_visible = []

            for evento in eventos:

                historial_visible.append(
                    evento
                )

                texto = (
                    f"⚔️ Ronda {ronda}\n\n"
                    f"{estado_inicial}\n\n"
                    f"{chr(10).join(historial_visible)}"
                )

                await mensaje.edit(
                    content=texto
                )

                await asyncio.sleep(1)

            estado_final = self.construir_estado()

            buffer = await generar_escena_raid(
                self.session,
                self.combate.jugadores,
                self.combate.hp_jugadores,
                self.combate.alpha,
                self.combate.hp_alpha,
                self.combate.hp_alpha_max,
                "bosque.png"
            )

            file = discord.File(
                buffer,
                filename="raid.png"
            )

            texto_final = (
                f"⚔️ Ronda {ronda}\n\n"
                f"{estado_final}\n\n"
                f"{chr(10).join(eventos)}"
            )

            await mensaje.edit(
                content=texto_final,
                attachments=[file]
            )

            ronda += 1

            await asyncio.sleep(1)

        ganador = self.combate.es_fin_del_juego()

        if ganador == "Jugadores":

            await mensaje.edit(
                content=(
                    "🏆 ¡Victoria!\n\n"
                    f"👹 {self.combate.alpha['nombre']} fue derrotado."
                )
            )

        elif ganador == "Alpha":

            await mensaje.edit(
                content=(
                    "💀 Derrota\n\n"
                    f"👹 {self.combate.alpha['nombre']} venció al equipo."
                )
            )