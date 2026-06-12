import asyncio
import logging
import random
import servicios
log = logging.getLogger(__name__)
from database import guardar_captura
import discord
from utils_imagenes import crear_imagen_encuentro
from regiones import obtener_siguiente_region, obtener_rango_region
from rarezas import (
    pokemon_por_rareza,
    generar_ids_safari_region
)
class SafariManager:

    def __init__(self):

        self.activo = False

        self.guild_id = None
        self.canal_id = None

        self.participantes = {}
        self.canal = None
        self.session = None
        self.creador_vistas = None
        self.encuentro_actual = {
            "pokemon_id": None,
            "nombre": None,
            "es_shiny": False,
            "tamano_factor": 1.0,
            "apuestas": {}
        }

        self.encuentro_numero = 0
        self.max_encuentros = 3

        self.tarea_principal = None

    async def iniciar_safari(
        self,
        guild_id,
        canal_id,
        canal,
        session,
        creador_vistas
    ):
        self.guild_id = guild_id
        self.canal_id = canal_id
        self.canal = canal
        self.session = session
        self.creador_vistas = creador_vistas
        self.activo = True
        self.participantes.clear()
        self.region_actual = obtener_siguiente_region()
        self.encuentro_actual = {
            "pokemon_id": None,
            "nombre": None,
            "es_shiny": False,
            "tamano_factor": 1.0,
            "apuestas": {}
        }

        self.encuentro_numero = 0

        log.info(
            f"🚙 Safari iniciado en guild {guild_id}"
        )

    async def finalizar_safari(self):

        if self.canal:
            await self.canal.send(
                "🏁 Safari finalizado."
            )

        log.info(
            f"🏁 Safari finalizado en guild {self.guild_id}"
        )

        self.activo = False

        self.guild_id = None
        self.canal_id = None


        ranking = sorted(
            self.participantes.items(),
            key=lambda x: x[1]["capturas"],
            reverse=True
        )

        texto = "🏆 Resultados del Safari\n\n"

        for posicion, (user_id, datos) in enumerate(ranking, start=1):

            texto += (
                f"{posicion}. <@{user_id}> - "
                f"{datos['capturas']} captura(s)\n"
            )

        await self.canal.send(texto)
        self.session = None
        self.creador_vistas = None
        
        self.participantes.clear()

        self.encuentro_actual = {
            "pokemon_id": None,
            "nombre": None,
            "es_shiny": False,
            "tamano_factor": 1.0,
            "apuestas": {}
        }

        self.encuentro_numero = 0

    async def ejecutar_encuentro(self):
    


        tamano_factor = round(
            random.uniform(0.50, 1.50),
            2
        )

        pokemons = []

        rango = obtener_rango_region(
            self.region_actual
        )

        ids_safari = generar_ids_safari_region(
            rango["inicio"],
            rango["fin"]
        )
        print("IDS SAFARI:", ids_safari)
        print(
            f"REGION: {self.region_actual} | "
            f"RANGO: {rango['inicio']}-{rango['fin']}"
        )
        encuentro_shiny = (
            random.random() <= 0.0025
        )
        for slot, pokemon_id_tmp in enumerate(
            ids_safari,
            start=1
        ):

            data_tmp, species_tmp = await servicios.obtener_pokemon(
                self.session,
                pokemon_id_tmp
            )

            if not data_tmp:
                continue

            pokemons.append({
                "slot": slot,
                "pokemon_id": pokemon_id_tmp,
                "nombre": data_tmp["name"].lower(),
                "capture_rate": species_tmp["capture_rate"],
                "es_shiny": encuentro_shiny,
                "tamano_factor": round(
                    random.uniform(0.50, 1.50),
                    2
                )
            })

        self.crear_encuentro(
            pokemons
        )
        from vistas_safari import VistaSeleccionPokemon
        view = VistaSeleccionPokemon(
            self.guild_id,
            self.encuentro_actual["pokemons"]
        )

        pokemon_texto = "\n".join(
            [
                f"{p['slot']}️⃣ {'✨ SHINY ✨ ' if p['es_shiny'] else ''}{p['nombre'].capitalize()}"
                for p in self.encuentro_actual["pokemons"]
            ]
        )
        embed = discord.Embed(
            title=f"🚙 Encuentro {self.encuentro_numero}/{self.max_encuentros}",
            description=(
                f"🐾 Pokémon disponibles:\n\n"
                f"{pokemon_texto}\n\n"
                f"⏳ Tienen 30 segundos para apostar."
            )
        )
        buffer = await crear_imagen_encuentro(
            self.encuentro_actual["pokemons"],
            self.session,
        )
        print("POKEMONS:", pokemons)
        print("BUFFER:", buffer)
        if buffer:
            print("IMAGEN GENERADA")
        else:
            print("NO SE GENERÓ IMAGEN")
        file = None

        if buffer:
            file = discord.File(
                buffer,
                filename="encuentro.png"
            )
        embed.set_image(url="attachment://encuentro.png")

        mensaje = await self.canal.send(
            embed=embed,
            file=file,
            view=view
        )
        view.message = mensaje

        await asyncio.sleep(30)

        apuestas = self.encuentro_actual["apuestas"]

        if not apuestas:

            await self.canal.send(
                "💨 Nadie intentó capturar al Pokémon."
            )

        else:

            await self.canal.send(
                f"🎯 Participaron {len(apuestas)} entrenador(es)."
            )

            lista = []

            for user_id, datos_apuesta in apuestas.items():

                lista.extend(
                    [user_id] * datos_apuesta["balls"]
                )

            ganador_id = random.choice(
                lista
            )

            slot_ganador = apuestas[ganador_id]["slot"]

            pokemon_elegido = next(
                p
                for p in self.encuentro_actual["pokemons"]
                if p["slot"] == slot_ganador
            )

            capture_rate = pokemon_elegido[
                "capture_rate"
            ]

            balls = apuestas[
                ganador_id
            ]["balls"]

            probabilidad = (
                0.10 +
                (capture_rate / 255) * 0.70
            )

            probabilidad += (
                (balls - 1) * 0.05
            )

            probabilidad = min(
                probabilidad,
                0.95
            )

            capturado = (
                random.random() <= probabilidad
            )

            print(
                f"CAPTURE RATE: {capture_rate} | "
                f"BALLS: {balls} | "
                f"PROB: {probabilidad:.2%}"
            )

            nombre = pokemon_elegido["nombre"].capitalize()
            es_shiny = pokemon_elegido["es_shiny"]
            tamano_factor = pokemon_elegido["tamano_factor"]

            if not capturado:

                await self.canal.send(
                    f"💨 {nombre} escapó de las Safari Balls de <@{ganador_id}>.\n"
                    f"🎯 Probabilidad de captura: {probabilidad:.0%}"
                )

                return
            print(
                f"GUARDANDO: {nombre} "
                f"user={ganador_id}"
            )
            try:

                await guardar_captura(
                    ganador_id,
                    nombre,
                    tamano_factor,
                    es_shiny
                )

            except Exception as e:

                log.error(
                    f"Error guardando captura Safari: {e}",
                    exc_info=True
                )

                await self.canal.send(
                    "❌ Ocurrió un error al guardar la captura."
                )

                return

            self.participantes[
                ganador_id
            ]["capturas"] += 1

            captura_texto = (
                f"✨ SHINY ✨ {nombre}"
                if es_shiny
                else nombre
            )

            await self.canal.send(
                f"🎉 <@{ganador_id}> capturó a {captura_texto}."
            )
        try:

            await guardar_captura(
                ganador_id,
                nombre,
                tamano_factor,
                es_shiny
            )
            self.participantes[
                ganador_id
            ]["capturas"] += 1
        except Exception as e:

            log.error(
                f"Error guardando captura Safari: {e}",
                exc_info=True
            )

            await self.canal.send(
                "❌ Ocurrió un error al guardar la captura."
            )

            return

        self.participantes[
            ganador_id
        ]["capturas"] += 1

        captura_texto = (
            f"✨ SHINY ✨ {nombre.capitalize()}"
            if es_shiny
            else nombre.capitalize()
        )

        await self.canal.send(
            f"🎉 <@{ganador_id}> capturó a {captura_texto}."
        )
    async def ejecutar_safari(self):
        self.encuentro_numero = 1

        while self.encuentro_numero <= self.max_encuentros:
            await self.ejecutar_encuentro()
            self.encuentro_numero += 1
        await self.finalizar_safari()

    def agregar_participante(
        self,
        user_id
    ):

        if not self.activo:
            return False

        if user_id in self.participantes:
            return False

        self.participantes[user_id] = {
            "balls": 18,
            "capturas": 0
        }

        log.info(
            f"🚙 Participante agregado: {user_id}"
        )

        return True

    def es_participante(
        self,
        user_id
    ):
        return user_id in self.participantes

    def obtener_participante(
        self,
        user_id
    ):
        return self.participantes.get(user_id)

    def cantidad_participantes(
        self
    ):
        return len(self.participantes)

    def crear_encuentro(
        self,
        pokemons
    ):

        self.encuentro_actual = {
            "pokemons": pokemons,
            "apuestas": {},
            "selecciones": {}
        }

        log.info(
            f"🐾 Encuentro creado con {len(pokemons)} Pokémon(s)"
        )

    def registrar_apuesta(
        self,
        user_id,
        cantidad,
        slot=1
        ):

        if user_id not in self.participantes:
            return False, "No participas en este Safari."

        if user_id in self.encuentro_actual["apuestas"]:
            return False, "Ya apostaste en este encuentro."

        datos = self.participantes[user_id]

        if datos["balls"] < cantidad:
            return False, "No tienes suficientes Safari Balls."

        datos["balls"] -= cantidad

        self.encuentro_actual["apuestas"][user_id] = {
            "balls": cantidad,
            "slot": slot
        }

        log.info(
            f"🎯 Apuesta: user={user_id} slot={slot} balls={cantidad}"
        )
        log.info(
            f"🎯 Usuario {user_id} apostó {cantidad} balls"
        )

        log.info(
            f"🎯 Apuestas actuales: {self.encuentro_actual['apuestas']}"
        )

        return True, "Apuesta registrada."


# ==========================
# Registro global
# ==========================

safaris_activos = {}


def obtener_safari(guild_id):

    return safaris_activos.get(
        guild_id
    )


def crear_safari(
    guild_id,
    canal_id
):

    safari = SafariManager()

    safaris_activos[guild_id] = safari

    return safari


def eliminar_safari(
    guild_id
):

    safaris_activos.pop(
        guild_id,
        None
    )
