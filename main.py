import os
import random
import asyncio
import asyncpg
import datetime
import discord
import aiohttp
import psycopg2
from discord.ext import commands
from dotenv import load_dotenv

# Módulos locales y de proyecto
import database
import servicios
import admin
import configuracion
import logger_config
import cache_service
import gestor_spawn
import setup_cache
import perfil
import intercambio

# Configuración específica
from configuracion import canal_restringido
from logger_config import log
from cache_service import db_cache
from setup_cache import prellenar_cache

# Vistas e interfaces
from vistas import PokedexView, BotonCaptura, InfoView, SpawnSelectionView
from vistas_combate import SelectorPaginado, VistaCombate
from vistas_batalla import SelectorBatalla
from vistas_equipo import abrir_equipo_en_privado

database.init_db()
# 1. CONFIGURACIÓN
load_dotenv()
TOKEN = os.getenv('TOKEN')
intents = discord.Intents.default()
intents.message_content = True
async def cargar_extensiones():
    # Agrega 'newpokedex' a tu lista principal. 
    # Si newpokedex.py está en la carpeta principal, no uses 'cogs.'
    extensiones = ['ivs_commands', 'inventario', 'equipo_slash', 'newpokedex']
    
    for ext in extensiones:
        try:
            await bot.load_extension(ext)
            log.info(f"✅ Extensión {ext} cargada correctamente.")
        except Exception as e:
            log.error(f"❌ Error al cargar {ext}: {e}")

async def setup_hook():
    # Simplemente llama a la función unificada
    await cargar_extensiones()

# 2. Reemplaza la línea que da error por esta (asegúrate de incluir tu prefijo real)
# Si tu bot usaba un prefijo como "!" o algo distinto, ponlo ahí:
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'), 
    intents=intents,
    case_insensitive=True,
    setup_hook=setup_hook
)


bot.setup_hook = cargar_extensiones
REGIONES = {
    "1": (1, 151), "2": (152, 251), "3": (252, 386),
    "4": (387, 493), "5": (494, 649), "6": (650, 721),
    "7": (722, 809), "8": (810, 905), "9": (906, 1025)
}

# 1. Tu función de conexión limpia y eficiente
def get_connection():
    """
    Establece conexión a la base de datos PostgreSQL.
    Requiere que la variable de entorno DATABASE_URL esté definida.
    """
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        # Esto lanzará un error descriptivo si el bot no tiene la URL configurada
        raise EnvironmentError("❌ La variable de entorno 'DATABASE_URL' no está definida.")
    return psycopg2.connect(db_url)

@bot.event
async def on_ready():
    # 0. Inicialización del Pool de conexiones de base de datos
    try:
        db_url = os.environ.get('DATABASE_URL')
        bot.db_pool = await asyncpg.create_pool(
            dsn=db_url,
            min_size=5,
            max_size=20
        )
        print("✅ Pool de base de datos inicializado correctamente.")
    except Exception as e:
        print(f"🚨 Error crítico al inicializar el pool de BD: {e}")

    configuracion.init_config_db()
    print(f'Bot conectado como {bot.user}')
    
    # 0. Inicializar sesión de red
    bot.session = aiohttp.ClientSession()
    
    # 1. SETUP DE GESTORES
    gestor_spawn.setup_gestor(bot)
    gestor_spawn.aplicar_filtro_spawn(bot)
    gestor_spawn.canales_ocupados.clear()

    try:
        synced = await bot.tree.sync()
        log.info(f"✅ {len(synced)} slash command(s) sincronizados.")
    except Exception as e:
        log.error(f"🚨 Error al sincronizar slash commands: {e}", exc_info=True)

    print("Base de datos, módulos y sesión de red verificados.")
    
    # Esto creará la tabla automáticamente si no existe al encender el bot
    await db_cache.inicializar_bd()
    
    # Verificamos si la tabla está vacía
    ids = await db_cache.obtener_ids_por_filtro()
    if not ids:
        print("⚠️ Tabla detectada pero vacía. Iniciando carga masiva...")
        await prellenar_cache() 
        print("✅ ¡Carga masiva completada!")
# 2. Tu evento de encendido con la inicialización correcta

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        return
    print(f"Error inesperado: {error}")

@bot.command()
@canal_restringido()
async def pokedex(ctx, *, filtro: str = None):
    """
    Uso: 
    !pokedex -> Muestra tu colección completa.
    !pokedex shiny -> Muestra tu colección de shinys.
    !pokedex legendarios -> Muestra tus Pokémon legendarios.
    !pokedex [1-9] -> Muestra la pokedex regional.
    !pokedex [tipo] -> Filtra tu colección por tipo.
    """
    if not hasattr(bot, 'session') or bot.session.closed:
        bot.session = aiohttp.ClientSession()

    # 1. Obtener la lista base de capturas del usuario
    es_shiny_mode = (filtro == "shiny")
    nombres_tenidos = database.obtener_capturas(ctx.author.id, solo_shiny=es_shiny_mode)
    
    ids_tenidos = set()
    for nombre in nombres_tenidos:
        id_p = await servicios.obtener_id_por_nombre(bot.session, nombre)
        if id_p: ids_tenidos.add(id_p)

    # 2. Determinar el contexto del filtro
    inicio, fin = 1, 1025
    region_label = "Colección"
    es_coleccion_personal = True

    if filtro:
        # Filtro de Regiones
        if filtro.isdigit() and filtro in REGIONES:
            inicio, fin = REGIONES[filtro]
            region_label = f"Región {filtro}"
            es_coleccion_personal = False
        
# Filtro de Legendarios y Míticos
        elif filtro.lower() == "legendarios":
            ids_filtrados = []
            for id_p in ids_tenidos:
                resultado = await servicios.obtener_pokemon(bot.session, id_p)
                # Extraemos 'data' y 'species' correctamente
                data, species = resultado if isinstance(resultado, tuple) else (resultado, None)
                
                # Si no obtuvimos species directamente, lo buscamos en el diccionario
                if not species and isinstance(data, dict):
                    # Asumimos que la lógica para obtener species ya ocurrió en servicios.obtener_pokemon
                    pass 

                # --- AQUÍ ESTÁ LA CORRECCIÓN ---
                # Ahora preguntamos por ambos: si es legendario O si es mítico
                es_legendario = species.get('is_legendary', False) if species else False
                es_mitico = species.get('is_mythical', False) if species else False
                
                if es_legendario or es_mitico:
                    ids_filtrados.append(id_p)
            
            if ids_filtrados:
                ids_tenidos = set(ids_filtrados)
                region_label = "Legendarios y Míticos"
            else:
                return await ctx.send("No tienes ningún Pokémon Legendario o Mítico registrado.")
        
        # Filtro de Tipos (solo si no es modo shiny ni es una región)
        elif not es_shiny_mode:
            ids_filtrados = await servicios.filtrar_capturas_por_tipo(bot.session, filtro, ids_tenidos)
            if ids_filtrados:
                ids_tenidos = set(ids_filtrados)
                region_label = f"Tipo {filtro.capitalize()}"
            else:
                return await ctx.send(f"No tienes Pokémon de tipo **{filtro.capitalize()}**.")

    # 3. Lanzar la vista
    view = PokedexView(
        region=region_label,
        inicio=inicio,
        fin=fin,
        tenidos=ids_tenidos,
        es_coleccion_personal=es_coleccion_personal,
        modo_shiny=es_shiny_mode
    )
    
    await view.generar_vista_pokedex(ctx, bot.session)



def generar_pista(data, species, pistas_usadas):
    pistas = []
    
    # Pista 1: Por tipo principal
    if data.get('types'):
        tipo_principal = data['types'][0]['type']['name'].capitalize()
        pistas.append(f"Se percibe una fuerte energía de tipo **{tipo_principal}**...")
    
    # Pista 2: Por región de origen
    gen = species.get('generation', {}).get('name', '')
    regiones = {
        'generation-i': 'Kanto', 'generation-ii': 'Johto', 'generation-iii': 'Hoenn',
        'generation-iv': 'Sinnoh', 'generation-v': 'Unova/Teselia', 'generation-vi': 'Kalos',
        'generation-vii': 'Alola', 'generation-viii': 'Galar', 'generation-ix': 'Paldea'
    }
    if gen in regiones:
        pistas.append(f"Los registros indican que es originario de **{regiones[gen]}**.")
        
    # Pista 3: Por características físicas
    peso_kg = data.get('weight', 0) / 10
    if peso_kg > 100:
        pistas.append("Debe ser enorme, se nota que es una criatura **muy pesada**.")
    elif peso_kg > 0 and peso_kg < 5:
        pistas.append("Es tan escurridizo que parece ser **muy ligero y pequeño**.")
    
    # --- EL FILTRO ANTI-REPETICIÓN CORREGIDO ---
    # Python solo entiende "for", no "para" 😅
    pistas_disponibles = [p for p in pistas if p not in pistas_usadas]
    
    if pistas_disponibles:
        return random.choice(pistas_disponibles)
    elif pistas:
        return random.choice(pistas)
    else:
        return "Una criatura sumamente misteriosa..."
