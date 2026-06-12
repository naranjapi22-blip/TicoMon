import random

REGIONES = {
    "Kanto": {
        "inicio": 1,
        "fin": 151
    },
    "Johto": {
        "inicio": 152,
        "fin": 251
    },
    "Hoenn": {
        "inicio": 252,
        "fin": 386
    },
    "Sinnoh": {
        "inicio": 387,
        "fin": 493
    },
    "Unova": {
        "inicio": 494,
        "fin": 649
    },
    "Kalos": {
        "inicio": 650,
        "fin": 721
    },
    "Alola": {
        "inicio": 722,
        "fin": 809
    },
    "Galar": {
        "inicio": 810,
        "fin": 905
    },
    "Paldea": {
        "inicio": 906,
        "fin": 1025
    }
}

_baraja_regiones = []


def obtener_siguiente_region():

    global _baraja_regiones

    if not _baraja_regiones:

        _baraja_regiones = list(
            REGIONES.keys()
        )

        random.shuffle(
            _baraja_regiones
        )

    return _baraja_regiones.pop(0)


def obtener_rango_region(
    nombre_region
):

    return REGIONES.get(
        nombre_region
    )