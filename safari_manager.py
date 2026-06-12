import asyncio
import logging
import random
import servicios
log = logging.getLogger(__name__)
from database import guardar_captura


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

        pokemon_id = random.randint(1, 151)

        data, species = await servicios.obtener_pokemon(
            self.session,
            pokemon_id
        )

        if not data:
            await self.canal.send(
                f"❌ Error obteniendo Pokémon {pokemon_id}"
            )
            return

        nombre = data["name"].capitalize()
        from mapeo_pokes import obtener_id_gif

        dex_id = data["id"]
        id_final = obtener_id_gif(dex_id)

        path_folder = "shiny" if es_shiny else "regular"

        url_gif = (
            f"https://www.shinyhunters.com/images/"
            f"{path_folder}/{id_final}.gif"
        )

        tamano_factor = round(
            random.uniform(0.50, 1.50),
            2
        )

        es_shiny = random.random() <= 0.01

        self.crear_encuentro(
            pokemon_id,
            nombre,
            es_shiny,
            tamano_factor
        )

        view = self.creador_vistas(
            self.guild_id
        )
        await self.canal.send(url_gif)
        mensaje = await self.canal.send(
            f"🚙 Encuentro {self.encuentro_numero}/{self.max_encuentros}\n\n"
            pokemon_texto = (
                f"✨ SHINY ✨ {nombre}"
                if es_shiny
                else nombre
            )
            f"⏳ Tienen 30 segundos para apostar.",
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

            for user_id, balls in apuestas.items():

                lista.extend(
                    [user_id] * balls
                )

            ganador_id = random.choice(
                lista
            )

            self.participantes[
                ganador_id
            ]["capturas"] += 1

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
            "balls": 15,
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
        pokemon_id,
        nombre,
        es_shiny=False,
        tamano_factor=1.0
    ):

        self.encuentro_actual = {
            "pokemon_id": pokemon_id,
            "nombre": nombre.lower(),
            "es_shiny": es_shiny,
            "tamano_factor": tamano_factor,
            "apuestas": {}
        }

        log.info(
            f"🐾 Encuentro creado: {nombre}"
        )

    def registrar_apuesta(
        self,
        user_id,
        cantidad
    ):

        if user_id not in self.participantes:
            return False, "No participas en este Safari."

        if user_id in self.encuentro_actual["apuestas"]:
            return False, "Ya apostaste en este encuentro."

        datos = self.participantes[user_id]

        if datos["balls"] < cantidad:
            return False, "No tienes suficientes Safari Balls."

        datos["balls"] -= cantidad

        self.encuentro_actual["apuestas"][user_id] = cantidad

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
