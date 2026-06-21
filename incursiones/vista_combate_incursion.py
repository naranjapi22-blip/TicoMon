import discord
import asyncio

from combate import CombateSim


class VistaCombateIncursion:

    def __init__(
        self,
        canal,
        equipo_jugador,
        alpha
    ):
        self.canal = canal

        self.combate = CombateSim(
            equipo_jugador,
            alpha
        )

    async def iniciar(self):

        mensaje = await self.canal.send(
            "⚔️ Comenzando incursión..."
        )

        ronda = 1
        historial = []

        while not self.combate.es_fin_del_juego():

            resultado = self.combate.ejecutar_ronda()

            historial.append(
                f"⚔️ Ronda {ronda}\n{resultado}"
            )

            await mensaje.edit(
                content="\n\n".join(historial)
            )

            ronda += 1

            await asyncio.sleep(2)

        ganador = self.combate.es_fin_del_juego()

        if ganador == "Jugador 1":

            historial.append(
                "🏆 ¡Victoria!\n\nAlpha derrotado."
            )

        else:

            historial.append(
                "💀 Derrota\n\nEl Alpha venció al equipo."
            )

        await mensaje.edit(
            content="\n\n".join(historial)
        )