# NOTA: Agrega este método auxiliar en tu clase o como función fuera:
async def auto_liberar_canal(channel_id, segundos):

    await asyncio.sleep(segundos)
    if channel_id in gestor_spawn.canales_ocupados:
        gestor_spawn.canales_ocupados.discard(channel_id)
        gestor_spawn.vistas_activas.pop(channel_id, None)
        print(f"🧹 [LIMPIEZA FORZADA] Canal {channel_id} liberado por seguridad.")



# --- COMANDO SPAWN CORREGIDO ---
@bot.command()
@canal_restringido()
@commands.cooldown(1, 10, commands.BucketType.user)
async def spawn(ctx):

    
    # 1. Filtros básicos de inicial y energía
    if not gestor_spawn.verificar_inicial(ctx.author.id):
        return await ctx.send("¡Bienvenido! Antes de tu aventura, elige tu Pokémon inicial con `!inicial`.")
    
    datos_intentos = await gestor_spawn.obtener_intentos(ctx.author.id)
    intentos, ultima_recarga = datos_intentos
    
    if intentos <= 0:
        return await ctx.send("❌ Has agotado tus intentos. Tus inciensos se recargan en 2 horas.")

    # 2. Descontamos energía inmediatamente (se revertirá si el proceso falla)
    await database.actualizar_energia_db(ctx.author.id, intentos - 1, ultima_recarga)

    try:
        # --- GENERACIÓN HÍBRIDA: RANGOS PONDERADOS + FILTRO DE RAREZA ---
        # 1. Pesos: 75% Comunes, 20% Raros, 5% Legendarios
        opciones_rangos = [(1, 493), (494, 809), (810, 1025)]
        pesos_rangos = [75, 20, 5] 

        ids_spawn = []
        data_pokes = [] # Inicializamos aquí
        intentos_generacion = 0
        
        while len(ids_spawn) < 3 and intentos_generacion < 50:
            intentos_generacion += 1
            
            rango = random.choices(opciones_rangos, weights=pesos_rangos, k=1)[0]
            id_cand = random.randint(rango[0], rango[1])
            
            # Solo descargamos si no hemos procesado este ID
            if id_cand not in ids_spawn:
                data, species = await servicios.obtener_pokemon(bot.session, id_cand)
                capture_rate = data.get('capture_rate', 100)
                
                # Filtro de rareza
                prob_spawn = min(1.0, capture_rate / 150) 
                if random.random() > prob_spawn:
                    continue 
                es_shiny = (random.randint(1, 50) == 1)
                # es_shiny = random.random() < (1 / 250)
                ids_spawn.append(id_cand)
                data_pokes.append((data, species, es_shiny))

        # Si quedaron menos de 3, rellenamos sin filtro para asegurar 3 opciones
        while len(data_pokes) < 3:
            id_cand = random.randint(1, 493)
            # Evitar repetidos en el relleno
            if id_cand not in ids_spawn:
                data, species = await servicios.obtener_pokemon(bot.session, id_cand)
                es_shiny = random.random() < (1 / 250)
                ids_spawn.append(id_cand)
                data_pokes.append((data, species, es_shiny))
        
        # Extraemos solo los datos que el collage necesita (data y species)
        datos_para_collage = [(d, s) for d, s, sh in data_pokes]

        # Pasamos la lista limpia al generador
        buffer_siluetas = await servicios.generar_collage_siluetas(bot.session, datos_para_collage)
        
        if not buffer_siluetas:
            # Revertimos energía si el collage falla
            await database.actualizar_energia_db(ctx.author.id, intentos, ultima_recarga)
            return await ctx.send("Hubo un problema al generar las siluetas.")

        imagen_final = discord.File(buffer_siluetas, filename="fragmentos.png")
        
        # Generación de pistas
        texto_pistas = ""
        pistas_usadas = []
        
        # CAMBIA ESTA LÍNEA DE AQUÍ ABAJO:
        # De: for i, (data, species) in enumerate(data_pokes):
        # A ESTO:
        for i, (data, species, es_shiny) in enumerate(data_pokes): 
            
            pista_texto = generar_pista(data, species, pistas_usadas) 
            pistas_usadas.append(pista_texto) 
            texto_pistas += f"**Opción [{i+1}]:** 🔎 {pista_texto}\n\n"

        embed = discord.Embed(
            title="❓ ¡Tres fragmentos misteriosos han aparecido!",
            description=f"Observa las siluetas y lee las pistas...\n\n{texto_pistas}**¿A cuál vas a intentar atrapar?**",
            color=discord.Color.dark_grey()
        )
        embed.set_image(url="attachment://fragmentos.png")       
        
        view = SpawnSelectionView(data_pokes, ctx.author)
        
        try:
            mensaje_enviado = await ctx.send(embed=embed, file=imagen_final, view=view)
            
            # Vinculación de vista y bloqueo de canal
            view.message = mensaje_enviado
            gestor_spawn.vistas_activas[ctx.channel.id] = view 
            gestor_spawn.canales_ocupados.add(ctx.channel.id)
            
            # Tarea de fondo para liberar el canal tras 305 segundos
            asyncio.create_task(auto_liberar_canal(ctx.channel.id, 305))

        except Exception as e:
            # Limpieza en caso de fallo al enviar mensaje
            gestor_spawn.canales_ocupados.discard(ctx.channel.id)
            gestor_spawn.vistas_activas.pop(ctx.channel.id, None)
            await database.actualizar_energia_db(ctx.author.id, intentos, ultima_recarga)
            log.error(f"Error al enviar mensaje en spawn: {e}", exc_info=True)
            await ctx.send("¡Se escaparon! Hubo un error al intentar enviar el encuentro.")

    except Exception as e:
        # Limpieza global si algo falla en la lógica de generación
        gestor_spawn.canales_ocupados.discard(ctx.channel.id)
        gestor_spawn.vistas_activas.pop(ctx.channel.id, None)
        await database.actualizar_energia_db(ctx.author.id, intentos, ultima_recarga)
        log.error(f"Error crítico en generación de spawn para {ctx.author.id}: {e}", exc_info=True)
        await ctx.send("¡Se escaparon! Hubo un error al intentar generar el encuentro.")
