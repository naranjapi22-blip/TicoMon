# imagencomb.py
import aiohttp
import io
from PIL import Image

async def generar_escena_combate(session, poke1_id, poke2_id):
    """Genera una imagen con dos Pokémon enfrentados."""
    url1 = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke1_id}.png"
    url2 = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke2_id}.png"

    async def descargar_img(url):
        async with session.get(url) as resp:
            data = await resp.read()
            return Image.open(io.BytesIO(data)).convert("RGBA")

    img1 = await descargar_img(url1)
    img2 = await descargar_img(url2)

    # Crear lienzo: Fondo (ej. 600x300)
    fondo = Image.new("RGBA", (600, 300), (240, 240, 240, 255))
    
    # Redimensionar Pokémon para que quepan
    img1 = img1.resize((200, 200))
    img2 = img2.resize((200, 200)).transpose(Image.FLIP_LEFT_RIGHT) # Espejado para que se miren
    
    # Pegar en el fondo
    fondo.paste(img1, (50, 50), img1)
    fondo.paste(img2, (350, 50), img2)
    
    # Guardar en buffer
    buffer = io.BytesIO()
    fondo.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer