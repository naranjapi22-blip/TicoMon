from discord.ext import commands
from incursiones.vista_incursion import VistaIncursion
from incursiones.incursion_manager import (
    crear_incursion,
    obtener_incursion
)


class Incursiones(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def incursion(self, ctx):

        existente = obtener_incursion(ctx.channel.id)

        if existente:
            await ctx.send(
                "❌ Ya existe una incursión activa en este canal."
            )
            return

        raid = crear_incursion(
            canal_id=ctx.channel.id,
            alpha="Dratini"
        )

        cantidad = len(raid.jugadores)

        await interaction.message.edit(
            content=
            f"🦖 Alpha {raid.alpha} apareció\n\n"
            f"Participantes: {cantidad}/3",
            view=self
        )

        raid.mensaje_id = mensaje.id


async def setup(bot):
    await bot.add_cog(Incursiones(bot))