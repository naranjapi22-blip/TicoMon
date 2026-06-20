from discord.ext import commands

from incursiones.incursion_manager import (
    crear_incursion,
    obtener_incursion
)
class Incursiones(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def incursion(self, ctx):
        await ctx.send("Raid creada")
async def setup(bot):
    await bot.add_cog(Incursiones(bot))
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

        mensaje = await ctx.send(
            "🦖 Alpha Dratini apareció\n\n"
            "Participantes: 0/3"
        )

        raid.mensaje_id = mensaje.id