from database import obtener_pokemon_local_nombre
from combate_calc import elegir_movimiento_automatico


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

    movimiento, movimiento_nombre = elegir_movimiento_automatico(
        pokemon["nombre"].lower(),
        {
            "atk": pokemon["attack"],
            "spa": pokemon["special_attack"]
        }
    )

    print(
        f"⚔️ Movimiento Alpha: "
        f"{movimiento_nombre} ({movimiento})"
    )

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

        # HP aumentado
        "hp_max": pokemon["hp"] * 35,

        # Ataque normal
        "atk": pokemon["attack"],
        "atk_esp": pokemon["special_attack"],

        # Defensa aumentada
        "def": int(pokemon["defense"] * 1.5),
        "def_esp": int(pokemon["special_defense"] * 1.5),

        # Velocidad normal
        "spd": pokemon["speed"],

        # Movimiento automático
        "movimiento": movimiento,
        "movimiento_nombre": movimiento_nombre,

        "id": pokemon["id"],
        "shiny": False
    }]