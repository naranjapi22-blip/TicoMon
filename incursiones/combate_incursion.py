from combate_servicios import preparar_equipo_desde_capturas
from incursiones.incursion_manager import eliminar_incursion
from incursiones.vista_combate_incursion import VistaCombateIncursion
from incursiones.alpha_factory import crear_alpha


async def iniciar_incursion(
    raid,
    session,
    canal
):

    alpha = crear_alpha(
        raid.alpha
    )

    equipo_jugador = []

    print("SELECCIONES:", raid.selecciones)

    for user_id, captura_id in raid.selecciones.items():

        print(
            f"Usuario={user_id} Captura={captura_id}"
        )

        equipo = await preparar_equipo_desde_capturas(
            session,
            user_id,
            [captura_id]
        )

        print(
            "Equipo devuelto:",
            len(equipo)
        )

        for p in equipo:
            print(
                p["nombre"],
                p["id"],
                p["species_showdown"]
            )

        equipo_jugador.extend(equipo)

    print(
        "TOTAL POKEMON:",
        len(equipo_jugador)
    )

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