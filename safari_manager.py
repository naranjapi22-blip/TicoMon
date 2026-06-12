import asyncio
import logging

log = logging.getLogger(__name__)


class SafariManager:

    def __init__(self):
        self.activo = False
        self.guild_id = None
        self.canal_id = None

        self.participantes = {}

        self.encuentro_actual = None

        self.encuentro_numero = 0
        self.max_encuentros = 10

        self.tarea_principal = None

    async def iniciar_safari(
        self,
        guild_id,
        canal_id
    ):
        self.activo = True

        self.guild_id = guild_id
        self.canal_id = canal_id

        self.participantes.clear()

        self.encuentro_actual = None

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

        self.participantes.clear()

        self.encuentro_actual = None

        self.encuentro_numero = 0

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
            f"✅ Participante agregado: {user_id}"
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
        return self.participantes.get(
            user_id
        )

    def cantidad_participantes(
        self
    ):
        return len(
            self.participantes
        )


# ==========================
# Registro global
# ==========================

safaris_activos = {}


def obtener_safari(
    guild_id
):
    return safaris_activos.get(
        guild_id
    )


def crear_safari(
    guild_id,
    canal_id
):

    safari = SafariManager()

    safaris_activos[
        guild_id
    ] = safari

    return safari


def eliminar_safari(
    guild_id
):

    safaris_activos.pop(
        guild_id,
        None
    )