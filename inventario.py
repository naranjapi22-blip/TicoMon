import discord
from discord.ext import commands
from database import get_connection

class Inventario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- COMANDO INVENTARIO ---
    @commands.command(name="inventario")
    async def ver_inventario(self, ctx):
        conn = get_connection()
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

        lista = ""
        for p in pokemones[:20]:
            id_p, nombre, shiny, porc = p
            emoji = "✨" if shiny else "⚪"
            
            if porc >= 85: color_pc = "💎" 
            elif porc >= 70: color_pc = "🔥" 
            else: color_pc = "⏺️" 
            
            lista += f"`[{id_p}]` {emoji} **{nombre.capitalize()}** | {color_pc} `{porc}%`\n"
        
        embed = discord.Embed(title=f"🎒 Inventario de {ctx.author.name}", color=discord.Color.green())
        embed.description = lista
        embed.set_footer(text="Usa !ivs [ID] para ver detalles técnicos.")
        await ctx.send(embed=embed)

    # --- COMANDO TOP ---
    @commands.command(name="top")
    async def ver_top(self, ctx):
        conn = get_connection()
        cursor = conn.cursor()
        
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
            await ctx.send("🎒 Aún no tienes Pokémon capturados.")
            return

        embed = discord.Embed(title=f"🏆 Top 10 Mejores Pokémon de {ctx.author.name}", color=discord.Color.gold())
        
        lista = ""
        for i, p in enumerate(top_pokemones, 1):
            id_p, nombre, shiny, porc = p
            emoji = "✨" if shiny else "⚪"
            medalla = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            lista += f"{medalla} `[{id_p}]` {emoji} **{nombre.capitalize()}** — `{porc}%`\n"
        
        embed.description = lista
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Inventario(bot))