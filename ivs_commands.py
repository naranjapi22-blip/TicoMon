import discord
from discord.ext import commands
from database import get_connection
import servicios
import math

# Fórmulas oficiales de Pokémon
def calcular_stat_lvl50(base, iv):
    return math.floor(((2 * base + iv) * 50 / 100) + 5)

def calcular_hp_lvl50(base, iv):
    return math.floor(((2 * base + iv) * 50 / 100) + 50 + 10)

class IvsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ivs")
    async def ver_ivs(self, ctx, id_pokemon: int):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pokemon_nombre, iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe, es_shiny
            FROM capturas 
            WHERE id = %s AND user_id = %s
        """, (str(id_pokemon), str(ctx.author.id)))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            await ctx.send("❌ No existe ningún Pokémon con ese ID en **tu** inventario.")
            return

        nombre, hp, atk, defs, spa, spd, spe, es_shiny = resultado
        ivs_list = [hp, atk, defs, spa, spd, spe]
        total = sum(ivs_list)
        porcentaje = round((total / 186) * 100, 2)
        
        if porcentaje >= 85: 
            color = discord.Color.gold()
            calidad = "💎 Épico"
        elif porcentaje >= 70: 
            color = discord.Color.green()
            calidad = "🔥 Excelente"
        else: 
            color = discord.Color.blue()
            calidad = "⏺️ Normal"

        emoji_shiny = "✨ " if es_shiny else ""
        
        embed = discord.Embed(title=f"{emoji_shiny}{nombre.capitalize()}", color=color)
        
        # 1. Estadísticas Detalladas
        try:
            data, _ = await servicios.obtener_pokemon(self.bot.session, nombre)
            if data:
                b = {s['stat']['name']: s['base_stat'] for s in data['stats']}
                
                embed.add_field(name="📊 Estadísticas (Total | Base | IVs)", value="━━━━━━━━━━━━━━━━━━━━", inline=False)
                
                # Función auxiliar definida dentro del método para acceso a datos
                def fmt(lvl50, base, ivs):
                    return f"**{lvl50:>3}** | {base:>3} | {ivs:>2}/31"

                embed.add_field(name="❤️ HP", value=fmt(calcular_hp_lvl50(b.get('hp',0), hp), b.get('hp',0), hp), inline=False)
                embed.add_field(name="⚔️ Atk", value=fmt(calcular_stat_lvl50(b.get('attack',0), atk), b.get('attack',0), atk), inline=False)
                embed.add_field(name="🛡️ Def", value=fmt(calcular_stat_lvl50(b.get('defense',0), defs), b.get('defense',0), defs), inline=False)
                embed.add_field(name="🔮 SpA", value=fmt(calcular_stat_lvl50(b.get('special-attack',0), spa), b.get('special-attack',0), spa), inline=False)
                embed.add_field(name="✨ SpD", value=fmt(calcular_stat_lvl50(b.get('special-defense',0), spd), b.get('special-defense',0), spd), inline=False)
                embed.add_field(name="⚡ Spe", value=fmt(calcular_stat_lvl50(b.get('speed',0), spe), b.get('speed',0), spe), inline=False)
        except Exception as e:
            print(f"Error cargando stats: {e}")

        # 2. Detalles Generales
        detalles = (
            f"🆔 **ID Único:** {id_pokemon}\n"
            f"⭐ **Calidad:** {calidad}\n"
            f"📈 **Potencial Total:** {total}/186 ({porcentaje}%)\n"
            f"✨ **Variocolor:** {'Sí' if es_shiny else 'No'}"
        )
        embed.add_field(name="📝 Detalles de Captura", value=detalles, inline=False)
        
        # 3. Imágenes
        try:
            dex_id = await servicios.obtener_id_por_nombre(self.bot.session, nombre)
            if dex_id:
                path_shiny = "shiny/" if es_shiny else ""
                img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{path_shiny}{dex_id}.png"
                thumb_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{path_shiny}{dex_id}.png"
                embed.set_image(url=img_url)
                embed.set_thumbnail(url=thumb_url)
        except Exception as e:
            print(f"Error cargando imágenes: {e}")
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IvsCommands(bot))