import asyncio

from safari_manager import SafariManager

SIMULACIONES = 100


async def main():

    total_capturas = 0

    for numero in range(SIMULACIONES):

        safari = SafariManager()

        safari.modo_test = True
        safari.activo = True

        for user_id in range(1, 101):

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

        capturas = sum(
            p["capturas"]
            for p in safari.participantes.values()
        )

        total_capturas += capturas

        print(
            f"Safari {numero+1}: "
            f"{capturas} capturas"
        )

    print()
    print("======== RESUMEN ========")
    print(
        f"Safaris simulados: {SIMULACIONES}"
    )
    print(
        f"Capturas totales: {total_capturas}"
    )


asyncio.run(main())