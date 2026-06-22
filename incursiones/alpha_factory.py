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

        # HP muy aumentado
        "hp_max": pokemon["hp"] * 200,

        # Mantener ataque normal
        "atk": pokemon["attack"],
        "atk_esp": pokemon["special_attack"],

        # Aumentar defensas
        "def": pokemon["defense"] * 2,
        "def_esp": pokemon["special_defense"] * 2,

        # Mantener velocidad normal
        "spd": pokemon["speed"],

        "id": pokemon["id"],
        "shiny": False
    }]