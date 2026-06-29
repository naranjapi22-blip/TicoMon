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

from mundo.mundo_manager import MundoManager


async def main():

    manager = MundoManager()

    await manager.iniciar()

    buffer = await manager.obtener_gif()

    os.makedirs(
        "output",
        exist_ok=True
    )

    with open(
        "output/mundo.gif",
        "wb"
    ) as f:

        f.write(buffer.getvalue())

    print(manager.world.tipo)

    print(manager.world.pokemons)


asyncio.run(main())