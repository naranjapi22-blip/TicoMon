import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
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

            # =====================
            # PLANTILLA
            # =====================

            base = Image.open(
                "assets/photodex_base.png"
            ).convert("RGBA")

            draw = ImageDraw.Draw(base)

            try:
                font_nombre = ImageFont.truetype(
                    "arial.ttf",
                    28
                )

                font_info = ImageFont.truetype(
                    "arial.ttf",
                    22
                )

            except:
                font_nombre = ImageFont.load_default()
                font_info = ImageFont.load_default()

            # =====================
            # SPRITE
            # =====================

            carpeta = "shiny" if es_shiny else "regular"

            ruta_sprite = (
                f"sprites/{carpeta}/{dex_id}.png"
            )

            sprite = Image.open(
                ruta_sprite
            ).convert("RGBA")

            sprite.thumbnail(
                (220, 220),
                Image.Resampling.NEAREST
            )

            # =====================
            # CENTRAR SPRITE
            # =====================

            pantalla_x = 30
            pantalla_y = 85

            pantalla_w = 320
            pantalla_h = 265

            x = pantalla_x + (
                (pantalla_w - sprite.width) // 2
            )

            y = pantalla_y + (
                (pantalla_h - sprite.height) // 2
            )

            base.paste(
                sprite,
                (x, y),
                sprite
            )

            # =====================
            # TEXTO
            # =====================

            texto_nombre = nombre.capitalize()

            if es_shiny:
                texto_nombre += " ✨"

            draw.text(
                (420, 430),
                texto_nombre,
                fill="black",
                font=font_nombre
            )

            draw.text(
                (420, 470),
                f"Captura #{id_pokemon}",
                fill="black",
                font=font_info
            )

            draw.text(
                (420, 510),
                f"Dex #{dex_id}",
                fill="black",
                font=font_info
            )

            # =====================
            # EXPORTAR
            # =====================

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