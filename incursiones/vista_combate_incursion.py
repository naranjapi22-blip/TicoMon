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

            poke1 = self.combate.jugadores[0]
            poke2 = self.combate.alpha

            hp1 = self.combate.hp_jugadores[0]
            hp1_max = poke1["hp_max"]

            hp2 = self.combate.hp_alpha
            hp2_max = self.combate.hp_alpha_max

            nombre1 = poke1["nombre"]
            nombre2 = poke2["nombre"]
            lineas_jugadores = []

            for i, pokemon in enumerate(self.combate.jugadores):

                hp = self.combate.hp_jugadores[i]

                lineas_jugadores.append(
                    f"{pokemon['nombre']}: {hp}/{pokemon['hp_max']} HP"
                )
            texto_ronda = (
                f"⚔️ Ronda {ronda}\n\n"
                f"{chr(10).join(lineas_jugadores)}\n\n"
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

            await asyncio.sleep(8)

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
