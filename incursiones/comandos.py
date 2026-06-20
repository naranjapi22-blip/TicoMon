from discord.ext import commands


class Incursiones(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def incursion(self, ctx):
        await ctx.send("Raid creada")


async def setup(bot):
    await bot.add_cog(Incursiones(bot))