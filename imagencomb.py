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
    es_shiny2=False
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

    img1_bytes = await obtener_sprite_bytes(session, poke1_id, es_shiny1, True)
    img2_bytes = await obtener_sprite_bytes(session, poke2_id, es_shiny2, False)

    img1 = Image.open(io.BytesIO(img1_bytes)).convert("RGBA")
    img2 = Image.open(io.BytesIO(img2_bytes)).convert("RGBA")

    img1 = preparar_sprite(img1, 200, 200)
    img2 = preparar_sprite(img2, 220, 140)

    pos1 = (100, 220)
    pos2 = (500, 60)

    fondo.paste(img2, pos2, img2)
    fondo.paste(img1, pos1, img1)

    buffer = io.BytesIO()
    fondo.save(buffer, format="PNG")
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

    # posiciones base 3 jugadores
    posiciones = [
        (60, 240),
        (200, 200),
        (340, 240)
    ]

    # dibujar jugadores
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

    # alpha enemigo
    alpha_bytes = await obtener_sprite_bytes(
        session,
        alpha["id"],
        False,
        False
    )

    alpha_img = Image.open(io.BytesIO(alpha_bytes)).convert("RGBA")
    alpha_img = preparar_sprite(alpha_img, 240, 240)

    fondo.paste(alpha_img, (540, 80), alpha_img)

    buffer = io.BytesIO()
    fondo.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer