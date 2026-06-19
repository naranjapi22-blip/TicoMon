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
    if not trainer:
        trainer = "ash"
    fondo = Image.new(
        "RGBA",
        (500, 220),
        (25, 25, 35, 255)
    )

    draw = ImageDraw.Draw(fondo)

    titulo = ImageFont.truetype(
        FONT,
        24
    )

    texto = ImageFont.truetype(
        FONT,
        24
    )

    if not trainer:
        trainer = "ash"

    trainer_path = (
        Path("sprites/trainers")
        / f"{trainer}.png"
    )

    if not trainer_path.exists():

        trainer_path = (
            Path("sprites/trainers")
            / "ash.png"
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
        (40, 35),
        trainer_img
    )

    fondo.paste(
        pokemon_img,
        (300, 35),
        pokemon_img
    )
    bbox = draw.textbbox(
        (0, 0),
        jugador,
        font=texto
    )

    draw.text(
        (
            170 - (bbox[2] - bbox[0]) // 2,
            235
        ),
        jugador,
        fill="white",
        font=texto
    )

    nombre_pokemon = pokemon.capitalize()

    bbox = draw.textbbox(
        (0, 0),
        nombre_pokemon,
        font=texto
    )

    draw.text(
        (
            480 - (bbox[2] - bbox[0]) // 2,
            235
        ),
        nombre_pokemon,
        fill="white",
        font=texto
    )
    titulo_texto = "CAPTURA EXITOSA"

    bbox = draw.textbbox(
        (0, 0),
        titulo_texto,
        font=titulo
    )

    draw.text(
        (
            (650 - (bbox[2] - bbox[0])) // 2,
            10
        ),
        titulo_texto,
        fill=(255, 215, 0),
        font=titulo
    )
    buffer = BytesIO()

    fondo.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer