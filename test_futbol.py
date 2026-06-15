import os

os.environ["DATABASE_URL"] = ""


from futbol import *
from futbol_stats import*
from simulador_futbol import *



resultado = simular_partido_usuarios(
    711104909461946398,
    113100351531417600
)

print(
    mostrar_partido(resultado)
)