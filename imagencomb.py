import io
import os
import aiohttp
import logging
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger('imagencomb')


# =========================
# SPRITE DOWNLOAD
# =========================
async def obtener_sprite_bytes(session, poke_id, es_shiny, es_espalda):
    base = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"

    async def descargar(back):
        partes = ["back"] if back else []
        if es_shiny:
            partes.append("shiny")

        url = (
            f"{base}/{'/'.join(partes)}/{poke_id}.png"
            if partes
            else f"{base}/{poke_id}.png"
        )

        async with session.get(url) as response:
            if response.status == 200:
                data = await response.read()
                if data:
                    return data

            raise Exception(f"HTTP {response.status}")

    try:
        return await descargar(es_espalda)
    except Exception:
        if es_espalda:
            return await descargar(False)
        raise


# =========================
# SPRITE PREP
# =========================
def preparar_sprite(img, max_w, max_h):
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    escala = min(3.0, max_w / img.width, max_h / img.height)

    return img.resize(
        (int(img.width * escala), int(img.height * escala)),
        Image.Resampling.NEAREST
    )


# =========================
# COMBATE NORMAL (2v1 legacy)
# =========================
async def generar_escena_combate(
    session,
    poke1_id,
    poke2_id,
    nombre1,
    nombre2,
    hp1,
    hp2,
    hp_max1,
    hp_max2,
    fondo_nombre,
    turno_jugador=0,
    es_shiny1=False,
    es_shiny2=False,
    trainer1=None,
    trainer2=None,
):

    carpeta_fondos = "fondos"
    ruta_fondo = os.path.join(carpeta_fondos, fondo_nombre)

    if not os.path.exists(ruta_fondo):
        fondo = Image.new("RGBA", (800, 400), (50, 50, 50, 255))
    else:
        fondo = Image.open(ruta_fondo).convert("RGBA")

    fondo = fondo.resize((800, 400), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(fondo)
    font = ImageFont.load_default()
    trainer_img1 = None
    trainer_img2 = None

    if trainer1:
        trainer_img1 = cargar_trainer(trainer1)

    if trainer2:
        trainer_img2 = cargar_trainer(trainer2)
    img1_bytes = await obtener_sprite_bytes(session, poke1_id, es_shiny1, True)
    img2_bytes = await obtener_sprite_bytes(session, poke2_id, es_shiny2, False)

    img1 = Image.open(io.BytesIO(img1_bytes)).convert("RGBA")
    img2 = Image.open(io.BytesIO(img2_bytes)).convert("RGBA")

    img1 = preparar_sprite(img1, 200, 200)
    img2 = preparar_sprite(img2, 220, 140)

    pos1 = (100, 220)
    pos2 = (500, 60)
    if trainer_img1:

        trainer_img1.thumbnail(
            (140, 140),
            Image.Resampling.LANCZOS
        )

        fondo.paste(
            trainer_img1,
            (20, 220),
            trainer_img1
        )

    if trainer_img2:

        trainer_img2.thumbnail(
            (140, 140),
            Image.Resampling.LANCZOS
        )

        fondo.paste(
            trainer_img2,
            (640, 10),
            trainer_img2
        )
    fondo.paste(img2, pos2, img2)
    fondo.paste(img1, pos1, img1)

    buffer = io.BytesIO()
    fondo.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer
async def generar_pantalla_victoria(
    session,
    poke_id,
    nombre,
    es_shiny,
    fondo_nombre,
    trainer,
):
    carpeta_fondos = "fondos"
    ruta_fondo = os.path.join(
        carpeta_fondos,
        fondo_nombre
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

    draw = ImageDraw.Draw(fondo)

    font = ImageFont.load_default()

    trainer_img = cargar_trainer(trainer)

    trainer_img.thumbnail(
        (180, 180),
        Image.Resampling.LANCZOS
    )

    fondo.paste(
        trainer_img,
        (40, 170),
        trainer_img
    )

    sprite_bytes = await obtener_sprite_bytes(
        session,
        poke_id,
        es_shiny,
        False
    )

    sprite = Image.open(
        io.BytesIO(sprite_bytes)
    ).convert("RGBA")

    sprite = preparar_sprite(
        sprite,
        260,
        260
    )

    fondo.paste(
        sprite,
        (420, 80),
        sprite
    )

    draw.text(
        (300, 20),
        "🏆 VICTORIA 🏆",
        fill="white",
        font=font
    )

    draw.text(
        (300, 55),
        nombre,
        fill="white",
        font=font
    )

    buffer = io.BytesIO()

    fondo.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer

# =========================
# RAID (3v1 base)
# =========================
async def generar_escena_raid(
    session,
    jugadores,
    hp_jugadores,
    alpha,
    hp_alpha,
    hp_alpha_max,
    fondo_nombre
):

    carpeta_fondos = "fondos"
    ruta_fondo = os.path.join(carpeta_fondos, fondo_nombre)

    if not os.path.exists(ruta_fondo):
        fondo = Image.new("RGBA", (800, 400), (50, 50, 50, 255))
    else:
        fondo = Image.open(ruta_fondo).convert("RGBA")

    fondo = fondo.resize((800, 400), Image.Resampling.LANCZOS)

    # POSICIONES RAID (IMPORTANTE)
    posiciones = [
        (60, 270),   # izquierda (Blastoise)
        (220, 210),  # centro (Charizard)
        (380, 270)   # derecha (Dragonite)
    ]

    # =========================
    # DIBUJAR JUGADORES (3)
    # =========================
    for i, p in enumerate(jugadores):

        img_bytes = await obtener_sprite_bytes(
            session,
            p["id"],
            False,
            True
        )

        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        img = preparar_sprite(img, 160, 160)

        fondo.paste(img, posiciones[i], img)

    # =========================
    # DIBUJAR ALPHA
    # =========================
    alpha_bytes = await obtener_sprite_bytes(
        session,
        alpha["id"],
        False,
        False
    )

    alpha_img = Image.open(io.BytesIO(alpha_bytes)).convert("RGBA")
    alpha_img = preparar_sprite(alpha_img, 300, 300)

    fondo.paste(alpha_img, (560, 60), alpha_img)

    buffer = io.BytesIO()
    fondo.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer
def cargar_trainer(nombre):

    ruta = os.path.join(
        "sprites",
        "trainers",
        f"{nombre}.png"
    )

    if not os.path.exists(ruta):

        ruta = os.path.join(
            "sprites",
            "trainers",
            "ash.png"
        )

    img = Image.open(ruta).convert("RGBA")

    return img