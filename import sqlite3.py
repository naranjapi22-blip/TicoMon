import sqlite3

conn = sqlite3.connect('fumo_data.db')
cursor = conn.cursor()

# Ver los nombres de columnas
cursor.execute("PRAGMA table_info(capturas)")
columnas = [info[1] for info in cursor.fetchall()]
print(f"Columnas encontradas: {columnas}")

# Ver si hay datos en la columna fecha
cursor.execute("SELECT pokemon_nombre, fecha FROM capturas LIMIT 5")
datos = cursor.fetchall()
print(f"Primeros 5 registros: {datos}")

conn.close()