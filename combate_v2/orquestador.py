from .motor import MotorCombate
from .director import DirectorCombate
from .narrador import NarradorCombate
from .presentador import PresentadorCombate


class CombateV2:

    def __init__(self):

        self.motor = MotorCombate()
        self.director = DirectorCombate()
        self.narrador = NarradorCombate()
        self.presentador = PresentadorCombate()

    def crear_historia(
        self,
        eventos,
        snapshots,
    ):

        return self.director.analizar(
            eventos,
            snapshots,
        )
    async def reproducir(
        self,
        eventos,
        snapshots,
        callback=None,
    ):

        historia = self.crear_historia(
            eventos,
            snapshots,
        )
        print("EVENTOS:", len(eventos))
        print("HISTORIA:", len(historia))
        await self.presentador.reproducir(
            historia,
            self.narrador,
            callback,
        )