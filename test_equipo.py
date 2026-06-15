import os
os.environ["DATABASE_URL"] = ""
from futbol import precargar_capturas

precargar_capturas()
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


def armar_equipo(jugadores):

    disponibles = jugadores.copy()

    equipo = {
        "PORTERO": [],
        "DEFENSA": [],
        "MEDIO": [],
        "DELANTERO": []
    }

    # PORTERO

    mejor = max(
        disponibles,
        key=lambda x: x["ratings"]["PORTERO"]
    )

    equipo["PORTERO"].append(mejor)

    disponibles.remove(mejor)

    # DEFENSAS

    disponibles.sort(
        key=lambda x: x["ratings"]["DEFENSA"],
        reverse=True
    )

    equipo["DEFENSA"] = disponibles[:4]

    for p in equipo["DEFENSA"]:
        disponibles.remove(p)

    # MEDIOS

    disponibles.sort(
        key=lambda x: x["ratings"]["MEDIO"],
        reverse=True
    )

    equipo["MEDIO"] = disponibles[:4]

    for p in equipo["MEDIO"]:
        disponibles.remove(p)

    # DELANTEROS

    disponibles.sort(
        key=lambda x: x["ratings"]["DELANTERO"],
        reverse=True
    )

    equipo["DELANTERO"] = disponibles[:2]

    return equipo


def calcular_fuerza_equipo(equipo):

    fuerza = {
        "POR": 0,
        "DEF": 0,
        "MED": 0,
        "ATQ": 0,
        "RIT": 0
    }

    for jugador in equipo["PORTERO"]:

        fuerza["POR"] += jugador["stats"]["POR"]

    for jugador in equipo["DEFENSA"]:

        fuerza["DEF"] += jugador["stats"]["DEF"]

        fuerza["RIT"] += jugador["stats"]["RIT"]

    for jugador in equipo["MEDIO"]:

        fuerza["MED"] += jugador["stats"]["CRE"]

        fuerza["RIT"] += jugador["stats"]["RIT"]

    for jugador in equipo["DELANTERO"]:

        fuerza["ATQ"] += jugador["stats"]["ATQ"]

        fuerza["RIT"] += jugador["stats"]["RIT"]

    fuerza["RIT"] = round(
        fuerza["RIT"] / 10,
        1
    )

    return fuerza


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

        nombres_equipo = [
            "blissey",
            "corviknight",
            "metagross",
            "dragonite",
            "garchomp",
            "lucario",
            "gardevoir",
            "pikachu",
            "charizard",
            "tyranitar",
            "snorlax"
        ]

        jugadores = []

        for fila in pokemons:

            nombre = fila[1].lower()

            if nombre not in nombres_equipo:
                continue

            stats = calcular_stats_futbol(
                fila[2],
                fila[3],
                fila[4],
                fila[5],
                fila[6],
                fila[7]
            )

            ratings = calcular_rating_posiciones(
                stats
            )

            jugadores.append({
                "nombre": fila[1],
                "stats": stats,
                "ratings": ratings
            })

        equipo = armar_equipo(
            jugadores
        )

        print("\n===== EQUIPO 4-4-2 =====")

        for rol in equipo:

            print(f"\n{rol}")

            for jugador in equipo[rol]:

                print(
                    jugador["nombre"]
                )

        fuerza = calcular_fuerza_equipo(
            equipo
        )

        print("\n===== FUERZA DEL EQUIPO =====")

        print(
            f"🧤 PORTERIA : {fuerza['POR']:.1f}"
        )

        print(
            f"🛡️ DEFENSA : {fuerza['DEF']:.1f}"
        )

        print(
            f"🧠 CREACION : {fuerza['MED']:.1f}"
        )

        print(
            f"⚽ ATAQUE : {fuerza['ATQ']:.1f}"
        )

        print(
            f"⚡ RITMO : {fuerza['RIT']:.1f}"
        )

    finally:

        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()