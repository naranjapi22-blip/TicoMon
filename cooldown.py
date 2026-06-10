import os
import sqlite3
import psycopg2
from datetime import datetime, timezone
from logger_config import log

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect('fumo_data.db')

def init_cooldown_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id BIGINT PRIMARY KEY,
            ultima_captura TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def verificar_cooldown(user_id):
    """Retorna True si puede capturar, False si está en cooldown."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute("SELECT ultima_captura FROM cooldowns WHERE user_id = %s", (user_id,))
    else:
        cursor.execute("SELECT ultima_captura FROM cooldowns WHERE user_id = ?", (user_id,))
    
    res = cursor.fetchone()
    conn.close()

    if res and res[0] is not None:
        valor = res[0]
        
        # 1. Estandarizamos el tipo de dato que viene de la DB
        if isinstance(valor, str):
            # SQLite devuelve el string ISO
            ultima_captura = datetime.fromisoformat(valor)
        else:
            # PostgreSQL devuelve un objeto datetime
            ultima_captura = valor

        # 2. Le inyectamos la zona UTC si la base de datos se la quitó
        if ultima_captura.tzinfo is None:
            ultima_captura = ultima_captura.replace(tzinfo=timezone.utc)
            
        ahora = datetime.now(timezone.utc)
        
        # 3. Restamos de forma segura (Ambos objetos son ahora UTC puros)
        if (ahora - ultima_captura).total_seconds() < 180:
            return False
            
    return True

def registrar_captura(user_id):
    """Guarda el momento actual como la última captura."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        ahora = datetime.now(timezone.utc)
        
        if DATABASE_URL:
            # Psycopg2 inserta mejor los objetos datetime directamente
            query = """
                INSERT INTO cooldowns (user_id, ultima_captura) VALUES (%s, %s)
                ON CONFLICT(user_id) DO UPDATE SET ultima_captura = EXCLUDED.ultima_captura
            """
            cursor.execute(query, (user_id, ahora))
        else:
            # SQLite necesita la representación en string
            cursor.execute("REPLACE INTO cooldowns (user_id, ultima_captura) VALUES (?, ?)", (user_id, ahora.isoformat()))
        
        conn.commit()
        log.info(f"⏱️ [Cooldown] Captura registrada para el usuario {user_id}.")

    except Exception as e:
        log.error(f"🚨 [ERROR Cooldown] No se pudo registrar captura del usuario {user_id}: {e}", exc_info=True)
        raise e
    finally:
        # Usamos finally para asegurar que la conexión siempre se cierra y no se queden "colgadas"
        if conn:
            try:
                conn.close()
            except:
                pass