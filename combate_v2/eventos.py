from dataclasses import dataclass


@dataclass
class Evento:

    tipo: str
    turno: int


@dataclass
class EventoInicio(Evento):

    pokemon1: str
    pokemon2: str


@dataclass
class EventoMovimiento(Evento):

    atacante: str
    movimiento: str


@dataclass
class EventoDaño(Evento):

    atacante: str
    defensor: str

    dano: int

    hp_actual: int
    hp_max: int

    critico: bool = False
    efectivo: float = 1.0



@dataclass
class EventoDebilitado(Evento):

    pokemon: str


@dataclass
class EventoCambioPokemon(Evento):

    entrenador: str

    sale: str
    entra: str


@dataclass
class EventoVictoria(Evento):

    ganador: str