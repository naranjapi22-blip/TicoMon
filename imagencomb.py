import io
from PIL import Image, ImageDraw, ImageFont

async def generar_escena_combate(session, poke1_id, poke2_id, nombre1, nombre2, hp1, hp2, hp_max1, hp_max2, turno_jugador=0, es_shiny1=False, es_shiny2=False):
    """
    Genera una escena de combate estilo consola clásica (Perspectiva isométrica/RPG).
    """
    
    # 1. Función para obtener las URLs correctas (Frente/Espalda y Normal/Shiny)
    def obtener_url(poke_id, es_shiny, es_espalda):
        base = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"
        partes = []
        if es_espalda:
            partes.append("back")
        if es_shiny:
            partes.append("shiny")
            
        if not partes:
            return f"{base}/{poke_id}.png"
        else:
            return f"{base}/{'/'.join(partes)}/{poke_id}.png"

    # P1 (Aliado) siempre de espaldas. P2 (Enemigo) siempre de frente.
    url1 = obtener_url(poke1_id, es_shiny1, es_espalda=True)
    url2 = obtener_url(poke2_id, es_shiny2, es_espalda=False)

    async def descargar_img(url):
        async with session.get(url) as resp:
            data = await resp.read()
            return Image.open(io.BytesIO(data)).convert("RGBA")

    img1 = await descargar_img(url1)
    img2 = await descargar_img(url2)

    # 2. Lienzo y Fondo (Estilo campo de batalla verde clásico)
    fondo = Image.new("RGBA", (800, 400), (135, 206, 235, 255)) # Cielo azul claro base
    draw = ImageDraw.Draw(fondo)
    
    # Dibujar el pasto (mitad inferior)
    draw.rectangle([0, 150, 800, 400], fill=(120, 200, 80, 255))
    
    # Dibujar plataformas (Césped)
    # Plataforma Enemigo (Arriba a la derecha)
    draw.ellipse([450, 110, 750, 170], fill=(90, 160, 60, 255), outline=(70, 130, 40, 255), width=3)
    # Plataforma Aliado (Abajo a la izquierda)
    draw.ellipse([50, 280, 350, 340], fill=(90, 160, 60, 255), outline=(70, 130, 40, 255), width=3)

    # 3. Escalar Sprites en estilo Pixel Art (NEAREST evita que se vean borrosos)
    scale_factor = 3
    img1 = img1.resize((img1.width * scale_factor, img1.height * scale_factor), Image.Resampling.NEAREST)
    img2 = img2.resize((img2.width * scale_factor, img2.height * scale_factor), Image.Resampling.NEAREST)

    # 4. Lógica de animación de ataque (pequeño movimiento si es su turno)
    offset_atk1 = (30, -20) if turno_jugador == 1 else (0, 0)
    offset_atk2 = (-30, 20) if turno_jugador == 2 else (0, 0)

    # Posiciones RPG clásicas
    pos1 = (80 + offset_atk1[0], 90 + offset_atk1[1])  # Aliado (Abajo Izquierda)
    pos2 = (480 + offset_atk2[0], 0 + offset_atk2[1]) # Enemigo (Arriba Derecha)

    # Pegar los Pokémon en el lienzo
    fondo.paste(img2, pos2, img2) # Primero el enemigo (más al fondo)
    fondo.paste(img1, pos1, img1) # Luego el aliado (más al frente)

    # 5. Función para dibujar los HUDs (Cajas de vida estilo juego)
    # Usamos la fuente por defecto de PIL (puedes cargar un .ttf pixel art más adelante si deseas)
    font = ImageFont.load_default()

    def dibujar_hud(x, y, nombre, vida_actual, vida_maxima):
        # Caja principal
        draw.rounded_rectangle([x, y, x + 280, y + 80], radius=10, fill=(240, 240, 230, 255), outline=(50, 50, 50, 255), width=4)
        
        # Sombra interior
        draw.rounded_rectangle([x+5, y+5, x + 275, y + 75], radius=8, fill=(255, 255, 245, 255))

        # Texto del Nombre
        draw.text((x + 20, y + 10), nombre.upper(), fill="black", font=font)
        
        # Contenedor de la barra de vida
        bar_x, bar_y = x + 60, y + 40
        bar_w, bar_h = 200, 15
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(80, 80, 80, 255), outline=(0,0,0), width=2)
        
        # Cálculo de la vida
        porcentaje = max(0, min(1, vida_actual / vida_maxima))
        ancho_actual = int(bar_w * porcentaje)
        
        # Color de vida
        if porcentaje > 0.5: color_hp = (46, 204, 113) # Verde
        elif porcentaje > 0.2: color_hp = (241, 196, 15) # Amarillo
        else: color_hp = (231, 76, 60) # Rojo
        
        # Barra de vida actual
        if ancho_actual > 0:
            draw.rectangle([bar_x, bar_y, bar_x + ancho_actual, bar_y + bar_h], fill=color_hp)
            
        # Texto de HP (Opcional, estilo 100/100)
        draw.text((x + 160, y + 60), f"{int(vida_actual)} / {int(vida_maxima)}", fill="black", font=font)

    # 6. Dibujar los HUDs en las posiciones cruzadas
    # HUD Enemigo (Arriba a la Izquierda)
    dibujar_hud(30, 30, nombre2, hp2, hp_max2)
    # HUD Aliado (Abajo a la Derecha)
    dibujar_hud(490, 280, nombre1, hp1, hp_max1)

    # Preparar buffer y retornar
    buffer = io.BytesIO()
    fondo.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer