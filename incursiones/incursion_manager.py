from incursiones.modelos import Incursion

incursiones_activas = {}


def crear_incursion(canal_id, alpha):
    raid = Incursion(canal_id, alpha)

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