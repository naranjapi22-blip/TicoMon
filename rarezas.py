import random



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
def obtener_rareza_safari(encuentro_numero=1):


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
        30,
        28,
        23,
        12,
        5,
        1.5,
        0.25
    ]

    boosts = {
        1: 1.00,
        2: 1.00,
        3: 1.10,
        4: 1.15,
        5: 1.25
    }

    boost = boosts.get(
        encuentro_numero,
        1.25
    )

    pesos[3] *= boost
    pesos[4] *= boost
    pesos[5] *= boost
    pesos[6] *= boost

    return random.choices(
        rarezas,
        weights=pesos,
        k=1
    )[0]
def obtener_pokemon_safari_region(
    inicio,
    fin,
    encuentro_numero=1
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
    fin,
    excluidos=None,
    encuentro_numero=1
):
    if excluidos is None:
        excluidos = set()

    ids_spawn = []

    while len(ids_spawn) < 3:

        pokemon_id = obtener_pokemon_safari_region(
            inicio,
            fin,
            encuentro_numero
        )

        if pokemon_id in ids_spawn:
            continue

        if pokemon_id in excluidos:
            continue

        ids_spawn.append(
            pokemon_id
        )

    return ids_spawn