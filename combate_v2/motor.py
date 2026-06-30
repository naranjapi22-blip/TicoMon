from .eventos import (
    EventoInicio,
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
    def obtener_snapshot(self, indice):

        return self.snapshots[indice]