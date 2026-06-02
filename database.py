import sqlite3
import asyncio
import datetime
import os
DATABASE_URL = os.environ.get('DATABASE_URL')
db_lock = asyncio.Lock()
import psycopg2

def get_connection():
    if DATABASE_URL:
        # Conexión a PostgreSQL (Producción en Render)
        return psycopg2.connect(DATABASE_URL)
    else:
        # Conexión a SQLite (Local)
        return sqlite3.connect('fumo_data.db')


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Creamos la tabla con la nueva columna 'pokeball' incluida desde el inicio
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS capturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pokemon_nombre TEXT,
            es_shiny INTEGER DEFAULT 0,
            pokeball TEXT DEFAULT 'Pokéball',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Intentamos añadir las columnas antiguas por compatibilidad
    try:
        cursor.execute("ALTER TABLE capturas ADD COLUMN es_shiny INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE capturas ADD COLUMN fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    # 3. NUEVO: Intentamos añadir la columna 'pokeball' por si la tabla ya existía de antes
    try:
        cursor.execute("ALTER TABLE capturas ADD COLUMN pokeball TEXT DEFAULT 'Pokéball'")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

async def guardar_captura(user_id, pokemon_nombre, es_shiny=False, pokeball='Pokéball'):
    async with db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        # Se añade 'pokeball' a los campos y al tuple de valores
        cursor.execute("INSERT INTO capturas (user_id, pokemon_nombre, es_shiny, pokeball) VALUES (?, ?, ?, ?)", 
                       (user_id, pokemon_nombre.lower(), 1 if es_shiny else 0, pokeball))
        conn.commit()
        conn.close()

def obtener_capturas(user_id, solo_shiny=False):
    conn = get_connection()
    cursor = conn.cursor()
    if solo_shiny:
        cursor.execute("SELECT pokemon_nombre FROM capturas WHERE user_id = ? AND es_shiny = 1", (user_id,))
    else:
        cursor.execute("SELECT pokemon_nombre FROM capturas WHERE user_id = ?", (user_id,))
    resultados = [fila[0] for fila in cursor.fetchall()]
    conn.close()
    return resultados

def obtener_versiones_pokemon(user_id, nombre_pokemon):
    conn = get_connection()
    cursor = conn.cursor()
    # Usamos .lower() aquí también
    cursor.execute("SELECT es_shiny FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", 
                   (user_id, nombre_pokemon.lower()))
    versiones = [fila[0] for fila in cursor.fetchall()]
    conn.close()
    return versiones

def obtener_info_captura(user_id, nombre_pokemon):
    """Retorna (fecha_primera_captura, cantidad_total)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MIN(fecha), COUNT(*) 
        FROM capturas 
        WHERE user_id = ? AND pokemon_nombre = ?
    """, (user_id, nombre_pokemon))
    resultado = cursor.fetchone()
    conn.close()
    return resultado
def init_energia_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS energia (
            user_id INTEGER PRIMARY KEY,
            intentos INTEGER DEFAULT 12,
            ultima_recarga TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def obtener_energia_db(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT intentos, ultima_recarga FROM energia WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res # Retorna (intentos, ultima_recarga_str) o None

def actualizar_energia_db(user_id, intentos, ultima_recarga):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO energia (user_id, intentos, ultima_recarga) VALUES (?, ?, ?)", 
                   (user_id, intentos, ultima_recarga.isoformat()))
    conn.commit()
    conn.close()
def obtener_lista_capturas(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    # DISTINCT para que no salgan repetidos en la lista de selección
    cursor.execute("SELECT DISTINCT pokemon_nombre FROM capturas WHERE user_id = ?", (user_id,))
    res = [row[0] for row in cursor.fetchall()]
    conn.close()
    return res