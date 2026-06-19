
from datetime import datetime, timezone
from logger_config import log
import database

def init_cooldown_db():
    conn = database.get_connection()
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

    conn = None

    try:
        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT ultima_captura FROM cooldowns WHERE user_id = %s",
            (user_id,)
        )

        res = cursor.fetchone()

    finally:
        if conn:
            try:
                cursor.close()
            except:
                pass

            conn.close()

    if not res or res[0] is None:
        return True

    ultima_captura = res[0]

    # Por si PostgreSQL devuelve datetime naive
    if ultima_captura.tzinfo is None:
        ultima_captura = ultima_captura.replace(
            tzinfo=timezone.utc
        )

    ahora = datetime.now(timezone.utc)

    return (ahora - ultima_captura).total_seconds() >= 180

def registrar_captura(user_id):
    conn = None

    try:
        conn = database.get_connection()
        cursor = conn.cursor()

        ahora = datetime.now(timezone.utc)

        query = """
            INSERT INTO cooldowns (user_id, ultima_captura)
            VALUES (%s, %s)
            ON CONFLICT(user_id)
            DO UPDATE SET ultima_captura = EXCLUDED.ultima_captura
        """

        cursor.execute(query, (user_id, ahora))

        conn.commit()

        log.info(
            f"⏱️ [Cooldown] Captura registrada para el usuario {user_id}."
        )

    except Exception as e:
        log.error(
            f"🚨 [ERROR Cooldown] No se pudo registrar captura del usuario {user_id}: {e}",
            exc_info=True
        )
        raise

    finally:
        if conn:
            try:
                cursor.close()
            except:
                pass

            try:
                conn.close()
            except:
                pass