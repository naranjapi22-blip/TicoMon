import io
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

async def generar_escena_combate(session, poke1_id, poke2_id, hp1, hp2, hp_max=200, turno_jugador=0):
    """
    Versión Híbrida mejorada: Genera la escena con barras de vida 
    dinámicas proporcionales al HP actual.
    """
    
    url1 = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke1_id}.png"
    url2 = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke2_id}.png"

    async def descargar_img(url):
        async with session.get(url) as resp:
            data = await resp.read()
            return Image.open(io.BytesIO(data)).convert("RGBA")

    img1 = await descargar_img(url1)
    img2 = await descargar_img(url2)

    # 1. Lienzo y Fondo
    fondo = Image.new("RGBA", (800, 400), (20, 20, 30, 255))
    draw = ImageDraw.Draw(fondo)
    for y in range(400):
        intensity = y / 400
        color = (int(20 + intensity * 40), int(20 + intensity * 20), int(40 + intensity * 60))
        draw.line([(0, y), (800, y)], fill=color)

    # 2. Función interna para dibujar la barra de vida dinámica
    def dibujar_barra(x, y, vida_actual, vida_maxima):
        ancho_total = 200
        alto_barra = 20
        # Cálculo proporcional: nunca supera el ancho total
        porcentaje = max(0, min(1, vida_actual / vida_maxima))
        ancho_actual = int(ancho_total * porcentaje)
        
        # Color según salud
        if porcentaje > 0.5: color = (46, 204, 113) # Verde
        elif porcentaje > 0.2: color = (241, 196, 15) # Amarillo
        else: color = (231, 76, 60) # Rojo
        
        # Fondo de la barra (gris oscuro)
        draw.rectangle([x, y, x + ancho_total, y + alto_barra], fill=(50, 50, 50))
        # Barra de vida
        draw.rectangle([x, y, x + ancho_actual, y + alto_barra], fill=color)
        # Borde
        draw.rectangle([x, y, x + ancho_total, y + alto_barra], outline="white", width=2)

    # Dibujar las barras (posiciones ajustadas arriba de cada pokemon)
    dibujar_barra(50, 40, hp1, hp_max)
    dibujar_barra(550, 40, hp2, hp_max)

    # 3. Mejora visual y composición
    img1 = img1.resize((260, 260), Image.Resampling.LANCZOS)
    img2 = img2.resize((260, 260), Image.Resampling.LANCZOS).transpose(Image.FLIP_LEFT_RIGHT)

    pos1 = (60, 100) if turno_jugador != 1 else (90, 100)
    pos2 = (490, 100) if turno_jugador != 2 else (460, 100)

    def aplicar_sombra(img):
        sombra = Image.new("RGBA", img.size, (0, 0, 0, 160))
        sombra.putalpha(img.split()[3])
        return sombra.filter(ImageFilter.GaussianBlur(8))

    s1 = aplicar_sombra(img1)
    s2 = aplicar_sombra(img2)
    
    fondo.paste(s1, (pos1[0]+10, 170), s1) 
    fondo.paste(s2, (pos2[0]+10, 170), s2) 
    fondo.paste(img1, pos1, img1)
    fondo.paste(img2, pos2, img2)

    buffer = io.BytesIO()
    fondo.save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return buffer