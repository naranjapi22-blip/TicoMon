from .eventos import (
    EventoInicio,
    EventoMovimiento,
    EventoDaño,
    EventoCambioPokemon,
    EventoVictoria,
    EventoKO,
)

import copy
from .paso import PasoCombate

class MotorCombate:

    def __init__(self):

        self.pasos = []
    def limpiar(self):

        self.pasos.clear()

    def inicio(
        self,
        equipos,
        pokemon1,
        pokemon2
    ):

        evento = EventoInicio(

            tipo="inicio",

            turno=0,

            pokemon1=pokemon1,

            pokemon2=pokemon2

        )

        self.agregar_paso(
            evento,
            equipos
        )

    def ataque(
        self,
        equipos,
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

        evento = EventoMovimiento(

            tipo="movimiento",

            turno=turno,

            atacante=atacante,

            movimiento=movimiento,

        )

        self.agregar_paso(
            evento,
            equipos
        )

        # ===========================
        # Nuevo evento: Daño
        # ===========================

        evento = EventoDaño(

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

        self.agregar_paso(
            evento,
            equipos
        )


    def cambio(
        self,
        equipos,
        turno,
        entrenador,
        sale,
        entra
    ):

        evento = EventoCambioPokemon(

            tipo="cambio",

            turno=turno,

            entrenador=entrenador,

            sale=sale,

            entra=entra

        )

        self.agregar_paso(
            evento,
            equipos
        )

    def victoria(
        self,
        equipos,
        turno,
        ganador
    ):

        evento = EventoVictoria(

            tipo="victoria",

            turno=turno,

            ganador=ganador

        )

        self.agregar_paso(
            evento,
            equipos
        )




    def agregar_paso(
        self,
        evento,
        equipos,
        pausa=1.5,
    ):


        self.pasos.append(

            PasoCombate(

                evento=evento,

                estado=copy.deepcopy(
                    equipos
                ),

                pausa=pausa

            )

        )
    def obtener_pasos(self):

        return self.pasos
def ko(
    self,
    equipos,
    turno,
    pokemon,
):

    evento = EventoKO(

        tipo="ko",

        turno=turno,

        pokemon=pokemon

    )

    self.agregar_paso(
        evento,
        equipos,
        pausa=2.2
    )