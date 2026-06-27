from pathlib import Path
import csv
import requests
import time

# ============================================
# Configuración
# ============================================

CSV_FILE = Path("pokemon_data.csv")

OUTPUT_DIR = Path("gifs")

REGULAR_DIR = OUTPUT_DIR / "regular"
SHINY_DIR = OUTPUT_DIR / "shiny"
BACK_DIR = OUTPUT_DIR / "back"
BACK_SHINY_DIR = OUTPUT_DIR / "back_shiny"

BACK_DIR.mkdir(parents=True, exist_ok=True)
BACK_SHINY_DIR.mkdir(parents=True, exist_ok=True)
REGULAR_DIR.mkdir(parents=True, exist_ok=True)
SHINY_DIR.mkdir(parents=True, exist_ok=True)

BASE_REGULAR = "https://play.pokemonshowdown.com/sprites/ani"
BASE_SHINY = "https://play.pokemonshowdown.com/sprites/ani-shiny"
BASE_BACK = "https://play.pokemonshowdown.com/sprites/ani-back"
BASE_BACK_SHINY = "https://play.pokemonshowdown.com/sprites/ani-back-shiny"
TIMEOUT = 20
RETRIES = 3

errores = []


# ============================================
# Conversión PokéAPI -> Showdown
# ============================================

SPECIAL_NAMES = {

    "mr-mime": "mrmime",
    "mr-rime": "mrrime",

    "mime-jr": "mimejr",

    "type-null": "typenull",

    "jangmo-o": "jangmoo",
    "hakamo-o": "hakamoo",
    "kommo-o": "kommoo",

    "farfetchd": "farfetchd",
    "sirfetchd": "sirfetchd",

    "porygon-z": "porygonz",

    "ho-oh": "hooh",

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
    "iron-valiant": "ironvaliant"

}


def showdown_name(nombre):

    nombre = nombre.lower()

    # Excepciones conocidas
    SPECIAL_NAMES = {

        "mr-mime": "mrmime",
        "mr-rime": "mrrime",
        "mime-jr": "mimejr",

        "type-null": "typenull",

        "jangmo-o": "jangmoo",
        "hakamo-o": "hakamoo",
        "kommo-o": "kommoo",

        "farfetchd": "farfetchd",
        "sirfetchd": "sirfetchd",

        "porygon-z": "porygonz",

        "ho-oh": "hooh",
    }

    if nombre in SPECIAL_NAMES:
        return SPECIAL_NAMES[nombre]

    # ==========================================
    # Formas regionales
    # ==========================================

    for sufijo in (
        "-alola",
        "-galar",
        "-hisui",
        "-paldea",
    ):

        if nombre.endswith(sufijo):

            base = nombre[:-len(sufijo)]

            region = sufijo[1:]

            return f"{base}-{region}"

    # ==========================================
    # Tauros Paldea
    # ==========================================

    nombre = nombre.replace(
        "taurospaldeacombatbreed",
        "tauros-paldea-combat"
    )

    nombre = nombre.replace(
        "taurospaldeablazebreed",
        "tauros-paldea-blaze"
    )

    nombre = nombre.replace(
        "taurospaldeaaquabreed",
        "tauros-paldea-aqua"
    )

    # ==========================================
    # Iron Pokémon
    # ==========================================

    iron = {
        "irontreads": "iron-treads",
        "ironbundle": "iron-bundle",
        "ironhands": "iron-hands",
        "ironjugulis": "iron-jugulis",
        "ironmoth": "iron-moth",
        "ironthorns": "iron-thorns",
        "ironvaliant": "iron-valiant",
        "ironleaves": "iron-leaves",
        "ironboulder": "iron-boulder",
        "ironcrown": "iron-crown",
    }

    if nombre in iron:
        return iron[nombre]

    paradox = {
        "wochien": "wo-chien",
        "chienpao": "chien-pao",
        "tinglu": "ting-lu",
        "chiyu": "chi-yu",
        "greattusk": "great-tusk",
        "screamtail": "scream-tail",
        "brutebonnet": "brute-bonnet",
        "fluttermane": "flutter-mane",
        "slitherwing": "slither-wing",
        "sandyshocks": "sandy-shocks",
        "roaringmoon": "roaring-moon",
        "walkingwake": "walking-wake",
        "gougingfire": "gouging-fire",
        "ragingbolt": "raging-bolt",
    }

    if nombre in paradox:
        return paradox[nombre]

    # ==========================================

    nombre = nombre.replace(".", "")
    nombre = nombre.replace("'", "")
    nombre = nombre.replace(":", "")
    nombre = nombre.replace(" ", "")

    return nombre
# ============================================
# Descargar un GIF
# ============================================

def descargar(url, destino):

    if destino.exists():
        return True

    for intento in range(RETRIES):

        try:

            r = requests.get(
                url,
                timeout=TIMEOUT,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
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


# ============================================
# Leer CSV
# ============================================

pokemon = []

with open(CSV_FILE, encoding="utf-8-sig") as f:

    reader = csv.DictReader(f)

    for row in reader:

        pokemon.append({

            "id": str(row["pokeapi_id"]).strip(),

            "nombre": showdown_name(
                row["nombre"].strip()
            )

        })

print(f"Pokémon encontrados: {len(pokemon)}")


# ============================================
# Descargar todos
# ============================================

total = len(pokemon)

for i, p in enumerate(pokemon, start=1):

    nombre = p["nombre"]
    pokeapi_id = p["id"]

    print(f"[{i}/{total}] {nombre}")

    url_regular = f"{BASE_REGULAR}/{nombre}.gif"
    url_shiny = f"{BASE_SHINY}/{nombre}.gif"
    url_back = f"{BASE_BACK}/{nombre}.gif"
    url_back_shiny = f"{BASE_BACK_SHINY}/{nombre}.gif"

    ok_regular = descargar(
        url_regular,
        REGULAR_DIR / f"{pokeapi_id}.gif"
    )

    ok_shiny = descargar(
        url_shiny,
        SHINY_DIR / f"{pokeapi_id}.gif"
    )

    ok_back = descargar(
        url_back,
        BACK_DIR / f"{pokeapi_id}.gif"
    )

    ok_back_shiny = descargar(
        url_back_shiny,
        BACK_SHINY_DIR / f"{pokeapi_id}.gif"
    )

    if not ok_regular:
        errores.append(
            f"Regular: {pokeapi_id} {nombre}"
        )

    if not ok_shiny:
        errores.append(
            f"Shiny: {pokeapi_id} {nombre}"
        )

    if not ok_back:
        errores.append(
            f"Back: {pokeapi_id} {nombre}"
        )

    if not ok_back_shiny:
        errores.append(
            f"Back Shiny: {pokeapi_id} {nombre}"
        )
# ============================================
# Guardar errores
# ============================================

print("\n======================================")
print("DESCARGA TERMINADA")
print("======================================")

print(f"Pokémon procesados : {total}")

regular_ok = len(list(REGULAR_DIR.glob("*.gif")))
shiny_ok = len(list(SHINY_DIR.glob("*.gif")))

print(f"GIF Regular : {regular_ok}")
print(f"GIF Shiny   : {shiny_ok}")

if errores:

    print(f"\nErrores encontrados: {len(errores)}")

    with open("errores.txt", "w", encoding="utf-8") as f:

        for e in errores:
            f.write(e + "\n")

    print("Se creó errores.txt")

else:

    print("\nTodos los GIF fueron descargados correctamente.")