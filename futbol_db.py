from database import get_connection


def crear_equipo_futbol(usuario_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO equipos_futbol (usuario_id)
            VALUES (%s)
            ON CONFLICT (usuario_id) DO NOTHING
        """, (usuario_id,))

        conn.commit()
        conn.close()

        print(f"✅ Equipo creado para {usuario_id}")

    except Exception as e:
        print(f"❌ Error: {e}")