@bot.command()
@canal_restringido()
async def info(ctx, *, nombre: str):
    nombre = nombre.lower().strip()
    versiones = database.obtener_versiones_pokemon(ctx.author.id, nombre)
    
    if not versiones:
        return await ctx.send(f"❌ No tienes a **{nombre.capitalize()}**.")

    data, _ = await servicios.obtener_pokemon(bot.session, nombre)
    mostrar_shiny = (1 in versiones)
    
    view = InfoView(ctx.author.id, data, versiones, mostrar_shiny)
    await view.enviar_embed(ctx)

perfil.iniciar_modulo_perfil(bot)

intercambio.iniciar_modulo_intercambio(bot)
@bot.event
async def on_command_error(ctx, error):
    # Esto silencia el error cuando un check falla
    if isinstance(error, commands.CheckFailure):
        return  # No hacemos nada, el usuario ya recibió el mensaje en el canal
    raise error
@bot.command(name="unlock")
@canal_restringido()
@commands.has_permissions(administrator=True)
async def unlock(ctx):

    gestor_spawn.canales_ocupados.clear() # Vacía el set por completo
    await ctx.send("✅ Todos los canales han sido desbloqueados manualmente.")

@bot.command(name="cooldowns")
@canal_restringido()
async def cooldowns(ctx):


    log.info(f"🔍 [Comando] El usuario {ctx.author.id} solicitó !cooldowns")

    try:
        # Obtenemos los datos
        intentos, ultima_recarga_raw = await gestor_spawn.obtener_intentos(ctx.author.id)
        
        # Lógica de tiempo (normalizada a UTC)
        ahora = datetime.datetime.now(datetime.timezone.utc)
        
        # Conversión segura
        if isinstance(ultima_recarga_raw, str):
            ultima_recarga = datetime.datetime.fromisoformat(ultima_recarga_raw)
        else:
            ultima_recarga = ultima_recarga_raw

        if ultima_recarga.tzinfo is None:
            ultima_recarga = ultima_recarga.replace(tzinfo=datetime.timezone.utc)
            
        tiempo_transcurrido = (ahora - ultima_recarga).total_seconds()
        tiempo_restante = max(0, 7200 - tiempo_transcurrido)
        
        minutos = int(tiempo_restante // 60)
        segundos = int(tiempo_restante % 60)
        
        embed = discord.Embed(
            title="🔋 Estado de tus Inciensos",
            color=discord.Color.blue()
        )
        embed.add_field(name="Intentos disponibles", value=f"**{intentos}/12**", inline=True)
        embed.add_field(name="Reseteo en", value=f"**{minutos}m {segundos}s**", inline=True)
        
        await ctx.send(embed=embed)
        log.info(f"✅ [Comando] Respuesta de !cooldowns enviada correctamente al usuario {ctx.author.id}")

    except Exception as e:
        # Esto capturará si hubo un error en la base de datos o en el cálculo
        log.error(f"🚨 [ERROR Comando] !cooldowns falló para el usuario {ctx.author.id}. Error: {e}", exc_info=True)
        await ctx.send("❌ Hubo un error al consultar tus datos. Por favor, intenta de nuevo más tarde.")
@bot.command(name="comandos")
@canal_restringido()
async def comandos(ctx):
    """Muestra la lista de comandos disponibles."""
    embed = discord.Embed(title="📜 Guía de Comandos", color=discord.Color.blue())
    embed.add_field(name="!spawn", value="Inicia un encuentro salvaje.", inline=False)
    embed.add_field(name="!pokedex", value="Muestra tu colección de Pokémon.", inline=False)
    embed.add_field(name="!perfil", value="Muestra tu tarjeta de entrenador.", inline=False)
    embed.add_field(name="!trade @usuario", value="Inicia un intercambio.", inline=False)
    embed.add_field(name="!cooldowns", value="Revisa tu energía de captura.", inline=False)
    embed.add_field(name="!info pokemon", value="Te da información del pokemon que tengas", inline=False)
    embed.add_field(name="!destacar", value="Pones tu pokemon en tu perfil(poner shiny si lo tienes)", inline=False)
    embed.add_field(name="!equipo", value="Gestiona tu equipo de hasta 9 Pokémon.", inline=False)
    embed.add_field(name="!combate @usuario", value="Duelo (selector clásico).", inline=False)
    embed.add_field(name="!batalla @usuario", value="Duelo con tu equipo guardado (selector privado).", inline=False)

    await ctx.send(embed=embed)
@bot.command(name="resetintentos")
@canal_restringido()
@commands.has_permissions(administrator=True)
async def resetintentos(ctx, usuario: discord.Member):
    """Resetea los intentos de un usuario a 12 (Admin)."""

    
    # Reseteamos a 12 intentos y la hora actual
    await database.actualizar_energia_db(usuario.id, 12, datetime.datetime.now())
    
    await ctx.send(f"✅ Se han reseteado los intentos de {usuario.display_name} a 12.")
# Comando para establecer el canal (solo administradores)
@bot.command(name="setcanal")
@commands.has_permissions(administrator=True)
async def setcanal(ctx, canal: discord.TextChannel):
    configuracion.set_canal(ctx.guild.id, canal.id)
    await ctx.send(f"✅ Los comandos ahora solo se permiten en {canal.mention}")

# Check global para los comandos
@bot.check
async def verificar_canal(ctx):
    # Si es mensaje privado, permitir siempre
    if ctx.guild is None:
        return True
        
    # Si es administrador, permitir siempre
    if ctx.author.guild_permissions.administrator:
        return True
    
    # Obtener el canal configurado
    canal_permitido = configuracion.obtener_canal(ctx.guild.id)
    
    # Si no hay canal configurado, se permite en todos
    if canal_permitido is None:
        return True
        
    # Si hay canal configurado, validar
    return ctx.channel.id == canal_permitido

# 1. Añade esta función para verificar la rareza
async def es_legendario(session, poke_id):
    url = f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}/"
    async with session.get(url) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get('is_legendary', False) or data.get('is_mythical', False)
    return False

