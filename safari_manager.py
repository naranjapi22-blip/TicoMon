import asyncio
import logging
import random
import servicios
from vistas_safari import VistaApuestasSafari
log = logging.getLogger(__name__)



class SafariManager:

    def __init__(self):

        self.activo = False

        self.guild_id = None
        self.canal_id = None

        self.participantes = {}
        self.canal = None
        self.session = None
        self.encuentro_actual = {
            "pokemon_id": None,
            "nombre": None,
            "es_shiny": False,
            "tamano_factor": 1.0,
            "apuestas": {}
        }

        self.encuentro_numero = 0
        self.max_encuentros = 10

        self.tarea_principal = None

    async def iniciar_safari(
        self,
        guild_id,
        canal_id,
        canal,
        session
    ):

        self.activo = True

        self.guild_id = guild_id
        self.canal_id = canal_id
        self.canal = canal
        self.session = session

        self.activo = True

        self.guild_id = guild_id
        self.canal_id = canal_id

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

        log.info(
            f"🏁 Safari finalizado en guild {self.guild_id}"
        )

        self.activo = False

        self.guild_id = None
        self.canal_id = None
        self.canal = None

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
        log.info(f"DEBUG data={data}")
        log.info(f"DEBUG species={species}")
        nombre = data["name"].capitalize()

        tamano_factor = round(
            random.uniform(0.50, 1.50),
            2
        )

        self.crear_encuentro(
            pokemon_id,
            nombre,
            False,
            tamano_factor
        )

        mensaje = await self.canal.send(
            f"🚙 Encuentro {self.encuentro_numero}/{self.max_encuentros}\n\n"
            f"🐾 ¡Un {nombre} apareció!\n\n"
            f"⏳ Tienen 30 segundos para apostar.",
            view=view
        )

        view.message = mensaje

        view = VistaApuestasSafari(
            self.guild_id
        )

        await asyncio.sleep(30)

    async def ejecutar_safari(self):
        self.encuentro_numero = 1

        while self.encuentro_numero <= self.max_encuentros:
            await self.ejecutar_encuentro()
            self.encuentro_numero += 1

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
