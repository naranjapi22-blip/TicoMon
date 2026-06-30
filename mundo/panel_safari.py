import io
import os
import database
from mundo.mundo_manager import mundo_manager
import random
from PIL import (
    Image,
    ImageSequence,
    ImageDraw,
    ImageFont
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
    draw = ImageDraw.Draw(
        fondo
    )

    try:

        font = ImageFont.truetype(
            "arial.ttf",
            22
        )

    except:

        font = ImageFont.load_default()

    world = mundo_manager.obtener_estado(
        guild_id
    )
    draw.text(

        (40,5),

        "🏕 Safari del Servidor",

        fill="white",

        font=font

    )
    porcentaje = world.porcentaje
    barra_x = 40
    barra_y = 30

    barra_w = 500
    barra_h = 24

    draw.rounded_rectangle(
        (
            barra_x,
            barra_y,
            barra_x + barra_w,
            barra_y + barra_h
        ),
        radius=10,
        fill=(45,45,45)
    )

    ancho = int(
        barra_w *
        porcentaje /
        100
    )

    draw.rounded_rectangle(
        (
            barra_x,
            barra_y,
            barra_x + ancho,
            barra_y + barra_h
        ),
        radius=10,
        fill=(70,200,80)
    )

    draw.text(
        (
            barra_x + barra_w + 15,
            barra_y - 2
        ),
        f"{porcentaje}%",
        fill="white",
        font=font
    )
    draw.text(

        (40,65),

        f"{world.progreso}/{world.objetivo} capturas",

        fill="white",

        font=font

    )
    inicio_x = 40
    inicio_y = 105

    for i in range(5):

        if i < world.safaris_utilizados:

            color = (160,160,160)

        elif i < world.safaris_desbloqueados:

            color = (50,220,80)

        else:

            color = (80,80,80)

        x = inicio_x + i * 40

        draw.ellipse(

            (
                x,
                inicio_y,
                x + 26,
                inicio_y + 26
            ),

            fill=color

        )

    draw.text(

    (40,190),

    "Últimas capturas",

    fill="white",

    font=font

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