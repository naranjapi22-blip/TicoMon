
import combate_calc
import database
from mapeo_naturalezas import naturaleza_a_showdown
from poke_env.data import GenData

_GEN_DATA = GenData.from_gen(9)

_IVS_PERFECTOS = {"hp": 31, "atk": 31, "def": 31, "spa": 31, "spd": 31, "spe": 31}


async def obtener_datos_combate(session, nombre_pokemon, *, ivs=None, naturaleza=None, es_shiny=False):
    """
    Consulta PokeAPI y arma el dict de luchador con stats lvl 50 (poke-env).
    """
    url = f"https://pokeapi.co/api/v2/pokemon/{nombre_pokemon.lower()}"

    try:
        async with session.get(url) as response:
            if response.status != 200:
                print(
                    f"PokeAPI devolvió {response.status} para {nombre_pokemon}"
                )
                return None

            data = await response.json()

            print(
                nombre_pokemon,
                data["id"],
                data["name"]
            )

            stats = {
                s["stat"]["name"]: s["base_stat"]
                for s in data["stats"]
            }

            data = await response.json()
            stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
            tipos = [t["type"]["name"] for t in data["types"]]
            species_showdown = await combate_calc.resolver_especie_showdown(session, nombre_pokemon)

            iv_dict = ivs or dict(_IVS_PERFECTOS)
            nature_showdown = naturaleza_a_showdown(naturaleza, _GEN_DATA.natures)
            computed = combate_calc.stats_desde_teambuilder(species_showdown, iv_dict, naturaleza)

            moveset = combate_calc.generar_moveset_combate(
            species_showdown,
            computed
             )
            return {
                "nombre": nombre_pokemon.capitalize(),
                "species_showdown": species_showdown,
                "nature_showdown": nature_showdown,
                "tipo": tipos,
                "ivs": iv_dict,
                "atk": computed["atk"],
                "atk_esp": computed["spa"],
                "def": computed["def"],
                "def_esp": computed["spd"],
                "spd": computed["spe"],
                "hp_max": computed["hp"],
                "moveset": moveset,
                "id": data["id"],
                "shiny": es_shiny,
            }
    except Exception as e:

        import traceback

        print(f"Error al obtener datos de {nombre_pokemon}: {e}")

        traceback.print_exc()

        return {
            "nombre": nombre_pokemon.capitalize(),
            "species_showdown": nombre_pokemon.lower(),
            "nature_showdown": "hardy",
            "tipo": ["normal"],
            "ivs": dict(_IVS_PERFECTOS),
            "atk": 50,
            "atk_esp": 50,
            "def": 50,
            "def_esp": 50,
            "spd": 50,
            "hp_max": 100,
            "movimiento": "tackle",
            "movimiento_nombre": "Tackle",
            "shiny": es_shiny,
        }

async def _fighter_desde_fila(session, user_id, fila):
    (
        captura_id,
        nombre,
        es_shiny,
        naturaleza,
        iv_hp,
        iv_atk,
        iv_def,
        iv_spa,
        iv_spd,
        iv_spe,
    ) = fila
    ivs = {
        "hp": iv_hp,
        "atk": iv_atk,
        "def": iv_def,
        "spa": iv_spa,
        "spd": iv_spd,
        "spe": iv_spe,
    }
    datos = await obtener_datos_combate(
        session,
        nombre,
        ivs=ivs,
        naturaleza=naturaleza,
        es_shiny=bool(es_shiny),
    )

    print(
        "Pokemon:",
        nombre,
        "->",
        "OK" if datos else "NONE"
    )

    if datos:
        datos["captura_id"] = captura_id

    return datos


async def preparar_equipo_desde_capturas(session, user_id, captura_ids: list) -> list:
    """Prepara luchadores con IVs y naturaleza reales desde capturas."""
    mapa = database.obtener_capturas_por_ids(user_id, captura_ids)
    equipo = []
    for cid in captura_ids:
        fila = mapa.get(int(cid))
        if not fila:
            continue
        fighter = await _fighter_desde_fila(session, user_id, fila)
        if fighter:
            equipo.append(fighter)
    return equipo


async def preparar_equipos_completos(session, lista_nombres):
    """Lista de nombres con IVs perfectos (para !combate)."""
    equipo = []
    for nombre in lista_nombres:
        datos = await obtener_datos_combate(session, nombre)
        if datos:
            equipo.append(datos)
    return equipo
