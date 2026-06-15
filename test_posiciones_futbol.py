import os
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_VWIP5pf7aGlw@ep-withered-brook-aq3njbjm-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

from database import get_connection



def calcular_stats_futbol(hp, atk, defense, spa, spd, speed):

    porteria = (
        hp * 0.5 +
        defense * 0.25 +
        spd * 0.25
    )

    defensa = (
        defense * 0.5 +
        spd * 0.3 +
        hp * 0.2
    )

    creacion = (
        spa * 0.5 +
        speed * 0.3 +
        spd * 0.2
    )

    ataque = (
        atk * 0.6 +
        speed * 0.2 +
        spa * 0.2
    )

    ritmo = speed

    return {
        "POR": round(porteria, 1),
        "DEF": round(defensa, 1),
        "CRE": round(creacion, 1),
        "ATQ": round(ataque, 1),
        "RIT": ritmo
    }


def calcular_rating_posiciones(stats):

    rating_portero = (
        stats["POR"] * 0.5 +
        stats["DEF"] * 0.3 +
        stats["RIT"] * 0.2
    )

    rating_defensa = (
        stats["DEF"] * 0.7 +
        stats["POR"] * 0.1 +
        stats["RIT"] * 0.2
    )

    rating_medio = (
        stats["CRE"] * 0.5 +
        stats["RIT"] * 0.3 +
        stats["ATQ"] * 0.2
    )

    rating_delantero = (
        stats["ATQ"] * 0.6 +
        stats["CRE"] * 0.2 +
        stats["RIT"] * 0.2
    )

    return {
        "PORTERO": round(rating_portero, 1),
        "DEFENSA": round(rating_defensa, 1),
        "MEDIO": round(rating_medio, 1),
        "DELANTERO": round(rating_delantero, 1)
    }


def main():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                nombre,
                hp,
                attack,
                defense,
                special_attack,
                special_defense,
                speed
            FROM pokemon_data
        """)

        pokemons = cursor.fetchall()

        pokemon_prueba = [
            "dragonite",
            "lucario",
            "blissey",
            "corviknight",
            "garchomp",
            "gardevoir",
            "snorlax",
            "pikachu",
            "metagross",
            "tyranitar",
            "charizard"
        ]

        print("\n===== FUTBOL POKEMON =====")

        for fila in pokemons:

            nombre = fila[1].lower()

            if nombre not in pokemon_prueba:
                continue

            stats = calcular_stats_futbol(
                fila[2],  # hp
                fila[3],  # atk
                fila[4],  # defense
                fila[5],  # spa
                fila[6],  # spd
                fila[7]   # speed
            )

            ratings = calcular_rating_posiciones(stats)

            mejor_posicion = max(
                ratings,
                key=ratings.get
            )

            print(f"\n{'=' * 40}")
            print(f"{fila[1].upper()}")
            print(f"{'=' * 40}")

            print(f"🧤 POR: {stats['POR']}")
            print(f"🛡️ DEF: {stats['DEF']}")
            print(f"🧠 CRE: {stats['CRE']}")
            print(f"⚽ ATQ: {stats['ATQ']}")
            print(f"⚡ RIT: {stats['RIT']}")

            print()

            print(f"🥅 Rating Portero:   {ratings['PORTERO']}")
            print(f"🛡️ Rating Defensa:   {ratings['DEFENSA']}")
            print(f"🧠 Rating Medio:     {ratings['MEDIO']}")
            print(f"⚽ Rating Delantero: {ratings['DELANTERO']}")

            print()
            print(f"⭐ MEJOR POSICIÓN: {mejor_posicion}")

    finally:

        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()