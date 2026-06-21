from combate import CombateSim
from combate_servicios import preparar_equipo_desde_capturas


alpha = [{
    "nombre": "Alpha Dratini",
    "hp_max": 400,
    "hp": 400,
    "atk": 120,
    "def": 120,
    "spa": 120,
    "spd": 120,
    "spe": 60,
    "id": 147
}]


async def iniciar_incursion(
    raid,
    session
):

    print("=== RAID INICIADA ===")

    for user_id, captura_id in raid.selecciones.items():

        equipo = await preparar_equipo_desde_capturas(
            session,
            user_id,
            [captura_id]
        )

        print("EQUIPO:")
        print(equipo)