import discord
import asyncio

class VistaExploracion(discord.ui.View):

    def __init__(self, manager):

        super().__init__(timeout=None)

        self.manager = manager

        self.reconstruir()

    def reconstruir(self):

        self.clear_items()

        exploracion = self.manager.world.exploracion

        # ==========================
        # LISTA DE POKÉMON
        # ==========================

        if exploracion.estado == "lista":

            for i, pokemon in enumerate(
                self.manager.world.pokemons_visibles()
            ):

                boton = discord.ui.Button(
                    label=pokemon["nombre"].capitalize(),
                    style=discord.ButtonStyle.green
                )

                boton.callback = self.crear_callback(i)

                self.add_item(boton)

            salir = discord.ui.Button(
                label="🚪 Salir",
                style=discord.ButtonStyle.red
            )

            salir.callback = self.salir

            self.add_item(salir)
        elif exploracion.estado == "capturando":

            pass
        # ==========================
        # POKÉMON SELECCIONADO
        # ==========================

        elif exploracion.estado == "pokemon":

            capturar = discord.ui.Button(
                label="🎯 Capturar",
                style=discord.ButtonStyle.green
            )

            capturar.callback = self.capturar

            self.add_item(capturar)

            volver = discord.ui.Button(
                label="⬅️ Volver",
                style=discord.ButtonStyle.gray
            )

            volver.callback = self.volver

            self.add_item(volver)

    def crear_callback(self, indice):

        async def callback(interaction):

            exploracion = self.manager.world.exploracion

            exploracion.estado = "pokemon"

            exploracion.pokemon_seleccionado = indice

            self.reconstruir()

            pokemon = self.manager.world.pokemons_visibles()[indice]

            await interaction.response.edit_message(
                content=(
                    f"🌿 **{pokemon['nombre'].capitalize()}**\n\n"
                    "¿Qué deseas hacer?"
                ),
                view=self
            )

        return callback

    async def capturar(self, interaction):

        exploracion = self.manager.world.exploracion

        exploracion.estado = "capturando"
        exploracion.captura_en_progreso = True

        self.reconstruir()

        await interaction.response.edit_message(
            content=(
                "🎯 **Intentando capturar...**\n\n"
                "⏳ Espera unos segundos..."
            ),
            view=self
        )

        await asyncio.sleep(5)

        exploracion.estado = "lista"
        exploracion.captura_en_progreso = False
        exploracion.pokemon_seleccionado = None

        self.reconstruir()

        nombres = []

        for pokemon in self.manager.world.pokemons_visibles():

            nombres.append(
                f"• {pokemon['nombre'].capitalize()}"
            )

        mensaje = (
            "❌ El Pokémon escapó.\n\n"
            f"🌍 **Mundo {self.manager.world.tipo.title()}**\n\n"
            + "\n".join(nombres)
        )

        await interaction.edit_original_response(
            content=mensaje,
            view=self
        )

    async def volver(self, interaction):

        exploracion = self.manager.world.exploracion

        exploracion.estado = "lista"

        exploracion.pokemon_seleccionado = None

        exploracion.captura_en_progreso = False
        self.reconstruir()

        nombres = []

        for pokemon in self.manager.world.pokemons_visibles():

            nombres.append(
                f"• {pokemon['nombre'].capitalize()}"
            )

        mensaje = (
            f"🌍 **Mundo {self.manager.world.tipo.title()}**\n\n"
            + "\n".join(nombres)
        )

        await interaction.response.edit_message(
            content=mensaje,
            view=self
        )

    async def salir(self, interaction):

        self.manager.world.finalizar_exploracion()

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="👋 Has salido del Mundo Pokémon.",
            view=self
        )