import os
import sqlite3
import psycopg2
import datetime
from logger_config import log


# Importamos la variable desde tu archivo de configuración o definimos aquí
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect('fumo_data.db')

def init_cooldown_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Usamos BIGINT para user_id (Discord IDs son grandes)
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
    
    # Sintaxis adaptada para Postgres (%s) y SQLite (?)
    if DATABASE_URL:
        cursor.execute("SELECT ultima_captura FROM cooldowns WHERE user_id = %s", (user_id,))
    else:
        cursor.execute("SELECT ultima_captura FROM cooldowns WHERE user_id = ?", (user_id,))
    
    res = cursor.fetchone()
    conn.close()

    if res:
        # Nota: Asegúrate de manejar si res[0] viene como cadena o datetime
        ultima_captura = datetime.datetime.fromisoformat(res[0]) if isinstance(res[0], str) else res[0]
        # Comparamos usando UTC para evitar problemas de zona horaria
        if (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - ultima_captura.replace(tzinfo=None)).total_seconds() < 180:
            return False
    return True

def registrar_captura(user_id):
    """Guarda el momento actual como la última captura."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        ahora = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        if DATABASE_URL:
            # Upsert en PostgreSQL
            query = """
                INSERT INTO cooldowns (user_id, ultima_captura) VALUES (%s, %s)
                ON CONFLICT(user_id) DO UPDATE SET ultima_captura = EXCLUDED.ultima_captura
            """
            cursor.execute(query, (str(user_id), ahora))
        else:
            # REPLACE en SQLite
            cursor.execute("REPLACE INTO cooldowns (user_id, ultima_captura) VALUES (?, ?)", (user_id, ahora))
        
        conn.commit()
        log.info(f"⏱️ [Cooldown] Captura registrada para el usuario {user_id} a las {ahora}.")
        conn.close()

    except Exception as e:
        log.error(f"🚨 [ERROR FATAL Cooldown] No se pudo registrar la última captura del usuario {user_id}. Error: {e}", exc_info=True)
        # Opcional: intentar cerrar la conexión si falló
        if 'conn' in locals() and conn:
            try:
                conn.close()
            except:
                pass
        raise e
        
    except Exception as e:
        # 1. Registramos el error en la consola
        log.error(f"⚠️ [Error Cooldown] No se pudo registrar el tiempo de espera para el usuario {user_id}. Error: {e}", exc_info=True)
        
        # 2. Medida de seguridad: cerramos la conexión si quedó abierta tras el fallo
        if 'conn' in locals() and conn:
            try:
                conn.close()
            except:
                pass