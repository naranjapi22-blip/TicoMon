# records.py

def verificar_y_actualizar_record(cursor, pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo):
    UMBRAL_XXL = 1.2
    UMBRAL_XXS = 0.8
    
    cursor.execute("SELECT * FROM RECORDS_ESPECIE WHERE pokemon_nombre = %s", (pokemon_nombre,))
    row = cursor.fetchone()
    
    # 1. CASO: NO EXISTE LA ESPECIE (Tu código original)
    if not row:
        if tamano_nuevo >= UMBRAL_XXL:
            # ... (tu insert original de XXL)
            return "NUEVO_RECORD_GRANDE"
        elif tamano_nuevo <= UMBRAL_XXS:
            # ... (tu insert original de XXS)
            return "NUEVO_RECORD_PEQUENO"
        return None

    # 2. CASO: LA ESPECIE YA EXISTE (Lo que te faltaba)
    # Suponiendo que row tiene (..., tamano_grande, ..., tamano_pequeno, ...)
    tamano_grande_actual = row[3] # Ajusta el índice según tu tabla
    tamano_pequeno_actual = row[7] # Ajusta el índice según tu tabla

    if tamano_nuevo >= UMBRAL_XXL and (tamano_grande_actual is None or tamano_nuevo > tamano_grande_actual):
        cursor.execute("UPDATE RECORDS_ESPECIE SET id_pokemon_grande=%s, user_id_grande=%s, tamano_grande=%s, fecha_grande=CURRENT_DATE WHERE pokemon_nombre=%s", 
                       (id_nuevo, user_id_nuevo, tamano_nuevo, pokemon_nombre))
        return "NUEVO_RECORD_GRANDE"

    elif tamano_nuevo <= UMBRAL_XXS and (tamano_pequeno_actual is None or tamano_nuevo < tamano_pequeno_actual):
        cursor.execute("UPDATE RECORDS_ESPECIE SET id_pokemon_pequeno=%s, user_id_pequeno=%s, tamano_pequeno=%s, fecha_pequeno=CURRENT_DATE WHERE pokemon_nombre=%s", 
                       (id_nuevo, user_id_nuevo, tamano_nuevo, pokemon_nombre))
        return "NUEVO_RECORD_PEQUENO"

    return None # Si no supera el récord, no retorna nada

    # Si ya existe el registro, actualizamos normalmente
    tamano_grande = row[3] if row[3] is not None else 0.0
    tamano_pequeno = row[7] if row[7] is not None else 99.0

    # Verificación XXL
    if tamano_nuevo >= UMBRAL_XXL and tamano_nuevo > tamano_grande:
        cursor.execute("""
            UPDATE RECORDS_ESPECIE 
            SET id_pokemon_grande = %s, user_id_grande = %s, tamano_grande = %s, fecha_grande = CURRENT_DATE 
            WHERE pokemon_nombre = %s
        """, (id_nuevo, user_id_nuevo, tamano_nuevo, pokemon_nombre))
        return "NUEVO_RECORD_GRANDE"

    # Verificación XXS
    if tamano_nuevo <= UMBRAL_XXS and tamano_nuevo < tamano_pequeno:
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