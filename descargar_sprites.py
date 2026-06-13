import os
import requests

os.makedirs("sprites/shiny", exist_ok=True)

TOTAL_POKEMON = 1025

for pokemon_id in range(1, TOTAL_POKEMON + 1):

    ruta = f"sprites/shiny/{pokemon_id}.png"

    if os.path.exists(ruta):
        continue

    url = (
        "https://raw.githubusercontent.com/"
        "PokeAPI/sprites/master/"
        f"sprites/pokemon/shiny/{pokemon_id}.png"
    )

    try:

        r = requests.get(
            url,
            timeout=10
        )

        if r.status_code != 200:
            print(
                f"ERROR {pokemon_id}"
            )
            continue

        with open(
            ruta,
            "wb"
        ) as f:

            f.write(r.content)

        print(
            f"OK {pokemon_id}"
        )

    except Exception as e:

        print(
            f"FALLO {pokemon_id}: {e}"
        )

print()
print("✅ DESCARGA SHINY COMPLETADA")