from database import obtener_pokemon_local_nombre


def crear_alpha(nombre_pokemon):

    pokemon = obtener_pokemon_local_nombre(
        nombre_pokemon
    )

    if not pokemon: 
        return None

    return [{
        "nombre": f"Alpha {pokemon['nombre'].capitalize()}",
        "species_showdown": pokemon["nombre"].lower(),
        "nature_showdown": "hardy",
        "tipo": pokemon["tipos"],
        "ivs": {
            "hp": 31,
            "atk": 31,
            "def": 31,
            "spa": 31,
            "spd": 31,
            "spe": 31
        },
        "atk": pokemon["attack"] * 5,
        "atk_esp": pokemon["special_attack"] * 5,
        "def": pokemon["defense"] * 5,
        "def_esp": pokemon["special_defense"] * 5,
        "spd": pokemon["speed"] * 2,
        "hp_max": pokemon["hp"] * 500,
        "movimiento": "tackle",
        "movimiento_nombre": "Tackle",
        "id": pokemon["id"],
        "shiny": False
    }]