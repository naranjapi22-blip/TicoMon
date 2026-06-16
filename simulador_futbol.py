import random
from futbol import ordenar_equipo_por_formacion
def equipo_a_dict(equipo):

    return {
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
        "delantero_2": equipo[11],
    }
def formatear_timeline(resultado, nombre_a, nombre_b):

    eventos = sorted(resultado["eventos"], key=lambda e: e["minuto"])

    texto = f"{nombre_a} vs {nombre_b}\n\n"

    for e in eventos:

        linea = formatear_evento(e)

        if e["equipo"] == "A":
            texto += f"{linea:<45}\n"
        else:
            texto += f"{' ' * 45}{linea}\n"

    return texto
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

    import random

    fuerza_a = calcular_fuerza_equipo(usuario_a)
    fuerza_b = calcular_fuerza_equipo(usuario_b)

    if fuerza_a is None:
        print(f"Equipo inválido usuario A: {usuario_a}")

    if fuerza_b is None:
        print(f"Equipo inválido usuario B: {usuario_b}")

    if fuerza_a is None or fuerza_b is None:
        return {"error": "Equipo inválido"}

    jugadores_a = obtener_jugadores_equipo(usuario_a)
    jugadores_b = obtener_jugadores_equipo(usuario_b)

    # 🔥 convertir estructura
    jugadores_a = equipo_a_dict(jugadores_a)
    jugadores_b = equipo_a_dict(jugadores_b)

    # 🔥 asegurar que no haya None
    jugadores_a = asegurar_equipo(jugadores_a)
    jugadores_b = asegurar_equipo(jugadores_b)

    resultado = simular_partido(fuerza_a, fuerza_b)

    eventos = []

    # =========================
    # 🔥 FUNCIÓN SEGURA PLAYER
    # =========================
    def safe_player(equipo):
        valores = [v for v in equipo.values() if v]
        if not valores:
            return None
        return random.choice(valores)

    def safe_nombre(captura):
        if not captura:
            return "Desconocido"
        return nombre_pokemon_captura(captura)

    # =========================
    # ⚽ GOLES
    # =========================
    for minuto, equipo in resultado["eventos"]:

        if equipo == "A":
            goleador = safe_player(jugadores_a)
        else:
            goleador = safe_player(jugadores_b)

        eventos.append({
            "tipo": "gol",
            "minuto": minuto,
            "equipo": equipo,
            "jugador": safe_nombre(goleador)
        })

    # =========================
    # 🟨 AMARILLAS
    # =========================
    cantidad_amarillas = random.randint(0, 3)

    for _ in range(cantidad_amarillas):

        equipo = random.choice(["A", "B"])

        if equipo == "A":
            captura = safe_player(jugadores_a)
        else:
            captura = safe_player(jugadores_b)

        minuto = minuto_libre(eventos)
        jugador = safe_nombre(captura)

        if not evitar_repeticion(eventos, jugador, minuto):

            eventos.append({
                "tipo": "amarilla",
                "minuto": minuto,
                "equipo": equipo,
                "jugador": jugador
            })

    # =========================
    # 🔴 ROJAS
    # =========================
    cantidad_rojas = random.randint(0, 1)

    for _ in range(cantidad_rojas):

        if random.random() > 0.1:
            continue

        equipo = random.choice(["A", "B"])

        if equipo == "A":
            captura = safe_player(jugadores_a)
        else:
            captura = safe_player(jugadores_b)

        minuto = minuto_libre(eventos)
        jugador = safe_nombre(captura)

        eventos.append({
            "tipo": "roja",
            "minuto": minuto,
            "equipo": equipo,
            "jugador": jugador
        })

    # =========================
    # 🦶 FALTAS
    # =========================
    cantidad_faltas = random.randint(1, 4)

    for _ in range(cantidad_faltas):

        equipo = random.choice(["A", "B"])

        if equipo == "A":
            captura = safe_player(jugadores_a)
        else:
            captura = safe_player(jugadores_b)

        minuto = minuto_libre(eventos)
        jugador = safe_nombre(captura)

        if not evitar_repeticion(eventos, jugador, minuto):

            eventos.append({
                "tipo": "falta",
                "minuto": minuto,
                "equipo": equipo,
                "jugador": jugador
            })

    # =========================
    # 🥅 POSTES
    # =========================
    cantidad_postes = random.randint(0, 2)

    for _ in range(cantidad_postes):

        equipo = random.choice(["A", "B"])

        if equipo == "A":
            captura = safe_player(jugadores_a)
        else:
            captura = safe_player(jugadores_b)

        minuto = minuto_libre(eventos)
        jugador = safe_nombre(captura)

        if not evitar_repeticion(eventos, jugador, minuto):

            eventos.append({
                "tipo": "poste",
                "minuto": minuto,
                "equipo": equipo,
                "jugador": jugador
            })

    # =========================
    # 🧤 PARADAS
    # =========================
    cantidad_paradas = random.randint(0, 3)

    for _ in range(cantidad_paradas):

        equipo = random.choice(["A", "B"])

        if equipo == "A":
            portero = jugadores_a.get("portero")
        else:
            portero = jugadores_b.get("portero")

        eventos.append({
            "tipo": "parada",
            "minuto": minuto_libre(eventos),
            "equipo": equipo,
            "jugador": safe_nombre(portero)
        })

    # =========================
    # 📊 FINAL
    # =========================
    eventos.sort(key=lambda e: e["minuto"])
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

    elif evento["tipo"] == "amarilla":
        return f"🟨 {evento['minuto']}' {evento['jugador']} recibe amarilla."

    elif evento["tipo"] == "roja":
        return f"🟥 {evento['minuto']}' {evento['jugador']} es expulsado."

    elif evento["tipo"] == "falta":
        return f"🦶 {evento['minuto']}' {evento['jugador']} comete una falta."

    elif evento["tipo"] == "poste":
        return f"🥅 {evento['minuto']}' {evento['jugador']} estrella el balón en el poste."

    elif evento["tipo"] == "parada":
        return f"🧤 {evento['minuto']}' Gran parada de {evento['jugador']}."
def asegurar_equipo(equipo):

    posiciones = [
        "portero",
        "defensa_1", "defensa_2", "defensa_3", "defensa_4",
        "medio_1", "medio_2", "medio_3", "medio_4",
        "delantero_1", "delantero_2"
    ]

    limpio = {}

    for pos in posiciones:
        limpio[pos] = equipo.get(pos) if equipo else None

    return limpio