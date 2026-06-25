import asyncio
import aiohttp
from PIL import Image

import imagen_raid


async def main():

    jugadores = [
        {"id": 9},      # Blastoise
        {"id": 6},      # Charizard
        {"id": 149},    # Dragonite
    ]

    hp = [100, 100, 100]

    alpha = {
        "id": 384   
    }

    async with aiohttp.ClientSession() as session:

        buffer = await imagen_raid.generar_escena_raid(
            session,
            jugadores,
            hp,
            alpha,
            500,
            500,
            "bosque.png"
        )

        imagen = Image.open(buffer)
        imagen.save("raid_test_v2.png")

        print("✅ Imagen creada: raid_test.png")


asyncio.run(main())