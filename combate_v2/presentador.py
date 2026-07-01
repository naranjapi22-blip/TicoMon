import asyncio


class PresentadorCombate:

    async def reproducir(
        self,
        pasos,
        narrador,
        callback=None,
    ):

        historial = []

        print("PASOS:", len(pasos))

        for paso in pasos:

            evento = paso.evento

            texto = narrador.narrar_evento(
                evento
            )

            if not texto:
                continue

            historial.append(texto)

            historial = historial[-3:]

            if callback:

                await callback(
                    paso,
                    historial.copy()
                )

            else:

                print("=" * 50)
                print("\n".join(historial))
                print("=" * 50)

            await asyncio.sleep(
                paso.pausa
            )