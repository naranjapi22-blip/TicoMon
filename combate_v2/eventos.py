from dataclasses import dataclass
from typing import Optional


@dataclass
class Evento:

    tipo: str
    turno: int


@dataclass
class EventoInicio(Evento):

    pokemon1: str
    pokemon2: str


@dataclass
class EventoAtaque(Evento):

    atacante: str
    defensor: str

    movimiento: str

    dano: int

    hp_actual: int
    hp_max: int

    critico: bool = False
    efectivo: float = 1.0

    debilitado: bool = False


@dataclass
class EventoCambioPokemon(Evento):

    entrenador: str

    sale: str
    entra: str


@dataclass
class EventoVictoria(Evento):

    ganador: str