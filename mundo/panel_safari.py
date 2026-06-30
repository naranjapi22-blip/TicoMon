import io
import os
import database
import random
from PIL import (
    Image,
    ImageSequence
)

POSICIONES = [
    (140,290),
    (270,290),
    (400,290),
    (530,290),
    (660,290),
]

async def generar_panel_safari(
    guild_id,
):
    capturas = database.obtener_ultimas_capturas(
        guild_id
    )

    pokemons = []

    for nombre, es_shiny in capturas[:5]:

        pokemon = database.obtener_pokemon_local_nombre(
            nombre
        )

        if not pokemon:
            continue

        pokemons.append({
            "id": pokemon["id"],
            "nombre": nombre,
            "shiny": bool(es_shiny)
        })
    carpeta_fondos = os.path.join(
        "animaciones",
        "assets",
        "fondos"
    )

    fondos = [
        f for f in os.listdir(carpeta_fondos)
        if f.lower().endswith(".png")
    ]

    if not fondos:
        raise FileNotFoundError(
            "No hay fondos disponibles."
        )

    ruta_fondo = os.path.join(
        carpeta_fondos,
        random.choice(fondos)
    )

    if not os.path.exists(ruta_fondo):
        fondo = Image.new(
            "RGBA",
            (800, 400),
            (50, 50, 50, 255)
        )
    else:
        fondo = Image.open(
            ruta_fondo
        ).convert("RGBA")

    fondo = fondo.resize(
        (800, 400),
        Image.Resampling.LANCZOS
    )

    # ==========================
    # CARGAR GIFS
    # ==========================

    gifs = []

    for pokemon in pokemons:

        try:

            frames = cargar_frames_gif_mundo(
                pokemon["id"],
                es_shiny=pokemon.get(
                    "shiny",
                    False
                )
            )

            gifs.append(frames)

        except Exception:

            continue

    # ==========================
    # TOTAL DE FRAMES
    # ==========================
    if not gifs:

        return None
    total_frames = min(
        32,
        max(
            len(frames)
            for frames in gifs
        )
    )

    escenas = []

    # ==========================
    # CREAR ESCENAS
    # ==========================

    for frame_index in range(total_frames):

        escena = fondo.copy()

        for posicion, frames in zip(
            POSICIONES,
            gifs
        ):
            x, y = posicion

            sprite = frames[
                frame_index % len(frames)
            ]

            w, h = sprite.size

            escena.paste(
                sprite,
                (
                    x - w // 2,
                    y - h // 2
                ),
                sprite
            )

        escenas.append(escena)

    # ==========================
    # EXPORTAR GIF
    # ==========================

    buffer = io.BytesIO()

    frames_gif = []

    for frame in escenas:

        frames_gif.append(
            frame.convert(
                "P",
                palette=Image.Palette.ADAPTIVE,
                colors=128
            )
        )

    frames_gif[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=frames_gif[1:],
        duration=80,
        loop=0,
        optimize=True,
        disposal=2
    )

    buffer.seek(0)

    return buffer
def cargar_frames_gif_mundo(
    poke_id,
    es_shiny=False,
    es_espalda=False
):

    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    from io import BytesIO

    R2_PUBLIC_URL = "https://pub-23cb564f6c174627926c1ac0409563d4.r2.dev"

    carpetas = []

    if es_espalda:
        if es_shiny:
            carpetas.append("back_shiny")

        carpetas.append("back")

        if es_shiny:
            carpetas.append("shiny")

        carpetas.append("regular")

    else:
        if es_shiny:
            carpetas.append("shiny")

        carpetas.append("regular")

    gif = None

    for carpeta in carpetas:

        url = f"{R2_PUBLIC_URL}/{carpeta}/{poke_id}.gif"

        try:

            req = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            with urlopen(req) as response:

                gif = Image.open(
                    BytesIO(response.read())
                )

            break

        except HTTPError:
            continue

    if gif is None:
        raise FileNotFoundError(
            f"No se encontró ningún GIF para {poke_id}"
        )

    frames = []

    for i, frame in enumerate(ImageSequence.Iterator(gif)):

        if i % 2:
            continue

        # Sin preparar_sprite()
        frame = frame.convert("RGBA")

        frames.append(frame)

    return frames