admin.setup(bot)


async def _validar_retador(ctx, oponente: discord.Member) -> bool:
    if oponente.bot:
        await ctx.send("❌ No puedes retar a un bot.")
        return False
    if oponente.id == ctx.author.id:
        await ctx.send("❌ ¡No puedes pelear contra ti mismo!")
        return False
    return True


async def _obtener_equipos_duelo(
    ctx,
    oponente: discord.Member,
    crear_selector,
    *,
    privado=False,
    fuente_lista=database.obtener_lista_capturas,
    mensaje_minimo="❌ Ambos jugadores necesitan al menos 3 Pokémon capturados.",
    resolver_seleccion=None,
):
    lista1 = fuente_lista(ctx.author.id)
    lista2 = fuente_lista(oponente.id)

    def _conteo(datos):
        if isinstance(datos, dict):
            return len(datos.get("valores", []))
        return len(datos)

    if _conteo(lista1) < 3 or _conteo(lista2) < 3:
        await ctx.send(mensaje_minimo)
        return None, None

    if not hasattr(bot, "session") or bot.session.closed:
        bot.session = aiohttp.ClientSession()

    async def elegir_equipo(jugador, lista):
        if privado:
            # privado=True: elegir_equipo_en_privado retorna directamente la lista
            return await vistas_batalla.elegir_equipo_en_privado(
                ctx, jugador, lista, crear_selector
            )
        
        # privado=False: usar el flujo normal con view.wait()
        view = crear_selector(jugador, lista)
        if isinstance(view, SelectorBatalla):
            embed = await view.crear_embed()
            msg = await ctx.send(
                f"⚔️ {jugador.mention}, elige tus 3 Pokémon:",
                embed=embed,
                view=view,
            )
        else:
            msg = await ctx.send(f"⚔️ {jugador.mention}, elige tus 3 Pokémon:", view=view)
        view.message = msg
        await view.wait()
        try:
            await msg.delete()
        except discord.HTTPException:
            pass
        seleccion = view.seleccionados
        if resolver_seleccion:
            return resolver_seleccion(jugador, seleccion)
        return seleccion

    equipo1 = await elegir_equipo(ctx.author, lista1)
    if len(equipo1) < 3:
        await ctx.send(f"❌ {ctx.author.mention} no completó la selección.")
        return None, None

    equipo2 = await elegir_equipo(oponente, lista2)
    if len(equipo2) < 3:
        await ctx.send(f"❌ {oponente.mention} no completó la selección.")
        return None, None

    return equipo1, equipo2


async def _iniciar_arena(ctx, oponente: discord.Member, equipo1, equipo2):
    msg_espera = await ctx.send("⏳ Preparando arena de combate...")
    vista_combate = VistaCombate(ctx.author, oponente, equipo1, equipo2, bot.session)
    try:
        await vista_combate.preparar_combate()
        await msg_espera.edit(content="✅ ¡Todo listo! Pulsa el botón para comenzar.", view=vista_combate)
    except Exception as e:
        await msg_espera.delete()
        await ctx.send(f"❌ Error al preparar el combate: {e}")


@bot.command(name="combate")
async def iniciar_combate(ctx, oponente: discord.Member):
    """Selección clásica (compatibilidad)."""
    if not await _validar_retador(ctx, oponente):
        return

    equipos = await _obtener_equipos_duelo(
        ctx,
        oponente,
        lambda jugador, lista: SelectorPaginado(jugador, lista),
    )
    if not equipos[0]:
        return
    await _iniciar_arena(ctx, oponente, equipos[0], equipos[1])


@bot.command(name="batalla")
async def iniciar_batalla(ctx, oponente: discord.Member):
    """Duelo con selector mejorado (miniaturas y búsqueda)."""
    if not await _validar_retador(ctx, oponente):
        return

    equipos = await _obtener_equipos_duelo(
        ctx,
        oponente,
        lambda jugador, lista: SelectorBatalla(jugador, lista, bot.session),
        privado=True,
        fuente_lista=database.obtener_equipo_selector,
        mensaje_minimo="❌ Necesitas al menos 3 Pokémon en tu equipo. Usa `!equipo`.",
        resolver_seleccion=lambda jugador, ids: database.nombres_desde_captura_ids(
            jugador.id, ids
        ),
    )
    if not equipos[0]:
        return
    await _iniciar_arena(ctx, oponente, equipos[0], equipos[1])


@bot.command(name="equipo")
@canal_restringido()
async def equipo(ctx):
    """Gestiona tu equipo de hasta 9 Pokémon (panel privado)."""
    if not hasattr(bot, "session") or bot.session.closed:
        bot.session = aiohttp.ClientSession()
    await abrir_equipo_en_privado(ctx, ctx.author, bot.session)


bot.run(TOKEN)
