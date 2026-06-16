
import database

TIER_COSTS = {
    "basic": 10,
    "standard": 20,
    "advanced": 40,
    "exceptional": 100
}

def get_evolution_cost(tier):
    return TIER_COSTS.get(tier, 20)


def get_evolutions(pokemon_nombre):

    conn = database.get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                evoluciona_a,
                metodo,
                tier,
                tipo_caramelo
            FROM pokemon_evolutions
            WHERE pokemon_nombre = %s
            ORDER BY evoluciona_a
        """, (
            pokemon_nombre.lower(),
        ))

        return cursor.fetchall()

    finally:

        cursor.close()
        conn.close()


def get_evolution_choice(pokemon_nombre, choice_number):

    evoluciones = get_evolutions(
        pokemon_nombre
    )

    if choice_number < 1:
        return None

    if choice_number > len(evoluciones):
        return None

    return evoluciones[choice_number - 1]

