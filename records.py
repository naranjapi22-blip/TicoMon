# records.py

def verificar_y_actualizar_record(cursor, pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo):
    """Verifica y actualiza récords con umbrales de validación."""
    
    # 1. Definimos los umbrales para que solo los extremos entren al Salón de la Fama
    UMBRAL_XXL = 1.2
    UMBRAL_XXS = 0.8
    
    cursor.execute("SELECT * FROM RECORDS_ESPECIE WHERE pokemon_nombre = %s", (pokemon_nombre,))
    row = cursor.fetchone()
    
    if not row:
        # Primera captura: Insertamos. 
        # NOTA: Si no quieres que un Pokémon normal sea el primer récord, 
        # puedes añadir un IF aquí para no insertar si el tamaño es normal.
        cursor.execute("""
            INSERT INTO RECORDS_ESPECIE (
                pokemon_nombre, id_pokemon_grande, user_id_grande, tamano_grande, fecha_grande, 
                id_pokemon_pequeno, user_id_pequeno, tamano_pequeno, fecha_pequeno
            )
            VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, %s, %s, CURRENT_DATE)
        """, (pokemon_nombre, id_nuevo, user_id_nuevo, tamano_nuevo, id_nuevo, user_id_nuevo, tamano_nuevo))
        return "NUEVO_RECORD_ABS"

    tamano_grande = row[3]
    tamano_pequeno = row[7]

    # 2. Verificación XXL: Solo si es mayor al récord actual Y supera el umbral
    if tamano_nuevo > tamano_grande and tamano_nuevo >= UMBRAL_XXL:
        cursor.execute("""
            UPDATE RECORDS_ESPECIE 
            SET id_pokemon_grande = %s, user_id_grande = %s, tamano_grande = %s, fecha_grande = CURRENT_DATE 
            WHERE pokemon_nombre = %s
        """, (id_nuevo, user_id_nuevo, tamano_nuevo, pokemon_nombre))
        return "NUEVO_RECORD_GRANDE"

    # 3. Verificación XXS: Solo si es menor al récord actual Y es menor al umbral
    if tamano_nuevo < tamano_pequeno and tamano_nuevo <= UMBRAL_XXS:
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