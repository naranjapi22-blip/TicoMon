import io
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

async def generar_escena_combate(session, poke1_id, poke2_id):
    """
    Genera una escena de combate profesional con fondo de estadio, 
    sombras proyectadas y arte oficial de alta calidad.
    """
    
    # URLs de arte oficial
    url1 = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke1_id}.png"
    url2 = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke2_id}.png"

    async def descargar_img(url):
        async with session.get(url) as resp:
            data = await resp.read()
            return Image.open(io.BytesIO(data)).convert("RGBA")

    img1 = await descargar_img(url1)
    img2 = await descargar_img(url2)

    # 1. Crear lienzo de 800x400 con fondo degradado épico
    fondo = Image.new("RGBA", (800, 400), (20, 20, 30, 255))
    draw = ImageDraw.Draw(fondo)
    for y in range(400):
        intensity = y / 400
        # Degradado de azul oscuro a gris acero
        color = (int(20 + intensity * 40), int(20 + intensity * 20), int(40 + intensity * 60))
        draw.line([(0, y), (800, y)], fill=color)

    # 2. Función para generar sombra suavizada (efecto profundidad)
    def aplicar_sombra(img, offset_x=0, offset_y=0):
        # Crear una capa de sombra basada en la transparencia del Pokémon
        sombra = Image.new("RGBA", img.size, (0, 0, 0, 160))
        # Usar el canal alfa del Pokémon original para la forma de la sombra
        sombra.putalpha(img.split()[3])
        # Difuminar para que se vea real
        sombra = sombra.filter(ImageFilter.GaussianBlur(8))
        return sombra

    # 3. Mejora visual de los Pokémon
    # Ajuste de contraste para que resalten más sobre el fondo
    enhancer1 = ImageEnhance.Contrast(img1)
    img1 = enhancer1.enhance(1.1)
    enhancer2 = ImageEnhance.Contrast(img2)
    img2 = enhancer2.enhance(1.1)
    
    # Redimensionar con alta calidad (LANCZOS)
    img1 = img1.resize((260, 260), Image.Resampling.LANCZOS)
    img2 = img2.resize((260, 260), Image.Resampling.LANCZOS).transpose(Image.FLIP_LEFT_RIGHT)
    
    # 4. Composición en el lienzo
    # Pegar sombras primero (con un pequeño desplazamiento)
    s1 = aplicar_sombra(img1)
    s2 = aplicar_sombra(img2)
    
    fondo.paste(s1, (60, 170), s1) # Sombra 1
    fondo.paste(s2, (510, 170), s2) # Sombra 2
    
    # Pegar los Pokémon sobre sus sombras
    fondo.paste(img1, (50, 100), img1)
    fondo.paste(img2, (500, 100), img2)

    # 5. Guardar resultado final
    buffer = io.BytesIO()
    fondo.save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return buffer