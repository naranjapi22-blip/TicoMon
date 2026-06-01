import sqlite3
import datetime

# Inicializar tabla de cooldown
def init_cooldown_db():
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id INTEGER PRIMARY KEY,
            ultima_captura TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def verificar_cooldown(user_id):
    """Retorna True si puede capturar, False si está en cooldown."""
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ultima_captura FROM cooldowns WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()

    if res:
        ultima_captura = datetime.datetime.fromisoformat(res[0])
        if (datetime.datetime.now() - ultima_captura).total_seconds() < 180: # 180 seg = 3 min
            return False
    return True

def registrar_captura(user_id):
    """Guarda el momento actual como la última captura."""
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO cooldowns (user_id, ultima_captura) VALUES (?, ?)", 
                   (user_id, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()