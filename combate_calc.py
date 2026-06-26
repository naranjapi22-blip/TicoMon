"""Cálculo de daño Gen 9 con poke-env (sin Node.js)."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass

from poke_env.battle import Battle
from poke_env.battle.move import Move
from poke_env.battle.pokemon import Pokemon
from poke_env.battle.pokemon_type import PokemonType
from poke_env.calc import damage_calc_gen9 as calc_gen9
from poke_env.data import GenData
from poke_env.data.normalize import to_id_str
from poke_env.teambuilder import TeambuilderPokemon

from logger_config import log
from mapeo_naturalezas import naturaleza_a_showdown

_GEN_DATA = GenData.from_gen(9)
_CALC_LOGGER = logging.getLogger("ticomon.combate_calc")
_SPECIES_CACHE: dict[str, str] = {}
# Necesitan un turno de carga
MOVIMIENTOS_CARGA = {
    "solarbeam",
    "solarblade",
    "skyattack",
    "meteorbeam",
    "electroshot",
    "dig",
    "dive",
    "fly",
    "bounce",
    "phantomforce",
    "shadowforce",
    "skullbash",
    "razorwind",
    "iceburn",
    "freezeshock",
}

# Obligan a recargar después
MOVIMIENTOS_RECARGA = {
    "hyperbeam",
    "gigaimpact",
    "blastburn",
    "frenzyplant",
    "hydrocannon",
    "rockwrecker",
    "roaroftime",
    "prismaticlaser",
    "eternabeam",
}

# Se autodestruyen o tienen un coste enorme
MOVIMIENTOS_SUICIDAS = {
    "explosion",
    "selfdestruct",
    "mistyexplosion",
    "steelbeam",
    "mindblown",
}

# Requieren una condición que no simulamos
MOVIMIENTOS_CONDICIONALES = {
    "dreameater",        # rival dormido
    "belch",             # haber comido baya
    "lastrespects",      # aliados muertos
    "steelroller",       # Terrain activo
    "focuspunch",        # no recibir daño
    "avalanche",         # recibir daño antes
    "revenge",           # recibir daño antes
    "payback",           # moverse último
    "retaliate",         # aliado debilitado
    "acrobatics",        # sin objeto
    "hex",               # rival con estado
    "venoshock",         # rival envenenado
    "brine",             # rival <50% HP
    "assurance",         # rival recibió daño
    "wakeupslap",        # rival dormido
    "smellingsalts",     # rival paralizado
    "weatherball",       # clima
    "terrainpulse",      # Terrain
    "expandingforce",    # Psychic Terrain
    "risingvoltage",     # Electric Terrain
    "grassyglide",       # Grassy Terrain
    "waterspout",
    "eruption",
    "reversal",
    "flail",
}

# Cambian estadísticas o preparan otro turno
MOVIMIENTOS_SETUP = {
    "swordsdance",
    "dragondance",
    "nastyplot",
    "bulkup",
    "calmmind",
    "irondefense",
    "amnesia",
    "agility",
    "rockpolish",
    "coil",
    "curse",
    "growth",
    "workup",
    "tailglow",
    "shellsmash",
    "quiverdance",
    "shiftgear",
    "honeclaws",
    "geomancy",
}

# Climas
MOVIMIENTOS_CLIMA = {
    "sunnyday",
    "raindance",
    "sandstorm",
    "hail",
    "snowscape",
}

# Terrains
MOVIMIENTOS_TERRAIN = {
    "electricterrain",
    "grassyterrain",
    "mistyterrain",
    "psychicterrain",
}

# Trampas
MOVIMIENTOS_HAZARDS = {
    "stealthrock",
    "spikes",
    "toxicspikes",
    "stickyweb",
}

# Recuperación
MOVIMIENTOS_RECUPERACION = {
    "recover",
    "softboiled",
    "roost",
    "slackoff",
    "healorder",
    "milkdrink",
    "moonlight",
    "morningsun",
    "synthesis",
    "shoreup",
    "strengthsap",
}

# Forzar cambio (no sirve en tu motor)
MOVIMIENTOS_CAMBIO = {
    "roar",
    "whirlwind",
    "dragontail",
    "circlethrow",
}

# Movimientos bloqueados por comportamiento extraño
MOVIMIENTOS_ESPECIALES = {
    "metronome",
    "assist",
    "copycat",
    "mirrormove",
    "mefirst",
    "sleeptalk",
    "naturepower",
    "celebrate",
    "holdhands",
    "happyhour",
    "futuresight"
    "waterspout",
    "roaroftime",
    "gigaimpact",
    "dragonascent",
    "psychoboost",
}
MOVIMIENTOS_EXCLUIDOS = (
    MOVIMIENTOS_CARGA
    | MOVIMIENTOS_RECARGA
    | MOVIMIENTOS_SUICIDAS
    | MOVIMIENTOS_CONDICIONALES
    | MOVIMIENTOS_SETUP
    | MOVIMIENTOS_CLIMA
    | MOVIMIENTOS_TERRAIN
    | MOVIMIENTOS_HAZARDS
    | MOVIMIENTOS_RECUPERACION
    | MOVIMIENTOS_CAMBIO
    | MOVIMIENTOS_ESPECIALES
)
@dataclass
class ResultadoDano:
    dano: int
    mensaje: str
    fallo: bool = False
    critico: bool = False

def _ivs_lista(fighter: dict) -> list[int]:
    ivs = fighter.get("ivs")
    if ivs:
        return [
            ivs.get("hp", 31),
            ivs.get("atk", 31),
            ivs.get("def", 31),
            ivs.get("spa", 31),
            ivs.get("spd", 31),
            ivs.get("spe", 31),
        ]
    return [31, 31, 31, 31, 31, 31]


def _crear_pokemon_showdown(fighter: dict) -> Pokemon:
    species = fighter["species_showdown"]
    nature = fighter.get("nature_showdown") or "hardy"
    move = fighter.get("movimiento")
    moves = [move] if move else []

    tb = TeambuilderPokemon(
        species=species,
        level=50,
        nature=nature.capitalize(),
        ivs=_ivs_lista(fighter),
        moves=moves,
        shiny=bool(fighter.get("shiny")),
    )
    return Pokemon(gen=9, teambuilder=tb)


def _identificador_batalla(fighter: dict, rol: str) -> str:
    return f"{rol}: {fighter['species_showdown'].capitalize()}"


def _contexto_batalla(atacante: dict, defensor: dict) -> Battle:
    battle = Battle("calc", "p1", _CALC_LOGGER, 9)
    battle._player_role = "p1"
    battle._opponent_role = "p2"

    id1 = _identificador_batalla(atacante, "p1")
    id2 = _identificador_batalla(defensor, "p2")
    battle._team = {id1: _crear_pokemon_showdown(atacante)}
    battle._opponent_team = {id2: _crear_pokemon_showdown(defensor)}
    return battle


def elegir_movimiento_automatico(
    species_showdown: str,
    stats: dict[str, int]
) -> tuple[str, str]:

    species_id = to_id_str(species_showdown)

    entry = _GEN_DATA.learnset.get(species_id)

    if not entry:
        return "tackle", "Tackle"

    learnset = entry.get("learnset", {})

    dex = _GEN_DATA.pokedex.get(
        species_id,
        {}
    )

    tipos = dex.get("types", [])

    prefer_physical = (
        stats.get("atk", 0)
        >=
        stats.get("spa", 0)
    )

    mejor = None

    for move_id in learnset:

        data = _GEN_DATA.moves.get(move_id)

        if not movimiento_valido_ia(
            move_id,
            data,
        ):
            continue

        bp = data.get("basePower") or 0
        accuracy = data.get("accuracy") or 100

        es_fisico = (
            data.get("category")
            == "Physical"
        )

        cat_bonus = (
            15
            if prefer_physical == es_fisico
            else 0
        )

        stab = (
            40
            if data.get("type") in tipos
            else 0
        )
        penalizacion = 0

        if move_id in {
            "dracometeor",
            "leafstorm",
            "overheat",
            "psychoboost",
        }:
            penalizacion += 20

        if move_id in {
            "closecombat",
            "superpower",
            "headlongrush",
        }:
            penalizacion += 15

        if move_id in {
            "bravebird",
            "flareblitz",
            "woodhammer",
            "doubleedge",
            "volttackle",
            "wavecrash",
        }:
            penalizacion += 10
        puntaje = (
            bp
            + stab
            + cat_bonus
            + min(accuracy, 100) // 10
            - penalizacion
        )
        nombre = data.get(
            "name",
            move_id
        )

        candidato = (
            puntaje,
            move_id,
            nombre
        )

        if (
            mejor is None
            or candidato[0] > mejor[0]
        ):
            mejor = candidato

    if mejor:
        return mejor[1], mejor[2]

    return "tackle", "Tackle"
def elegir_movimiento_alpha(
    species_showdown: str,
    stats: dict[str, int]
) -> tuple[str, str]:


    species_id = to_id_str(species_showdown)

    entry = _GEN_DATA.learnset.get(species_id)

    if not entry:
        return "tackle", "Tackle"

    learnset = entry.get("learnset", {})

    dex = _GEN_DATA.pokedex.get(
        species_id,
        {}
    )

    tipos = dex.get("types", [])

    prefer_physical = (
        stats.get("atk", 0)
        >=
        stats.get("spa", 0)
    )

    candidatos = []

    for move_id in learnset:

        data = _GEN_DATA.moves.get(move_id)

        if not movimiento_valido_ia(
            move_id,
            data,
        ):
            continue

        bp = data.get("basePower") or 0
        accuracy = data.get("accuracy") or 100

        es_fisico = (
            data.get("category")
            == "Physical"
        )

        cat_bonus = (
            15
            if prefer_physical == es_fisico
            else 0
        )

        stab = (
            40
            if data.get("type") in tipos
            else 0
        )
        penalizacion = 0

        if move_id in {
            "dracometeor",
            "leafstorm",
            "overheat",
            "psychoboost",
        }:
            penalizacion += 20

        if move_id in {
            "closecombat",
            "superpower",
            "headlongrush",
        }:
            penalizacion += 15

        if move_id in {
            "bravebird",
            "flareblitz",
            "woodhammer",
            "doubleedge",
            "volttackle",
            "wavecrash",
        }:
            penalizacion += 10
        puntaje = (
            bp
            + stab
            + cat_bonus
            + min(accuracy, 100) // 10
            - penalizacion
        )

        nombre = data.get(
            "name",
            move_id
        )

        candidatos.append(
            (
                puntaje,
                move_id,
                nombre
            )
        )

    if not candidatos:
        return "tackle", "Tackle"

    candidatos.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    top = candidatos[:3]

    pesos = [70, 20, 10][:len(top)]

    elegido = random.choices(
        top,
        weights=pesos,
        k=1
    )[0]

    return elegido[1], elegido[2]
def stats_desde_teambuilder(
    species_showdown: str,
    ivs: dict[str, int],
    naturaleza_es: str | None,
) -> dict[str, int]:
    nature = naturaleza_a_showdown(naturaleza_es, _GEN_DATA.natures)
    iv_list = [
        ivs.get("hp", 31),
        ivs.get("atk", 31),
        ivs.get("def", 31),
        ivs.get("spa", 31),
        ivs.get("spd", 31),
        ivs.get("spe", 31),
    ]
    tb = TeambuilderPokemon(
        species=species_showdown,
        level=50,
        nature=nature.capitalize(),
        ivs=iv_list,
    )
    mon = Pokemon(gen=9, teambuilder=tb)
    return dict(mon.stats)


async def resolver_especie_showdown(session, nombre_local: str) -> str:
    """Resuelve nombre de captura (es/en) al id de especie de Showdown."""
    clave = nombre_local.lower().strip()
    if clave in _SPECIES_CACHE:
        return _SPECIES_CACHE[clave]

    if clave in _GEN_DATA.pokedex:
        _SPECIES_CACHE[clave] = clave
        return clave

    import aiohttp

    try:
        async with session.get(f"https://pokeapi.co/api/v2/pokemon/{clave}") as resp:
            if resp.status != 200:
                _SPECIES_CACHE[clave] = clave
                return clave
            data = await resp.json()

        species_url = data["species"]["url"]
        async with session.get(species_url) as resp:
            if resp.status != 200:
                _SPECIES_CACHE[clave] = clave
                return clave
            species_data = await resp.json()

        for entry in species_data.get("names", []):
            if entry.get("language", {}).get("name") == "en":
                en = to_id_str(entry["name"])
                _SPECIES_CACHE[clave] = en
                return en
    except (aiohttp.ClientError, KeyError, TypeError) as e:
        log.warning(f"No se pudo resolver especie Showdown para {nombre_local}: {e}")

    _SPECIES_CACHE[clave] = clave
    return clave


def _etiqueta_efectividad(move: Move, defensor: dict) -> str:
    move_type = move.type
    if move_type is None:
        return ""

    tipos_def = defensor.get("tipo") or []
    if not tipos_def:
        return ""

    mult = 1.0
    for tipo_nombre in tipos_def:
        try:
            tipo_def = PokemonType.from_name(tipo_nombre)
        except (ValueError, KeyError):
            continue
        mult *= calc_gen9.get_move_effectiveness(move, move_type, tipo_def)

    if mult >= 2:
        return " ¡Es súper efectivo!"
    if 0 < mult <= 0.5:
        return " No es muy efectivo..."
    if mult == 0:
        return " No afecta al objetivo..."
    return ""


def calcular_dano(atacante: dict, defensor: dict) -> ResultadoDano:
    """Calcula daño de un turno usando poke-env. Fallback a fórmula simple si falla."""
    try:
        return _calcular_dano_showdown(atacante, defensor)
    except Exception as e:
        log.warning(f"Fallback de daño para {atacante.get('nombre')}: {e}", exc_info=True)
        return _calcular_dano_fallback(atacante, defensor)


def _calcular_dano_showdown(atacante: dict, defensor: dict) -> ResultadoDano:
    move_id = atacante.get("movimiento", "tackle")
    move = Move(move_id, gen=9)
    move_nombre = atacante.get("movimiento_nombre") or move.entry.get("name", move_id)

    battle = _contexto_batalla(atacante, defensor)
    id_atk = _identificador_batalla(atacante, "p1")
    id_def = _identificador_batalla(defensor, "p2")

    accuracy = move.accuracy
    acc_pct = 100
    if accuracy is not None:
        acc_pct = accuracy * 100 if accuracy <= 1 else accuracy
    if acc_pct < 100 and random.randint(1, 100) > acc_pct:
        return ResultadoDano(
            0,
            f"💨 ¡{atacante['nombre']} usó **{move_nombre}** pero falló!",
            fallo=True,
        )

    es_critico = random.randint(1, 24) == 1
    print("ATACANTE:", atacante["nombre"])
    print("DEFENSOR:", defensor["nombre"])
    print("MOVE:", move_id)
    print("TIPOS DEF:", defensor.get("tipo"))
    dano_min, dano_max = calc_gen9.calculate_damage(id_atk, id_def, move, battle, is_critical=es_critico)
    print("DAÑO:", dano_min, dano_max)
    if dano_max <= 0:
        return ResultadoDano(
            0,
            f"💨 ¡{atacante['nombre']} usó **{move_nombre}** pero no hizo daño!",
            fallo=True,
        )

    dano = random.randint(int(dano_min), int(dano_max)) if dano_max > dano_min else int(dano_max)
    dano = max(0, dano)

    prefijo = "💥 ¡GOLPE CRÍTICO!" if es_critico else f"⚡ **{move_nombre}**"
    sufijo = _etiqueta_efectividad(move, defensor)
    mensaje = f"{prefijo} **{atacante['nombre']}** causa {dano} HP.{sufijo}"

    return ResultadoDano(dano=dano, mensaje=mensaje, critico=es_critico)


def _calcular_dano_fallback(atacante: dict, defensor: dict) -> ResultadoDano:
    stat_ofensivo = max(atacante.get("atk", 50), atacante.get("atk_esp", 50))
    def_stat = defensor.get("def", 50)
    dano = max(3, int((stat_ofensivo / (def_stat + 15)) * 25 * random.uniform(0.85, 1.0)))
    mensaje = f"✨ **{atacante['nombre']}** causa {dano} HP."
    return ResultadoDano(dano=dano, mensaje=mensaje)
def movimiento_valido_ia(
    move_id: str,
    data: dict,
) -> bool:

    if move_id in MOVIMIENTOS_EXCLUIDOS:
        return False

    if not data:
        return False

    if data.get("category") == "Status":
        return False

    if (data.get("basePower") or 0) <= 0:
        return False

    accuracy = data.get("accuracy") or 100

    if accuracy < 80:
        return False

    flags = data.get("flags", {})

    if (
        flags.get("charge")
        or flags.get("recharge")
        or flags.get("mustcharge")
    ):
        return False

    return True