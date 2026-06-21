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

        while not self.combate.es_fin_del_juego():

            resultado = self.combate.ejecutar_ronda()

            await mensaje.edit(
                content=
                f"⚔️ Ronda {ronda}\n\n"
                f"{resultado}"
            )

            ronda += 1

            await asyncio.sleep(2)

        ganador = self.combate.es_fin_del_juego()

        if ganador == "Jugador 1":

            await mensaje.edit(
                content=
                "🏆 ¡Victoria!\n\n"
                "Alpha derrotado."
            )

        else:

            await mensaje.edit(
                content=
                "💀 Derrota\n\n"
                "El Alpha venció al equipo."
            )