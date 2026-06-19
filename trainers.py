from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from io import BytesIO

CARPETA_TRAINERS = Path(
    "sprites/trainers"
)

TRAINERS = sorted(
    archivo.stem
    for archivo in CARPETA_TRAINERS.glob("*.png")
)


async def generar_imagen_trainers(
    pagina=0
):

    POR_PAGINA = 10

    inicio = pagina * POR_PAGINA
    fin = inicio + POR_PAGINA

    trainers = TRAINERS[inicio:fin]

    columnas = 5
    filas = 2

    ancho_celda = 220
    alto_celda = 220

    ancho = columnas * ancho_celda
    alto = filas * alto_celda + 80

    imagen = Image.new(
        "RGBA",
        (ancho, alto),
        (30, 30, 30)
    )

    draw = ImageDraw.Draw(imagen)

    try:

        fuente_titulo = ImageFont.truetype(
            "arial.ttf",
            36
        )

        fuente_nombre = ImageFont.truetype(
            "arial.ttf",
            20
        )

    except:

        fuente_titulo = ImageFont.load_default()
        fuente_nombre = ImageFont.load_default()

    total_paginas = (
        len(TRAINERS) + POR_PAGINA - 1
    ) // POR_PAGINA

    draw.text(
        (20, 20),
        f"Entrenadores ({pagina + 1}/{total_paginas})",
        fill="white",
        font=fuente_titulo
    )

    y_offset = 80

    for indice, trainer in enumerate(trainers):

        columna = indice % columnas
        fila = indice // columnas

        x = columna * ancho_celda
        y = fila * alto_celda + y_offset

        ruta = (
            CARPETA_TRAINERS
            / f"{trainer}.png"
        )

        try:

            sprite = Image.open(
                ruta
            ).convert("RGBA")

            sprite.thumbnail(
                (120, 120)
            )

            sprite_x = (
                x +
                (ancho_celda - sprite.width) // 2
            )

            sprite_y = y + 10

            imagen.paste(
                sprite,
                (sprite_x, sprite_y),
                sprite
            )

        except Exception as e:

            print(
                f"Error cargando {trainer}: {e}"
            )

        numero_real = (
            inicio + indice + 1
        )

        nombre = (
            trainer
            .replace("-", " ")
            .replace("_", " ")
            .title()
        )

        texto = (
            f"{numero_real}. {nombre}"
        )

        bbox = draw.textbbox(
            (0, 0),
            texto,
            font=fuente_nombre
        )

        texto_ancho = (
            bbox[2] - bbox[0]
        )

        draw.text(
            (
                x +
                (ancho_celda - texto_ancho) // 2,
                y + 150
            ),
            texto,
            fill="white",
            font=fuente_nombre
        )

    buffer = BytesIO()

    imagen.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer