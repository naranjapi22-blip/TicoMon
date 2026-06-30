import asyncio


class PresentadorCombate:

    async def reproducir(
        self,
        escenas,
        narrador,
        callback=None,
    ):

        print("ESCENAS:", len(escenas))

        for escena in escenas:

            print("ESCENA", escena["turno"])

            for evento in escena["eventos"]:

                texto = narrador.narrar_evento(
                    evento
                )

                if callback:
                    await callback(
                        escena,
                        evento,
                        texto
                    )

                else:

                    print("=" * 50)
                    print(texto)
                    print("=" * 50)

                # Pausa corta entre eventos
                await asyncio.sleep(1.5)

            # Pausa de la escena (KO, cambio, victoria...)
            await asyncio.sleep(
                escena["pausa"]
            )