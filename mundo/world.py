from datetime import date


class World:

    def __init__(self, guild_id):

        self.guild_id = guild_id

        self.fecha = date.today()

        self.objetivo = 100

        self.progreso = 0

        self.safaris_desbloqueados = 0

        self.safaris_utilizados = 0

    @property
    def porcentaje(self):

        if self.objetivo == 0:
            return 0

        return int(
            (self.progreso / self.objetivo) * 100
        )

    @property
    def safaris_disponibles(self):

        return max(
            0,
            self.safaris_desbloqueados -
            self.safaris_utilizados
        )

    def sumar_progreso(self, cantidad=1):

        self.progreso += cantidad

    def usar_safari(self):

        if self.safaris_disponibles > 0:

            self.safaris_utilizados += 1

            return True

        return False
    def obtener_objetivos_safari(self):

        objetivos = []

        for i in range(1, 6):

            objetivo = (
                self.objetivo * i
            ) // 5

            objetivos.append(objetivo)

        return objetivos