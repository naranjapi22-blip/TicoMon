import discord
import database

def iniciar_modulo_ranking_legend(bot):

    @bot.command(name="rankinglegend")
    async def rankinglegend(ctx):
        await ctx.send("Ranking legendario funcionando")