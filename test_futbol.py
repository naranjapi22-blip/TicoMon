import os
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_VWIP5pf7aGlw@ep-withered-brook-aq3njbjm-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
import time

from database import cargar_cache_pokemon
from futbol import precargar_capturas
from simulador_futbol import (
    simular_partido_usuarios,
    mostrar_partido,
    formatear_evento

)

cargar_cache_pokemon()
precargar_capturas()

usuario_a = 711104909461946398
usuario_b = 113100351531417600

resultado = simular_partido_usuarios(
    usuario_a,
    usuario_b
)

for evento in resultado["eventos"]:
    print(formatear_evento(evento))