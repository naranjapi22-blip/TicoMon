import discord
from discord.ext import commands
from PIL import Image
import io


class PhotoDex(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="photodex")
    async def photodex(self, ctx, captura_id: int):

        try:

            base = Image.open(
                "assets/photodex_base.png"
            ).convert("RGBA")

            buffer = io.BytesIO()

            base.save(
                buffer,
                format="PNG"
            )

            buffer.seek(0)

            archivo = discord.File(
                buffer,
                filename="photodex.png"
            )

            await ctx.send(
                file=archivo
            )

        except Exception as e:

            await ctx.send(
                f"❌ Error: {e}"
            )


async def setup(bot):
    await bot.add_cog(
        PhotoDex(bot)
    )