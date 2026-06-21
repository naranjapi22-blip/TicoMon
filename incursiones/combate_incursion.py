from combate import CombateSim
from combate_servicios import preparar_equipo_desde_capturas
from incursion_manager import eliminar_incursion

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
    "hp_max": 400,
    "movimiento": "dragonrush",
    "movimiento_nombre": "Dragon Rush",
    "id": 147,
    "shiny": False
}]


async def iniciar_incursion(
    raid,
    session
):

    print("=== RAID INICIADA ===")

    equipo_jugador = []

    for user_id, captura_id in raid.selecciones.items():

        equipo = await preparar_equipo_desde_capturas(
            session,
            user_id,
            [captura_id]
        )

        equipo_jugador.extend(equipo)

    print("EQUIPO JUGADOR:")
    print(equipo_jugador)

    sim = CombateSim(
        equipo_jugador,
        alpha
    )

    resultado = []

    while not sim.es_fin_del_juego():

        resultado.append(
            sim.ejecutar_ronda()
        )

    ganador = sim.es_fin_del_juego()

    if ganador == "Jugador 1":
        resultado.append(
            "\n🏆 ¡Victoria contra Alpha Dratini!"
        )
    else:
        resultado.append(
            "\n💀 Alpha Dratini ha derrotado al equipo."
        )

    texto_final = "\n".join(resultado)

    eliminar_incursion(
        raid.canal_id
    )

    return texto_final