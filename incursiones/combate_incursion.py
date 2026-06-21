from combate import CombateSim


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


async def iniciar_incursion(raid):

    print("=== RAID INICIADA ===")

    print("Jugadores:")
    print(raid.jugadores)

    print("Selecciones:")
    print(raid.selecciones)