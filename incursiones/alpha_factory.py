from database import obtener_pokemon_local_nombre


def crear_alpha(nombre_pokemon):

    nombre_pokemon = (
        str(nombre_pokemon)
        .replace("Alpha ", "")
        .strip()
        .lower()
    )

    print(f"🎯 Creando Alpha: {nombre_pokemon}")

    pokemon = obtener_pokemon_local_nombre(
        nombre_pokemon
    )

    if not pokemon:
        print(f"❌ Pokémon no encontrado: {nombre_pokemon}")
        return None

    print(f"✅ Datos encontrados: {pokemon['nombre']}")

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
        "hp_max": pokemon["hp"] * 35,

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