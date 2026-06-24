from incursiones.modelos import Incursion
import asyncio
incursiones_activas = {}


def crear_incursion(canal_id, canal, alpha):
    raid = Incursion(canal_id, alpha)
    asyncio.create_task(timeout_incursion(raid, canal, 30))
    incursiones_activas[canal_id] = raid

    return raid


def obtener_incursion(canal_id):
    return incursiones_activas.get(canal_id)


def eliminar_incursion(canal_id):
    incursiones_activas.pop(canal_id, None)
    
def obtener_por_mensaje(mensaje_id):

    for raid in incursiones_activas.values():

        if raid.mensaje_id == mensaje_id:
            return raid

    return None
async def timeout_incursion(raid, canal, segundos=30):

    await asyncio.sleep(segundos)

    if raid.estado in (
        "esperando",
        "lista",
        "seleccion"
    ):

        raid.cerrar()

        eliminar_incursion(
            raid.canal_id
        )

        await canal.send(
            "❌ La incursión se cerró por inactividad."
        )