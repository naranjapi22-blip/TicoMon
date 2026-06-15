from database import get_connection
import database
CACHE_RATING = {}
CACHE_CAPTURAS = {}
from futbol_stats import (
    calcular_stats_futbol,
    calcular_rating_posiciones
)
POSICIONES_FUTBOL = [
    "portero",

    "defensa_1",
    "defensa_2",
    "defensa_3",
    "defensa_4",

    "medio_1",
    "medio_2",
    "medio_3",
    "medio_4",

    "delantero_1",
    "delantero_2"
]
def precargar_capturas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, pokemon_nombre, es_shiny
        FROM capturas
    """)

    rows = cursor.fetchall()
    conn.close()

    global CACHE_CAPTURAS
    CACHE_CAPTURAS = {r[0]: r for r in rows}
def crear_equipo_futbol(usuario_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO equipos_futbol (usuario_id)
            VALUES (%s)
            ON CONFLICT (usuario_id) DO NOTHING
        """, (usuario_id,))

        conn.commit()
        conn.close()

        print("✅ Equipo creado")

    except Exception as e:
        print(f"❌ Error: {e}")
from database import get_connection


def obtener_equipo_futbol(usuario_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM equipos_futbol
            WHERE usuario_id = %s
        """, (usuario_id,))

        equipo = cursor.fetchone()

        conn.close()

        return equipo

    except Exception as e:
        print(f"❌ Error: {e}")
        return None
def tiene_equipo_futbol(usuario_id):
    equipo = obtener_equipo_futbol(usuario_id)
    return equipo is not None
def actualizar_posicion_futbol(usuario_id, posicion, pokemon_id):
    try:

        if posicion not in POSICIONES_FUTBOL:
            raise ValueError(f"Posición inválida: {posicion}")

        conn = get_connection()
        cursor = conn.cursor()

        query = f"""
            UPDATE equipos_futbol
            SET {posicion} = %s
            WHERE usuario_id = %s
        """

        cursor.execute(query, (pokemon_id, usuario_id))

        conn.commit()
        conn.close()

        print("✅ Posición actualizada")

    except Exception as e:
        print(f"❌ Error: {e}")
def quitar_posicion_futbol(usuario_id, posicion):
    try:

        if posicion not in POSICIONES_FUTBOL:
            raise ValueError(f"Posición inválida: {posicion}")

        conn = get_connection()
        cursor = conn.cursor()

        query = f"""
            UPDATE equipos_futbol
            SET {posicion} = NULL
            WHERE usuario_id = %s
        """

        cursor.execute(query, (usuario_id,))

        conn.commit()
        conn.close()

        print("✅ Posición eliminada")

    except Exception as e:
        print(f"❌ Error: {e}")
def pokemon_ya_en_equipo(usuario_id, pokemon_id):

    equipo = obtener_equipo_futbol(usuario_id)

    if not equipo:
        return False

    posiciones = equipo[1:12]

    return pokemon_id in posiciones
def mostrar_equipo_futbol(usuario_id):

    equipo = obtener_equipo_futbol(usuario_id)

    if not equipo:
        return "No tiene equipo."

    texto = ""

    texto += f"🧤 PORTERO\n{nombre_captura(equipo[1])}\n\n"

    texto += "🛡 DEFENSAS\n"
    texto += f"{nombre_captura(equipo[2])}\n"
    texto += f"{nombre_captura(equipo[3])}\n"
    texto += f"{nombre_captura(equipo[4])}\n"
    texto += f"{nombre_captura(equipo[5])}\n\n"

    texto += "🎯 MEDIOS\n"
    texto += f"{nombre_captura(equipo[6])}\n"
    texto += f"{nombre_captura(equipo[7])}\n"
    texto += f"{nombre_captura(equipo[8])}\n"
    texto += f"{nombre_captura(equipo[9])}\n\n"

    texto += "⚔ DELANTEROS\n"
    texto += f"{nombre_captura(equipo[10])}\n"
    texto += f"{nombre_captura(equipo[11])}"

    return texto
def obtener_captura(captura_id):

    if captura_id in CACHE_CAPTURAS:
        return CACHE_CAPTURAS[captura_id]

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id,
                   pokemon_nombre,
                   es_shiny
            FROM capturas
            WHERE id = %s
        """, (captura_id,))

        captura = cursor.fetchone()

        conn.close()

        CACHE_CAPTURAS[captura_id] = captura

        return captura

    except Exception as e:
        print(f"❌ Error: {e}")
        return None
