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
        (900, 400),
        (25, 25, 35, 255)
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
        (220, 220),
        Image.NEAREST
    )

    pokemon_img = pokemon_img.resize(
        (220, 220),
        Image.NEAREST
    )

    fondo.paste(
        trainer_img,
        (120, 90),
        trainer_img
    )

    fondo.paste(
        pokemon_img,
        (560, 90),
        pokemon_img
    )
    draw.text(
        (145, 320),
        trainer.replace("-", " ").title(),
        fill="white",
        font=texto
        )

    draw.text(
        (575, 320),
        pokemon.capitalize(),
        fill="white",
        font=texto
    )
    draw.text(
        (250, 25),
        "CAPTURA EXITOSA",
        fill=(255, 215, 0),
        font=titulo
    )

    draw.text(
        (220, 360),
        f"{jugador} capturó a {pokemon.capitalize()}",
        fill=(220, 220, 220),
        font=texto
    )

    buffer = BytesIO()

    fondo.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer