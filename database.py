import sqlite3
import asyncio
import datetime
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
db_lock = asyncio.Lock()

def get_connection():
    if DATABASE_URL:
        # Se conecta a Neon (PostgreSQL)
        return psycopg2.connect(DATABASE_URL)
    else:
        # Se conecta a SQLite (Local)
        return sqlite3.connect('fumo_data.db')

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Creamos la tabla (Usamos SERIAL para Postgres, AUTOINCREMENT para SQLite)
    if DATABASE_URL:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS capturas (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                pokemon_nombre TEXT,
                es_shiny INTEGER DEFAULT 0,
                pokeball TEXT DEFAULT 'Pokéball',
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
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
    conn.commit()
    conn.close()

async def guardar_captura(user_id, pokemon_nombre, es_shiny=False, pokeball='Pokéball'):
    async with db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:
            cursor.execute("INSERT INTO capturas (user_id, pokemon_nombre, es_shiny, pokeball) VALUES (%s, %s, %s, %s)", 
                           (str(user_id), pokemon_nombre.lower(), 1 if es_shiny else 0, pokeball))
        else:
            cursor.execute("INSERT INTO capturas (user_id, pokemon_nombre, es_shiny, pokeball) VALUES (?, ?, ?, ?)", 
                           (user_id, pokemon_nombre.lower(), 1 if es_shiny else 0, pokeball))
        conn.commit()
        conn.close()

def ejecutar_consulta(query_pg, query_sql, params):
    """Auxiliar para ejecutar consultas con diferentes sintaxis"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query_pg if DATABASE_URL else query_sql, params)
    res = cursor.fetchall()
    conn.close()
    return res

def obtener_capturas(user_id, solo_shiny=False):
    if DATABASE_URL:
        q = "SELECT pokemon_nombre FROM capturas WHERE user_id = %s" + (" AND es_shiny = 1" if solo_shiny else "")
        res = ejecutar_consulta(q, q.replace("%s", "?"), (str(user_id),))
    else:
        q = "SELECT pokemon_nombre FROM capturas WHERE user_id = ?" + (" AND es_shiny = 1" if solo_shiny else "")
        res = ejecutar_consulta(q.replace("%s", "?"), q, (user_id,))
    return [fila[0] for fila in res]

def obtener_versiones_pokemon(user_id, nombre_pokemon):
    if DATABASE_URL:
        res = ejecutar_consulta("SELECT es_shiny FROM capturas WHERE user_id = %s AND pokemon_nombre = %s", 
                               "SELECT es_shiny FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", 
                               (str(user_id), nombre_pokemon.lower()))
    else:
        res = ejecutar_consulta("SELECT es_shiny FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", 
                               "SELECT es_shiny FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", 
                               (user_id, nombre_pokemon.lower()))
    return [fila[0] for fila in res]

def obtener_info_captura(user_id, nombre_pokemon):
    conn = get_connection()
    cursor = conn.cursor()
    if DATABASE_URL:
        cursor.execute("SELECT MIN(fecha), COUNT(*) FROM capturas WHERE user_id = %s AND pokemon_nombre = %s", (str(user_id), nombre_pokemon.lower()))
    else:
        cursor.execute("SELECT MIN(fecha), COUNT(*) FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", (user_id, nombre_pokemon.lower()))
    res = cursor.fetchone()
    conn.close()
    return res

def init_energia_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS energia (
            user_id BIGINT PRIMARY KEY,
            intentos INTEGER DEFAULT 12,
            ultima_recarga TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def obtener_energia_db(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    if DATABASE_URL:
        cursor.execute("SELECT intentos, ultima_recarga FROM energia WHERE user_id = %s", (str(user_id),))
    else:
        cursor.execute("SELECT intentos, ultima_recarga FROM energia WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def actualizar_energia_db(user_id, intentos, ultima_recarga):
    conn = get_connection()
    cursor = conn.cursor()
    ahora_str = ultima_recarga.isoformat()
    if DATABASE_URL:
        cursor.execute("""
            INSERT INTO energia (user_id, intentos, ultima_recarga) VALUES (%s, %s, %s)
            ON CONFLICT(user_id) DO UPDATE SET intentos = EXCLUDED.intentos, ultima_recarga = EXCLUDED.ultima_recarga
        """, (str(user_id), intentos, ahora_str))
    else:
        cursor.execute("REPLACE INTO energia (user_id, intentos, ultima_recarga) VALUES (?, ?, ?)", 
                       (user_id, intentos, ahora_str))
    conn.commit()
    conn.close()