def nombre_captura(captura_id):

    if captura_id is None:
        return "Vacío"

    captura = obtener_captura(captura_id)

    if not captura:
        return "Desconocido"

    _, nombre, es_shiny = captura

    if es_shiny:
        return f"✨ {nombre.capitalize()}"

    return nombre.capitalize()
def captura_pertenece_usuario(usuario_id, captura_id):
    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id,
                pokemon_id,
                pokemon_nombre,
                es_shiny
            FROM capturas
            WHERE id = %s
        """, (captura_id,))


        resultado = cursor.fetchone()

        conn.close()

        return resultado is not None

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
def colocar_pokemon_equipo(usuario_id, captura_id, posicion):

    if not tiene_equipo_futbol(usuario_id):
        return False, "No tienes equipo de fútbol."

    if posicion not in POSICIONES_FUTBOL:
        return False, "Posición inválida."

    captura = obtener_captura(captura_id)

    if not captura:
        return False, "La captura no existe."

    if not captura_pertenece_usuario(usuario_id, captura_id):
        return False, "Ese Pokémon no te pertenece."

    if pokemon_ya_en_equipo(usuario_id, captura_id):
        return False, "Ese Pokémon ya está en tu alineación."

    actualizar_posicion_futbol(
        usuario_id,
        posicion,
        captura_id
    )

    return True, "Pokémon agregado correctamente."
def obtener_posicion_pokemon(usuario_id, captura_id):

    equipo = obtener_equipo_futbol(usuario_id)

    if not equipo:
        return None

    mapa = {
        "portero": equipo[1],

        "defensa_1": equipo[2],
        "defensa_2": equipo[3],
        "defensa_3": equipo[4],
        "defensa_4": equipo[5],

        "medio_1": equipo[6],
        "medio_2": equipo[7],
        "medio_3": equipo[8],
        "medio_4": equipo[9],

        "delantero_1": equipo[10],
        "delantero_2": equipo[11]
    }

    for posicion, pokemon in mapa.items():
        if pokemon == captura_id:
            return posicion

    return None
def mover_pokemon_equipo(usuario_id, captura_id, nueva_posicion):

    if nueva_posicion not in POSICIONES_FUTBOL:
        return False, "Posición inválida."

    posicion_actual = obtener_posicion_pokemon(
        usuario_id,
        captura_id
    )

    if not posicion_actual:
        return False, "Ese Pokémon no está en tu equipo."

    quitar_posicion_futbol(
        usuario_id,
        posicion_actual
    )

    actualizar_posicion_futbol(
        usuario_id,
        nueva_posicion,
        captura_id
    )

    return True, "Pokémon movido correctamente."
def obtener_rating_pokemon(captura_id):

    if captura_id in CACHE_RATING:
        return CACHE_RATING[captura_id]

    captura = obtener_captura(captura_id)

    if not captura:
        return None

    nombre = captura[1].lower().strip()

    datos = obtener_datos_pokemon(nombre)

    if not datos:
        print(f"❌ No existe en pokemon_data: {nombre}")
        return None

    stats = calcular_stats_futbol(
        datos["hp"],
        datos["attack"],
        datos["defense"],
        datos["spa"],
        datos["spd"],
        datos["speed"]
    )

    ratings = calcular_rating_posiciones(stats)

    resultado = {
        "POR": ratings["PORTERO"],
        "DEF": ratings["DEFENSA"],
        "MED": ratings["MEDIO"],
        "DEL": ratings["DELANTERO"]
    }

    CACHE_RATING[captura_id] = resultado

    return resultado
def promedio(lista):

    valores = [x for x in lista if x is not None]

    if not valores:
        return 0

    return round(sum(valores) / len(valores), 1)
def safe_promedio(lista):
    if not lista:
        return 0
    return promedio(lista)


def calcular_fuerza_equipo(usuario_id):

    equipo = obtener_equipo_futbol(usuario_id)

    if not equipo:
        return None

    # --------------------
    # PORTERO
    # --------------------
    rating_portero = 0

    if equipo[1]:
        stats = obtener_rating_pokemon(equipo[1])

        if stats:
            rating_portero = stats.get("POR", 0)

    # --------------------
    # DEFENSAS
    # --------------------
    ratings_defensa = []

    for captura_id in equipo[2:6]:

        if captura_id:

            stats = obtener_rating_pokemon(captura_id)

            if not stats:
                print(f"ERROR DEFENSA: {captura_id}")
                continue

            ratings_defensa.append(stats.get("DEF", 0))

    # --------------------
    # MEDIOS
    # --------------------
    ratings_medio = []

    for captura_id in equipo[6:10]:

        if captura_id:

            stats = obtener_rating_pokemon(captura_id)

            if not stats:
                print(f"ERROR MEDIO: {captura_id}")
                continue

            ratings_medio.append(stats.get("MED", 0))

    # --------------------
    # DELANTEROS
    # --------------------
    ratings_delantero = []

    for captura_id in equipo[10:12]:

        if captura_id:

            stats = obtener_rating_pokemon(captura_id)

            if not stats:
                print(f"ERROR DELANTERO: {captura_id}")
                continue

            ratings_delantero.append(stats.get("DEL", 0))

    # --------------------
    # FUERZA FINAL
    # --------------------
    fuerza = {
        "POR": round(rating_portero, 1),
        "DEF": round(safe_promedio(ratings_defensa), 1),
        "MED": round(safe_promedio(ratings_medio), 1),
        "DEL": round(safe_promedio(ratings_delantero), 1)
    }

    valores = [v for v in fuerza.values() if v > 0]

    fuerza["GLOBAL"] = round(sum(valores) / len(valores), 1) if valores else 0

    return fuerza
def normalizar_nombre(nombre):

    return (
        nombre.lower()
        .replace("-", " ")
        .replace("_", " ")
        .strip()
    )
MAPA_FORMAS = {
    "morpeko full belly": "morpeko",
    "brute bonnet": "brute bonnet",
    "giratina origin": "giratina",
    "shaymin sky": "shaymin"
}
def obtener_datos_pokemon(nombre):

    nombre = MAPA_FORMAS.get(nombre, nombre)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT hp, attack, defense,
               special_attack, special_defense, speed
        FROM pokemon_data
        WHERE LOWER(nombre) = %s
    """, (nombre,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "hp": row[0],
        "attack": row[1],
        "defense": row[2],
        "spa": row[3],
        "spd": row[4],
        "speed": row[5]
    }
