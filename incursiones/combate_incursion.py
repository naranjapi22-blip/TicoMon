from combate_servicios import preparar_equipo_desde_capturas
from incursiones.incursion_manager import eliminar_incursion
from incursiones.vista_combate_incursion import VistaCombateIncursion


alpha = [{
    "nombre": "Alpha Tyranitar",
    "species_showdown": "tyranitar",
    "nature_showdown": "hardy",
    "tipo": ["rock", "dark"],
    "ivs": {
        "hp": 31,
        "atk": 31,
        "def": 31,
        "spa": 31,
        "spd": 31,
        "spe": 31
    },
    "atk": 180,
    "atk_esp": 140,
    "def": 180,
    "def_esp": 180,
    "spd": 120,
    "hp_max": 15000,
    "movimiento": "stoneedge",
    "movimiento_nombre": "Stone Edge",
    "id": 248,
    "shiny": False
}]


async def iniciar_incursion(
    raid,
    session,
    canal
):

    equipo_jugador = []

    for user_id, captura_id in raid.selecciones.items():

        equipo = await preparar_equipo_desde_capturas(
            session,
            user_id,
            [captura_id]
        )

        equipo_jugador.extend(equipo)
    vista = VistaCombateIncursion(
        canal,
        session,
        equipo_jugador,
        alpha
    )

    await vista.iniciar()

    eliminar_incursion(
        raid.canal_id
    )