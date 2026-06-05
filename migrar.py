import sqlite3
import psycopg2

# 1. Configuración de conexiones
sqlite_db = 'fumo_data.db'
pg_url = 'postgresql://neondb_owner:npg_imQxuH3TeK5p@ep-withered-brook-aq3njbjm.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require' # Pega aquí tu URL de Neon

# 2. Conectar
sqlite_conn = sqlite3.connect(sqlite_db)
pg_conn = psycopg2.connect(pg_url)

sqlite_cursor = sqlite_conn.cursor()
pg_cursor = pg_conn.cursor()

# Lista de tablas a migrar
tablas = ['capturas', 'canales_config', 'energia', 'iniciacion', 'perfiles', 'equipo']

for tabla in tablas:
    print(f"Migrando tabla: {tabla}...")
    sqlite_cursor.execute(f"SELECT * FROM {tabla}")
    datos = sqlite_cursor.fetchall()
    
    # Crear query de inserción dinámica
    columnas = [description[0] for description in sqlite_cursor.description]
    query = f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({', '.join(['%s']*len(columnas))})"
    
    for fila in datos:
        try:
            pg_cursor.execute(query, fila)
        except Exception as e:
            print(f"Error en {tabla}: {e}")

pg_conn.commit()
print("¡Migración completada con éxito!")

pg_cursor.close()
pg_conn.close()
sqlite_conn.close()