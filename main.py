import discord
import aiohttp
import random
import os
import database
import servicios
from discord.ext import commands
from dotenv import load_dotenv
from vistas import PokedexView, BotonCaptura, InfoView, SpawnSelectionView # <-- Añade SpawnSelectionView
import configuracion
from configuracion import canal_restringido
from discord.ext import commands
import discord
from discord.ext import commands
import admin
import vistas_combate
from vistas_combate import SelectorPaginado, VistaCombate
import psycopg2
import sqlite3
from logger_config import log

database.init_db()
# 1. CONFIGURACIÓN
load_dotenv()
TOKEN = os.getenv('TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'), 
    intents=intents,
    case_insensitive=True
)

REGIONES = {
    "1": (1, 151), "2": (152, 251), "3": (252, 386),
    "4": (387, 493), "5": (494, 649), "6": (650, 721),
    "7": (722, 809), "8": (810, 905), "9": (906, 1025)
}

@bot.event
async def on_ready():
    configuracion.init_config_db()
    print(f'Bot conectado como {bot.user}')
    
    # 0. INICIALIZAR SESIÓN DE RED (¡Esto soluciona el error!)
    bot.session = aiohttp.ClientSession()
    
def get_connection():
    # Render y otros servicios en la nube usan variables de entorno
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url:
        # Conexión a PostgreSQL (Producción)
        return psycopg2.connect(db_url)
    else:
        # Conexión a SQLite (Local - Desarrollo)
        return sqlite3.connect('fumo_data.db')
    
    # 2. Inicializar base de datos de iniciación y comandos
    import gestor_spawn
    gestor_spawn.setup_gestor(bot)
    gestor_spawn.aplicar_filtro_spawn(bot)
    
    # 3. Limpieza de seguridad
    gestor_spawn.canales_ocupados.clear() 
    
    print("Base de datos, módulos y sesión de red verificados.")

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
        if filtro.isdigit() and filtro in REGIONES:
            inicio, fin = REGIONES[filtro]
            region_label = f"Región {filtro}"
            es_coleccion_personal = False
        elif not es_shiny_mode:
            # Si no es región ni 'shiny', intentamos filtrar por tipo
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




# --- COMANDO SPAWN CORREGIDO ---
@bot.command()
@canal_restringido()
@commands.cooldown(1, 10, commands.BucketType.user)
async def spawn(ctx):
    import gestor_spawn
    import database
    
    # 1. Filtros básicos
    if not gestor_spawn.verificar_inicial(ctx.author.id):
        return await ctx.send("¡Bienvenido! Antes de tu aventura, elige tu Pokémon inicial con `!inicial`.")
    
    # Obtenemos datos persistentes de la base de datos
    datos_intentos = await gestor_spawn.obtener_intentos(ctx.author.id)
    intentos = datos_intentos[0]
    ultima_recarga = datos_intentos[1]
    
    if intentos <= 0:
        return await ctx.send("❌ Has agotado tus intentos. Tus inciensos se recargan en 2 horas.")

    # 2. Registro de energía persistente
    database.actualizar_energia_db(ctx.author.id, intentos - 1, ultima_recarga)

    # 3. Bloqueo de canal
    gestor_spawn.canales_ocupados.add(ctx.channel.id)

    try:
        # Generación de IDs con filtro de legendarios
        ids_spawn = []
        while len(ids_spawn) < 3:
            azar = random.random()
            if azar < 0.80: id_cand = random.randint(1, 493)
            elif azar < 0.95: id_cand = random.randint(494, 809)
            else: id_cand = random.randint(810, 1025)
            
            # FILTRO: Si es legendario, solo aceptarlo con un 5% de probabilidad
            if await es_legendario(bot.session, id_cand):
                if random.random() > 0.05: 
                    continue # Rechazado, buscar otro
            
            ids_spawn.append(id_cand)
        
        # Obtención de datos
        data_pokes = []
        for poke_id in ids_spawn:
            data, species = await servicios.obtener_pokemon(bot.session, poke_id)
            data_pokes.append((data, species))
        
        buffer_siluetas = await servicios.generar_collage_siluetas(bot.session, data_pokes)
        if not buffer_siluetas:
            gestor_spawn.canales_ocupados.discard(ctx.channel.id)
            database.actualizar_energia_db(ctx.author.id, intentos, ultima_recarga)
            return await ctx.send("Hubo un problema al generar las siluetas.")

        imagen_final = discord.File(buffer_siluetas, filename="fragmentos.png")
        
        # Pistas
        texto_pistas = ""
        pistas_usadas = []
        for i, (data, species) in enumerate(data_pokes):
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
        mensaje_enviado = await ctx.send(embed=embed, file=imagen_final, view=view)
        view.message = mensaje_enviado

    except Exception as e:
        gestor_spawn.canales_ocupados.discard(ctx.channel.id)
        database.actualizar_energia_db(ctx.author.id, intentos, ultima_recarga)
        print(f"Error en spawn: {e}")
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
import perfil
perfil.iniciar_modulo_perfil(bot)
import intercambio
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
    import gestor_spawn
    gestor_spawn.canales_ocupados.clear() # Vacía el set por completo
    await ctx.send("✅ Todos los canales han sido desbloqueados manualmente.")

@bot.command(name="cooldowns")
@canal_restringido()
async def cooldowns(ctx):
    import gestor_spawn
    import datetime

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
    
    msg = await ctx.send(embed=embed)
@bot.command(name="resetintentos")
@canal_restringido()
@commands.has_permissions(administrator=True)
async def resetintentos(ctx, usuario: discord.Member):
    """Resetea los intentos de un usuario a 12 (Admin)."""
    import datetime
    import database
    
    # Reseteamos a 12 intentos y la hora actual
    database.actualizar_energia_db(usuario.id, 12, datetime.datetime.now())
    
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
def canal_restringido():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        if not configuracion.es_canal_permitido(ctx):
            # Opcional: Avisar al usuario
            # await ctx.send("❌ No puedes usar comandos aquí.")
            return False
        return True
    return commands.check(predicate)

# 1. Añade esta función para verificar la rareza
async def es_legendario(session, poke_id):
    url = f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}/"
    async with session.get(url) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get('is_legendary', False) or data.get('is_mythical', False)
    return False

admin.setup(bot)


@bot.command(name="combate")
async def iniciar_combate(ctx, oponente: discord.Member):
    # 1. Validaciones
    if oponente.bot:
        return await ctx.send("❌ No puedes retar a un bot.")
    if oponente.id == ctx.author.id:
        return await ctx.send("❌ ¡No puedes pelear contra ti mismo!")

    # 2. Obtención de datos
    lista1 = database.obtener_lista_capturas(ctx.author.id)
    lista2 = database.obtener_lista_capturas(oponente.id)
    
    if len(lista1) < 3 or len(lista2) < 3:
        return await ctx.send("❌ Ambos jugadores necesitan al menos 3 Pokémon capturados.")

    # 3. Jugador 1 elige equipo (usamos una función helper para limpiar el código)
    async def obtener_equipo(jugador, lista):
        view = vistas_combate.SelectorPaginado(jugador, lista)
        msg = await ctx.send(f"⚔️ {jugador.mention}, elige tus 3 Pokémon:", view=view)
        await view.wait()
        await msg.delete() # Borramos el mensaje de selección para no dejar basura
        return view.seleccionados

    equipo1 = await obtener_equipo(ctx.author, lista1)
    if len(equipo1) < 3:
        return await ctx.send(f"❌ {ctx.author.mention} canceló la selección.")

    equipo2 = await obtener_equipo(oponente, lista2)
    if len(equipo2) < 3:
        return await ctx.send(f"❌ {oponente.mention} canceló la selección.")

    # 4. Inicio de la simulación
    msg_espera = await ctx.send("⏳ Preparando arena de combate...")
    
    vista_combate = vistas_combate.VistaCombate(
        ctx.author, oponente, equipo1, equipo2, bot.session
    )
    
    try:
        await vista_combate.preparar_combate()
        await msg_espera.edit(content="✅ ¡Todo listo! Pulsa el botón para comenzar.", view=vista_combate)
    except Exception as e:
        await msg_espera.delete()
        await ctx.send(f"❌ Error al preparar el combate: {e}")
bot.run(TOKEN)