import os
import database 
import datetime
import discord
from discord.ext import commands
from logger_config import log

# --- 1. ESTADO TEMPORAL ---
canales_ocupados = set()

# --- 2. GESTIÓN DE ENERGÍA PERSISTENTE ---
async def obtener_intentos(user_id):
    try:
        log.debug(f"🔍 Obteniendo intentos para user {user_id}")
        ahora = datetime.datetime.now(datetime.timezone.utc)
        datos = database.obtener_energia_db(user_id)
        
        if not datos:
            log.info(f"📍 Primer acceso de user {user_id}, creando registro con 12 intentos")
            database.actualizar_energia_db(user_id, 12, ahora)
            return 12, ahora
            
        intentos, ultima_recarga_raw = datos

        # --- CORRECCIÓN AQUÍ ---
        # Si ya es un objeto datetime, no necesitamos convertirlo
        if isinstance(ultima_recarga_raw, datetime.datetime):
            ultima_recarga = ultima_recarga_raw
        else:
            # Si es un string, lo convertimos
            ultima_recarga = datetime.datetime.fromisoformat(str(ultima_recarga_raw))
        # -----------------------
        
        # Asegurarnos de que ambas tengan zona horaria para comparar correctamente
        if ultima_recarga.tzinfo is None:
            ultima_recarga = ultima_recarga.replace(tzinfo=datetime.timezone.utc)

        # Comprobar si pasaron 2 horas (7200 segundos)
        tiempo_transcurrido = (ahora - ultima_recarga).total_seconds()
        if tiempo_transcurrido >= 7200:
            log.info(f"⏰ Recarga de energía: User {user_id} - Tiempo transcurrido: {tiempo_transcurrido:.0f}s")
            database.actualizar_energia_db(user_id, 12, ahora)
            return 12, ahora
        
        log.info(f"✅ Intentos obtenidos: User {user_id} - Intentos: {intentos} - Próxima recarga en {7200 - tiempo_transcurrido:.0f}s")
        return intentos, ultima_recarga
    except Exception as e:
        log.error(f"🚨 Error al obtener intentos para user {user_id}: {e}", exc_info=True)
        return 0, datetime.datetime.now(datetime.timezone.utc)

# --- 3. FILTRO DE SPAWN ---
def aplicar_filtro_spawn(bot):
    @bot.check
    async def check_spawn(ctx):
        try:
            if ctx.command.name != "spawn":
                return True
            
            log.debug(f"🎯 Validando spawn: User {ctx.author.id} - Canal {ctx.channel.id}")
            
            if ctx.channel.id in canales_ocupados:
                log.warning(f"⚠️ Canal ocupado: {ctx.channel.id} - User {ctx.author.id}")
                await ctx.send("❌ Ya hay un encuentro en curso en este canal.")
                return False
            
            if not verificar_inicial(ctx.author.id):
                log.warning(f"⚠️ Usuario sin inicial: {ctx.author.id}")
                await ctx.send("¡Bienvenido! Antes de tu aventura, elige tu Pokémon inicial con el comando `!inicial`.")
                return False
                
            datos_energia = await obtener_intentos(ctx.author.id)
            if datos_energia[0] <= 0:
                log.warning(f"⚠️ Usuario sin intentos: {ctx.author.id}")
                await ctx.send("❌ Has agotado tus intentos. Tus inciensos se recargan en 2 horas.")
                return False
            
            log.info(f"✅ Spawn validado: User {ctx.author.id} - Intentos: {datos_energia[0]}")
            return True
        except Exception as e:
            log.error(f"🚨 Error en check_spawn: {e}", exc_info=True)
            return False

# --- 4. CONFIGURACIÓN DE INICIALIZACIÓN ---
def init_db_inicial():
    try:
        log.info("📍 Inicializando tabla de iniciación...")
        conn = database.get_connection()
        cursor = conn.cursor()
        # BIGINT es la forma correcta de manejar IDs de Discord en Postgres
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS iniciacion (
                user_id BIGINT PRIMARY KEY,
                recibio_inicial INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
        log.info("✅ Tabla 'iniciacion' creada/verificada")
    except Exception as e:
        log.error(f"🚨 Error al inicializar tabla de iniciación: {e}", exc_info=True)
        raise

def verificar_inicial(user_id):
    try:
        log.debug(f"🔍 Verificando inicial para user {user_id}")
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # ASEGURAMOS que el ID sea string siempre para evitar conflictos con BIGINT
        uid = str(user_id)
        
        if os.environ.get('DATABASE_URL'):
            cursor.execute("SELECT recibio_inicial FROM iniciacion WHERE user_id = %s", (uid,))
        else:
            cursor.execute("SELECT recibio_inicial FROM iniciacion WHERE user_id = ?", (uid,))
            
        res = cursor.fetchone()
        conn.close()
        
        tiene_inicial = res is not None and res[0] == 1
        if tiene_inicial:
            log.info(f"✅ User {user_id} tiene inicial")
        else:
            log.info(f"⚠️ User {user_id} sin inicial")
        
        return tiene_inicial
    except Exception as e:
        log.error(f"🚨 Error al verificar inicial para user {user_id}: {e}", exc_info=True)
        return False

def setup_gestor(bot):
    try:
        log.info("📍 Configurando gestor de spawn...")
        init_db_inicial()
        database.init_energia_db()
        log.info("✅ Gestor de spawn configurado")

        @bot.command(name="inicial")
        async def inicial(ctx):
            try:
                log.info(f"🎯 Comando inicial ejecutado por user {ctx.author.id}")
                
                if verificar_inicial(ctx.author.id):
                    log.warning(f"⚠️ User {ctx.author.id} ya tiene inicial")
                    return await ctx.send("❌ Ya has recibido tu Pokémon inicial.")
                
                log.info(f"✅ Mostrando selector de inicial para user {ctx.author.id}")
                from vistas import SeleccionInicialView
                view = SeleccionInicialView(ctx.author.id)
                await ctx.send(embed=view.get_embed(), view=view)
            except Exception as e:
                log.error(f"🚨 Error en comando inicial: {e}", exc_info=True)
                await ctx.send("❌ Hubo un error al procesar tu selección inicial.")
    except Exception as e:
        log.error(f"🚨 Error al configurar gestor de spawn: {e}", exc_info=True)
        raise
