import os

os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_Hutvcn08ZSFA@ep-withered-brook-aq3njbjm-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

import database

pokemon = database.obtener_pokemon_local_nombre(
    "charizard"
)

print(pokemon)
