import io
import os
import logging
from PIL import Image
from PIL import Image, ImageFilter
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

    ruta_fondo = os.path.join(
        os.path.dirname(__file__),
        fondo_nombre
    )

    if not os.path.exists(ruta_fondo):
        fondo = Image.new("RGBA", (800, 400), (50, 50, 50, 255))
    else:
        fondo = Image.open(ruta_fondo).convert("RGBA")

    fondo = fondo.resize((800, 400), Image.Resampling.LANCZOS)


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
# RAID (3v1)
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


    # ==================================================
    # CARGAR SPRITES DE LOS JUGADORES
    # ==================================================

    sprites = []

    for p in jugadores:

        img_bytes = await obtener_sprite_bytes(
            session,
            p["id"],
            False,
            True
        )

        img = Image.open(
            io.BytesIO(img_bytes)
        ).convert("RGBA")

        img = preparar_sprite(
            img,
            160,
            160
        )

        sprites.append(
            (p, img)
        )

    # ==================================================
    # CALCULAR CENTRO DEL GRUPO
    # ==================================================

    ESPACIO = 25

    ancho_total = sum(
        img.width
        for _, img in sprites
    )

    ancho_total += (
        ESPACIO *
        (len(sprites) - 1)
    )

    CENTRO_JUGADORES = 400

    x_actual = int(
        CENTRO_JUGADORES -
        ancho_total / 2
    )
    # ==================================================
    # ALPHA
    # ==================================================

    alpha_bytes = await obtener_sprite_bytes(
        session,
        alpha["id"],
        False,
        False
    )

    alpha_img = Image.open(
        io.BytesIO(alpha_bytes)
    ).convert("RGBA")

    alpha_img = preparar_sprite(
        alpha_img,
        300,
        300
    )
    # =========================
    # AURA ROJA
    # =========================

    aura = Image.new("RGBA", alpha_img.size, (0, 0, 0, 0))

    pixeles = aura.load()
    alpha_pixeles = alpha_img.getchannel("A").load()

    for y in range(alpha_img.height):
        for x in range(alpha_img.width):
            if alpha_pixeles[x, y] > 0:
                pixeles[x, y] = (255, 0, 0, 180)

    aura = aura.filter(ImageFilter.GaussianBlur(12))
    CENTRO_ALPHA = 440

    x_alpha = int(
        CENTRO_ALPHA -
        alpha_img.width / 2
    )

    Y_ALPHA = 50  # Más pequeño = más arriba

    # Aura detrás
    fondo.paste(
        aura,
        (x_alpha, Y_ALPHA),
        aura
    )

    # Alpha encima
    fondo.paste(
        alpha_img,
        (x_alpha, Y_ALPHA),
        alpha_img
    )

    # ==================================================
    # DIBUJAR JUGADORES
    # ==================================================

    for i, (p, img) in enumerate(sprites):

        if len(sprites) == 3:
            y = [270, 210, 270][i]

        elif len(sprites) == 2:
            y = 240

        else:
            y = 240

        fondo.paste(
            img,
            (int(x_actual), y),
            img
        )

        x_actual += img.width + ESPACIO



    # ==================================================
    # EXPORTAR
    # ==================================================

    buffer = io.BytesIO()

    fondo.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer