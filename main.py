import os
import random
import asyncio
import asyncpg
from datetime import datetime, timezone
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
from rarezas import pokemon_por_rareza
# Vistas e interfaces
from vistas import PokedexView, BotonCaptura, InfoView, SpawnSelectionView
from vistas_combate import SelectorPaginado, VistaCombate
import vistas_batalla
from vistas_batalla import SelectorBatalla
from vistas_equipo import abrir_equipo_en_privado
from rankingdex import iniciar_modulo_ranking
from rankinglegend import iniciar_modulo_ranking_legend
from rankingshiny import iniciar_modulo_ranking_shiny
from vistas import liberar_canal_completo
from database import guardar_captura
from regiones import obtener_siguiente_region
# Variables globales
from rarezas import pokemon_por_rareza
database.init_db()
# 1. CONFIGURACIÓN
load_dotenv()
TOKEN = os.getenv('TOKEN')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True




async def cargar_extensiones():
    # Agrega 'newpokedex' a tu lista principal. 
    # Si newpokedex.py está en la carpeta principal, no uses 'cogs.'
    extensiones = ['ivs_commands', 'inventario', 'equipo_slash', 'newpokedex','ranking_roles']
    
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

    await configuracion.init_config_db(bot)
    print(f'Bot conectado como {bot.user}')
    
    # 0. Inicializar sesión de red
    bot.session = aiohttp.ClientSession()

    # Cargar listas de rareza 
    print("Entrando en on_ready")
    await inicializar_rarezas_spawn()
    print("Terminó inicializar_rarezas_spawn")
    database.cargar_cache_pokemon()
    print("✅ Cache Pokémon cargada")
    #print("✅ Pokémon clasificados por rareza.")
    # 1. SETUP DE GESTORES
    gestor_spawn.setup_gestor(bot)
    gestor_spawn.aplicar_filtro_spawn(bot)
    gestor_spawn.canales_ocupados.clear()
    iniciar_modulo_ranking(bot)
    iniciar_modulo_ranking_legend(bot)
    iniciar_modulo_ranking_shiny(bot)
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

    if isinstance(error, commands.CheckFailure):
        return

    if isinstance(error, commands.CommandOnCooldown):
        seconds = round(error.retry_after, 2)

        await ctx.send(
            f"⏳ Estás en cooldown. "
            f"Intenta de nuevo en **{seconds} segundos**."
        )

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
        # Cargar listas de rareza
        await cargar_pokemon_por_rareza(bot.session)
        print("✅ Pokémon clasificados por rareza.")
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

                pokemon = database.obtener_pokemon_local(id_p)

                if pokemon and (
                    pokemon["es_legendario"]
                    or pokemon["es_mitico"]
                ):
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
    try:
        await asyncio.sleep(segundos)

        liberar_canal_completo(channel_id)

        print(
            f"🧹 [LIMPIEZA FORZADA] Canal {channel_id} liberado por seguridad."
        )

    except asyncio.CancelledError:
        pass



# --- COMANDO SPAWN CORREGIDO ---
@bot.command()
@canal_restringido()
@commands.cooldown(1, 10, commands.BucketType.user)
async def spawn(ctx):

    intentos = ctx.intentos
    ultima_recarga = ctx.ultima_recarga

    # Descontamos energía inmediatamente
    await database.actualizar_energia_db(
        ctx.bot,
        ctx.author.id,
        intentos - 1,
        ultima_recarga
    )

    # 🔒 Bloquear canal inmediatamente
    gestor_spawn.canales_ocupados.add(
        ctx.channel.id
    )

    log.info(
        f"🔒 Canal bloqueado: {ctx.channel.id}"
    )

    try:
        # --- GENERACIÓN POR RAREZA ---
        ids_spawn, rarezas_spawn = generar_ids_spawn()
        data_pokes = []

        log.info(f"Spawn generado: {ids_spawn}")

        # FASE 3: DESCARGA PARALELA
        tasks = [
            servicios.obtener_pokemon(
                bot.session,
                pid
            )
            for pid in ids_spawn
        ]

        import time

        inicio_api = time.perf_counter()

        resultados = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        print(
            f"OBTENER_POKEMON: "
            f"{time.perf_counter() - inicio_api:.3f}s"
        )

        # FASE 4: Procesamiento de datos
        for resultado in resultados:

            if isinstance(resultado, Exception):
                log.warning(
                    f"Error obteniendo Pokémon: {resultado}"
                )
                continue

            data, species = resultado

            if not data:
                continue

            es_shiny = (random.randint(1, 50) == 1)
            pokemon_id = data["id"]
            rareza = rarezas_spawn[pokemon_id]

            data_pokes.append(
                (data, species, es_shiny, rareza)
            )

        # NUEVO BLOQUE
        if not data_pokes:

            liberar_canal_completo(
                ctx.channel.id
            )

            await database.actualizar_energia_db(
                ctx.bot,
                ctx.author.id,
                intentos,
                ultima_recarga
            )

            log.warning(
                "⚠️ Spawn cancelado: no se pudo obtener ningún Pokémon válido."
            )

            return await ctx.send(
                "❌ No se pudo generar ningún Pokémon válido."
            )

        # Extraemos solo datos para collage
        datos_para_collage = [
            (d, s)
            for d, s, sh, r in data_pokes
        ]

        # Pasamos la lista limpia al generador
        inicio_siluetas = time.perf_counter()

        buffer_siluetas = await servicios.generar_collage_siluetas(
            ctx.bot.session,
            datos_para_collage,
            tenidos=[]
        )

        print(
            f"SILUETAS: "
            f"{time.perf_counter() - inicio_siluetas:.3f}s"
        )
        
        if not buffer_siluetas:

            liberar_canal_completo(
                ctx.channel.id
            )

            await database.actualizar_energia_db(
                ctx.bot,
                ctx.author.id,
                intentos,
                ultima_recarga
            )

            return await ctx.send(
                "Hubo un problema al generar las siluetas."
            )

        imagen_final = discord.File(buffer_siluetas, filename="fragmentos.png")
        
        # Generación de pistas
        texto_pistas = ""
        pistas_usadas = []
        for i, (data, species, es_shiny, rareza) in enumerate(data_pokes):
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
            view.message = mensaje_enviado
            gestor_spawn.vistas_activas[ctx.channel.id] = view 

            task = asyncio.create_task(
                auto_liberar_canal(
                    ctx.channel.id,
                    305
                )
            )

            gestor_spawn.tareas_limpieza[
                ctx.channel.id
            ] = task

        except Exception as e:
            liberar_canal_completo(
                ctx.channel.id
            )
            await database.actualizar_energia_db(ctx.bot, ctx.author.id, intentos, ultima_recarga)
            log.error(f"Error al enviar mensaje en spawn: {e}", exc_info=True)
            await ctx.send("¡Se escaparon! Hubo un error al intentar enviar el encuentro.")

    except Exception as e:
        liberar_canal_completo(
            ctx.channel.id
        )
        await database.actualizar_energia_db(ctx.bot, ctx.author.id, intentos, ultima_recarga)
        log.error(f"Error crítico en generación de spawn para {ctx.author.id}: {e}", exc_info=True)
        await ctx.send("¡Se escaparon! Hubo un error al intentar generar el encuentro.")
@bot.command()
@canal_restringido()
async def info(ctx, *, nombre: str):
    nombre = nombre.lower().strip()
    versiones = database.obtener_versiones_pokemon(ctx.author.id, nombre)
    
    if not versiones:
        return await ctx.send(f"❌ No tienes a **{nombre.capitalize()}**.")

    pokemon = database.obtener_pokemon_local_nombre(nombre)

    if not pokemon:
        return await ctx.send("Pokémon no encontrado.")

    mostrar_shiny = (1 in versiones)

    view = InfoView(
        ctx.author.id,
        pokemon,
        versiones,
        mostrar_shiny
    )
    await view.enviar_embed(ctx)

perfil.iniciar_modulo_perfil(bot)

intercambio.iniciar_modulo_intercambio(bot)

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
        intentos, ultima_recarga_raw = await gestor_spawn.obtener_intentos(
            ctx.bot,
            ctx.author.id
        )
        
        # Lógica de tiempo (normalizada a UTC)
        ahora = datetime.now(timezone.utc)
        
        # Conversión segura
        if isinstance(ultima_recarga_raw, str):
            ultima_recarga = datetime.fromisoformat(ultima_recarga_raw)
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
    await database.actualizar_energia_db(bot, usuario.id, 12, datetime.now(timezone.utc))
        
    await ctx.send(f"✅ Se han reseteado los intentos de {usuario.display_name} a 12.")
# Comando para establecer el canal (solo administradores)
@bot.command(name="setcanal")
@commands.has_permissions(administrator=True)
async def setcanal(ctx, canal: discord.TextChannel):

    await configuracion.set_canal(
        ctx.bot,
        ctx.guild.id,
        canal.id
    )

    await ctx.send(
        f"✅ Los comandos ahora solo se permiten en {canal.mention}"
    )
@bot.check
async def verificar_canal(ctx):
    # Si es mensaje privado, permitir siempre
    if ctx.guild is None:
        return True
        
    # Si es administrador, permitir siempre
    if ctx.author.guild_permissions.administrator:
        return True
    
    # Obtener el canal configurado
    canal_permitido = await configuracion.obtener_canal(
        ctx.bot,
        ctx.guild.id
    )

    # Si no hay canal configurado, se permite en todos
    if canal_permitido is None:
        return True
        
    # Si hay canal configurado, validar
    return ctx.channel.id == canal_permitido

# 1. Añade esta función para verificar la rareza
async def es_legendario(session, poke_id):
    try:
        url = f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}/"

        timeout = aiohttp.ClientTimeout(
            total=5
        )

        async with session.get(
            url,
            timeout=timeout
        ) as resp:

            if resp.status == 200:
                data = await resp.json()

                return (
                    data.get('is_legendary', False)
                    or data.get('is_mythical', False)
                )

    except Exception as e:
        log.warning(
            f"Error verificando legendario {poke_id}: {e}"
        )

    return False

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
        # 1. Obtenemos la selección (sea por método privado o público)
        if privado:
            seleccion = await vistas_batalla.elegir_equipo_en_privado(
                ctx, jugador, lista, crear_selector
            )
        else:
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

        # 2. LA MAGIA: Traducimos SIEMPRE, sin importar si fue privado o no
        if resolver_seleccion:
            return resolver_seleccion(jugador, seleccion)
        return seleccion

    equipo1 = await elegir_equipo(ctx.author, lista1)
    if not equipo1 or len(equipo1) < 3:
        await ctx.send(f"❌ {ctx.author.mention} no completó la selección.")
        return None, None

    equipo2 = await elegir_equipo(oponente, lista2)
    if not equipo2 or len(equipo2) < 3:
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
async def cargar_pokemon_por_rareza(session):
    # Limpiamos las listas por si la función se ejecuta más de una vez
    for rareza in pokemon_por_rareza:
        pokemon_por_rareza[rareza].clear()

    for pokemon_id in range(1, 1026):
        data, species = await servicios.obtener_pokemon(session, pokemon_id)

        if not data:
            continue

        capture_rate = data.get("capture_rate", 45)

        es_legendario, es_mitico = database.obtener_tipo_especial(pokemon_id)

        if es_legendario:
            pokemon_por_rareza["legendario"].append(pokemon_id)

        elif es_mitico:
            pokemon_por_rareza["mitico"].append(pokemon_id)

        else:
            if capture_rate >= 200:
                pokemon_por_rareza["muy_comun"].append(pokemon_id)

            elif capture_rate >= 120:
                pokemon_por_rareza["comun"].append(pokemon_id)

            elif capture_rate >= 60:
                pokemon_por_rareza["poco_comun"].append(pokemon_id)

            elif capture_rate >= 30:
                pokemon_por_rareza["raro"].append(pokemon_id)

            else:
                pokemon_por_rareza["epico"].append(pokemon_id)

    print("=== Pokémon por rareza ===")
    for rareza, lista in pokemon_por_rareza.items():
        print(f"{rareza}: {len(lista)}")


async def inicializar_rarezas_spawn():
    global pokemon_por_rareza

    # Limpiar listas por si se vuelve a ejecutar
    for rareza in pokemon_por_rareza:
        pokemon_por_rareza[rareza].clear()

    datos = database.obtener_datos_rareza()

    for pokemon_id, capture_rate, es_legendario, es_mitico in datos:

        if es_legendario:
            pokemon_por_rareza["legendario"].append(pokemon_id)

        elif es_mitico:
            pokemon_por_rareza["mitico"].append(pokemon_id)

        else:
            if capture_rate >= 200:
                pokemon_por_rareza["muy_comun"].append(pokemon_id)

            elif capture_rate >= 120:
                pokemon_por_rareza["comun"].append(pokemon_id)

            elif capture_rate >= 60:
                pokemon_por_rareza["poco_comun"].append(pokemon_id)

            elif capture_rate >= 30:
                pokemon_por_rareza["raro"].append(pokemon_id)

            else:
                pokemon_por_rareza["epico"].append(pokemon_id)

    log.info("=== Rarezas cargadas ===")
    log.info(f"Muy comunes: {len(pokemon_por_rareza['muy_comun'])}")
    log.info(f"Comunes: {len(pokemon_por_rareza['comun'])}")
    log.info(f"Poco comunes: {len(pokemon_por_rareza['poco_comun'])}")
    log.info(f"Raros: {len(pokemon_por_rareza['raro'])}")
    log.info(f"Épicos: {len(pokemon_por_rareza['epico'])}")
    log.info(f"Míticos: {len(pokemon_por_rareza['mitico'])}")
    log.info(f"Legendarios: {len(pokemon_por_rareza['legendario'])}")
def generar_ids_spawn():
    ids_spawn = []
    rarezas_spawn = {}
    rarezas = [
        "muy_comun",
        "comun",
        "poco_comun",
        "raro",
        "epico",
        "mitico",
        "legendario"
    ]

    pesos = [
    47,      # muy_comun
    30,      # comun
    15,      # poco_comun
    7,       # raro
    0.83,    # epico
    0.067,   # mitico
    0.033    # legendario
    ]

    salio_legendario = False
    salio_mitico = False

    while len(ids_spawn) < 3:

        rarezas_disponibles = rarezas.copy()
        pesos_disponibles = pesos.copy()

        if salio_legendario:
            indice = rarezas_disponibles.index("legendario")
            rarezas_disponibles.pop(indice)
            pesos_disponibles.pop(indice)

        if salio_mitico:
            indice = rarezas_disponibles.index("mitico")
            rarezas_disponibles.pop(indice)
            pesos_disponibles.pop(indice)

        rareza_elegida = random.choices(
            rarezas_disponibles,
            weights=pesos_disponibles,
            k=1
        )[0]
        
        pokemon_disponibles = pokemon_por_rareza[rareza_elegida]

        if not pokemon_disponibles:
            continue

        pokemon_id = random.choice(pokemon_disponibles)

        if pokemon_id in ids_spawn:
            continue

        ids_spawn.append(pokemon_id)
        rarezas_spawn[pokemon_id] = rareza_elegida

        if rareza_elegida == "legendario":
            salio_legendario = True

        elif rareza_elegida == "mitico":
            salio_mitico = True
    return ids_spawn, rarezas_spawn

from safari_manager import (
    obtener_safari,
    crear_safari,
    eliminar_safari
)
from vistas_safari import (
    VistaParticiparSafari,
    VistaApuestasSafari
)
@bot.command()
@canal_restringido()
async def safari(ctx):

    safari = obtener_safari(
        ctx.guild.id
    )

    if safari and safari.activo:
        return await ctx.send(
            "🚙 Ya hay un Safari activo."
        )

    safari = crear_safari(
        ctx.guild.id,
        ctx.channel.id
    )

    await safari.iniciar_safari(
        ctx.guild.id,
        ctx.channel.id,
        ctx.channel,
        bot.session,
        lambda guild_id: VistaApuestasSafari(guild_id)
    )

    embed = discord.Embed(
        title="🚙 Safari Pokémon",
        description=(
            "El recorrido comenzará en 60 segundos.\n\n"
            "Presiona el botón para subir a la camioneta."
        ),
        color=discord.Color.green()
    )

    view = VistaParticiparSafari(
        ctx.guild.id
    )

    mensaje = await ctx.send(
        embed=embed,
        view=view
    )

    view.message = mensaje

    # -------------------------
    # ESPERA INSCRIPCIONES
    # -------------------------

    await asyncio.sleep(60)

    participantes = safari.cantidad_participantes()

    if participantes == 0:

        await ctx.send(
            "🚙 Nadie abordó la camioneta.\n"
            "El Safari fue cancelado."
        )

        await safari.finalizar_safari()

        eliminar_safari(
            ctx.guild.id
        )

        return

    await ctx.send(
        f"🚙 El Safari ha comenzado.\n\n"
        f"🌎 Región: {safari.region_actual}"
    )
    await safari.ejecutar_safari()
    return


bot.run(TOKEN)
