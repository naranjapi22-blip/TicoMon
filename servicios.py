import io
from cachetools import TTLCache
import asyncio
from logger_config import log
from PIL import (
    Image,
    ImageFilter,
    ImageDraw,
    ImageFont
)
import aiohttp
from database import obtener_nombre_local
# 1. Creamos una caché que:
# - Guarda máximo 600 imágenes (maxsize)
# - Las mantiene solo por 1 hora (ttl=3600 segundos) para liberar espacio
_cache_imagenes = TTLCache(maxsize=600, ttl=3600)



pokemon_cache = TTLCache(
    maxsize=2000,
    ttl=86400
)
async def obtener_pokemon(session, nombre_o_id):
    try:
        cache_key = str(nombre_o_id).lower()

        if cache_key in pokemon_cache:
            log.debug(f"⚡ Cache hit: {cache_key}")
            return pokemon_cache[cache_key]

        log.debug(f"Cache miss: {cache_key}")

        url = f"https://pokeapi.co/api/v2/pokemon/{cache_key}"

        timeout = aiohttp.ClientTimeout(total=5)

        async with session.get(
            url,
            timeout=timeout
        ) as response:

            if response.status == 200:
                data = await response.json()

                species_url = data['species']['url']

                async with session.get(
                    species_url,
                    timeout=timeout
                ) as s_resp:

                    if s_resp.status == 200:
                        species = await s_resp.json()

                        rate = species.get(
                            'capture_rate',
                            45
                        )

                        log.debug(
                            f"Pokémon {data['name']} cargado. Rate: {rate}"
                        )

                        data['capture_rate'] = rate

                        pokemon_cache[cache_key] = (
                            data,
                            species
                        )

                        return data, species
                        
        return None, None

    except Exception:
        log.exception("Error al obtener datos del Pokémon")
        return None, None

# 2. Obtener nombre por ID
async def obtener_nombre_por_id(session, id_p):
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{id_p}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                nombre = data['name']
                log.debug(f"✅ Nombre obtenido para ID {id_p}: {nombre}")
                return nombre
            else:
                log.warning(f"⚠️ No se encontró nombre para ID {id_p}")
    except Exception as e:
        log.error(f"🚨 Error al obtener nombre para ID {id_p}: {e}", exc_info=True)
    return "???"

# 3. Obtener ID por nombre


# 4. Filtro de silueta (si no tienes el poke, se vuelve negro)
def aplicar_filtro_silueta(img):
    try:
        img = img.convert("RGBA")
        # Separamos los canales
        r, g, b, a = img.split()
        # Creamos una máscara negra del mismo tamaño
        silueta = Image.new("L", img.size, 0)
        # Combinamos la silueta con el canal Alpha original
        img = Image.merge("RGBA", (silueta, silueta, silueta, a))
        log.debug("✅ Filtro de silueta aplicado (modo rápido)")
        return img
    except Exception as e:
        log.error(f"🚨 Error al aplicar filtro de silueta: {e}", exc_info=True)
        return img

async def generar_collage(session, data_pokes, tenidos=None, es_shiny=False):

    if tenidos is None:
        tenidos = []

    try:

        celda_ancho = 140
        celda_alto = 150

        cols = 5
        filas = (len(data_pokes) + cols - 1) // cols

        async def obtener_y_procesar(
            id_poke,
            url
        ):

            try:

                cache_key = (
                    f"{id_poke}_shiny"
                    if es_shiny
                    else str(id_poke)
                )

                if cache_key not in _cache_imagenes:

                    async with session.get(url) as resp:

                        if resp.status == 200:

                            _cache_imagenes[
                                cache_key
                            ] = await resp.read()

                if cache_key in _cache_imagenes:

                    img = Image.open(
                        io.BytesIO(
                            _cache_imagenes[cache_key]
                        )
                    ).convert("RGBA")

                    # Sprite más grande
                    img = img.resize(
                        (105, 105),
                        Image.Resampling.NEAREST
                    )

                    if id_poke not in tenidos:
                        img = aplicar_filtro_silueta(img)

                    nombre = obtener_nombre_local(
                        id_poke
                    )

                    return (
                        img,
                        nombre.capitalize()
                    )

            except Exception:
                log.exception(f"Error procesando Pokémon {id_poke}")

            return None

        tareas = [
            obtener_y_procesar(id_poke, url)
            for id_poke, url in data_pokes
        ]

        resultados = await asyncio.gather(
            *tareas
        )

        collage = Image.new(
            "RGBA",
            (
                celda_ancho * cols,
                celda_alto * filas
            ),
            (0, 0, 0, 0)
        )

        draw = ImageDraw.Draw(collage)

        try:

            font = ImageFont.truetype(
                "fonts/DejaVuSans-Bold.ttf",
                18
            )

        except Exception:
            log.warning("No se pudo cargar la fuente, usando la predeterminada.")
            font = ImageFont.load_default()

        resultados = [
            r
            for r in resultados
            if r is not None
        ]


        for idx, (img, nombre) in enumerate(
            resultados
        ):

            x = (
                idx % cols
            ) * celda_ancho

            y = (
                idx // cols
            ) * celda_alto

            # Sprite centrado
            sprite_x = (
                x
                + (celda_ancho - 105) // 2
            )

            collage.paste(
                img,
                (sprite_x, y),
                img
            )

            text_bbox = draw.textbbox(
                (0, 0),
                nombre,
                font=font
            )

            text_width = (
                text_bbox[2]
                - text_bbox[0]
            )

            text_x = (
                x
                + (celda_ancho - text_width) // 2
            )

            text_y = y + 112

            draw.text(
                (
                    text_x,
                    text_y
                ),
                nombre,
                fill=(255, 255, 255),
                font=font,
                stroke_width=2,
                stroke_fill=(0, 0, 0)
            )

        buffer = io.BytesIO()

        collage.save(
            buffer,
            format="PNG"
        )

        buffer.seek(0)


        return buffer

    except Exception as e:

        log.error(
            f"🚨 Error al generar collage: {e}",
            exc_info=True
        )

        return None

