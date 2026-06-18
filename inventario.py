import discord
from discord.ext import commands
import database
import servicios

# --- CLASE PARA LOS BOTONES DE PÁGINAS ---
class PaginadorInventario(discord.ui.View):
    def __init__(self, ctx, embeds):
        super().__init__(timeout=180)

        self.ctx = ctx
        self.embeds = embeds
        self.pagina_actual = 0
        self.message = None

        if len(self.embeds) <= 1:
            self.btn_anterior.disabled = True
            self.btn_siguiente.disabled = True

    async def on_timeout(self):

        for item in self.children:
            item.disabled = True

        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(
        label="◀️ Anterior",
        style=discord.ButtonStyle.secondary,
        custom_id="ant"
    )
    async def btn_anterior(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "❌ Solo el dueño puede cambiar de página.",
                ephemeral=True
            )

        self.pagina_actual = (
            self.pagina_actual - 1
        ) % len(self.embeds)

        await interaction.response.edit_message(
            embed=self.embeds[self.pagina_actual]
        )

    @discord.ui.button(
        label="Siguiente ▶️",
        style=discord.ButtonStyle.secondary,
        custom_id="sig"
    )
    async def btn_siguiente(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "❌ Solo el dueño puede cambiar de página.",
                ephemeral=True
            )

        self.pagina_actual = (
            self.pagina_actual + 1
        ) % len(self.embeds)

        await interaction.response.edit_message(
            embed=self.embeds[self.pagina_actual]
        )


class Inventario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="inventario")
    async def ver_inventario(self, ctx):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, pokemon_nombre, es_shiny, 
                ((iv_hp + iv_atk + iv_def + iv_spa + iv_spd + iv_spe) * 100 / 186) as porcentaje
            FROM capturas 
            WHERE user_id = %s 
            ORDER BY id DESC
        """, (str(ctx.author.id),))
        pokemones = cursor.fetchall()
        conn.close()
        
        if not pokemones:
            await ctx.send("🎒 Tu inventario está vacío.")
            return

        elementos_por_pagina = 10
        paginas = [pokemones[i:i + elementos_por_pagina] for i in range(0, len(pokemones), elementos_por_pagina)]
        embeds = []

        for i, pagina in enumerate(paginas):
            lista = ""

            for p in pagina:
                id_p, nombre, shiny, porc = p

                emoji = "✨" if shiny else "⚪"

                if porc >= 85:
                    color_pc = "💎"
                elif porc >= 70:
                    color_pc = "🔥"
                else:
                    color_pc = "⏺️"

                lista += (
                    f"{emoji} **{nombre.capitalize()}** "
                    f"`[{id_p}]` | {color_pc} `{int(porc)}%`\n"
                )

            embed = discord.Embed(
                title=f"🎒 Inventario de {ctx.author.name}",
                color=discord.Color.green()
            )

            embed.description = lista

            embed.set_footer(
                text=f"Página {i+1}/{len(paginas)} | Usa !ivs [ID] para detalles."
            )

            embeds.append(embed)

        # ← AQUÍ TERMINA EL FOR

        view = PaginadorInventario(
            ctx,
            embeds
        )

        mensaje = await ctx.send(
            embed=embeds[0],
            view=view
        )

        view.message = mensaje

@commands.command(name="top")
async def ver_top(self, ctx, tipo=None):

    TIPOS_VALIDOS = {
        "normal",
        "fire",
        "water",
        "grass",
        "electric",
        "ice",
        "fighting",
        "poison",
        "ground",
        "flying",
        "psychic",
        "bug",
        "rock",
        "ghost",
        "dragon",
        "dark",
        "steel",
        "fairy"
    }

    if tipo:

        tipo = tipo.lower()

        if tipo not in TIPOS_VALIDOS:

            return await ctx.send(
                f"❌ Tipo inválido: {tipo}"
            )

    conn = database.get_connection()
    cursor = conn.cursor()

    if tipo:

        cursor.execute("""
            SELECT
                c.id,
                c.pokemon_nombre,
                c.es_shiny,
                p.id AS dex_id,
                ((c.iv_hp + c.iv_atk + c.iv_def +
                c.iv_spa + c.iv_spd + c.iv_spe) * 100 / 186) AS porcentaje
            FROM capturas c
            LEFT JOIN pokemon_data p
                ON c.pokemon_nombre = p.nombre
            WHERE c.user_id = %s
            AND LOWER(p.tipos) LIKE %s
            ORDER BY porcentaje DESC
            LIMIT 5
        """, (
            str(ctx.author.id),
            f"%{tipo}%"
        ))

    else:

        cursor.execute("""
            SELECT
                c.id,
                c.pokemon_nombre,
                c.es_shiny,
                p.id AS dex_id,
                ((c.iv_hp + c.iv_atk + c.iv_def +
                c.iv_spa + c.iv_spd + c.iv_spe) * 100 / 186) AS porcentaje
            FROM capturas c
            LEFT JOIN pokemon_data p
                ON c.pokemon_nombre = p.nombre
            WHERE c.user_id = %s
            ORDER BY porcentaje DESC
            LIMIT 5
        """, (str(ctx.author.id),))

    top_pokemones = cursor.fetchall()
    conn.close()

    if not top_pokemones:

        if tipo:

            await ctx.send(
                f"❌ No tienes Pokémon tipo **{tipo}**."
            )

        else:

            await ctx.send(
                "❌ Aún no tienes Pokémon capturados."
            )

        return

    imagen_top = await servicios.generar_imagen_top(
        top_pokemones,
        tipo=tipo
    )

    if not imagen_top:

        await ctx.send(
            "❌ Error generando imagen."
        )

        return

    archivo = discord.File(
        imagen_top,
        filename="top.png"
    )

    titulo = (
        f"🏆 Tus 5 mejores Pokémon tipo {tipo.capitalize()}"
        if tipo
        else "🏆 Tus 5 mejores Pokémon"
    )

    embed = discord.Embed(
        title=titulo,
        color=discord.Color.gold()
    )

    embed.set_image(
        url="attachment://top.png"
    )

    await ctx.send(
        embed=embed,
        file=archivo
    )
async def setup(bot):
    await bot.add_cog(Inventario(bot))