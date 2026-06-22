from combate_servicios import preparar_equipo_desde_capturas
from incursiones.incursion_manager import eliminar_incursion
from incursiones.vista_combate_incursion import VistaCombateIncursion
from incursiones.alpha_factory import crear_alpha
from incursiones.alphas import obtener_alpha_aleatorio

async def iniciar_incursion(
    raid,
    session,
    canal
):


    nombre_alpha = obtener_alpha_aleatorio()

    alpha = crear_alpha(nombre_alpha)

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