# 6 Función para filtrar los IDs de un tipo específico que el usuario YA tiene
async def filtrar_capturas_por_tipo(session, tipo, tenidos):
    """
    Filtra los IDs de Pokémon que el usuario tiene (tenidos)
    comparándolos con los que pertenecen a un tipo específico.
    """
    try:
        log.debug(f"🔍 Filtrando capturas por tipo: {tipo}")
        
        if tipo == "all":
            return sorted(list(tenidos))
        
        url = f"https://pokeapi.co/api/v2/type/{tipo}"
        async with session.get(url) as r:
            if r.status == 200:
                data = await r.json()
                # Extraemos los IDs del tipo desde la respuesta de la API
                ids_del_tipo = {int(p['pokemon']['url'].split('/')[-2]) for p in data['pokemon']}
                # Devolvemos solo los IDs que están en la lista 'tenidos' del usuario
                resultado = sorted([id_poke for id_poke in tenidos if id_poke in ids_del_tipo])
                return resultado
            else:
                log.warning(f"⚠️ Tipo no encontrado: {tipo} (Status: {r.status})")
    except Exception as e:
        log.error(f"🚨 Error al filtrar por tipo {tipo}: {e}", exc_info=True)
    
    return []


async def generar_collage_siluetas(session, data_pokes, tenidos=None, es_shiny=False):
    """Genera el collage para el SPAWN (3 fragmentos)."""
    try:
        siluetas = []
        
        for idx, (data, _) in enumerate(data_pokes):
            try:
                # 1. Lógica de URL Shiny o Normal
                pokemon_id = data["id"]

                if es_shiny:
                    ruta_sprite = f"sprites/shiny/{pokemon_id}.png"
                else:
                    ruta_sprite = f"sprites/regular/{pokemon_id}.png"

                img = Image.open(
                    ruta_sprite
                ).convert("RGBA")

                silueta = generar_silueta_simple(img)

                siluetas.append(
                    silueta.resize(
                        (128, 128),
                        Image.Resampling.NEAREST
                    )
                )
                                                            
                                                            
                                                        
            
            except Exception as e:
                log.error(f"🚨 Error procesando silueta {idx + 1}: {e}", exc_info=True)
                
        if not siluetas:
            return None
        
        composite_width = (128 * len(siluetas)) + (10 * (len(siluetas) - 1))

        composite = Image.new(
            'RGBA',
            (composite_width, 128),
            (255, 255, 255, 0)
        )

        x_offset = 0

        for s in siluetas:
            composite.paste(
                s,
                (x_offset, 0),
                s
            )

            x_offset += 138
            
        buffer = io.BytesIO()
        composite.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    except Exception as e:
        log.error(f"🚨 Error al generar collage de siluetas: {e}", exc_info=True)
        return None


async def obtener_especie_desde_data(session, data):
    """Obtiene el JSON de la especie dado el objeto data del Pokémon."""
    try:
        species_url = data['species']['url']
        async with session.get(species_url) as resp:
            if resp.status == 200:
                return await resp.json()
    except Exception:
        log.exception("Error al obtener especie")
    return None
