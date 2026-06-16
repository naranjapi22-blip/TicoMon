import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://neondb_owner:npg_p5iDhwvBjV0N@ep-withered-brook-aq3njbjm-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"


conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Cache para no consultar la misma cadena varias veces
processed_chains = set()


def get_tipo_primario(nombre):
    cur.execute("""
        SELECT tipos
        FROM pokemon_data
        WHERE nombre = %s
    """, (nombre,))
    
    row = cur.fetchone()

    if not row:
        return None

    return row["tipos"].split(",")[0]


def insertar(origen, destino, metodo):
    tipo = get_tipo_primario(destino)

    cur.execute("""
        INSERT INTO pokemon_evolutions
        (pokemon_nombre, evoluciona_a, metodo, tipo_caramelo)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """, (
        origen,
        destino,
        metodo,
        tipo
    ))


def recorrer(chain_node):
    origen = chain_node["species"]["name"]
    evoluciones = chain_node["evolves_to"]

    if not evoluciones:
        return

    metodo = "choice" if len(evoluciones) > 1 else None

    for evo in evoluciones:

        destino = evo["species"]["name"]

        trigger = None

        if evo["evolution_details"]:
            trigger = evo["evolution_details"][0]["trigger"]["name"]

        if trigger == "trade":
            metodo_final = "trade"
        elif metodo == "choice":
            metodo_final = "choice"
        else:
            metodo_final = "candy"

        insertar(
            origen,
            destino,
            metodo_final
        )

        recorrer(evo)


print("Leyendo Pokémon...")

cur.execute("""
    SELECT nombre
    FROM pokemon_data
""")

pokemons = cur.fetchall()

for p in pokemons:

    nombre = p["nombre"]

    try:

        species_url = f"https://pokeapi.co/api/v2/pokemon-species/{nombre}"
        species = requests.get(species_url, timeout=20).json()

        chain_url = species["evolution_chain"]["url"]

        if chain_url in processed_chains:
            continue

        processed_chains.add(chain_url)

        chain = requests.get(chain_url, timeout=20).json()

        recorrer(chain["chain"])

        print(f"✓ {nombre}")

    except Exception as e:
        print(f"✗ {nombre}: {e}")

conn.commit()

cur.close()
conn.close()
print(f"Cadenas procesadas: {len(processed_chains)}")
print("Importación completada.")