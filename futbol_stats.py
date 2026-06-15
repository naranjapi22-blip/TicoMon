
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
from database import get_connection


