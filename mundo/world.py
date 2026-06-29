import random

from database import (
    obtener_pokemon_aleatorios_por_tipo
)

from mundo.imagen_mundo import (
    generar_escena_mundo
)

from mundo.exploracion import Exploracion
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

        # Siempre habrá 3 espacios en el mundo
        self.pokemons = [
            None,
            None,
            None
        ]
        self.ultimo_pokemon = None

        self.ultimo_bioma = None
        self.exploracion = None

    def iniciar(self):

        self.tipo = random.choice(TIPOS)

        pokemons = obtener_pokemon_aleatorios_por_tipo(
            self.tipo,
            3
        )

        self.pokemons = [
            pokemons[0],
            pokemons[1],
            pokemons[2]
        ]

    def agregar_pokemon(self):

        for i in range(len(self.pokemons)):

            if self.pokemons[i] is None:

                pokemon = obtener_pokemon_aleatorios_por_tipo(
                    self.tipo,
                    1
                )[0]

                self.pokemons[i] = pokemon

                return True

        return False

    def eliminar_pokemon(self, indice):

        if 0 <= indice < len(self.pokemons):

            self.pokemons[indice] = None

    def pokemons_visibles(self):

        return [
            pokemon
            for pokemon in self.pokemons
            if pokemon is not None
        ]

    async def generar_gif(self):

        return await generar_escena_mundo(
            self.pokemons_visibles(),
            self.tipo
        )
    def evolucionar(self):

        if None in self.pokemons:

            self.agregar_pokemon()
    def esta_ocupado(self):

        return self.exploracion is not None


    def iniciar_exploracion(self, jugador_id):

        if self.esta_ocupado():
            return False



        self.exploracion = Exploracion(
            jugador_id
        )

        return True


    def finalizar_exploracion(self):

        self.exploracion = None