def contar_jugadores_equipo(usuario_id):

    equipo = obtener_equipo_futbol(usuario_id)

    if not equipo:
        return 0

    posiciones = equipo[1:12]

    return sum(
        1
        for pokemon in posiciones
        if pokemon is not None
    )


def mostrar_fuerza_equipo(usuario_id):
    print("\n===== DEBUG EQUIPO =====")
    print(equipo)
    fuerza = calcular_fuerza_equipo(usuario_id)

    if not fuerza:
        return "No tiene equipo."

    jugadores = contar_jugadores_equipo(usuario_id)

    return (
        f"⚽ FUERZA DEL EQUIPO\n\n"
        f"👥 Alineación: {jugadores}/11\n\n"
        f"🧤 Portería: {fuerza['POR']}\n"
        f"🛡 Defensa: {fuerza['DEF']}\n"
        f"🎯 Medio: {fuerza['MED']}\n"
        f"⚔ Ataque: {fuerza['DEL']}\n\n"
        f"⭐ Global: {fuerza['GLOBAL']}"
    )
def obtener_jugadores_equipo(usuario_id):

    equipo = obtener_equipo_futbol(usuario_id)

    if not equipo:
        return None

    return {
        "portero": equipo[1],

        "defensas": [
            equipo[2],
            equipo[3],
            equipo[4],
            equipo[5]
        ],

        "medios": [
            equipo[6],
            equipo[7],
            equipo[8],
            equipo[9]
        ],

        "delanteros": [
            equipo[10],
            equipo[11]
        ]
    }
def nombre_pokemon_captura(captura_id):

    captura = obtener_captura(captura_id)

    if not captura:
        return "Desconocido"

    return captura[1].capitalize()