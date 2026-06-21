import io
import os
import aiohttp
import logging
from PIL import Image, ImageDraw, ImageFont

# Configuración de logs para este módulo
log = logging.getLogger('imagencomb')

async def generar_escena_combate(session, poke1_id, poke2_id, nombre1, nombre2, hp1, hp2, hp_max1, hp_max2, fondo_nombre, turno_jugador=0, es_shiny1=False, es_shiny2=False):
    
    # 1. Cargar fondo
    carpeta_fondos = "fondos"
    ruta_fondo = os.path.join(carpeta_fondos, fondo_nombre)
    
    if not os.path.exists(ruta_fondo):
        log.warning(f"Fondo no encontrado: {ruta_fondo}. Usando fondo por defecto.")
        fondo = Image.new("RGBA", (800, 400), (50, 50, 50, 255))
    else:
        fondo = Image.open(ruta_fondo).convert("RGBA")
    
    fondo = fondo.resize((800, 400), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(fondo)

    async def obtener_sprite_bytes(poke_id, es_shiny, es_espalda):
            base = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"
            
            async def descargar(es_espalda_actual):
                partes = ["back"] if es_espalda_actual else []
                if es_shiny: partes.append("shiny")
                url = f"{base}/{'/'.join(partes)}/{poke_id}.png" if partes else f"{base}/{poke_id}.png"
                
                log.info(f"Descargando sprite: {url}")
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        if len(data) > 0:
                            return data
                    # Si no es 200 o está vacío, lanzamos excepción para capturarla fuera
                    raise Exception(f"HTTP {response.status}")

            try:
                # 1. Intentamos la petición original
                return await descargar(es_espalda)
            except Exception as e:
                log.warning(f"Fallo al obtener sprite (espalda={es_espalda}): {e}. Intentando fallback...")
                
                # 2. Fallback: Si falló el de espalda, intentamos el frontal
                if es_espalda:
                    try:
                        return await descargar(False)
                    except Exception as e2:
                        raise Exception(f"Fallo crítico en ambos sprites: {e2}")
                else:
                    # Si ya era frontal y falló, no hay más donde buscar
                    raise e

    # 3. Obtener imágenes con manejo de errores
    try:
        img1_bytes = await obtener_sprite_bytes(poke1_id, es_shiny1, True)
        img2_bytes = await obtener_sprite_bytes(poke2_id, es_shiny2, False)
        
        img1 = Image.open(io.BytesIO(img1_bytes)).convert("RGBA")
        img2 = Image.open(io.BytesIO(img2_bytes)).convert("RGBA")
    except Exception as e:
        log.error(f"Fallo crítico al obtener sprites: {e}", exc_info=True)
        raise e

    # 4. Preparar sprites
    def preparar_sprite(img, max_w, max_h):
        bbox = img.getbbox()
        if bbox: img = img.crop(bbox)
        escala = min(3.0, max_w / img.width, max_h / img.height)
        return img.resize((int(img.width * escala), int(img.height * escala)), Image.Resampling.NEAREST)

    img1 = preparar_sprite(img1, 200, 200)
    img2 = preparar_sprite(img2, 220, 140)

    # 5. Posicionamiento
    pos1 = (100 + (30 if turno_jugador == 1 else 0), 220 + (-20 if turno_jugador == 1 else 0))
    pos2 = (500 + (-30 if turno_jugador == 2 else 0), 60 + (20 if turno_jugador == 2 else 0))

    fondo.paste(img2, pos2, img2)
    fondo.paste(img1, pos1, img1)

    # 6. Dibujo del HUD
    font = ImageFont.load_default()
    def dibujar_hud(x, y, nombre, vida_actual, vida_maxima):
        draw.rounded_rectangle([x, y, x + 310, y + 65], radius=6, fill=(248, 248, 240, 220), outline=(60, 60, 60, 255), width=3)
        draw.text((x + 15, y + 12), nombre.upper(), fill=(40, 40, 40), font=font)
        bar_x, bar_y, bar_w = x + 130, y + 15, 160
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 12], fill=(80, 80, 80, 255), outline=(0,0,0), width=1)
        porcentaje = max(0, min(1, vida_actual / vida_maxima))
        color_hp = (46, 204, 113) if porcentaje > 0.5 else (241, 196, 15) if porcentaje > 0.2 else (231, 76, 60)
        draw.rectangle([bar_x, bar_y, bar_x + int(bar_w * porcentaje), bar_y + 12], fill=color_hp)
        draw.text((x + 225, y + 35), f"{int(vida_actual)} / {int(vida_maxima)}", fill=(60, 60, 60), font=font)

    dibujar_hud(30, 30, nombre2, hp2, hp_max2)
    dibujar_hud(460, 290, nombre1, hp1, hp_max1)

    buffer = io.BytesIO()
    fondo.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
async def generar_escena_raid(
    session,
    jugadores,
    hp_jugadores,
    alpha,
    hp_alpha,
    hp_alpha_max,
    fondo_nombre
):
    print("RAID SPRITES")

    for p in jugadores:
        print(p["nombre"], p["id"])
    return await generar_escena_combate(
        session,
        jugadores[0]["id"],
        alpha["id"],
        jugadores[0]["nombre"],
        alpha["nombre"],
        hp_jugadores[0],
        hp_alpha,
        jugadores[0]["hp_max"],
        hp_alpha_max,
        fondo_nombre
    )