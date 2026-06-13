import asyncio

from safari_manager import SafariManager

# ====================================
# CONFIGURACIÓN
# ====================================

JUGADORES = 100
SIMULACIONES = 1000

# ====================================


async def main():

    total_capturas = 0

    for numero in range(SIMULACIONES):

        safari = SafariManager()

        safari.modo_test = True
        safari.activo = True

        for user_id in range(1, JUGADORES + 1):

            safari.participantes[user_id] = {
                "balls": 9,
                "capturas": 0
            }

        for encuentro in range(1, 6):

            pokemons = [
                {
                    "slot": 1,
                    "nombre": "magikarp",
                    "capture_rate": 255,
                    "es_shiny": False,
                    "tamano_factor": 1.0
                },
                {
                    "slot": 2,
                    "nombre": "pikachu",
                    "capture_rate": 190,
                    "es_shiny": False,
                    "tamano_factor": 1.0
                },
                {
                    "slot": 3,
                    "nombre": "bagon",
                    "capture_rate": 45,
                    "es_shiny": False,
                    "tamano_factor": 1.0
                }
            ]

            safari.crear_encuentro(
                pokemons
            )

            await safari.simular_encuentro()

        capturas_safari = sum(
            datos["capturas"]
            for datos in safari.participantes.values()
        )

        total_capturas += capturas_safari

    # ====================================
    # RESUMEN
    # ====================================

    pokemon_generados = (
        SIMULACIONES * 5 * 3
    )

    escapes = (
        pokemon_generados - total_capturas
    )

    porcentaje = (
        total_capturas /
        pokemon_generados
    ) * 100

    print()
    print("=" * 60)
    print("RESUMEN STRESS TEST SAFARI")
    print("=" * 60)

    print(
        f"Jugadores simulados : {JUGADORES}"
    )

    print(
        f"Safaris simulados   : {SIMULACIONES}"
    )

    print(
        f"Encuentros totales  : {SIMULACIONES * 5}"
    )

    print(
        f"Pokémon generados   : {pokemon_generados}"
    )

    print(
        f"Capturas totales    : {total_capturas}"
    )

    print(
        f"Escapes totales     : {escapes}"
    )

    print(
        f"% Captura           : {porcentaje:.2f}%"
    )

    print()
    print("TABLA")
    print("-" * 60)

    print(
        "| Jugadores | Safaris | Pokémon | Capturas | Escapes | % |"
    )

    print(
        f"| {JUGADORES:^10} | "
        f"{SIMULACIONES:^7} | "
        f"{pokemon_generados:^7} | "
        f"{total_capturas:^8} | "
        f"{escapes:^7} | "
        f"{porcentaje:>6.2f}% |"
    )

    print("-" * 60)


asyncio.run(main())