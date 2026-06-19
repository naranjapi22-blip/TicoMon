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
        (750, 350),
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

    # Recortar transparencia
    trainer_img = trainer_img.crop(
        trainer_img.getbbox()
    )

    pokemon_img = pokemon_img.crop(
        pokemon_img.getbbox()
    )

    trainer_img = trainer_img.resize(
        (280, 280),
        Image.NEAREST
    )

    pokemon_img = pokemon_img.resize(
        (260, 260),
        Image.NEAREST
    )

    fondo.paste(
        trainer_img,
        (50, 40),
        trainer_img
    )

    fondo.paste(
        pokemon_img,
        (430, 60),
        pokemon_img
    )
    bbox = draw.textbbox(
        (0, 0),
        jugador,
        font=texto
    )

    draw.text(
        (
            220 - (bbox[2] - bbox[0]) // 2,
            350
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
            670 - (bbox[2] - bbox[0]) // 2,
            350
        ),
        nombre_pokemon,
        fill="white",
        font=texto
    )
    draw.text(
        (180, 20),
        "CAPTURA EXITOSA",
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