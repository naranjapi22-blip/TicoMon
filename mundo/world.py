import random

from database import (
    obtener_pokemon_aleatorios_por_tipo
)

from mundo.imagen_mundo import (
    generar_escena_mundo
)


TIPOS = [
    "grass",
    "fire",
    "water",
    "electric",
    "psychic",
    "ghost",
    "dragon",
    "steel",
    "fairy",
    "ice",
    "fighting",
    "poison",
    "flying",
    "bug",
    "rock",
    "ground",
    "normal",
    "dark",
]


class World:

    def __init__(self):

        self.tipo = None

        self.pokemons = []

        self.ocupado = False

        self.jugador = None

    def iniciar(self):

        self.tipo = random.choice(
            TIPOS
        )

        self.pokemons = (
            obtener_pokemon_aleatorios_por_tipo(
                self.tipo,
                3
            )
        )

    async def generar_gif(self):

        return await generar_escena_mundo(
            self.pokemons,
            self.tipo
        )