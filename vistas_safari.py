import discord

from safari_manager import obtener_safari
from PIL import Image
from io import BytesIO
import aiohttp

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
                "🎯 Safari Balls: 15"
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
                f"🎯 Apostaste {self.cantidad} Safari Ball{'s' if self.cantidad > 1 else ''} al slot {self.slot}.",
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
        timeout=30
    ):

        super().__init__(
            timeout=timeout
        )

        self.guild_id = guild_id

        self.add_item(
            BotonApuesta(
                guild_id,
                1
            )
        )

        self.add_item(
            BotonApuesta(
                guild_id,
                2
            )
        )

        self.add_item(
            BotonApuesta(
                guild_id,
                3
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
async def crear_imagen_encuentro(pokemons, session):

    sprites = []

    for pokemon in pokemons:

        pokemon_id = pokemon["pokemon_id"]

        if pokemon["es_shiny"]:
            url = (
                "https://raw.githubusercontent.com/"
                "PokeAPI/sprites/master/"
                f"sprites/pokemon/shiny/{pokemon_id}.png"
            )
        else:
            url = (
                "https://raw.githubusercontent.com/"
                "PokeAPI/sprites/master/"
                f"sprites/pokemon/{pokemon_id}.png"
            )

        try:

            async with session.get(url) as resp:

                if resp.status != 200:
                    continue

                data = await resp.read()

            sprite = Image.open(
                BytesIO(data)
            ).convert("RGBA")

            sprites.append(sprite)

        except Exception:
            continue

    if not sprites:
        return None

    ancho_total = sum(
        sprite.width
        for sprite in sprites
    )

    alto_maximo = max(
        sprite.height
        for sprite in sprites
    )

    imagen_final = Image.new(
        "RGBA",
        (ancho_total, alto_maximo),
        (255, 255, 255, 0)
    )

    x_actual = 0

    for sprite in sprites:

        y_actual = (
            alto_maximo - sprite.height
        ) // 2

        imagen_final.paste(
            sprite,
            (x_actual, y_actual),
            sprite
        )

        x_actual += sprite.width

    buffer = BytesIO()

    imagen_final.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer