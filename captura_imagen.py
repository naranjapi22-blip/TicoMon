from io import BytesIO
from pathlib import Path

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


FONT = "fonts/DejaVuSans-Bold.ttf"


async def generar_imagen_captura(
    trainer,
    pokemon_id,
    es_shiny,
    jugador,
    pokemon
):

    fondo = Image.new(
        "RGBA",
        (800, 300),
        (30, 30, 40, 255)
    )

    draw = ImageDraw.Draw(fondo)

    titulo = ImageFont.truetype(
        FONT,
        36
    )

    texto = ImageFont.truetype(
        FONT,
        24
    )

    trainer_path = (
        Path("sprites/trainers")
        / f"{trainer}.png"
    )

    if es_shiny:

        pokemon_path = (
            Path("sprites/shiny")
            / f"{pokemon_id}.png"
        )

    else:

        pokemon_path = (
            Path("sprites/regular")
            / f"{pokemon_id}.png"
        )

    trainer_img = Image.open(
        trainer_path
    ).convert("RGBA")

    pokemon_img = Image.open(
        pokemon_path
    ).convert("RGBA")

    trainer_img = trainer_img.resize(
        (160, 160),
        Image.NEAREST
    )

    pokemon_img = pokemon_img.resize(
        (160, 160),
        Image.NEAREST
    )

    fondo.paste(
        trainer_img,
        (120, 70),
        trainer_img
    )

    fondo.paste(
        pokemon_img,
        (520, 70),
        pokemon_img
    )

    draw.text(
        (240, 20),
        "🎉 CAPTURA EXITOSA",
        fill="white",
        font=titulo
    )

    draw.text(
        (190, 245),
        f"{jugador} capturó {pokemon.capitalize()}",
        fill="white",
        font=texto
    )

    buffer = BytesIO()

    fondo.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer