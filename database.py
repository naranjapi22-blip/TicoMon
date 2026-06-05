import sqlite3
import asyncio
import datetime
import os
import psycopg2
from logger_config import log
import logging
import random

DATABASE_URL = os.environ.get('DATABASE_URL')
db_lock = asyncio.Lock()

# --- Lógica de IVs (puedes poner esto en utils.py e importarlo) ---
def generar_iv_final():
    if random.random() < 0.005:  # 0.5% probabilidad de 0
        return 0
    return sum(random.randint(1, 6) for _ in range(5)) + 1


def get_connection():
    try:
        if DATABASE_URL:
            # Se conecta a Neon (PostgreSQL)
            conn = psycopg2.connect(DATABASE_URL)
            log.debug("✅ Conexión a PostgreSQL establecida")
            return conn
        else:
            # Se conecta a SQLite (Local)
            conn = sqlite3.connect('fumo_data.db')
            log.debug("✅ Conexión a SQLite establecida")
            return conn
    except Exception as e:
        log.error(f"🚨 Error al conectar a la base de datos: {e}", exc_info=True)
        raise

def init_db():
    try:
        log.info("📍 Inicializando base de datos...")
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
            log.info("✅ Tabla 'capturas' creada/verificada en PostgreSQL")
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
            log.info("✅ Tabla 'capturas' creada/verificada en SQLite")
        
        conn.commit()
        conn.close()
        log.info("✅ Base de datos inicializada correctamente")
        
    except Exception as e:
        log.error(f"🚨 Error al inicializar la base de datos: {e}", exc_info=True)
        raise

async def guardar_captura(user_id, pokemon_nombre, es_shiny=False, pokeball='Pokéball'):
    async with db_lock:
        conn = None
        try:
            log.debug(f"💾 Guardando captura: {pokemon_nombre} (User: {user_id}, Shiny: {es_shiny})")
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # 🔥 SOLUCIÓN AQUÍ: Generamos números 100% aleatorios del 0 al 31 inclusive
            iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe = [random.randint(0, 31) for _ in range(6)]
            
            fecha_ahora = datetime.datetime.now(datetime.timezone.utc)
            
            if DATABASE_URL:
                cursor.execute("""
                    INSERT INTO capturas (
                        user_id, pokemon_nombre, es_shiny, pokeball, fecha, 
                        iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (str(user_id), pokemon_nombre.lower(), 1 if es_shiny else 0, 
                      pokeball, fecha_ahora, iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe))
            else:
                cursor.execute("""
                    INSERT INTO capturas (
                        user_id, pokemon_nombre, es_shiny, pokeball, fecha, 
                        iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, pokemon_nombre.lower(), 1 if es_shiny else 0, 
                      pokeball, fecha_ahora, iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe))
            
            conn.commit()
            log.info(f"✅ Captura guardada: {pokemon_nombre.capitalize()} - User {user_id} - IVs ({iv_hp}/{iv_atk}/{iv_def}/{iv_spa}/{iv_spd}/{iv_spe}) - Shiny: {es_shiny}")
            
        except Exception as e:
            log.error(f"🚨 Error al guardar captura para user {user_id}, pokemon {pokemon_nombre}: {e}", exc_info=True)
            raise
        finally:
            if conn:
                conn.close()

def ejecutar_consulta(query_pg, query_sql, params):
    """Auxiliar para ejecutar consultas con diferentes sintaxis"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query_pg if DATABASE_URL else query_sql, params)
        res = cursor.fetchall()
        log.debug(f"✅ Consulta ejecutada: {len(res)} resultados")
        return res
    except Exception as e:
        log.error(f"🚨 Error al ejecutar consulta: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()

def obtener_capturas(user_id, solo_shiny=False):
    try:
        log.debug(f"🔍 Obteniendo capturas para user {user_id} (Solo shiny: {solo_shiny})")
        if DATABASE_URL:
            q = "SELECT pokemon_nombre FROM capturas WHERE user_id = %s" + (" AND es_shiny = 1" if solo_shiny else "")
            res = ejecutar_consulta(q, q.replace("%s", "?"), (str(user_id),))
        else:
            q = "SELECT pokemon_nombre FROM capturas WHERE user_id = ?" + (" AND es_shiny = 1" if solo_shiny else "")
            res = ejecutar_consulta(q.replace("%s", "?"), q, (user_id,))
        
        capturas = [fila[0] for fila in res]
        log.info(f"✅ Se obtuvieron {len(capturas)} capturas para user {user_id}")
        return capturas
    except Exception as e:
        log.error(f"🚨 Error al obtener capturas: {e}", exc_info=True)
        return []

def obtener_versiones_pokemon(user_id, nombre_pokemon):
    try:
        log.debug(f"🔍 Obteniendo versiones de {nombre_pokemon} para user {user_id}")
        if DATABASE_URL:
            res = ejecutar_consulta("SELECT es_shiny FROM capturas WHERE user_id = %s AND pokemon_nombre = %s", 
                                   "SELECT es_shiny FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", 
                                   (str(user_id), nombre_pokemon.lower()))
        else:
            res = ejecutar_consulta("SELECT es_shiny FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", 
                                   "SELECT es_shiny FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", 
                                   (user_id, nombre_pokemon.lower()))
        
        versiones = [fila[0] for fila in res]
        log.info(f"✅ Se obtuvieron {len(versiones)} versiones de {nombre_pokemon} para user {user_id}")
        return versiones
    except Exception as e:
        log.error(f"🚨 Error al obtener versiones de {nombre_pokemon}: {e}", exc_info=True)
        return []

def obtener_info_captura(user_id, nombre_pokemon):
    conn = None
    try:
        log.debug(f"🔍 Obteniendo info de captura: {nombre_pokemon} - User {user_id}")
        conn = get_connection()
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("SELECT MIN(fecha), COUNT(*) FROM capturas WHERE user_id = %s AND pokemon_nombre = %s", (str(user_id), nombre_pokemon.lower()))
        else:
            cursor.execute("SELECT MIN(fecha), COUNT(*) FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", (user_id, nombre_pokemon.lower()))
        
        res = cursor.fetchone()
        log.info(f"✅ Info de captura obtenida: {nombre_pokemon} - Cantidad: {res[1] if res else 0}")
        return res
    except Exception as e:
        log.error(f"🚨 Error al obtener info de captura: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()

def init_energia_db():
    try:
        log.info("📍 Inicializando tabla de energía...")
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
        log.info("✅ Tabla 'energia' creada/verificada")
    except Exception as e:
        log.error(f"🚨 Error al inicializar tabla de energía: {e}", exc_info=True)
        raise

def obtener_energia_db(user_id):
    conn = None
    try:
        log.debug(f"🔍 Obteniendo energía para user {user_id}")
        conn = get_connection()
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("SELECT intentos, ultima_recarga FROM energia WHERE user_id = %s", (str(user_id),))
        else:
            cursor.execute("SELECT intentos, ultima_recarga FROM energia WHERE user_id = ?", (user_id,))
        
        res = cursor.fetchone()
        if res:
            log.info(f"✅ Energía obtenida: User {user_id} - Intentos: {res[0]}")
        else:
            log.warning(f"⚠️ No se encontró energía para user {user_id}")
        return res
    except Exception as e:
        log.error(f"🚨 Error al obtener energía: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()

def actualizar_energia_db(user_id, intentos, ultima_recarga):
    conn = None
    try:
        log.debug(f"💾 Actualizando energía: User {user_id} - Intentos: {intentos}")
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
        log.info(f"✅ Energía actualizada: User {user_id} - Intentos: {intentos}")
    except Exception as e:
        log.error(f"🚨 Error al actualizar energía: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()

def obtener_lista_capturas(user_id):
    conn = None
    try:
        log.debug(f"🔍 Obteniendo lista de capturas únicas para user {user_id}")
        conn = get_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:
            cursor.execute("SELECT DISTINCT pokemon_nombre FROM capturas WHERE user_id = %s", (str(user_id),))
        else:
            cursor.execute("SELECT DISTINCT pokemon_nombre FROM capturas WHERE user_id = ?", (user_id,))
            
        res = [row[0] for row in cursor.fetchall()]
        log.info(f"✅ Lista de capturas obtenida: User {user_id} - {len(res)} pokémon únicos")
        return res
    except Exception as e:
        log.error(f"🚨 Error al obtener lista de capturas: {e}", exc_info=True)
        return []
    finally:
        if conn:
            conn.close()
