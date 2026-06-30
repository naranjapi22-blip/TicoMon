import asyncio


class PresentadorCombate:

    async def reproducir(
        self,
        timeline,
        narrador,
        callback=None,
    ):

        historial = []

        print("EVENTOS:", len(timeline))

        for paso in timeline:

            evento = paso["evento"]

            texto = narrador.narrar_evento(
                evento
            )

            if texto:

                historial.append(texto)

                historial = historial[-4:]

            if callback:

                await callback(
                    paso,
                    historial
                )

            else:

                print("=" * 50)
                print("\n".join(historial))
                print("=" * 50)

            await asyncio.sleep(
                paso["pausa"]
            )