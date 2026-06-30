from .eventos import (
    EventoInicio,
    EventoMovimiento,
    EventoDaño,
    EventoAtaque,
    EventoCambioPokemon,
    EventoVictoria,
)

import copy


class MotorCombate:

    def __init__(self):

        self.eventos = []
        self.snapshots = []

    def limpiar(self):

        self.eventos.clear()
        self.snapshots.clear()

    def inicio(
        self,
        pokemon1,
        pokemon2
    ):

        self.eventos.append(

            EventoInicio(
                tipo="inicio",
                turno=0,
                pokemon1=pokemon1,
                pokemon2=pokemon2
            )

        )

    def ataque(
        self,
        turno,
        atacante,
        defensor,
        movimiento,
        dano,
        hp_actual,
        hp_max,
        critico=False,
        efectivo=1.0,
        debilitado=False,
    ):

        # ===========================
        # Nuevo evento: Movimiento
        # ===========================

        self.eventos.append(

            EventoMovimiento(

                tipo="movimiento",

                turno=turno,

                atacante=atacante,

                movimiento=movimiento,

            )

        )

        # ===========================
        # Nuevo evento: Daño
        # ===========================

        self.eventos.append(

            EventoDaño(

                tipo="dano",

                turno=turno,

                atacante=atacante,

                defensor=defensor,

                dano=dano,

                hp_actual=hp_actual,

                hp_max=hp_max,

                critico=critico,

                efectivo=efectivo,

            )

        )

        # ===========================
        # Evento antiguo (compatibilidad)
        # ===========================

        self.eventos.append(

            EventoAtaque(

                tipo="ataque",

                turno=turno,

                atacante=atacante,

                defensor=defensor,

                movimiento=movimiento,

                dano=dano,

                hp_actual=hp_actual,

                hp_max=hp_max,

                critico=critico,

                efectivo=efectivo,

                debilitado=debilitado

            )

        )

    def cambio(
        self,
        turno,
        entrenador,
        sale,
        entra
    ):

        self.eventos.append(

            EventoCambioPokemon(

                tipo="cambio",

                turno=turno,

                entrenador=entrenador,

                sale=sale,

                entra=entra

            )

        )

    def victoria(
        self,
        turno,
        ganador
    ):

        self.eventos.append(

            EventoVictoria(

                tipo="victoria",

                turno=turno,

                ganador=ganador

            )

        )

    def obtener_eventos(self):

        return list(self.eventos)

    def snapshot(self, equipos):

        self.snapshots.append(
            copy.deepcopy(equipos)
        )

    def snapshot(
        self,
        evento,
        equipos
    ):

        self.snapshots.append({

            "evento": evento,

            "estado": copy.deepcopy(equipos)

        })