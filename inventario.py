import discord
from discord.ext import commands
import database

# --- CLASE PARA LOS BOTONES DE PÁGINAS ---
class PaginadorInventario(discord.ui.View):
    def __init__(self, ctx, embeds):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.embeds = embeds
        self.pagina_actual = 0
        
        if len(self.embeds) <= 1:
            self.btn_anterior.disabled = True
            self.btn_siguiente.disabled = True

    @discord.ui.button(label="◀️ Anterior", style=discord.ButtonStyle.secondary, custom_id="ant")
    async def btn_anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Solo el dueño puede cambiar de página.", ephemeral=True)
        self.pagina_actual = (self.pagina_actual - 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.pagina_actual])

    @discord.ui.button(label="Siguiente ▶️", style=discord.ButtonStyle.secondary, custom_id="sig")
    async def btn_siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Solo el dueño puede cambiar de página.", ephemeral=True)
        self.pagina_actual = (self.pagina_actual + 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.pagina_actual])


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
                if porc >= 85: color_pc = "💎" 
                elif porc >= 70: color_pc = "🔥" 
                else: color_pc = "⏺️" 
                
                lista += f"{emoji} **{nombre.capitalize()}** `[{id_p}]` | {color_pc} `{int(porc)}%`\n"
            
            embed = discord.Embed(title=f"🎒 Inventario de {ctx.author.name}", color=discord.Color.green())
            embed.description = lista
            embed.set_footer(text=f"Página {i+1}/{len(paginas)} | Usa !ivs [ID] para detalles.")
            embeds.append(embed)

        view = PaginadorInventario(ctx, embeds)
        await ctx.send(embed=embeds[0], view=view)

    @commands.command(name="top")
    async def ver_top(self, ctx):
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Ranking PERSONAL (solo tus Pokémon)
        cursor.execute("""
            SELECT id, pokemon_nombre, es_shiny, 
                   ((iv_hp + iv_atk + iv_def + iv_spa + iv_spd + iv_spe) * 100 / 186) as porcentaje 
            FROM capturas 
            WHERE user_id = %s 
            ORDER BY porcentaje DESC 
            LIMIT 10
        """, (str(ctx.author.id),))
        
        top_pokemones = cursor.fetchall()
        conn.close()
        
        if not top_pokemones:
            await ctx.send("❌ Aún no tienes Pokémon capturados.")
            return

        embed = discord.Embed(title=f"🏆 Tus 10 mejores Pokémon", color=discord.Color.gold())
        
        lista = ""
        for i, p in enumerate(top_pokemones, 1):
            id_p, nombre, shiny, porc = p
            emoji = "✨" if shiny else "⚪"
            
            # Formato simple: Medalla, Emoji, Nombre, ID y porcentaje
            medalla = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            lista += f"{medalla} {emoji} **{nombre.capitalize()}** `[{id_p}]` — `{int(porc)}%`\n"
        
        embed.description = lista
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Inventario(bot))