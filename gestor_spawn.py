import os
import sqlite3
import psycopg2
import datetime
import database 

# --- 1. ESTADO TEMPORAL ---
canales_ocupados = set()

# --- 2. GESTIÓN DE ENERGÍA PERSISTENTE ---
async def obtener_intentos(user_id):
    ahora = datetime.datetime.now(datetime.timezone.utc)
    # Usamos las funciones que ya migramos en database.py
    datos = database.obtener_energia_db(user_id)
    
    if not datos:
        database.actualizar_energia_db(user_id, 12, ahora)
        return 12, ahora
        
    intentos, ultima_recarga_str = datos
    ultima_recarga = datetime.datetime.fromisoformat(ultima_recarga_str)
    
    # Comprobar si pasaron 2 horas (7200 segundos)
    if (ahora.replace(tzinfo=None) - ultima_recarga.replace(tzinfo=None)).total_seconds() >= 7200:
        database.actualizar_energia_db(user_id, 12, ahora)
        return 12, ahora
        
    return intentos, ultima_recarga

# --- 3. FILTRO DE SPAWN ---
def aplicar_filtro_spawn(bot):
    @bot.check
    async def check_spawn(ctx):
        if ctx.command.name != "spawn":
            return True
        
        if ctx.channel.id in canales_ocupados:
            await ctx.send("❌ Ya hay un encuentro en curso en este canal.")
            return False
            
        if not verificar_inicial(ctx.author.id):
            await ctx.send("¡Bienvenido! Antes de tu aventura, elige tu Pokémon inicial con el comando `!inicial`.")
            return False
            
        datos_energia = await obtener_intentos(ctx.author.id)
        if datos_energia[0] <= 0:
            await ctx.send("❌ Has agotado tus intentos. Tus inciensos se recargan en 2 horas.")
            return False
            
        return True

# --- 4. CONFIGURACIÓN DE INICIALIZACIÓN ---
def init_db_inicial():
    conn = database.get_connection()
    cursor = conn.cursor()
    # Usamos BIGINT para asegurar compatibilidad con Discord IDs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS iniciacion (
            user_id BIGINT PRIMARY KEY,
            recibio_inicial INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def verificar_inicial(user_id):
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Sintaxis adaptable para Postgres o SQLite
    if os.environ.get('DATABASE_URL'):
        cursor.execute("SELECT recibio_inicial FROM iniciacion WHERE user_id = %s", (str(user_id),))
    else:
        cursor.execute("SELECT recibio_inicial FROM iniciacion WHERE user_id = ?", (user_id,))
        
    res = cursor.fetchone()
    conn.close()
    return res and res[0] == 1

def setup_gestor(bot):
    init_db_inicial()
    database.init_energia_db() 

    @bot.command(name="inicial")
    async def inicial(ctx):
        if verificar_inicial(ctx.author.id):
            return await ctx.send("❌ Ya has recibido tu Pokémon inicial.")
        
        from vistas import SeleccionInicialView
        view = SeleccionInicialView(ctx.author.id)
        await ctx.send(embed=view.get_embed(), view=view)