# Añade esto a servicios.py
def obtener_sprite_escalado(imagen_pil, factor):
    """
    Escala la imagen del Pokemon basándose en el tamano_factor guardado.
    """
    ancho, alto = imagen_pil.size
    # Escala el tamaño: base * factor
    nuevo_ancho = int(ancho * factor)
    nuevo_alto = int(alto * factor)
    
    # Redimensionamos
    return imagen_pil.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
def procesar_sprite_pokemon(imagen_base, tamano_factor, estado_record=None):
    """
    Escala el sprite y aplica un efecto de aura brillante (Glow) si es récord.
    """
    try:
        # 1. Escalado base
        escala_ajustada = tamano_factor * 0.85 
        ancho, alto = imagen_base.size
        nuevo_ancho = int(ancho * escala_ajustada)
        nuevo_alto = int(alto * escala_ajustada)
        
        sprite_escalado = imagen_base.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
        
         # 2. Aplicar Boost Visual (Efecto Resplandor Intenso)

        if estado_record:

            # Color: Oro para grande, Plata para pequeño

            color_aura = (255, 215, 0, 255) if estado_record == "grande" else (192, 192, 192, 255)

           

            # Aumentamos el margen para que el brillo tenga espacio para expandirse

            margen = 50

            ancho_aura = nuevo_ancho + (margen * 2)

            alto_aura = nuevo_alto + (margen * 2)

           

            # Creamos el lienzo del aura

            aura_layer = Image.new("RGBA", (ancho_aura, alto_aura), (0, 0, 0, 0))

           

            # 1. CREAR MÁSCARA DE RESPLANDOR (Más fuerte)

            # Dibujamos una silueta más gruesa para que el desenfoque sea mayor

            from PIL import ImageEnhance

           

            # Creamos una versión "glow" del sprite: convertimos el sprite a un color sólido

            glow = sprite_escalado.copy()

            # Convertimos a blanco para que el color brille más

            pixels = glow.load()

            for y in range(glow.size[1]):

                for x in range(glow.size[0]):

                    if pixels[x, y][3] > 0: # Si no es transparente

                        pixels[x, y] = color_aura

           

            # Aplicamos desenfoque agresivo para crear el brillo

            glow = glow.filter(ImageFilter.GaussianBlur(10))

            # Potenciamos el brillo con un enhancer

            enhancer = ImageEnhance.Brightness(glow)

            glow = enhancer.enhance(3.0) # ¡Esto hace que brille mucho más!


            # 2. COMPOSICIÓN

            # Pegamos el brillo varias veces para que sea denso

            aura_layer.paste(glow, (margen - 10, margen - 10), glow)

            aura_layer.paste(glow, (margen + 10, margen + 10), glow)

           

            # Pegamos el sprite original encima

            aura_layer.paste(sprite_escalado, (margen, margen), sprite_escalado)

           

            sprite_escalado = aura_layer

            nuevo_ancho, nuevo_alto = sprite_escalado.size 

        # 3. Lienzo transparente de 500x500 (Paso final de centrado)
        lienzo = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
        
        # 4. Centrar
        pos_x = (500 - nuevo_ancho) // 2
        pos_y = (500 - nuevo_alto) // 2
        
        lienzo.paste(sprite_escalado, (pos_x, pos_y), sprite_escalado)
        return lienzo

    except Exception as e:
        log.error(f"🚨 Error al procesar sprite con Boost Visual: {e}")
        return imagen_base
def generar_silueta_simple(imagen):
    """
    Convierte un sprite PNG transparente en una silueta negra.
    """

    _, _, _, alpha = imagen.split()

    silueta = Image.new(
        "RGBA",
        imagen.size,
        (0, 0, 0, 255)
    )

    silueta.putalpha(alpha)

    return silueta
