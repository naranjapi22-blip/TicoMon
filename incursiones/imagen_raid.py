import io
import os
import logging
from PIL import Image
from PIL import ImageFilter
log = logging.getLogger('imagencomb')
from PIL import ImageSequence
from imagencomb import obtener_sprite_bytes

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
def crear_aura(img):

    aura = Image.new(
        "RGBA",
        img.size,
        (0, 0, 0, 0)
    )

    pixeles = aura.load()

    alpha = img.getchannel("A").load()

    for y in range(img.height):

        for x in range(img.width):

            if alpha[x, y] > 0:

                pixeles[x, y] = (
                    255,
                    0,
                    0,
                    180
                )

    return aura.filter(
        ImageFilter.GaussianBlur(12)
    )

def cargar_frames_gif(
    poke_id,
    max_w,
    max_h,
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

        frame = preparar_sprite(
            frame.convert("RGBA"),
            max_w,
            max_h
        )

        if es_espalda:

            frames.append(frame)

        else:

            frames.append(
                (
                    frame,
                    crear_aura(frame)
                )
            )

    return frames

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

def renderizar_frame_raid(
    fondo,
    sprites,
    alpha_img,
    aura,
):

    escena = fondo.copy()

    # ==================================================
    # CALCULAR CENTRO DEL GRUPO
    # ==================================================

    ESPACIO = 25

    ancho_total = sum(
        img.width
        for _, img in sprites
    )

    ancho_total += ESPACIO * (len(sprites) - 1)

    CENTRO_JUGADORES = 400

    x_actual = int(
        CENTRO_JUGADORES -
        ancho_total / 2
    )


    # ==================================================
    # ALPHA
    # ==================================================

    CENTRO_ALPHA = 440

    x_alpha = int(
        CENTRO_ALPHA -
        alpha_img.width / 2
    )

    Y_ALPHA = 50

    escena.paste(
        aura,
        (x_alpha, Y_ALPHA),
        aura
    )

    escena.paste(
        alpha_img,
        (x_alpha, Y_ALPHA),
        alpha_img
    )

    # ==================================================
    # JUGADORES
    # ==================================================

    # =====================================
    # POSICIONES PREDEFINIDAS
    # =====================================

    if len(sprites) == 3:

        posiciones = [
            (120, 250),   # Izquierda
            (260, 250),   # Centro adelantado
            (410, 250),   # Derecha
        ]

    elif len(sprites) == 2:

        posiciones = [
            (170, 235),
            (340, 235),
        ]

    else:

        posiciones = [
            (250, 230)
        ]

    for (p, img), (x, y) in zip(sprites, posiciones):

        escena.paste(
            img,
            (x, y),
            img
        )
# =====================================
# FUTUROS EFECTOS
# =====================================

# Barras de HP
# Daño flotante
# Clima
# Estado
# Sacudida de pantalla
    return escena
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

    # =====================================
    # CARGAR JUGADORES
    # =====================================

    sprites = []

    for p in jugadores:

        frames = cargar_frames_gif(
            p["id"],
            145,
            145,
            es_shiny=p.get("shiny", False),
            es_espalda=True
        )

        sprites.append(
            (
                p,
                frames[0]
            )
        )

    # Cargar el Alpha una sola vez
    alpha_frames = cargar_frames_gif(
        alpha["id"],
        260,
        260,
        es_espalda=False
    )
    alpha_img, aura = alpha_frames[0]

    # =====================================
    # RENDER
    # =====================================

    escena = renderizar_frame_raid(
        fondo,
        sprites,
        alpha_img,
        aura
    )

    # =====================================
    # EXPORTAR
    # =====================================

    buffer = io.BytesIO()

    escena.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer
async def generar_escena_raid_gif(
    session,
    jugadores,
    hp_jugadores,
    alpha,
    hp_alpha,
    hp_alpha_max,
    fondo_nombre
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

    # =====================================
    # CARGAR GIFS
    # =====================================

    sprites = []

    for p in jugadores:

        frames = cargar_frames_gif(
            p["id"],
            145,
            145,
            es_shiny=p.get("shiny", False),
            es_espalda=True
        )

        sprites.append(
            (p, frames)
        )

    alpha_frames = cargar_frames_gif(
        alpha["id"],
        260,
        260,
        es_espalda=False
    )




    # =====================================
    # TOTAL DE FRAMES
    # =====================================

    MAX_FRAMES = 32

    total_frames = min(
        MAX_FRAMES,
        max(
            len(alpha_frames),
            *[
                len(frames)
                for _, frames in sprites
            ]
        )
    )



    # =====================================
    # CREAR ESCENAS
    # =====================================

    resultado = []

    for frame_index in range(total_frames):

        # ==========================
        # Jugadores (frame actual)
        # ==========================

        sprites_frame = []

        for p, frames in sprites:

            frame = frames[
                frame_index % len(frames)
            ]

            sprites_frame.append(
                (p, frame)
            )

        # ==========================
        # Alpha (frame actual)
        # ==========================

        alpha_img, aura = alpha_frames[
            frame_index % len(alpha_frames)
        ]


        # ==========================
        # Renderizar escena
        # ==========================

        escena = renderizar_frame_raid(
            fondo,
            sprites_frame,
            alpha_img,
            aura
        )

        resultado.append(
            escena
        )


    # =====================================
    # EXPORTAR GIF
    # =====================================

    buffer = io.BytesIO()
    frames_gif = []

    for frame in resultado:

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