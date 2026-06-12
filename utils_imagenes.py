from PIL import Image
from io import BytesIO

async def crear_imagen_encuentro(pokemons, session):

    sprites = []

    for pokemon in pokemons:

        pokemon_id = pokemon["pokemon_id"]

        if pokemon["es_shiny"]:
            url = (
                "https://raw.githubusercontent.com/"
                "PokeAPI/sprites/master/"
                f"sprites/pokemon/shiny/{pokemon_id}.png"
            )
        else:
            url = (
                "https://raw.githubusercontent.com/"
                "PokeAPI/sprites/master/"
                f"sprites/pokemon/{pokemon_id}.png"
            )

        try:

            print("URL:", url)

            async with session.get(url) as resp:

                print("STATUS:", resp.status)

                if resp.status != 200:
                    continue

                data = await resp.read()

            sprite = Image.open(
                BytesIO(data)
            ).convert("RGBA")

            sprites.append(sprite)

        except Exception:
            continue

    if not sprites:
        return None

    ancho_total = sum(
        sprite.width
        for sprite in sprites
    )

    alto_maximo = max(
        sprite.height
        for sprite in sprites
    )

    imagen_final = Image.new(
        "RGBA",
        (ancho_total, alto_maximo),
        (255, 255, 255, 0)
    )

    x_actual = 0

    for sprite in sprites:

        y_actual = (
            alto_maximo - sprite.height
        ) // 2

        imagen_final.paste(
            sprite,
            (x_actual, y_actual),
            sprite
        )

        x_actual += sprite.width

    buffer = BytesIO()

    imagen_final.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer