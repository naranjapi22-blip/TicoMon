# records.py

def verificar_y_actualizar_record(cursor, pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo, fecha_captura):
    UMBRAL_XXL = 1.2
    UMBRAL_XXS = 0.8
    tamano_nuevo = float(tamano_nuevo)
    

    cursor.execute("SELECT * FROM RECORDS_ESPECIE WHERE pokemon_nombre = %s", (pokemon_nombre,))
    row = cursor.fetchone()
    
    # Valores por defecto para comparación
    grande_actual = row[3] if row and row[3] is not None else 0.0
    pequeno_actual = row[7] if row and row[7] is not None else 99.0

    # 1. VERIFICACIÓN XXL (Grande)
    if tamano_nuevo >= UMBRAL_XXL and tamano_nuevo > grande_actual:
        if not row:
            # INSERT: Se agregó fecha_captura
            cursor.execute("""
                INSERT INTO RECORDS_ESPECIE (pokemon_nombre, id_pokemon_grande, user_id_grande, tamano_grande, fecha_grande)
                VALUES (%s, %s, %s, %s, %s)
            """, (pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo, fecha_captura))
        else:
            # UPDATE: Se agregó fecha_captura
            cursor.execute("""
                UPDATE RECORDS_ESPECIE 
                SET id_pokemon_grande = %s, user_id_grande = %s, tamano_grande = %s, fecha_grande = %s 
                WHERE pokemon_nombre = %s
            """, (id_nuevo, user_id_nuevo, tamano_nuevo, fecha_captura, pokemon_nombre))
        return "NUEVO_RECORD_GRANDE"

    # 2. VERIFICACIÓN XXS (Pequeño)
    elif tamano_nuevo <= UMBRAL_XXS and tamano_nuevo < pequeno_actual:
        if not row:
            # INSERT: Se agregó fecha_captura
            cursor.execute("""
                INSERT INTO RECORDS_ESPECIE (pokemon_nombre, id_pokemon_pequeno, user_id_pequeno, tamano_pequeno, fecha_pequeno)
                VALUES (%s, %s, %s, %s, %s)
            """, (pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo, fecha_captura))
        else:
            # UPDATE: Se agregó fecha_captura
            cursor.execute("""
                UPDATE RECORDS_ESPECIE 
                SET id_pokemon_pequeno = %s, user_id_pequeno = %s, tamano_pequeno = %s, fecha_pequeno = %s 
                WHERE pokemon_nombre = %s
            """, (id_nuevo, user_id_nuevo, tamano_nuevo, fecha_captura, pokemon_nombre))
        return "NUEVO_RECORD_PEQUENO"

    return None

def obtener_estado_record(cursor, pokemon_nombre, id_pokemon):
    """
    Retorna 'grande', 'pequeno' o None.
    """
    cursor.execute("""
        SELECT id_pokemon_grande, id_pokemon_pequeno 
        FROM RECORDS_ESPECIE 
        WHERE pokemon_nombre = %s
    """, (pokemon_nombre,))
    res = cursor.fetchone()
    
    if not res:
        return None
    
    if res[0] == id_pokemon:
        return "grande"
    if res[1] == id_pokemon:
        return "pequeno"
    
    return None
def recalcular_record_liberado(
    cursor,
    pokemon_nombre,
    captura_id,
    tipo_record,
    excluir_ids=None,
):
    excluir = {int(captura_id)}
    if excluir_ids:
        excluir.update(int(i) for i in excluir_ids)
    ph = ",".join(["%s"] * len(excluir))
    excluir_sql = f"AND id NOT IN ({ph})"

    if tipo_record == "XXL":

        cursor.execute(f"""
            SELECT
                id,
                user_id,
                tamano_factor,
                fecha
            FROM capturas
            WHERE pokemon_nombre = %s
              {excluir_sql}
              AND tamano_factor >= 1.2
            ORDER BY tamano_factor DESC
            LIMIT 1
        """, (
            pokemon_nombre,
            *excluir,
        ))

        nuevo = cursor.fetchone()

        if nuevo:

            cursor.execute("""
                UPDATE RECORDS_ESPECIE
                SET
                    id_pokemon_grande = %s,
                    user_id_grande = %s,
                    tamano_grande = %s,
                    fecha_grande = %s
                WHERE pokemon_nombre = %s
            """, (
                nuevo[0],
                nuevo[1],
                nuevo[2],
                nuevo[3],
                pokemon_nombre
            ))

        else:

            cursor.execute("""
                UPDATE RECORDS_ESPECIE
                SET
                    id_pokemon_grande = NULL,
                    user_id_grande = NULL,
                    tamano_grande = NULL,
                    fecha_grande = NULL
                WHERE pokemon_nombre = %s
            """, (
                pokemon_nombre,
            ))
    elif tipo_record == "XXS":

        cursor.execute(f"""
            SELECT
                id,
                user_id,
                tamano_factor,
                fecha
            FROM capturas
            WHERE pokemon_nombre = %s
              {excluir_sql}
              AND tamano_factor <= 0.8
            ORDER BY tamano_factor ASC
            LIMIT 1
        """, (
            pokemon_nombre,
            *excluir,
        ))

        nuevo = cursor.fetchone()

        if nuevo:

            cursor.execute("""
                UPDATE RECORDS_ESPECIE
                SET
                    id_pokemon_pequeno = %s,
                    user_id_pequeno = %s,
                    tamano_pequeno = %s,
                    fecha_pequeno = %s
                WHERE pokemon_nombre = %s
            """, (
                nuevo[0],
                nuevo[1],
                nuevo[2],
                nuevo[3],
                pokemon_nombre
            ))

        else:

            cursor.execute("""
                UPDATE RECORDS_ESPECIE
                SET
                    id_pokemon_pequeno = NULL,
                    user_id_pequeno = NULL,
                    tamano_pequeno = NULL,
                    fecha_pequeno = NULL
                WHERE pokemon_nombre = %s
            """, (
                pokemon_nombre,
            ))