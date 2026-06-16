import random

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

    probabilidad = 0.25 + (diferencia * 0.007)

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
    obtener_jugadores_equipo,
    nombre_pokemon_captura,
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

def simular_partido_usuarios(usuario_a, usuario_b):

    fuerza_a = calcular_fuerza_equipo(usuario_a)
    fuerza_b = calcular_fuerza_equipo(usuario_b)

    if fuerza_a is None or fuerza_b is None:
        return {"error": "Equipo inválido"}

    jugadores_a = obtener_jugadores_equipo(usuario_a)
    jugadores_b = obtener_jugadores_equipo(usuario_b)

    resultado = simular_partido(
        fuerza_a,
        fuerza_b
    )

    eventos = []

    # GOLES
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

        eventos.append({
            "tipo": "gol",
            "minuto": minuto,
            "equipo": equipo,
            "jugador": nombre_pokemon_captura(goleador)
        })

    # TARJETAS
    cantidad_amarillas = random.randint(0, 3)

    for _ in range(cantidad_amarillas):

        equipo = random.choice(["A", "B"])

        if equipo == "A":
            captura = elegir_jugador_evento(jugadores_a)
        else:
            captura = elegir_jugador_evento(jugadores_b)
    if not evitar_repeticion(eventos, jugador, minuto):
        eventos.append({
            "tipo": "amarilla",
            "minuto": minuto_libre(eventos),
            "equipo": equipo,
            "jugador": nombre_pokemon_captura(captura)
        })
    cantidad_rojas = random.randint(0, 1)

    for _ in range(cantidad_rojas):

        if random.random() > 0.1:
            continue

        equipo = random.choice(["A", "B"])

        if equipo == "A":
            captura = elegir_jugador_evento(jugadores_a)
        else:
            captura = elegir_jugador_evento(jugadores_b)

        eventos.append({
            "tipo": "roja",
            "minuto": minuto_libre(eventos),
            "equipo": equipo,
            "jugador": nombre_pokemon_captura(captura)
        })
    # FALTAS
    
    cantidad_faltas = random.randint(1, 4)

    for _ in range(cantidad_faltas):

        equipo = random.choice(["A", "B"])

        if equipo == "A":
            captura = elegir_jugador_evento(jugadores_a)
        else:
            captura = elegir_jugador_evento(jugadores_b)
    if not evitar_repeticion(eventos, jugador, minuto):

        eventos.append({
            "tipo": "falta",
            "minuto": minuto_libre(eventos),
            "equipo": equipo,
            "jugador": nombre_pokemon_captura(captura)
        })
    cantidad_postes = random.randint(0, 2)

    for _ in range(cantidad_postes):

        equipo = random.choice(["A", "B"])

        if equipo == "A":
            captura = elegir_jugador_evento(jugadores_a)
        else:
            captura = elegir_jugador_evento(jugadores_b)
    if not evitar_repeticion(eventos, jugador, minuto):
        eventos.append({
            "tipo": "poste",
            "minuto": minuto_libre(eventos),
            "equipo": equipo,
            "jugador": nombre_pokemon_captura(captura)
        })
    cantidad_paradas = random.randint(0, 3)

    for _ in range(cantidad_paradas):

        equipo = random.choice(["A", "B"])

        if equipo == "A":
            portero = jugadores_a["portero"]
        else:
            portero = jugadores_b["portero"]

        eventos.append({
            "tipo": "parada",
            "minuto": minuto_libre(eventos),
            "equipo": equipo,
            "jugador": nombre_pokemon_captura(portero)
        })        
    eventos.sort(
        key=lambda e: e["minuto"]
    )

    resultado["eventos"] = eventos

    return resultado
