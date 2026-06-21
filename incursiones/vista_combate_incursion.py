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
            j1 = self.combate.equipos["Jugador 1"]
            j2 = self.combate.equipos["Jugador 2"]

            hp1 = j1["hp"][j1["activo"]]
            hp1_max = j1["hp_max"][j1["activo"]]

            hp2 = j2["hp"][j2["activo"]]
            hp2_max = j2["hp_max"][j2["activo"]]

            nombre1 = j1["pokes"][j1["activo"]]["nombre"]
            nombre2 = j2["pokes"][j2["activo"]]["nombre"]
            historial.append(
                f"⚔️ Ronda {ronda}\n\n"
                f"🔥 {nombre1}: {hp1}/{hp1_max} HP\n"
                f"🐉 {nombre2}: {hp2}/{hp2_max} HP\n\n"
                f"{resultado}"
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