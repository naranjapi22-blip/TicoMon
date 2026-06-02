import aiohttp
import io
from PIL import Image, ImageDraw, ImageFont
import io
import random
from PIL import Image, ImageChops, ImageDraw, ImageOps


# --- NUEVA FUNCIÓN AUXILIAR PARA LA HIERBA VERDE ---
def generar_capa_hierba(width, height):
    """Genera una capa transparente con hojas de hierba verde en la parte inferior."""
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
    
    return capa_hierba

# --- FUNCIÓN AUXILIAR PARA GENERAR HIERBA ALTA ---
def generar_mascara_hierba(width, height):
    """Genera una textura procedimental de puntas de hierba sobre fondo transparente."""
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
    
    # Devolvemos la máscara lista para usarse
    return mask


# 1. Obtener datos de un Pokémon desde PokeAPI
async def obtener_pokemon(session, nombre_o_id):
    url = f"https://pokeapi.co/api/v2/pokemon/{str(nombre_o_id).lower()}"
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            # La especie contiene información sobre si es legendario
            species_url = data['species']['url']
            async with session.get(species_url) as s_resp:
                species = await s_resp.json()
                return data, species
        return None, None

# 2. Obtener nombre por ID
async def obtener_nombre_por_id(session, id_p):
    url = f"https://pokeapi.co/api/v2/pokemon/{id_p}"
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return data['name']
    return "???"

# Definimos una sola función robusta
async def obtener_id_por_nombre(session, nombre):
    """
    Recibe la sesión y el nombre. 
    Es eficiente porque reutiliza la sesión del bot.
    """
    url = f"https://pokeapi.co/api/v2/pokemon/{nombre.lower()}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data['id']
    except Exception as e:
        print(f"Error buscando ID para {nombre}: {e}")
    return None

# 4. Filtro de silueta (si no tienes el poke, se vuelve negro)
def aplicar_filtro_silueta(img):
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = []
    for item in data:
        if item[3] > 0: # Si no es transparente, lo pintamos negro
            new_data.append((0, 0, 0, 255))
        else:
            new_data.append(item)
    img.putdata(new_data)
    return img

# 5. Generar collage con nombres y siluetas
async def generar_collage(session, data_pokes, tenidos):
    celda_ancho = 110
    celda_alto = 130 
    cols = 5
    filas = (len(data_pokes) + cols - 1) // cols
    
    collage = Image.new('RGBA', (celda_ancho * cols, celda_alto * filas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(collage)
    
    # Intentar cargar fuente (ajusta la ruta si estás en Linux)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    for idx, (id_poke, url) in enumerate(data_pokes):
        async with session.get(url) as resp:
            if resp.status == 200:
                img_data = await resp.read()
                img = Image.open(io.BytesIO(img_data)).convert('RGBA')
                img = img.resize((96, 96))
                
                # Si el usuario NO tiene el Pokémon, aplicar silueta
                if id_poke not in tenidos:
                    img = aplicar_filtro_silueta(img)
                
                x = (idx % cols) * celda_ancho
                y = (idx // cols) * celda_alto
                
                # Pegar imagen
                collage.paste(img, (x + 7, y), img)
                
                # Dibujar nombre
                nombre = await obtener_nombre_por_id(session, id_poke)
                nombre_display = nombre.capitalize()
                
                # Centrar texto
                text_bbox = draw.textbbox((0, 0), nombre_display, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = x + (celda_ancho - text_width) // 2
                
                draw.text((text_x, y + 100), nombre_display, fill="white", font=font)
            
    buffer = io.BytesIO()
    collage.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
# 6 Función para filtrar los IDs de un tipo específico que el usuario YA tiene
async def filtrar_capturas_por_tipo(session, tipo, tenidos):
    """
    Filtra los IDs de Pokémon que el usuario tiene (tenidos)
    comparándolos con los que pertenecen a un tipo específico.
    """
    if tipo == "all":
        return sorted(list(tenidos))
    
    url = f"https://pokeapi.co/api/v2/type/{tipo}"
    async with session.get(url) as r:
        if r.status == 200:
            data = await r.json()
            # Extraemos los IDs del tipo desde la respuesta de la API
            ids_del_tipo = {int(p['pokemon']['url'].split('/')[-2]) for p in data['pokemon']}
            # Devolvemos solo los IDs que están en la lista 'tenidos' del usuario
            return sorted([id_poke for id_poke in tenidos if id_poke in ids_del_tipo])
    
    return []
async def procesar_imagen_fragmento(session, url):
    """Descarga, recorta y aplica el efecto de 'Hierba Alta' a la silueta HD."""
    async with session.get(url) as r:
        if r.status != 200: return None
        data = await r.read()
        
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    
    # Recortamos el espacio vacío alrededor del Pokémon
    alpha = img.getchannel('A')
    bbox = alpha.getbbox()
    if not bbox: return None 
    
    img_conteudo = img.crop(bbox)
    width, height = img_conteudo.size
    
    # --- AJUSTE DE TAMAÑO (PUNTO DULCE) ---
    # Usamos el 60% (0.60). Es más grande para que se note la forma estructural,
    # pero no tan grande para que salga el Pokémon entero.
    crop_w = int(width * 0.60)
    crop_h = int(height * 0.60)
    
    # Buscamos una coordenada al azar para el recorte que contenga algo del Pokémon
    fragmento = None
    for _ in range(15): # Más intentos porque el recorte es más grande
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
            break
            
    if fragmento is None: return None # Fallback de seguridad

# --- APLICAR SILUETA (NEGRO) ---
    negro = Image.new('RGBA', fragmento.size, (0, 0, 0, 255))
    silueta_completa = ImageChops.composite(negro, fragmento, fragmento)
    
    # --- LA NUEVA MAGIA: PEGAR LA HIERBA VERDE ---
    # 1. Generamos la capa con los dibujos de hierba verde
    capa_verde = generar_capa_hierba(fragmento.width, fragmento.height)
    
    # 2. Pegamos la hierba verde encima de la silueta negra.
    # Usamos la misma capa_verde como máscara para que no pegue el fondo transparente.
    silueta_completa.paste(capa_verde, (0, 0), mask=capa_verde)
    
    return silueta_completa

async def generar_collage_siluetas(session, data_pokes):
    """Genera un collage horizontal con los 3 fragmentos de silueta."""
    siluetas = []
    for data, _ in data_pokes:
        # AQUÍ ESTÁ LA MAGIA: Cambiamos el sprite chiquito por el Arte Oficial gigante
        try:
            url = data['sprites']['other']['official-artwork']['front_default']
        except KeyError:
            # Si por casualidad un Pokémon no tiene arte oficial, usamos el normal de respaldo
            url = data['sprites']['front_default']
            
        fragmento = await procesar_imagen_fragmento(session, url)
        if fragmento:
            siluetas.append(fragmento.resize((150, 150), Image.Resampling.LANCZOS))
            
    if not siluetas: return None
    
    composite_width = (150 * 3) + (10 * 2) 
    composite = Image.new('RGBA', (composite_width, 150), (255, 255, 255, 0))
    
    x_offset = 0
    for s in siluetas:
        composite.paste(s, (x_offset, 0), s)
        x_offset += 160
        
    buffer = io.BytesIO()
    composite.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

async def obtener_url_arte_oficial(session, poke_id):
    """Retorna solo la URL del arte oficial para mostrarlo sin procesar."""
    url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return data['sprites']['other']['official-artwork']['front_default']
    return None
