import random

ALPHAS_DISPONIBLES = [
    "charizard",
    "venusaur",
    "blastoise",
    "dragonite",
    "tyranitar",
    "metagross",
    "garchomp",
    "lucario",
    "volcarona",
    "hydreigon",
    "mamoswine",
    "togekiss",
]


def obtener_alpha_aleatorio():
    return random.choice(ALPHAS_DISPONIBLES)