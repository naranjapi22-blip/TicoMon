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

            texto = narrador.narrar(
                escena
            )

            if callback:

                await callback(
                    escena,
                    texto
                )

            else:

                print("=" * 50)
                print(
                    f"Turno {escena['turno']}"
                )
                print(texto)
                print("=" * 50)
            print("ESCENA", escena["turno"])
            await asyncio.sleep(
                escena["pausa"]
            )