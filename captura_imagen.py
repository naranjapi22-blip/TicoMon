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

    fondo = Image.new(
        "RGBA",
        (500, 260),
        (25, 25, 35, 255)
    )

    draw = ImageDraw.Draw(fondo)

    titulo_font = ImageFont.truetype(
        FONT,
        24
    )

    texto_font = ImageFont.truetype(
        FONT,
        24
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

    # Trainer un poco más pequeño
    trainer_img = trainer_img.resize(
        (140, 140),
        Image.NEAREST
    )

    # Escalar Pokémon según tamaño original
    if pokemon_img.width < 64 or pokemon_img.height < 64:

        pokemon_size = 180

    else:

        pokemon_size = 160

    pokemon_img = pokemon_img.resize(
        (pokemon_size, pokemon_size),
        Image.NEAREST
    )

    # Posiciones
    trainer_x = 60
    trainer_y = 35

    pokemon_x = 280
    pokemon_y = 35

    if pokemon_size == 180:
        pokemon_y = 25

    fondo.paste(
        trainer_img,
        (trainer_x, trainer_y),
        trainer_img
    )

    fondo.paste(
        pokemon_img,
        (pokemon_x, pokemon_y),
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
            140 - (bbox[2] - bbox[0]) // 2,
            210
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
            390 - (bbox[2] - bbox[0]) // 2,
            210
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
            (500 - (bbox[2] - bbox[0])) // 2,
            10
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