def mostrar_partido(resultado):

    texto = ""

    texto += "⚽ PARTIDO AMISTOSO\n\n"

    texto += (
        f"Equipo A {resultado['goles_a']} - "
        f"{resultado['goles_b']} Equipo B\n\n"
    )

    for evento in resultado["eventos"]:

        if evento["tipo"] == "gol":

            texto += (
                f"⚽ {evento['minuto']}' "
                f"{evento['jugador']} "
                f"({evento['equipo']})\n"
            )

        elif evento["tipo"] == "amarilla":

            texto += (
                f"🟨 {evento['minuto']}' "
                f"{evento['jugador']} "
                f"({evento['equipo']}) recibe tarjeta amarilla.\n"
            )

        elif evento["tipo"] == "falta":

            texto += (
                f"🦶 {evento['minuto']}' "
                f"{evento['jugador']} "
                f"({evento['equipo']}) comete una falta.\n"
            )
        elif evento["tipo"] == "poste":

            texto += (
                f"🥅 {evento['minuto']}' "
                f"{evento['jugador']} "
                f"({evento['equipo']}) estrella el balón en el poste.\n"
            )        
        elif evento["tipo"] == "parada":

            texto += (
                f"🧤 {evento['minuto']}' "
                f"Gran parada de "
                f"{evento['jugador']} "
                f"({evento['equipo']}).\n"
            )    
        elif evento["tipo"] == "roja":

            texto += (
                f"🟥 {evento['minuto']}' "
                f"{evento['jugador']} "
                f"({evento['equipo']}) es expulsado.\n"
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
def elegir_jugador_evento(jugadores):

    todos = []

    if jugadores["portero"]:
        todos.append(jugadores["portero"])

    todos.extend(
        jugador
        for jugador in jugadores["defensas"]
        if jugador is not None
    )

    todos.extend(
        jugador
        for jugador in jugadores["medios"]
        if jugador is not None
    )

    todos.extend(
        jugador
        for jugador in jugadores["delanteros"]
        if jugador is not None
    )

    return random.choice(todos)
def minuto_libre(eventos):

    zonas = [
        (1, 45),
        (46, 90)
    ]

    zona = random.choices(
        zonas,
        weights=[40, 60],
        k=1
    )[0]

    intentos = 0

    while True:

        minuto = random.randint(zona[0], zona[1])

        if not any(e["minuto"] == minuto for e in eventos):
            return minuto

        intentos += 1

        if intentos > 20:
            return random.randint(1, 90)
def formatear_evento(evento):

    if evento["tipo"] == "gol":
        return (
            f"⚽ {evento['minuto']}' "
            f"{evento['jugador']} "
            f"({evento['equipo']})"
        )

    elif evento["tipo"] == "amarilla":
        return (
            f"🟨 {evento['minuto']}' "
            f"{evento['jugador']} "
            f"({evento['equipo']}) recibe tarjeta amarilla."
        )

    elif evento["tipo"] == "roja":
        return (
            f"🟥 {evento['minuto']}' "
            f"{evento['jugador']} "
            f"({evento['equipo']}) es expulsado."
        )

    elif evento["tipo"] == "falta":
        return (
            f"🦶 {evento['minuto']}' "
            f"{evento['jugador']} "
            f"({evento['equipo']}) comete una falta."
        )

    elif evento["tipo"] == "poste":
        return (
            f"🥅 {evento['minuto']}' "
            f"{evento['jugador']} "
            f"({evento['equipo']}) estrella el balón en el poste."
        )

    elif evento["tipo"] == "parada":
        return (
            f"🧤 {evento['minuto']}' "
            f"Gran parada de "
            f"{evento['jugador']} "
            f"({evento['equipo']})."
        )
def formatear_evento(evento):

    if evento["tipo"] == "gol":
        return (
            f"⚽ {evento['minuto']}' "
            f"{evento['jugador']} "
            f"({evento['equipo']})"
        )

    elif evento["tipo"] == "amarilla":
        return (
            f"🟨 {evento['minuto']}' "
            f"{evento['jugador']} "
            f"({evento['equipo']}) recibe tarjeta amarilla."
        )

    elif evento["tipo"] == "roja":
        return (
            f"🟥 {evento['minuto']}' "
            f"{evento['jugador']} "
            f"({evento['equipo']}) es expulsado."
        )

    elif evento["tipo"] == "falta":
        return (
            f"🦶 {evento['minuto']}' "
            f"{evento['jugador']} "
            f"({evento['equipo']}) comete una falta."
        )

    elif evento["tipo"] == "poste":
        return (
            f"🥅 {evento['minuto']}' "
            f"{evento['jugador']} "
            f"({evento['equipo']}) estrella el balón en el poste."
        )

    elif evento["tipo"] == "parada":
        return (
            f"🧤 {evento['minuto']}' "
            f"Gran parada de "
            f"{evento['jugador']} "
            f"({evento['equipo']})."
        )
def evitar_repeticion(eventos, nuevo_jugador, nuevo_minuto, margen=10):

    for e in eventos:

        if e.get("jugador") == nuevo_jugador:

            if abs(e["minuto"] - nuevo_minuto) <= margen:
                return True

    return False
def formatear_evento(evento):

    if evento["tipo"] == "gol":
        return f"⚽ {evento['minuto']}' {evento['jugador']} ({evento['equipo']})"

    if evento["tipo"] == "amarilla":
        return f"🟨 {evento['minuto']}' {evento['jugador']} recibe amarilla."

    if evento["tipo"] == "roja":
        return f"🟥 {evento['minuto']}' {evento['jugador']} es expulsado."

    if evento["tipo"] == "falta":
        return f"🦶 {evento['minuto']}' {evento['jugador']} comete falta."

    if evento["tipo"] == "poste":
        return f"🥅 {evento['minuto']}' {evento['jugador']} estrella el balón en el poste."

    if evento["tipo"] == "parada":
        return f"🧤 {evento['minuto']}' Gran parada de {evento['jugador']}."