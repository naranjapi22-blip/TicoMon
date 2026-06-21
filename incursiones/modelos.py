class Incursion:

    def __init__(self, canal_id, alpha):
        self.canal_id = canal_id
        self.alpha = alpha

        self.jugadores = []
        self.selecciones = {}

        self.estado = "esperando"

        self.mensaje_id = None
        self.selector_mensaje_id = None

    @property
    def llena(self):
        return len(self.jugadores) >= 3

    @property
    def selecciones_completas(self):
        return len(self.selecciones) >= 1  # prueba temporal

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

    def seleccionar_pokemon(
        self,
        user_id,
        pokemon_id
    ):

        self.selecciones.setdefault(
            user_id,
            []
        )

        self.selecciones[user_id].append(
            pokemon_id
        )