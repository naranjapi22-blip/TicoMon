from combate_v2.narrador import NarradorCombate
from combate_v2.presentador import PresentadorCombate


class CombateV2:

    def __init__(self):

        self.narrador = NarradorCombate()
        self.presentador = PresentadorCombate()

    async def reproducir(
        self,
        pasos,
        callback=None,
    ):

        await self.presentador.reproducir(

            pasos,

            self.narrador,

            callback,

        )