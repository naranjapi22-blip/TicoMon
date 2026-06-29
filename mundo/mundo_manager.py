import asyncio
import discord
from mundo.vista_mundo import VistaMundo
from mundo.vista_exploracion import VistaExploracion
from mundo.world import World


class MundoManager:

    def __init__(self):

        self.world = World()

        self.canal = None
        self.mensaje = None

        self.loop_task = None

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
            ),
            view=VistaMundo(self)
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

    async def evolucionar(self):

        self.world.evolucionar()

        if self.mensaje:

            gif = await self.obtener_gif()

            await self.mensaje.edit(
                attachments=[
                    discord.File(
                        gif,
                        filename="mundo.gif"
                    )
                ]
            )

    async def loop(self):

        while True:

            await asyncio.sleep(180)

            await self.evolucionar()

    async def iniciar_loop(self):

        if self.loop_task is None:

            self.loop_task = asyncio.create_task(
                self.loop()
            )   
    async def abrir_exploracion(self, interaction):

        nombres = []

        for i, pokemon in enumerate(
            self.world.pokemons_visibles(),
            start=1
        ):

            nombres.append(
                f"{i}. {pokemon['nombre'].capitalize()}"
            )

        mensaje = (
            f"🌍 **Mundo {self.world.tipo.title()}**\n\n"
            + "\n".join(nombres)
        )

        await interaction.response.send_message(
            mensaje,
            view=VistaExploracion(self),
            ephemeral=True
        )