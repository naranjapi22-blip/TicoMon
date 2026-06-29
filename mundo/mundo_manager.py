import discord

from mundo.world import World


class MundoManager:

    def __init__(self):

        self.world = World()

        self.canal = None

        self.mensaje = None

    async def iniciar(self):

        self.world.iniciar()

    async def obtener_gif(self):

        return await self.world.generar_gif()

    async def publicar(self, canal):

        self.canal = canal

        gif = await self.obtener_gif()

        self.mensaje = await canal.send(
            file=discord.File(
                gif,
                filename="mundo.gif"
            )
        )

    async def actualizar(self):

        self.world.iniciar()

        gif = await self.obtener_gif()

        if self.mensaje is None:
            return

        await self.mensaje.edit(
            attachments=[
                discord.File(
                    gif,
                    filename="mundo.gif"
                )
            ]
        )