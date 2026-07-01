import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io

import database
import servicios

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
                    32
                )

                font_info = ImageFont.truetype(
                    "arial.ttf",
                    24
                )

            except:

                font_nombre = ImageFont.load_default()
                font_info = ImageFont.load_default()



            # =====================
            # OFFICIAL ARTWORK
            # =====================

            data, species = await servicios.obtener_pokemon(
                self.bot.session,
                dex_id
            )

            if not data:
                await ctx.send(
                    "❌ No se pudo obtener información del Pokémon."
                )
                return

            if es_shiny:

                artwork_url = (
                    data["sprites"]["other"]["official-artwork"]
                    .get("front_shiny")
                )

                if not artwork_url:
                    artwork_url = (
                        data["sprites"]["other"]["official-artwork"]
                        .get("front_default")
                    )

            else:

                artwork_url = (
                    data["sprites"]["other"]["official-artwork"]
                    .get("front_default")
                )

            if not artwork_url:
                await ctx.send(
                    "❌ No se encontró artwork."
                )
                return

            async with self.bot.session.get(
                artwork_url
            ) as resp:

                if resp.status != 200:
                    await ctx.send(
                        "❌ Error descargando artwork."
                    )
                    return

                artwork_bytes = await resp.read()

            sprite = Image.open(
                io.BytesIO(artwork_bytes)
            ).convert("RGBA")
            MARCO_X = 55
            MARCO_Y = 80

            MARCO_W = 250
            MARCO_H = 190
            max_w = MARCO_W - 10
            max_h = MARCO_H - 10
            sprite.thumbnail(
                (
                    MARCO_W - 10,
                    MARCO_H - 10
                ),
                Image.Resampling.LANCZOS
            )

            x = MARCO_X + (
                (MARCO_W - sprite.width) // 2
            )

            y = MARCO_Y + (
                (MARCO_H - sprite.height) // 2
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
                (440, 150),
                texto_nombre,
                fill="black",
                font=font_nombre
            )

            draw.text(
                (440, 195),
                f"Captura #{id_pokemon}",
                fill="black",
                font=font_info
            )

            draw.text(
                (440, 235),
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