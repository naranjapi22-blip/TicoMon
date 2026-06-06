# records.py

def verificar_y_actualizar_record(cursor, pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo):
    """Verifica y actualiza récords usando el cursor de la conexión actual."""
    
    # Obtenemos el registro actual con descripción de columnas para mapear a diccionario
    cursor.execute("SELECT * FROM RECORDS_ESPECIE WHERE pokemon_nombre = %s", (pokemon_nombre,))
    row = cursor.fetchone()
    
    if not row:
        # PRIMERA CAPTURA: Insertamos
        cursor.execute("""
            INSERT INTO RECORDS_ESPECIE (
                pokemon_nombre, id_pokemon_grande, user_id_grande, tamano_grande, fecha_grande, 
                id_pokemon_pequeno, user_id_pequeno, tamano_pequeno, fecha_pequeno
            )
            VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, %s, %s, CURRENT_DATE)
        """, (pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo, id_nuevo, user_id_nuevo, tamano_nuevo))
        return "NUEVO_RECORD_ABS"

    # Si usas cursor normal, los datos vienen en una tupla. 
    # Mapeo según tu tabla (ajusta si el orden de columnas es distinto):
    # 0: nombre, 1: id_g, 2: user_g, 3: tam_g, 4: fecha_g, 5: id_p, 6: user_p, 7: tam_p, 8: fecha_p
    tamano_grande = row[3]
    tamano_pequeno = row[7]

    # Verificación de Grande (XXL)
    if tamano_nuevo > tamano_grande:
        cursor.execute("""
            UPDATE RECORDS_ESPECIE 
            SET id_pokemon_grande = %s, user_id_grande = %s, tamano_grande = %s, fecha_grande = CURRENT_DATE 
            WHERE pokemon_nombre = %s
        """, (id_nuevo, user_id_nuevo, tamano_nuevo, pokemon_nombre))
        return "NUEVO_RECORD_GRANDE"

    # Verificación de Pequeño (XXS)
    if tamano_nuevo < tamano_pequeno:
        cursor.execute("""
            UPDATE RECORDS_ESPECIE 
            SET id_pokemon_pequeno = %s, user_id_pequeno = %s, tamano_pequeno = %s, fecha_pequeno = CURRENT_DATE 
            WHERE pokemon_nombre = %s
        """, (id_nuevo, user_id_nuevo, tamano_nuevo, pokemon_nombre))
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