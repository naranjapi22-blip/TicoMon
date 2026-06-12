import discord

from safari_manager import obtener_safari


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