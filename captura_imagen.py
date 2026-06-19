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
    trainer = trainer or "ash"

    ANCHO = 320
    ALTO = 180

    fondo = Image.new(
        "RGBA",
        (ANCHO, ALTO),
        (25, 25, 35, 255)
    )

    draw = ImageDraw.Draw(fondo)

    titulo_font = ImageFont.truetype(
        FONT,
        18
    )

    texto_font = ImageFont.truetype(
        FONT,
        16
    )

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
        (90, 90),
        Image.NEAREST
    )

    pokemon_img = pokemon_img.resize(
        (90, 90),
        Image.NEAREST
    )

    fondo.paste(
        trainer_img,
        (25, 35),
        trainer_img
    )

    fondo.paste(
        pokemon_img,
        (205, 35),
        pokemon_img
    )

    # Nombre jugador
    bbox = draw.textbbox(
        (0, 0),
        jugador,
        font=texto_font
    )

    draw.text(
        (
            70 - (bbox[2] - bbox[0]) // 2,
            135
        ),
        jugador,
        fill="white",
        font=texto_font
    )

    # Nombre Pokémon
    nombre_pokemon = pokemon.capitalize()

    bbox = draw.textbbox(
        (0, 0),
        nombre_pokemon,
        font=texto_font
    )

    draw.text(
        (
            250 - (bbox[2] - bbox[0]) // 2,
            135
        ),
        nombre_pokemon,
        fill="white",
        font=texto_font
    )

    # Título
    titulo_texto = "CAPTURA EXITOSA"

    bbox = draw.textbbox(
        (0, 0),
        titulo_texto,
        font=titulo_font
    )

    draw.text(
        (
            (ANCHO - (bbox[2] - bbox[0])) // 2,
            8
        ),
        titulo_texto,
        fill=(255, 215, 0),
        font=titulo_font
    )

    buffer = BytesIO()

    fondo.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer