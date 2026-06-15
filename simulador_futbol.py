import random
CACHE_RATING = {}
CACHE_CAPTURAS = {}
CACHE_POKEMON = {}
from futbol import (
    obtener_jugadores_equipo,
    nombre_pokemon_captura
)

def calcular_posesion(med_a, med_b):

    total = med_a + med_b

    if total <= 0:
        return 0.5, 0.5

    return (
        med_a / total,
        med_b / total
    )


def calcular_ocasiones(posesion, total_ocasiones):

    return round(
        posesion * total_ocasiones
    )
def probabilidad_gol(delantera, porteria):

    diferencia = delantera - porteria

    probabilidad = 0.25 + (diferencia * 0.005)

    probabilidad = max(
        0.10,
        min(0.60, probabilidad)
    )

    return probabilidad
def simular_partido(fuerza_a, fuerza_b):

    posesion_a, posesion_b = calcular_posesion(
        fuerza_a["MED"],
        fuerza_b["MED"]
    )

    total_ocasiones = random.randint(8, 15)

    ocasiones_a = calcular_ocasiones(
        posesion_a,
        total_ocasiones
    )

    ocasiones_b = total_ocasiones - ocasiones_a

    goles_a = 0
    goles_b = 0
    eventos = []

    prob_a = probabilidad_gol(
        fuerza_a["DEL"],
        fuerza_b["POR"]
    )

    prob_b = probabilidad_gol(
        fuerza_b["DEL"],
        fuerza_a["POR"]
    )

    for _ in range(ocasiones_a):

        if random.random() < prob_a:

            goles_a += 1

            eventos.append(
                (
                    random.randint(1, 90),
                    "A"
                )
            )

    for _ in range(ocasiones_b):

        if random.random() < prob_b:

            goles_b += 1

            eventos.append(
                (
                    random.randint(1, 90),
                    "B"
                )
            )

    return {
        "goles_a": goles_a,
        "goles_b": goles_b,
        "posesion_a": round(posesion_a * 100, 1),
        "posesion_b": round(posesion_b * 100, 1),
        "ocasiones_a": ocasiones_a,
        "ocasiones_b": ocasiones_b,
        "eventos": eventos
    }


from futbol import (
    calcular_fuerza_equipo,
    contar_jugadores_equipo
)

def elegir_goleador(delanteros, medios):

    candidatos = []

    candidatos.extend(delanteros)
    candidatos.extend(delanteros)
    candidatos.extend(delanteros)

    candidatos.extend(medios)

    candidatos = [
        p for p in candidatos
        if p is not None
    ]

    return random.choice(candidatos)
def simular_partido_usuarios(
    usuario_a,
    usuario_b,
    
):

    fuerza_a = calcular_fuerza_equipo(usuario_a)
    fuerza_b = calcular_fuerza_equipo(usuario_b)

    jugadores_a = obtener_jugadores_equipo(usuario_a)
    jugadores_b = obtener_jugadores_equipo(usuario_b)

    resultado = simular_partido(
        fuerza_a,
        fuerza_b
    )

    eventos_reales = []

    for minuto, equipo in resultado["eventos"]:

        if equipo == "A":

            goleador = elegir_goleador(
                jugadores_a["delanteros"],
                jugadores_a["medios"]
            )

        else:

            goleador = elegir_goleador(
                jugadores_b["delanteros"],
                jugadores_b["medios"]
            )

        eventos_reales.append(
            (
                minuto,
                nombre_pokemon_captura(goleador),
                equipo
            )
        )

    eventos_reales.sort(
        key=lambda x: x[0]
    )

    resultado["eventos"] = eventos_reales

    return resultado
def simular_partido_usuarios(usuario_a, usuario_b):

    CACHE_RATING.clear()  # 👈 esto va aquí dentro

    fuerza_a = calcular_fuerza_equipo(usuario_a)
    fuerza_b = calcular_fuerza_equipo(usuario_b)

    if fuerza_a is None or fuerza_b is None:
        return {"error": "Equipo inválido"}

    jugadores_a = obtener_jugadores_equipo(usuario_a)
    jugadores_b = obtener_jugadores_equipo(usuario_b)

    resultado = simular_partido(fuerza_a, fuerza_b)

    eventos_reales = []

    for minuto, equipo in resultado["eventos"]:

        if equipo == "A":
            goleador = elegir_goleador(
                jugadores_a["delanteros"],
                jugadores_a["medios"]
            )
        else:
            goleador = elegir_goleador(
                jugadores_b["delanteros"],
                jugadores_b["medios"]
            )

        eventos_reales.append(
            (minuto, nombre_pokemon_captura(goleador), equipo)
        )

    eventos_reales.sort(key=lambda x: x[0])

    resultado["eventos"] = eventos_reales

    return resultado
def mostrar_partido(resultado):

    texto = ""

    texto += "⚽ PARTIDO AMISTOSO\n\n"

    texto += (
        f"Equipo A {resultado['goles_a']} - "
        f"{resultado['goles_b']} Equipo B\n\n"
    )

    for minuto, goleador, equipo in resultado["eventos"]:

        texto += (
            f"⚽ {minuto}' "
            f"{goleador} ({equipo})\n"
        )

    texto += "\n📊 ESTADÍSTICAS\n\n"

    texto += (
        f"Posesión: "
        f"{resultado['posesion_a']}% - "
        f"{resultado['posesion_b']}%\n"
    )

    texto += (
        f"Ocasiones: "
        f"{resultado['ocasiones_a']} - "
        f"{resultado['ocasiones_b']}"
    )

    return texto