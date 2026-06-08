import aiohttp
import io
import random
from PIL import Image, ImageChops, ImageDraw, ImageOps
from cachetools import TTLCache
import asyncio
from logger_config import log
from PIL import Image, ImageDraw, ImageFilter
import os
# 1. Creamos una caché que:
# - Guarda máximo 600 imágenes (maxsize)
# - Las mantiene solo por 1 hora (ttl=3600 segundos) para liberar espacio
_cache_imagenes = TTLCache(maxsize=600, ttl=3600)


# --- NUEVA FUNCIÓN AUXILIAR PARA LA HIERBA VERDE ---
def generar_capa_hierba(width, height):
    """Genera una capa transparente con hojas de hierba verde en la parte inferior."""
    try:
        # Creamos un lienzo totalmente transparente
        capa_hierba = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa_hierba)
        
        ancho_hoja = width // 15 # Hojas un poco más anchas
        if ancho_hoja < 5: ancho_hoja = 5
        num_hojas = (width // ancho_hoja) + 2
        
        # Tres tonos de verde para que se vea más realista y con profundidad
        colores_verde = [
            (56, 142, 60, 255),   # Verde oscuro
            (76, 175, 80, 255),   # Verde clásico de Pokémon
            (102, 187, 106, 255)  # Verde un poco más claro
        ]
        
        # Dibujamos los triángulos (hojas) de abajo hacia arriba
        for i in range(num_hojas):
            x_start = (i * ancho_hoja) - (ancho_hoja // 2)
            
            point1 = (x_start, height) # Base izquierda
            
            # Altura aleatoria del pasto (cubre entre el 30% y el 70% del recuadro)
            altura_pico = random.randint(int(height * 0.3), int(height * 0.7))
            point2 = (x_start + ancho_hoja // 2, height - altura_pico) # Pico
            
            point3 = (x_start + ancho_hoja, height) # Base derecha
            
            # Elegimos un verde al azar para esta hoja
            color_hoja = random.choice(colores_verde)
            
            # Dibujamos la hoja verde en nuestro lienzo transparente
            draw.polygon([point1, point2, point3], fill=color_hoja)
        
        log.debug(f"✅ Capa de hierba generada: {width}x{height}")
        return capa_hierba
    except Exception as e:
        log.error(f"🚨 Error al generar capa de hierba: {e}", exc_info=True)
        return None

# --- FUNCIÓN AUXILIAR PARA GENERAR HIERBA ALTA ---
def generar_mascara_hierba(width, height):
    """Genera una textura procedimental de puntas de hierba sobre fondo transparente."""
    try:
        # Creamos una imagen transparente en modo 'L' (Grayscale para máscaras)
        mask = Image.new('L', (width, height), 0) # 0 = Negro (transparente/oculto)
        draw = ImageDraw.Draw(mask)
        
        # Parámetros de la hierba
        ancho_hoja = width // 20 # Definimos el ancho de cada 'triángulo' de hierba
        if ancho_hoja < 5: ancho_hoja = 5 # Mínimo para que se note
        num_hojas = (width // ancho_hoja) + 2
        
        # Dibujamos triángulos (puntas de hierba) desde el fondo de la imagen hacia arriba
        for i in range(num_hojas):
            x_start = (i * ancho_hoja) - (ancho_hoja // 2)
            
            # Geometría del triángulo de hierba
            point1 = (x_start, height) # Base izquierda
            
            # El pico de la hierba (altura aleatoria para variedad, cubre del 40% al 80% de la altura)
            altura_pico = random.randint(int(height * 0.4), int(height * 0.8))
            point2 = (x_start + ancho_hoja // 2, height - altura_pico) # Pico
            
            point3 = (x_start + ancho_hoja, height) # Base derecha
            
            # Dibujamos el triángulo en BLANCO (255 = Opaco/Visible en la máscara)
            draw.polygon([point1, point2, point3], fill=255)
        
        # Invertimos la máscara. Queremos que la HIERBA sea transparente, 
        # y el resto (arriba de la hierba) sea opaco para mostrar al Pokémon.
        mask = ImageOps.invert(mask)
        
        log.debug(f"✅ Máscara de hierba generada: {width}x{height}")
        return mask
    except Exception as e:
        log.error(f"🚨 Error al generar máscara de hierba: {e}", exc_info=True)
        return None


# 1. Obtener datos de un Pokémon desde PokeAPI
async def obtener_pokemon(session, nombre_o_id):
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{str(nombre_o_id).lower()}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                species_url = data['species']['url']
                async with session.get(species_url) as s_resp:
                    if s_resp.status == 200:
                        species = await s_resp.json()
                        
                        # --- AQUÍ ESTÁ EL DATO CRÍTICO ---
                        # capture_rate viene en el objeto species de la PokeAPI
                        rate = species.get('capture_rate', 45) # 45 es el estándar para raros
                        
                        log.info(f"✅ Pokémon {data['name']} cargado. Rate: {rate}")
                        # Devolvemos el rate dentro del diccionario de datos
                        data['capture_rate'] = rate 
                        return data, species
        return None, None
    except Exception as e:
        log.error(f"🚨 Error al obtener datos: {e}")
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
async def obtener_id_por_nombre(session, nombre):
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{nombre.lower()}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                id_poke = data['id']
                log.debug(f"✅ ID obtenido para {nombre}: {id_poke}")
                return id_poke
            else:
                log.warning(f"⚠️ No se encontró ID para {nombre}")
    except Exception as e:
        log.error(f"🚨 Error al obtener ID para {nombre}: {e}", exc_info=True)
    return None

# 4. Filtro de silueta (si no tienes el poke, se vuelve negro)
def aplicar_filtro_silueta(img):
    try:
        img = img.convert("RGBA")
        data = img.getdata()
        new_data = []
        for item in data:
            if item[3] > 0: # Si no es transparente, lo pintamos negro
                new_data.append((0, 0, 0, 255))
            else:
                new_data.append(item)
        img.putdata(new_data)
        log.debug(f"✅ Filtro de silueta aplicado")
        return img
    except Exception as e:
        log.error(f"🚨 Error al aplicar filtro de silueta: {e}", exc_info=True)
        return img

# 1. Definimos una caché global simple fuera de la función
_cache_imagenes = {}

async def generar_collage(session, data_pokes, tenidos):
    try:
        log.info(f"🎨 Generando collage para {len(data_pokes)} pokémon")
        celda_ancho = 110
        celda_alto = 130 
        cols = 5
        filas = (len(data_pokes) + cols - 1) // cols
        
        # Función interna para procesar una sola celda (con caché)
        async def obtener_y_procesar(id_poke, url):
            try:
                # Si no está en caché, descargamos
                if id_poke not in _cache_imagenes:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            _cache_imagenes[id_poke] = await resp.read()
                            log.debug(f"📥 Imagen descargada y cacheada: ID {id_poke}")
                
                # Si logramos tener los bytes (ya sea desde caché o recién descargado)
                if id_poke in _cache_imagenes:
                    img = Image.open(io.BytesIO(_cache_imagenes[id_poke])).convert('RGBA')
                    img = img.resize((96, 96))
                    if id_poke not in tenidos:
                        img = aplicar_filtro_silueta(img)
                    
                    nombre = await obtener_nombre_por_id(session, id_poke)
                    return img, nombre.capitalize()
            except Exception as e:
                log.error(f"🚨 Error procesando pokémon {id_poke}: {e}", exc_info=True)
            return None

        # 2. Ejecutar todas las tareas en paralelo
        tareas = [obtener_y_procesar(id_poke, url) for id_poke, url in data_pokes]
        resultados = await asyncio.gather(*tareas)
        
        # 3. Dibujar el collage final
        collage = Image.new('RGBA', (celda_ancho * cols, celda_alto * filas), (0, 0, 0, 0))
        draw = ImageDraw.Draw(collage)
        
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()

        # Filtramos nulos por si alguna descarga falló
        resultados = [r for r in resultados if r is not None]
        log.info(f"✅ {len(resultados)}/{len(data_pokes)} pokémon procesados exitosamente")

        for idx, (img, nombre) in enumerate(resultados):
            x = (idx % cols) * celda_ancho
            y = (idx // cols) * celda_alto
            
            collage.paste(img, (x + 7, y), img)
            
            text_bbox = draw.textbbox((0, 0), nombre, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text((x + (celda_ancho - text_width) // 2, y + 100), nombre, fill="white", font=font)
                
        buffer = io.BytesIO()
        collage.save(buffer, format="PNG")
        buffer.seek(0)
        log.info(f"✅ Collage generado exitosamente: {celda_ancho * cols}x{celda_alto * filas}")
        return buffer
    except Exception as e:
        log.error(f"🚨 Error al generar collage: {e}", exc_info=True)
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
            log.info(f"✅ Mostrando todas las capturas: {len(tenidos)} pokémon")
            return sorted(list(tenidos))
        
        url = f"https://pokeapi.co/api/v2/type/{tipo}"
        async with session.get(url) as r:
            if r.status == 200:
                data = await r.json()
                # Extraemos los IDs del tipo desde la respuesta de la API
                ids_del_tipo = {int(p['pokemon']['url'].split('/')[-2]) for p in data['pokemon']}
                # Devolvemos solo los IDs que están en la lista 'tenidos' del usuario
                resultado = sorted([id_poke for id_poke in tenidos if id_poke in ids_del_tipo])
                log.info(f"✅ Filtro completado: {len(resultado)} pokémon de tipo {tipo}")
                return resultado
            else:
                log.warning(f"⚠️ Tipo no encontrado: {tipo} (Status: {r.status})")
    except Exception as e:
        log.error(f"🚨 Error al filtrar por tipo {tipo}: {e}", exc_info=True)
    
    return []

async def procesar_imagen_fragmento(session, url):
    """Descarga, recorta y aplica el efecto de 'Hierba Alta' a la silueta HD."""
    try:
        log.debug(f"📥 Procesando fragmento de imagen: {url}")
        
        async with session.get(url) as r:
            if r.status != 200:
                log.warning(f"⚠️ Error descargando imagen: {url} (Status: {r.status})")
                return None
            data = await r.read()
            
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        log.debug(f"✅ Imagen descargada: {img.size}")
        
        # Recortamos el espacio vacío alrededor del Pokémon
        alpha = img.getchannel('A')
        bbox = alpha.getbbox()
        if not bbox:
            log.warning(f"⚠️ No se encontró contenido en imagen: {url}")
            return None 
        
        img_conteudo = img.crop(bbox)
        width, height = img_conteudo.size
        log.debug(f"✅ Contenido extraído: {width}x{height}")
        
        # --- AJUSTE DE TAMAÑO (PUNTO DULCE) ---
        # Usamos el 60% (0.60). Es más grande para que se note la forma estructural,
        # pero no tan grande para que salga el Pokémon entero.
        crop_w = int(width * 0.60)
        crop_h = int(height * 0.60)
        
        # Buscamos una coordenada al azar para el recorte que contenga algo del Pokémon
        fragmento = None
        for intento in range(15): # Más intentos porque el recorte es más grande
            x = random.randint(0, width - crop_w)
            # Preferimos recortes de la mitad superior para el efecto de hierba
            y = random.randint(0, int((height - crop_h) * 0.7)) 
            
            fragmento = img_conteudo.crop((x, y, x + crop_w, y + crop_h))
            
            # Verificamos que el recorte tenga contenido significativo
            alpha_frag = fragmento.getchannel('A')
            # getcolors devuelve None si hay más colores, o una lista si es uniforme.
            # Si la mayoría de píxeles son transparentes, getcolors[(0, ...)] tendrá un conteo alto.
            total_píxeles = crop_w * crop_h
            transparentes = alpha_frag.getcolors(total_píxeles)
            
            # Si no hay píxeles transparentes o menos del 90% lo son, aceptamos el recorte.
            if not transparentes or (transparentes[0][1] == 0 and (transparentes[0][0] < total_píxeles * 0.90)):
                log.debug(f"✅ Fragmento válido encontrado en intento {intento + 1}")
                break
                
        if fragmento is None:
            log.warning(f"⚠️ No se pudo encontrar fragmento válido después de 15 intentos")
            return None

        # --- APLICAR SILUETA (NEGRO) ---
        negro = Image.new('RGBA', fragmento.size, (0, 0, 0, 255))
        silueta_completa = ImageChops.composite(negro, fragmento, fragmento)
        
        # --- LA NUEVA MAGIA: PEGAR LA HIERBA VERDE ---
        # 1. Generamos la capa con los dibujos de hierba verde
        capa_verde = generar_capa_hierba(fragmento.width, fragmento.height)
        
        # 2. Pegamos la hierba verde encima de la silueta negra.
        # Usamos la misma capa_verde como máscara para que no pegue el fondo transparente.
        if capa_verde:
            silueta_completa.paste(capa_verde, (0, 0), mask=capa_verde)
        
        log.info(f"✅ Fragmento procesado exitosamente: {silueta_completa.size}")
        return silueta_completa
    except Exception as e:
        log.error(f"🚨 Error procesando fragmento de imagen: {e}", exc_info=True)
        return None

async def generar_collage_siluetas(session, data_pokes):
    """Genera un collage horizontal con los 3 fragmentos de silueta."""
    try:
        log.info(f"🎨 Generando collage de siluetas para {len(data_pokes)} pokémon")
        siluetas = []
        for idx, (data, _) in enumerate(data_pokes):
            try:
                # AQUÍ ESTÁ LA MAGIA: Cambiamos el sprite chiquito por el Arte Oficial gigante
                try:
                    url = data['sprites']['other']['official-artwork']['front_default']
                except KeyError:
                    # Si por casualidad un Pokémon no tiene arte oficial, usamos el normal de respaldo
                    url = data['sprites']['front_default']
                    log.debug(f"⚠️ Usando sprite de respaldo para pokémon {idx + 1}")
                    
                fragmento = await procesar_imagen_fragmento(session, url)
                if fragmento:
                    siluetas.append(fragmento.resize((150, 150), Image.Resampling.LANCZOS))
                    log.debug(f"✅ Silueta {idx + 1} procesada")
            except Exception as e:
                log.error(f"🚨 Error procesando silueta {idx + 1}: {e}", exc_info=True)
                
        if not siluetas:
            log.error(f"❌ No se pudo procesar ninguna silueta")
            return None
        
        log.info(f"✅ {len(siluetas)} siluetas procesadas")
        
        composite_width = (150 * 3) + (10 * 2) 
        composite = Image.new('RGBA', (composite_width, 150), (255, 255, 255, 0))
        
        x_offset = 0
        for s in siluetas:
            composite.paste(s, (x_offset, 0), s)
            x_offset += 160
            
        buffer = io.BytesIO()
        composite.save(buffer, format='PNG')
        buffer.seek(0)
        log.info(f"✅ Collage de siluetas generado: {composite_width}x150")
        return buffer
    except Exception as e:
        log.error(f"🚨 Error al generar collage de siluetas: {e}", exc_info=True)
        return None

async def obtener_url_arte_oficial(session, poke_id):
    """Retorna solo la URL del arte oficial para mostrarlo sin procesar."""
    try:
        log.debug(f"🔍 Obteniendo URL de arte oficial para pokémon: {poke_id}")
        url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                url_arte = data['sprites']['other']['official-artwork']['front_default']
                log.info(f"✅ URL de arte oficial obtenida para pokémon {poke_id}")
                return url_arte
            else:
                log.warning(f"⚠️ Pokémon no encontrado: {poke_id}")
    except Exception as e:
        log.error(f"🚨 Error al obtener URL de arte: {e}", exc_info=True)
    return None
async def obtener_especie_desde_data(session, data):
    """Obtiene el JSON de la especie dado el objeto data del Pokémon."""
    try:
        species_url = data['species']['url']
        async with session.get(species_url) as resp:
            if resp.status == 200:
                return await resp.json()
    except Exception as e:
        log.error(f"🚨 Error al obtener especie: {e}")
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