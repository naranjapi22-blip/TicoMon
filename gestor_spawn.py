import sqlite3
import datetime
import database # Asegúrate de que este sea tu archivo database.py

# --- 1. MEMORIA TEMPORAL ---
# Mantenemos el set de canales ocupados aquí porque es un estado de tiempo real
canales_ocupados = set()

# --- 2. GESTIÓN DE ENERGÍA PERSISTENTE ---
async def obtener_intentos(user_id):
    ahora = datetime.datetime.now()
    # Consultamos la energía en la base de datos persistente
    datos = database.obtener_energia_db(user_id) # Esta función la creamos en el paso anterior
    
    if not datos:
        # Si no existe registro, creamos uno con 12 intentos y guardamos
        database.actualizar_energia_db(user_id, 12, ahora)
        return 12, ahora
        
    intentos, ultima_recarga_str = datos
    ultima_recarga = datetime.datetime.fromisoformat(ultima_recarga_str)
    
    # Comprobar si pasaron 2 horas (7200 segundos)
    if (ahora - ultima_recarga).total_seconds() >= 7200:
        database.actualizar_energia_db(user_id, 12, ahora)
        return 12, ahora
        
    return intentos, ultima_recarga

# --- 3. FILTRO DE SPAWN ---
def aplicar_filtro_spawn(bot):
    @bot.check
    async def check_spawn(ctx):
        if ctx.command.name != "spawn":
            return True
        
        # Bloqueo de canal
        if ctx.channel.id in canales_ocupados:
            await ctx.send("❌ Ya hay un encuentro en curso en este canal.")
            return False
            
        # Verificación de Iniciación
        if not verificar_inicial(ctx.author.id):
            await ctx.send("¡Bienvenido! Antes de tu aventura, elige tu Pokémon inicial con el comando `!inicial`.")
            return False
            
        # Verificación de Energía usando la DB
        datos_energia = await obtener_intentos(ctx.author.id)
        if datos_energia[0] <= 0:
            await ctx.send("❌ Has agotado tus intentos. Tus inciensos se recargan en 2 horas.")
            return False
            
        return True

# --- 4. CONFIGURACIÓN INICIAL ---
def init_db_inicial():
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS iniciacion (
            user_id INTEGER PRIMARY KEY,
            recibio_inicial INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def verificar_inicial(user_id):
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT recibio_inicial FROM iniciacion WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res and res[0] == 1

def setup_gestor(bot):
    init_db_inicial()
    database.init_energia_db() # Inicializamos la tabla de energía en la DB

    @bot.command(name="inicial")
    async def inicial(ctx):
        if verificar_inicial(ctx.author.id):
            return await ctx.send("❌ Ya has recibido tu Pokémon inicial.")
        
        from vistas import SeleccionInicialView
        view = SeleccionInicialView(ctx.author.id)
        await ctx.send(embed=view.get_embed(), view=view)