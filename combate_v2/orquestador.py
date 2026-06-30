from combate_v2.director import DirectorCombate
from combate_v2.narrador import NarradorCombate
from combate_v2.presentador import PresentadorCombate


class CombateV2:

    def __init__(self):

        self.director = DirectorCombate()
        self.narrador = NarradorCombate()
        self.presentador = PresentadorCombate()

    def crear_timeline(
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

        timeline = self.crear_timeline(
            eventos,
            snapshots,
        )

        await self.presentador.reproducir(
            timeline,
            self.narrador,
            callback,
        )