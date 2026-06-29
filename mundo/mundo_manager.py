import asyncio

from mundo.world import World


class MundoManager:

    def __init__(self):

        self.world = World()

        self.canal = None

        self.mensaje = None

    async def iniciar(self, canal):

        self.canal = canal

        self.world.iniciar()

        await self.publicar()

    async def publicar(self):

        gif = await self.world.generar_gif()

        self.mensaje = await self.canal.send(
            file=discord.File(
                gif,
                filename="mundo.gif"
            )
        )

    async def actualizar(self):

        self.world.iniciar()

        gif = await self.world.generar_gif()

        await self.mensaje.edit(
            attachments=[
                discord.File(
                    gif,
                    filename="mundo.gif"
                )
            ]
        )