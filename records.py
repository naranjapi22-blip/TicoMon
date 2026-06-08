# records.py

def verificar_y_actualizar_record(cursor, pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo):
    UMBRAL_XXL = 1.2
    UMBRAL_XXS = 0.8
    tamano_nuevo = float(tamano_nuevo)
    
    print(f"DEBUG: Verificando récord para {pokemon_nombre}. Tamaño: {tamano_nuevo}")

    cursor.execute("SELECT * FROM RECORDS_ESPECIE WHERE pokemon_nombre = %s", (pokemon_nombre,))
    row = cursor.fetchone()
    
    # Valores por defecto para comparación si no hay registro
    # Si no existe, usamos 0.0 para que cualquier XXL supere a 0
    # Y 99.0 para que cualquier XXS sea menor a 99
    grande_actual = row[3] if row and row[4] is not None else 0.0
    pequeno_actual = row[7] if row and row[8] is not None else 99.0

    # 1. VERIFICACIÓN XXL (Grande)
    if tamano_nuevo >= UMBRAL_XXL and tamano_nuevo > grande_actual:
        if not row:
            # INSERT si no existe registro
            cursor.execute("""
                INSERT INTO RECORDS_ESPECIE (pokemon_nombre, id_pokemon_grande, user_id_grande, tamano_grande, fecha_grande)
                VALUES (%s, %s, %s, %s, CURRENT_DATE)
            """, (pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo))
        else:
            # UPDATE si ya existe
            cursor.execute("""
                UPDATE RECORDS_ESPECIE 
                SET id_pokemon_grande = %s, user_id_grande = %s, tamano_grande = %s, fecha_grande = CURRENT_DATE 
                WHERE pokemon_nombre = %s
            """, (id_nuevo, user_id_nuevo, tamano_nuevo, pokemon_nombre))
        return "NUEVO_RECORD_GRANDE"

    # 2. VERIFICACIÓN XXS (Pequeño)
    elif tamano_nuevo <= UMBRAL_XXS and tamano_nuevo < pequeno_actual:
        if not row:
            # INSERT si no existe registro
            cursor.execute("""
                INSERT INTO RECORDS_ESPECIE (pokemon_nombre, id_pokemon_pequeno, user_id_pequeno, tamano_pequeno, fecha_pequeno)
                VALUES (%s, %s, %s, %s, CURRENT_DATE)
            """, (pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo))
        else:
            # UPDATE si ya existe
            cursor.execute("""
                UPDATE RECORDS_ESPECIE 
                SET id_pokemon_pequeno = %s, user_id_pequeno = %s, tamano_pequeno = %s, fecha_pequeno = CURRENT_DATE 
                WHERE pokemon_nombre = %s
            """, (id_nuevo, user_id_nuevo, tamano_nuevo, pokemon_nombre))
        return "NUEVO_RECORD_PEQUENO"

    return None

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