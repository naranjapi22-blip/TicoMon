import discord
import asyncio
import imagencomb


async def prueba_animacion(
    canal,
    session,
    jugadores,
    alpha
):

    mensaje = await canal.send(
        "🧪 Prueba de animación"
    )

    # Estado inicial

    buffer = await imagencomb.generar_escena_raid(
        session,
        jugadores,
        [120, 120, 120],
        alpha,
        1000,
        1000,
        "bosque.png"
    )

    await mensaje.edit(
        content="Estado inicial",
        attachments=[
            discord.File(
                buffer,
                filename="raid.png"
            )
        ]
    )

    await asyncio.sleep(2)

    # Alpha recibe daño

    buffer = await imagencomb.generar_escena_raid(
        session,
        jugadores,
        [120, 120, 120],
        alpha,
        700,
        1000,
        "bosque.png"
    )

    await mensaje.edit(
        content="☄️ Draco Meteor",
        attachments=[
            discord.File(
                buffer,
                filename="raid.png"
            )
        ]
    )

    await asyncio.sleep(2)

    # Jugador recibe daño

    buffer = await imagencomb.generar_escena_raid(
        session,
        jugadores,
        [50, 120, 120],
        alpha,
        700,
        1000,
        "bosque.png"
    )

    await mensaje.edit(
        content="⚡ Stone Edge",
        attachments=[
            discord.File(
                buffer,
                filename="raid.png"
            )
        ]
    )