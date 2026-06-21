import discord
import asyncio
import imagencomb

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

    async def iniciar(self):

        mensaje = await self.canal.send(
            "⚔️ Comenzando incursión..."
        )

        ronda = 1

        while not self.combate.es_fin_del_juego():

            resultado = self.combate.ejecutar_ronda()

            j1 = self.combate.equipos["Jugador 1"]
            j2 = self.combate.equipos["Jugador 2"]

            poke1 = j1["pokes"][j1["activo"]]
            poke2 = j2["pokes"][j2["activo"]]

            hp1 = j1["hp"][j1["activo"]]
            hp1_max = j1["hp_max"][j1["activo"]]

            hp2 = j2["hp"][j2["activo"]]
            hp2_max = j2["hp_max"][j2["activo"]]

            nombre1 = poke1["nombre"]
            nombre2 = poke2["nombre"]

            texto_ronda = (
                f"⚔️ Ronda {ronda}\n\n"
                f"🔥 {nombre1}: {hp1}/{hp1_max} HP\n"
                f"🐉 {nombre2}: {hp2}/{hp2_max} HP\n\n"
                f"{resultado}"
            )

            buffer = await imagencomb.generar_escena_combate(
                self.session,
                poke1["id"],
                poke2["id"],
                nombre1,
                nombre2,
                hp1,
                hp2,
                hp1_max,
                hp2_max,
                "bosque.png"
            )

            file = discord.File(
                buffer,
                filename="raid.png"
            )

            await mensaje.edit(
                content=texto_ronda,
                attachments=[file]
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
