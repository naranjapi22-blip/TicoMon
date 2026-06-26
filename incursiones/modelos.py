class Incursion:


    def __init__(self, canal_id, alpha):
        self.canal_id = canal_id
        self.alpha = alpha

        self.jugadores = []
        self.selecciones = {}

        self.estado = "esperando"

        self.mensaje_id = None
        self.selector_mensaje_id = None

        self.combate_iniciado = False
        self.timeout_sala = None
    @property
    def llena(self):
        return len(self.jugadores) >= 3

    @property
    def selecciones_completas(self):
        # 3 jugadores = 3 selecciones
        return len(self.selecciones) >= 3

    def agregar_jugador(self, user_id, nombre):
        if self.estado != "esperando":
            return False
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

    def seleccionar_pokemon(self, user_id, pokemon_id):
        self.selecciones[user_id] = pokemon_id
        print(
        f"SELECCIONES: {len(self.selecciones)}/3"
        )
        return True
    
    def cerrar(self):

        self.estado = "cerrada"

        if self.timeout_sala:
            self.timeout_sala.cancel()
            self.timeout_sala = None