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

    def agregar_jugador(self, user_id):
        if user_id in self.jugadores:
            return False

        if self.llena:
            return False

        self.jugadores.append(user_id)
        return True