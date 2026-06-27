from pathlib import Path
import requests
import time
import csv
# ==========================================================
# CONFIGURACIÓN
# ==========================================================

TOTAL_POKEMON = 1025

TIMEOUT = 20
RETRIES = 3

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASES = {

    "regular":
        "https://play.pokemonshowdown.com/sprites/ani",

    "shiny":
        "https://play.pokemonshowdown.com/sprites/ani-shiny",

    "back":
        "https://play.pokemonshowdown.com/sprites/ani-back",

    "back_shiny":
        "https://play.pokemonshowdown.com/sprites/ani-back-shiny",

}
OUTPUT = Path("gifs")

CARPETAS = {}

for nombre in BASES:

    carpeta = OUTPUT / nombre

    carpeta.mkdir(
        parents=True,
        exist_ok=True
    )

    CARPETAS[nombre] = carpeta

errores = []
CSV_FILE = Path("pokemon_data.csv")

pokemon = []

with open(CSV_FILE, encoding="utf-8-sig") as f:

    reader = csv.DictReader(f)

    for row in reader:

        pokemon.append({

            "id": int(row["pokeapi_id"]),

            "nombre": row["nombre"].strip().lower()

        })

print(f"Pokémon cargados: {len(pokemon)}")
# ==========================================================
# HTTP
# ==========================================================

def obtener_json(url):

    r = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT
    )

    r.raise_for_status()

    return r.json()


def descargar(url, destino):

    if destino.exists():
        return True

    for _ in range(RETRIES):

        try:

            r = requests.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT
            )

            if r.status_code == 200:

                with open(destino, "wb") as f:
                    f.write(r.content)

                return True

            if r.status_code == 404:

                return False

        except Exception:

            pass

        time.sleep(1)

    return False
# ==========================================================
# POKÉAPI -> SHOWDOWN
# ==========================================================

SPECIAL = {

    "mr-mime": "mrmime",
    "mr-rime": "mrrime",
    "mime-jr": "mimejr",

    "type-null": "typenull",

    "ho-oh": "hooh",

    "porygon-z": "porygonz",

    "jangmo-o": "jangmoo",
    "hakamo-o": "hakamoo",
    "kommo-o": "kommoo",

    "wo-chien": "wochien",
    "chien-pao": "chienpao",
    "ting-lu": "tinglu",
    "chi-yu": "chiyu",

    "great-tusk": "greattusk",
    "scream-tail": "screamtail",
    "brute-bonnet": "brutebonnet",
    "flutter-mane": "fluttermane",
    "slither-wing": "slitherwing",
    "sandy-shocks": "sandyshocks",

    "iron-treads": "irontreads",
    "iron-bundle": "ironbundle",
    "iron-hands": "ironhands",
    "iron-jugulis": "ironjugulis",
    "iron-moth": "ironmoth",
    "iron-thorns": "ironthorns",
    "roaring-moon": "roaringmoon",
    "iron-valiant": "ironvaliant",

    "walking-wake": "walkingwake",
    "gouging-fire": "gougingfire",
    "raging-bolt": "ragingbolt",
    "iron-boulder": "ironboulder",
    "iron-crown": "ironcrown",
    "iron-leaves": "ironleaves",

}

def showdown_name(nombre):

    nombre = nombre.lower()

    if nombre in SPECIAL:
        return SPECIAL[nombre]

    return nombre

# ==========================================================
# DESCARGAR POKÉMON
# ==========================================================

def descargar_pokemon(pokemon):

    poke_id = pokemon["id"]

    nombre = showdown_name(
        pokemon["nombre"]
    )

    print(
        f"[{poke_id}] {nombre}"
    )

    for carpeta, base in BASES.items():

        url = (
            f"{base}/{nombre}.gif"
        )

        destino = (
            CARPETAS[carpeta] /
            f"{poke_id}.gif"
        )

        ok = descargar(
            url,
            destino
        )

        if ok:

            print(
                f"   ✓ {carpeta}"
            )

        else:

            print(
                f"   ✗ {carpeta}"
            )

            errores.append(url)
# ==========================================================
# MAIN
# ==========================================================

print("=" * 60)
print("DESCARGANDO GIFS")
print("=" * 60)

for poke in pokemon:

    descargar_pokemon(poke)
print()
print("=" * 60)
print("RESUMEN")

print(f"Errores: {len(errores)}")

if errores:

    with open(
        "errores.txt",
        "w",
        encoding="utf-8"
    ) as f:

        for e in errores:
            f.write(f"{e}\n")

    print("Se creó errores.txt")

print("Proceso terminado.")

for p in pokemon:
    if "-" in p["nombre"]:
        print(p["nombre"])