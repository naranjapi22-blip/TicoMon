import asyncio
import os
import sys

ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

sys.path.insert(0, ROOT)

from mundo.imagen_mundo import generar_escena_mundo


async def main():

    pokemons = [
        {
            "id": 1,
            "nombre": "Bulbasaur",
            "shiny": False,
        },
        {
            "id": 25,
            "nombre": "Pikachu",
            "shiny": False,
        },
        {
            "id": 4,
            "nombre": "Charmander",
            "shiny": False,
        },
    ]

    buffer = await generar_escena_mundo(
        pokemons,
        "grass",
    )

    os.makedirs("output", exist_ok=True)

    with open("output/mundo.gif", "wb") as f:
        f.write(buffer.getvalue())

    print("✅ GIF generado en output/mundo.gif")


asyncio.run(main())