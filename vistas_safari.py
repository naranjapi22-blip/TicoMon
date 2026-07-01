import discord
import random
import database
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
        from safari_manager import obtener_safari
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

        from safari_manager import obtener_safari

        safari = obtener_safari(
            interaction.guild.id
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
        from safari_manager import obtener_safari

        safari = obtener_safari(
            interaction.guild.id
        )

        balls = safari.obtener_balls(
            interaction.user.id
        )

        await interaction.response.send_message(
            f"🎯 Elegiste a {self.nombre}.\n\n"
            f"🎒 Safari Balls disponibles: {balls}\n\n"
            f"¿Cuántas Safari Balls deseas usar?",
            view=VistaApuestasSafari(
                self.guild_id,
                self.slot
            ),
            ephemeral=True
        )
class BotonRevisarPokedex(discord.ui.Button):

    def __init__(self, guild_id):

        super().__init__(
            label="Revisar Pokédex",
            emoji="📖",
            style=discord.ButtonStyle.secondary,
            row=1
        )

        self.guild_id = guild_id

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        from safari_manager import obtener_safari

        safari = obtener_safari(
            self.guild_id
        )

        if (
            safari is None
            or not safari.activo
        ):
            return await interaction.response.send_message(
                "❌ El Safari ya terminó.",
                ephemeral=True
            )

        mensaje = "📖 **Pokédex**\n\n"

        capturadas = safari.pokedex_cache.get(
            interaction.user.id,
            set()
        )

        mensaje = "📖 **Pokédex**\n\n"

        for pokemon in safari.encuentro_actual["pokemons"]:

            emoji = (
                "✅"
                if pokemon["nombre"].lower() in capturadas
                else "❌"
            )

            mensaje += (
                f"{emoji} {pokemon['nombre'].capitalize()}\n"
            )

        await interaction.response.send_message(
            mensaje,
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

        self.add_item(
            BotonRevisarPokedex(
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

class VistaSituacionSafari(discord.ui.View):

    def __init__(self, situacion):

        super().__init__(timeout=20)

        self.situacion = situacion
        self.votos_a = 0
        self.votos_b = 0
        self.votos_c = 0
        self.votantes = set()
        self.modificador_ganador = {}

        btn_a = discord.ui.Button(
            label=situacion["opcion_a"],
            style=discord.ButtonStyle.success
        )

        btn_b = discord.ui.Button(
            label=situacion["opcion_b"],
            style=discord.ButtonStyle.secondary
        )
        btn_c = discord.ui.Button(
            label=situacion["opcion_c"],
            style=discord.ButtonStyle.primary
        )
        btn_a.callback = self.votar_a
        btn_b.callback = self.votar_b
        btn_c.callback = self.votar_c
        self.add_item(btn_a)
        self.add_item(btn_b)
        self.add_item(btn_c)
    async def votar_a(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id in self.votantes:

            return await interaction.response.send_message(
                "❌ Ya votaste.",
                ephemeral=True
            )

        self.votantes.add(
            interaction.user.id
        )

        self.votos_a += 1

        await interaction.response.send_message(
            f"✅ Votaste por: {self.situacion['opcion_a']}",
            ephemeral=True
        )

    async def votar_b(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id in self.votantes:

            return await interaction.response.send_message(
                "❌ Ya votaste.",
                ephemeral=True
            )

        self.votantes.add(
            interaction.user.id
        )

        self.votos_b += 1

        await interaction.response.send_message(
            f"✅ Votaste por: {self.situacion['opcion_b']}",
            ephemeral=True
        )
    async def votar_c(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id in self.votantes:

            return await interaction.response.send_message(
                "❌ Ya votaste.",
                ephemeral=True
            )

        self.votantes.add(
            interaction.user.id
        )

        self.votos_c += 1

        await interaction.response.send_message(
            f"✅ Votaste por: {self.situacion['opcion_c']}",
            ephemeral=True
        )

    def resolver_resultado(self):

        votos = {
            "A": self.votos_a,
            "B": self.votos_b,
            "C": self.votos_c
        }

        max_votos = max(
            votos.values()
        )

        ganadores = [
            opcion
            for opcion, cantidad
            in votos.items()
            if cantidad == max_votos
        ]

        resultado = random.choice(
            ganadores
        )

        if resultado == "A":

            self.modificador_ganador = (
                self.situacion["modificador_a"]
            )

        elif resultado == "B":

            self.modificador_ganador = (
                self.situacion["modificador_b"]
            )

        else:

            self.modificador_ganador = (
                self.situacion["modificador_c"]
            )

        return resultado