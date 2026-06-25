from discord.ext import commands

from incursiones.vista_incursion import VistaIncursion
from incursiones.selector_incursion import SelectorIncursion
from incursiones.incursion_manager import (
    crear_incursion,
    obtener_incursion
)
from incursiones.modelos import Incursion

from database import obtener_equipo_selector
from incursiones.alphas import (
    obtener_alpha_aleatorio
)

class Incursiones(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def incursion(self, ctx):
        print(">>> Entró a !incursion")
        existente = obtener_incursion(ctx.channel.id)

        if existente:
            await ctx.send(
                "❌ Ya existe una incursión activa en este canal."
            )
            return

        nombre_alpha = obtener_alpha_aleatorio()

        print(
            f"👹 Alpha generado: "
            f"{nombre_alpha}"
        )

        raid = crear_incursion(
            canal_id=ctx.channel.id,
            canal=ctx.channel,
            alpha=nombre_alpha
        )

        mensaje = await ctx.send(
            f"🦖 Alpha {raid.alpha.capitalize()} apareció\n\n"
            f"Participantes: 0/3",
            view=VistaIncursion()
        )

        raid.mensaje_id = mensaje.id

    @commands.command()
    async def selectorraid(self, ctx):

        raid = Incursion(
            canal_id=0,
            alpha="Dratini"
        )

        await ctx.send(
            "🎯 Selecciona un Pokémon",
            view=SelectorIncursion(raid)
        )

    @commands.command()
    async def debugteam(self, ctx):

        equipo = obtener_equipo_selector(
            ctx.author.id
        )

        await ctx.send(
            f"```{equipo}```"
        )


async def setup(bot):
    await bot.add_cog(Incursiones(bot))