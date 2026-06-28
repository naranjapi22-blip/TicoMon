from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pathlib import Path

DESTINO = Path("faltantes")
DESTINO.mkdir(exist_ok=True)

BASE = "https://play.pokemonshowdown.com/sprites/ani"

POKEMON = {
    32: "nidoranm",
    785: "tapukoko",
    786: "tapulele",
    787: "tapubulu",
    788: "tapufini",
    990: "irontreads",
    991: "ironbundle",
    992: "ironhands",
    993: "ironjugulis",
    994: "ironmoth",
    995: "ironthorns",
    1001: "wochien",
    1002: "chienpao",
    1003: "tinglu",
    1004: "chiyu",
    1006: "ironvaliant",
    1008: "miraidon",
    1010: "ironleaves",
    1014: "okidogi",
    1015: "munkidori",
    1016: "fezandipiti",
    1017: "ogerpon",
    1022: "ironboulder",
    1023: "ironcrown",
    1024: "terapagos",
    1025: "pecharunt",
    10168: "mrmimegalar",
    10250: "taurospaldeacombat",
    10251: "taurospaldeablaze",
    10252: "taurospaldeaaqua",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/137.0 Safari/537.36"
    ),
    "Referer": "https://play.pokemonshowdown.com/",
}

for dex, nombre in POKEMON.items():

    url = f"{BASE}/{nombre}.gif"
    destino = DESTINO / f"{dex}.gif"

    try:

        req = Request(
            url,
            headers=HEADERS
        )

        with urlopen(req) as response:

            datos = response.read()

        with open(destino, "wb") as f:

            f.write(datos)

        print(f"✔ {nombre}")

    except HTTPError as e:

        print(f"✘ {nombre} ({e.code})")

    except Exception as e:

        print(f"✘ {nombre} ({e})")