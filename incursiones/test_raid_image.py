import asyncio
import aiohttp

from incursiones import imagen_raid


async def main():

    jugadores = [
        {"id": 9},      # Blastoise
        {"id": 6},      # Charizard
        {"id": 149},    # Dragonite
    ]

    hp = [100, 100, 100]

    alpha = {
        "id": 484
    }

    async with aiohttp.ClientSession() as session:

        buffer = await imagen_raid.generar_escena_raid_gif(
            session,
            jugadores,
            hp,
            alpha,
            500,
            500,
            "bosque.png"
        )

        with open("raid.gif", "wb") as f:
            f.write(buffer.getvalue())

        print("GIF creado")



asyncio.run(main())