
import database

def get_evolutions(pokemon_nombre):

    conn = database.get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                evoluciona_a,
                metodo,
                tier
            FROM pokemon_evolutions
            WHERE pokemon_nombre = %s
            ORDER BY evoluciona_a
        """, (
            pokemon_nombre.lower(),
        ))

        return cursor.fetchall()

    finally:

        cursor.close()
        conn.close()

