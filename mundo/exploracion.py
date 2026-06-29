from datetime import datetime
import time


class Exploracion:

    def __init__(self, jugador_id):

        self.jugador_id = jugador_id

        self.inicio = datetime.utcnow()

        self.estado = "lista"

        self.pokemon_seleccionado = None

        self.captura_en_progreso = False

        self.mensaje = None

        self.estado = "lista"

        self.inicio = time.time()