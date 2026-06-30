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
                if evento.tipo == "ataque":
                    await asyncio.sleep(2)

                elif evento.tipo == "cambio":
                    await asyncio.sleep(2.5)

                elif evento.tipo == "victoria":
                    await asyncio.sleep(5)

                else:
                    await asyncio.sleep(2)
