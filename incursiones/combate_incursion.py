from combate_servicios import preparar_equipo_desde_capturas
from incursiones.incursion_manager import eliminar_incursion
from incursiones.vista_combate_incursion import VistaCombateIncursion


alpha = [{
    "nombre": "Alpha Dratini",
    "species_showdown": "dratini",
    "nature_showdown": "hardy",
    "tipo": ["dragon"],
    "ivs": {
        "hp": 31,
        "atk": 31,
        "def": 31,
        "spa": 31,
        "spd": 31,
        "spe": 31
    },
    "atk": 120,
    "atk_esp": 120,
    "def": 120,
    "def_esp": 120,
    "spd": 60,
    "hp_max": 10000,
    "movimiento": "dragonrush",
    "movimiento_nombre": "Dragon Rush",
    "id": 147,
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