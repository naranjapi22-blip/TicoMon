from datetime import date

import database

from mundo.world import World
from mundo.mundo_manager import mundo_manager

class MundoManager:

    def calcular_objetivo(
        self,
        guild_id
    ):
        # Temporal
        return 100

    def obtener_estado(
        self,
        guild_id
    ):

        fila = database.obtener_world(
            guild_id
        )

        if not fila:

            objetivo = self.calcular_objetivo(
                guild_id
            )

            database.crear_world(
                guild_id,
                date.today(),
                objetivo
            )

            fila = database.obtener_world(
                guild_id
            )

        world = World(
            guild_id
        )

        (
            world.fecha,
            world.objetivo,
            world.progreso,
            world.safaris_desbloqueados,
            world.safaris_utilizados
        ) = fila

        if world.fecha != date.today():

            objetivo = self.calcular_objetivo(
                guild_id
            )

            database.reiniciar_world(
                guild_id,
                date.today(),
                objetivo
            )

            return self.obtener_estado(
                guild_id
            )

        return world

    def sumar_progreso(
        self,
        guild_id,
        cantidad=1
    ):

        world = self.obtener_estado(
            guild_id
        )

        world.sumar_progreso(
            cantidad
        )

        desbloqueados = min(
            5,
            world.porcentaje // 20
        )

        nuevo = (
            desbloqueados >
            world.safaris_desbloqueados
        )

        world.safaris_desbloqueados = desbloqueados

        database.guardar_world(
            world
        )

        return nuevo

    def usar_safari(
        self,
        guild_id
    ):

        world = self.obtener_estado(
            guild_id
        )

        if not world.usar_safari():

            return False

        database.guardar_world(
            world
        )

        return True


mundo_manager = MundoManager()