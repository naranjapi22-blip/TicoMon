pokemon_por_rareza = {
    "muy_comun": [],
    "comun": [],
    "poco_comun": [],
    "raro": [],
    "epico": [],
    "mitico": [],
    "legendario": []
}
# safari_manager.py
def obtener_rareza_safari():

    rarezas = [
        "muy_comun",
        "comun",
        "poco_comun",
        "raro",
        "epico",
        "mitico",
        "legendario"
    ]

    pesos = [
        47,
        30,
        15,
        7,
        0.83,
        0.067,
        0.033
    ]

    return random.choices(
        rarezas,
        weights=pesos,
        k=1
    )[0]
def obtener_pokemon_safari_region(
    inicio,
    fin
):

    while True:

        rareza = obtener_rareza_safari()

        pokemon_disponibles = [
            pokemon_id
            for pokemon_id in pokemon_por_rareza[rareza]
            if inicio <= pokemon_id <= fin
        ]

        if not pokemon_disponibles:
            continue

        pokemon_id = random.choice(
            pokemon_disponibles
        )

        return pokemon_id
def generar_ids_safari_region(
    inicio,
    fin
):

    ids_spawn = []

    while len(ids_spawn) < 3:

        pokemon_id = obtener_pokemon_safari_region(
            inicio,
            fin
        )

        if pokemon_id in ids_spawn:
            continue

        ids_spawn.append(
            pokemon_id
        )

    return ids_spawn