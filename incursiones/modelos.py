class Incursion:

    def __init__(self, canal_id, alpha):
        self.canal_id = canal_id
        self.alpha = alpha

        self.jugadores = []

        self.estado = "esperando"

        self.mensaje_id = None
    @property
    def llena(self):
        return len(self.jugadores) >= 3

    def agregar_jugador(self, user_id, nombre):

        for jugador in self.jugadores:
            if jugador["id"] == user_id:
                return False

        if self.llena:
            return False

        self.jugadores.append({
            "id": user_id,
            "nombre": nombre
        })

        return True