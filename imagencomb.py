import io
from PIL import Image, ImageDraw, ImageFont

async def generar_escena_combate(session, poke1_id, poke2_id, nombre1, nombre2, hp1, hp2, hp_max1, hp_max2, turno_jugador=0, es_shiny1=False, es_shiny2=False):
    
    # 1. Función para obtener URLs (Frente/Espalda y Normal/Shiny)
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

    url1 = obtener_url(poke1_id, es_shiny1, es_espalda=True)
    url2 = obtener_url(poke2_id, es_shiny2, es_espalda=False)

    async def descargar_img(url):
        async with session.get(url) as resp:
            data = await resp.read()
            return Image.open(io.BytesIO(data)).convert("RGBA")

    img1 = await descargar_img(url1)
    img2 = await descargar_img(url2)

    # --- EL SECRETO: RECORTAR LA TRANSPARENCIA ---
    # Esto elimina el espacio vacío para poder posicionarlos tocando el suelo
    bbox1 = img1.getbbox()
    if bbox1: img1 = img1.crop(bbox1)
    
    bbox2 = img2.getbbox()
    if bbox2: img2 = img2.crop(bbox2)

    # Escalar Sprites
    scale_factor = 3
    img1 = img1.resize((int(img1.width * scale_factor), int(img1.height * scale_factor)), Image.Resampling.NEAREST)
    img2 = img2.resize((int(img2.width * scale_factor), int(img2.height * scale_factor)), Image.Resampling.NEAREST)

    # 2. Lienzo y Fondo mejorados
    fondo = Image.new("RGBA", (800, 400), (160, 208, 224, 255)) # Cielo más suave
    draw = ImageDraw.Draw(fondo)
    draw.rectangle([0, 180, 800, 400], fill=(112, 200, 104, 255)) # Pasto más natural

    # 3. Plataformas (Centros calculados)
    centro_enemigo = (600, 160)
    draw.ellipse([460, 130, 740, 190], fill=(90, 160, 60, 255)) # Sombra enemigo

    centro_aliado = (220, 320)
    draw.ellipse([60, 280, 380, 360], fill=(90, 160, 60, 255)) # Sombra aliado

    # 4. Lógica de animación de ataque
    offset_atk1 = (30, -20) if turno_jugador == 1 else (0, 0)
    offset_atk2 = (-30, 20) if turno_jugador == 2 else (0, 0)

    # Posicionamiento exacto (centrado horizontal, apoyado verticalmente en la base)
    pos1 = (
        centro_aliado[0] - (img1.width // 2) + offset_atk1[0],
        centro_aliado[1] - img1.height + 20 + offset_atk1[1] 
    )
    pos2 = (
        centro_enemigo[0] - (img2.width // 2) + offset_atk2[0],
        centro_enemigo[1] - img2.height + 20 + offset_atk2[1]
    )

    # Pegar los Pokémon (Enemigo primero, luego aliado por la perspectiva)
    fondo.paste(img2, pos2, img2)
    fondo.paste(img1, pos1, img1)

    # 5. Función para dibujar los HUDs (Diseño GBA/DS)
    font = ImageFont.load_default()

    def dibujar_hud(x, y, nombre, vida_actual, vida_maxima):
        # Caja principal más delgada y rectangular
        draw.rounded_rectangle([x, y, x + 310, y + 65], radius=6, fill=(248, 248, 240, 255), outline=(60, 60, 60, 255), width=3)
        
        # Nombre alineado a la izquierda
        draw.text((x + 15, y + 12), nombre.upper(), fill=(40, 40, 40), font=font)
        
        # Contenedor de la barra de vida alineada a la derecha
        bar_x, bar_y = x + 130, y + 15
        bar_w, bar_h = 160, 12
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(80, 80, 80, 255), outline=(0,0,0), width=1)
        
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
            
        # Texto de HP debajo de la barra
        draw.text((x + 225, y + 35), f"{int(vida_actual)} / {int(vida_maxima)}", fill=(60, 60, 60), font=font)

    # 6. Dibujar los HUDs en posiciones estratégicas
    # HUD Enemigo (Arriba Izquierda)
    dibujar_hud(30, 30, nombre2, hp2, hp_max2)
    
    # HUD Aliado (Abajo Derecha)
    dibujar_hud(460, 290, nombre1, hp1, hp_max1)

    # Preparar buffer y retornar
    buffer = io.BytesIO()
    fondo.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer