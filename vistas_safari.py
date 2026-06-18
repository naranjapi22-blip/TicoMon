import discord

from safari_manager import obtener_safari
from PIL import Image
from io import BytesIO
import aiohttp
ACCIONES_EXPEDICION = [
    ("cebo", "🍓 Tirar Cebo"),
    ("huellas", "🔍 Seguir Huellas"),
    ("ruido", "🔥 Hacer Ruido"),
    ("continuar", "🚙 Continuar")
]
class BotonParticipar(discord.ui.Button):

    def __init__(self, guild_id):
        super().__init__(
            label="Participar",
            emoji="🚙",
            style=discord.ButtonStyle.success
        )

        self.guild_id = guild_id

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        safari = obtener_safari(
            self.guild_id
        )

        if not safari:

            return await interaction.response.send_message(
                "❌ Este Safari ya no existe.",
                ephemeral=True
            )

        if not safari.activo:

            return await interaction.response.send_message(
                "❌ Este Safari ya terminó.",
                ephemeral=True
            )

        if safari.es_participante(
            interaction.user.id
        ):

            return await interaction.response.send_message(
                "🚙 Ya estás dentro del Safari.",
                ephemeral=True
            )

        agregado = safari.agregar_participante(
            interaction.user.id
        )

        if not agregado:

            return await interaction.response.send_message(
                "❌ No fue posible unirte al Safari.",
                ephemeral=True
            )

        await interaction.response.send_message(
            (
                "🚙 Te has unido al Safari.\n\n"
                "🎯 Safari Balls: 9"
            ),
            ephemeral=True
        )


class VistaParticiparSafari(discord.ui.View):

    def __init__(
        self,
        guild_id,
        timeout=60
    ):
        super().__init__(
            timeout=timeout
        )

        self.guild_id = guild_id

        self.add_item(
            BotonParticipar(
                guild_id
            )
        )

    async def on_timeout(self):

        for item in self.children:
            item.disabled = True

        try:
            if hasattr(self, "message"):
                await self.message.edit(
                    view=self
                )
        except Exception:
            pass
class BotonApuesta(discord.ui.Button):

    def __init__(self, guild_id, cantidad,slot=1):

        super().__init__(
            label=f"{cantidad} Ball{'s' if cantidad > 1 else ''}",
            emoji="🎯",
            style=discord.ButtonStyle.primary
        )

        self.guild_id = guild_id
        self.cantidad = cantidad
        self.slot = slot
    async def callback(
        self,
        interaction: discord.Interaction
    ):

        safari = obtener_safari(
            self.guild_id
        )

        if not safari:

            return await interaction.response.send_message(
                "❌ El Safari ya no existe.",
                ephemeral=True
            )

        ok, mensaje = safari.registrar_apuesta(
            interaction.user.id,
            self.cantidad,
            self.slot
        )

        if ok:

            return await interaction.response.send_message(
                mensaje,
                ephemeral=True
            )

        await interaction.response.send_message(
            f"❌ {mensaje}",
            ephemeral=True
        )


class VistaApuestasSafari(discord.ui.View):

    def __init__(
        self,
        guild_id,
        slot,
        timeout=30
    ):

        super().__init__(
            timeout=timeout
        )

        self.guild_id = guild_id
        self.slot = slot

        self.add_item(
            BotonApuesta(
                guild_id,
                1,
                slot
            )
        )

        self.add_item(
            BotonApuesta(
                guild_id,
                2,
                slot
            )
        )

        self.add_item(
            BotonApuesta(
                guild_id,
                3,
                slot
            )
        )
class BotonSeleccionPokemon(discord.ui.Button):

    def __init__(
        self,
        guild_id,
        slot,
        nombre
    ):

        super().__init__(
            label=f"{slot}️⃣ {nombre}",
            style=discord.ButtonStyle.success
        )

        self.guild_id = guild_id
        self.slot = slot
        self.nombre = nombre

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.send_message(
            f"🎯 Elegiste a {self.nombre}.\n\n"
            f"¿Cuántas Safari Balls deseas usar?",
            view=VistaApuestasSafari(
                self.guild_id,
                self.slot
            ),
            ephemeral=True
        )
class VistaSeleccionPokemon(discord.ui.View):

    def __init__(
        self,
        guild_id,
        pokemons,
        timeout=30
    ):

        super().__init__(
            timeout=timeout
        )

        self.guild_id = guild_id

        for pokemon in pokemons:

            self.add_item(
                BotonSeleccionPokemon(
                    guild_id,
                    pokemon["slot"],
                    pokemon["nombre"].capitalize()
                )
            )

    async def on_timeout(self):

        for item in self.children:
            item.disabled = True

        try:
            if hasattr(self, "message"):
                await self.message.edit(
                    view=self
                )
        except Exception:
            pass
class VistaDecisionSafari(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=20)

        self.votos = {
            "cebo": 0,
            "huellas": 0,
            "ruido": 0,
            "continuar": 0
        }

        self.votantes = set()

        self.resultado = None

        self.add_item(BotonCebo())
        self.add_item(BotonHuellas())
        self.add_item(BotonRuido())
        self.add_item(BotonContinuar())
class BotonIzquierda(discord.ui.Button):

    def __init__(
        self,
        texto
    ):
        super().__init__(
            label="Sendero estrecho",
            emoji="🌲",
            style=discord.ButtonStyle.primary
        )

    async def callback(
        self,
        interaction
    ):

        view = self.view

        if interaction.user.id in view.votantes:

            return await interaction.response.send_message(
                "Ya votaste.",
                ephemeral=True
            )

        view.votantes.add(
            interaction.user.id
        )

        view.votos["izquierda"] += 1

        await interaction.response.send_message(
            "Votaste por el sendero estrecho.",
            ephemeral=True
        )
class BotonDerecha(discord.ui.Button):

    def __init__(
        self,
        texto
    ):

        super().__init__(
            label=texto,
            style=discord.ButtonStyle.primary
        )

    async def callback(
        self,
        interaction
    ):

        view = self.view

        if interaction.user.id in view.votantes:

            return await interaction.response.send_message(
                "Ya votaste.",
                ephemeral=True
            )

        view.votantes.add(
            interaction.user.id
        )

        view.votos["derecha"] += 1

        await interaction.response.send_message(
            "Votaste por el camino principal.",
            ephemeral=True
        )
class BotonCebo(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Tirar Cebo",
            emoji="🍓",
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction):

        view = self.view

        if interaction.user.id in view.votantes:

            return await interaction.response.send_message(
                "Ya votaste.",
                ephemeral=True
            )

        view.votantes.add(interaction.user.id)

        view.votos["cebo"] += 1

        await interaction.response.send_message(
            "Votaste por tirar cebo.",
            ephemeral=True
        )
class BotonHuellas(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Seguir Huellas",
            emoji="🔍",
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction):

        view = self.view

        if interaction.user.id in view.votantes:

            return await interaction.response.send_message(
                "Ya votaste.",
                ephemeral=True
            )

        view.votantes.add(interaction.user.id)

        view.votos["huellas"] += 1

        await interaction.response.send_message(
            "Votaste por seguir huellas.",
            ephemeral=True
        )
class BotonRuido(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Hacer Ruido",
            emoji="🔥",
            style=discord.ButtonStyle.danger
        )

    async def callback(self, interaction):

        view = self.view

        if interaction.user.id in view.votantes:

            return await interaction.response.send_message(
                "Ya votaste.",
                ephemeral=True
            )

        view.votantes.add(interaction.user.id)

        view.votos["ruido"] += 1

        await interaction.response.send_message(
            "Votaste por hacer ruido.",
            ephemeral=True
        )
class BotonContinuar(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Continuar",
            emoji="🚙",
            style=discord.ButtonStyle.secondary
        )

    async def callback(self, interaction):

        view = self.view

        if interaction.user.id in view.votantes:

            return await interaction.response.send_message(
                "Ya votaste.",
                ephemeral=True
            )

        view.votantes.add(interaction.user.id)

        view.votos["continuar"] += 1

        await interaction.response.send_message(
            "Votaste por continuar avanzando.",
            ephemeral=True
        )