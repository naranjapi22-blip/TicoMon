import discord
from discord.ext import commands
from PIL import Image
import io

import database


class PhotoDex(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="photodex")
    async def photodex(self, ctx, id_pokemon: int):

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT c.pokemon_nombre,
                       c.es_shiny,
                       p.id
                FROM capturas c
                LEFT JOIN pokemon_data p
                    ON c.pokemon_nombre = p.nombre
                WHERE c.id = %s
                AND c.user_id = %s
            """, (
                str(id_pokemon),
                str(ctx.author.id)
            ))

            resultado = cursor.fetchone()

            if not resultado:
                await ctx.send(
                    "❌ No existe ningún Pokémon con ese ID en tu inventario."
                )
                return

            nombre, es_shiny, dex_id = resultado

            if dex_id is None:
                await ctx.send(
                    "❌ No se pudo obtener el Dex ID."
                )
                return

            # =========================
            # Plantilla
            # =========================

            base = Image.open(
                "assets/photodex_base.png"
            ).convert("RGBA")

            # =========================
            # Sprite
            # =========================

            carpeta = "shiny" if es_shiny else "regular"

            ruta_sprite = (
                f"sprites/{carpeta}/{dex_id}.png"
            )

            sprite = Image.open(
                ruta_sprite
            ).convert("RGBA")

            # Tamaño inicial para prueba
            sprite.thumbnail(
                (600, 600),
                Image.Resampling.LANCZOS
            )

            # =========================
            # Posición en pantalla izquierda
            # =========================

            x = 220
            y = 120

            base.paste(
                sprite,
                (x, y),
                sprite
            )

            # =========================
            # Guardar
            # =========================

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

        finally:
            conn.close()


async def setup(bot):
    await bot.add_cog(
        PhotoDex(bot)
    )