async def generar_imagen_top(
    top_pokemones,
    tipo=None
):

    try:

        ancho = 750
        alto_fila = 95
        alto = (len(top_pokemones) * alto_fila) + 140

        imagen = Image.new(
            "RGBA",
            (ancho, alto),
            (35, 39, 42, 255)
        )

        draw = ImageDraw.Draw(imagen)

        try:

            fuente_titulo = ImageFont.truetype(
                "arial.ttf",
                40
            )

            fuente = ImageFont.truetype(
                "arial.ttf",
                28
            )

            fuente_header = ImageFont.truetype(
                "arial.ttf",
                22
            )

            fuente_iv = ImageFont.truetype(
                "arial.ttf",
                32
            )

        except Exception:

            fuente_titulo = ImageFont.load_default()
            fuente = ImageFont.load_default()
            fuente_header = ImageFont.load_default()
            fuente_iv = ImageFont.load_default()
            pass
        # =========================
        # TÍTULO
        # =========================

        titulo = "TOP 5 IVs"

        if tipo:
            titulo = f"TOP 5 IVs • {tipo.upper()}"

        draw.text(
            (20, 20),
            titulo,
            fill=(255, 215, 0),
            font=fuente_titulo
        )
        # =========================
        # CABECERAS
        # =========================

        draw.text(
            (110, 85),
            "POS",
            fill=(180, 180, 180),
            font=fuente_header
        )

        draw.text(
            (180, 85),
            "POKEMON",
            fill=(180, 180, 180),
            font=fuente_header
        )

        draw.text(
            (450, 85),
            "ID",
            fill=(180, 180, 180),
            font=fuente_header
        )

        draw.text(
            (560, 85),
            "IV",
            fill=(180, 180, 180),
            font=fuente_header
        )

        draw.line(
            [(10, 115), (740, 115)],
            fill=(80, 80, 80),
            width=2
        )

        # =========================
        # POKÉMON
        # =========================

        for i, pokemon in enumerate(top_pokemones):

            id_captura, nombre, shiny, dex_id, porcentaje = pokemon

            carpeta = (
                "shiny"
                if shiny
                else "regular"
            )

            ruta_sprite = (
                f"sprites/{carpeta}/{dex_id}.png"
            )

            y = 130 + (i * alto_fila)

            try:

                sprite = (
                    Image.open(ruta_sprite)
                    .convert("RGBA")
                    .resize(
                        (80, 80),
                        Image.Resampling.NEAREST
                    )
                )

                imagen.paste(
                    sprite,
                    (15, y),
                    sprite
                )

            except Exception:

                log.warning(
                    f"No se encontró sprite: {ruta_sprite}"
                )

            # =========================
            # TOP 3 ESPECIAL
            # =========================

            if i == 0:
                posicion = "#1"
                color_pos = (255, 215, 0)
            elif i == 1:
                posicion = "#2"
                color_pos = (192, 192, 192)
            elif i == 2:
                posicion = "#3"
                color_pos = (205, 127, 50)
            else:
                posicion = f"#{i+1}"
                color_pos = (255, 255, 255)

            # =========================
            # NOMBRE
            # =========================

            nombre_mostrar = nombre.capitalize()

            if shiny:
                nombre_mostrar += " *"

            # POSICIÓN

            draw.text(
                (110, y + 20),
                posicion,
                fill=color_pos,
                font=fuente
            )

            # NOMBRE

            draw.text(
                (180, y + 20),
                nombre_mostrar,
                fill=(255, 255, 255),
                font=fuente
            )

            # ID

            draw.text(
                (450, y + 20),
                f"[{id_captura}]",
                fill=(180, 180, 180),
                font=fuente
            )

            # COLOR IV

            if porcentaje >= 85:
                color_iv = (0, 255, 127)
            elif porcentaje >= 70:
                color_iv = (255, 215, 0)
            else:
                color_iv = (255, 255, 255)

            # IV GRANDE

            draw.text(
                (560, y + 15),
                f"{porcentaje:.1f}%",
                fill=color_iv,
                font=fuente_iv
            )

            # Separador

            draw.line(
                [
                    (90, y + 90),
                    (740, y + 90)
                ],
                fill=(55, 55, 55),
                width=1
            )

        buffer = io.BytesIO()

        imagen.save(
            buffer,
            format="PNG"
        )

        buffer.seek(0)

        return buffer

    except Exception as e:

        log.error(
            f"Error generando TOP: {e}",
            exc_info=True
        )

        return None
from urllib.request import Request, urlopen
from urllib.error import HTTPError

R2_PUBLIC_URL = "https://pub-23cb564f6c174627926c1ac0409563d4.r2.dev"

_gif_existentes = {}

def obtener_url_gif(dex_id, es_shiny=False):

    cache_key = (dex_id, es_shiny)

    if cache_key in _gif_existentes:
        return _gif_existentes[cache_key]

    if es_shiny:

        url_shiny = (
            f"{R2_PUBLIC_URL}/shiny/{dex_id}.gif?v=2"
        )

        try:

            req = Request(
                url_shiny,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            with urlopen(req):
                pass

            _gif_existentes[cache_key] = url_shiny

            return url_shiny

        except HTTPError:

            pass

    url_regular = (
        f"{R2_PUBLIC_URL}/regular/{dex_id}.gif?v=2"
    )

    _gif_existentes[cache_key] = url_regular

    return url_regular