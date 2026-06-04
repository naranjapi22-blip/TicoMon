import discord
from discord.ext import commands
from database import get_connection
import servicios

# Función para evaluar cada IV individualmente al estilo de los juegos oficiales
def evaluar_iv(valor):
    if valor == 31: return "Inmejorable"
    elif valor == 30: return "Espectacular"
    elif 26 <= valor <= 29: return "Genial"
    elif 16 <= valor <= 25: return "Notable"
    elif 1 <= valor <= 15: return "Decente"
    else: return "Cojea un poco"

class IvsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ivs")
    async def ver_ivs(self, ctx, id_pokemon: int):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Filtramos por ID de captura Y por el ID del usuario
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
        ivs = [hp, atk, defs, spa, spd, spe]
        total = sum(ivs)
        porcentaje = round((total / 186) * 100, 2)
        
        # Color dinámico y etiqueta de calidad
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
        
        # 1. Título principal
        embed = discord.Embed(title=f"{emoji_shiny}{nombre.capitalize()}", color=color)
        
        # 2. Detalles Generales
        detalles = (
            f"🆔 **ID Único:** {id_pokemon}\n"
            f"⭐ **Calidad:** {calidad}\n"
            f"📈 **Potencial Total:** {total}/186 ({porcentaje}%)\n"
            f"✨ **Variocolor:** {'Sí' if es_shiny else 'No'}"
        )
        embed.add_field(name="📝 Detalles de Captura", value=detalles, inline=False)
        
        # 3. Estadísticas Base (Lado izquierdo)
        try:
            data, _ = await servicios.obtener_pokemon(self.bot.session, nombre)
            if data:
                b_stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
                base_format = f"""```yaml
Hp    : {b_stats.get('hp', 0)}
Atk   : {b_stats.get('attack', 0)}
Def   : {b_stats.get('defense', 0)}
SpA   : {b_stats.get('special-attack', 0)}
SpD   : {b_stats.get('special-defense', 0)}
Spe   : {b_stats.get('speed', 0)}
```"""
                embed.add_field(name="📊 Stats Base", value=base_format, inline=True)
        except Exception as e:
            print(f"Error cargando stats base: {e}")

        # 4. Valores Individuales (IVs) (Lado derecho)
        stats_format = f"""```yaml
Hp    : {hp:>2}/31
Atk   : {atk:>2}/31
Def   : {defs:>2}/31
SpA   : {spa:>2}/31
SpD   : {spd:>2}/31
Spe   : {spe:>2}/31
```"""
        embed.add_field(name="🧬 IVs", value=stats_format, inline=True)
        
        # 5. Obtener Imágenes
        try:
            dex_id = await servicios.obtener_id_por_nombre(self.bot.session, nombre)
            if dex_id:
                path_shiny = "shiny/" if es_shiny else ""
                img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{path_shiny}{dex_id}.png"
                embed.set_image(url=img_url)
                thumb_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{path_shiny}{dex_id}.png"
                embed.set_thumbnail(url=thumb_url)
        except Exception as e:
            print(f"Error cargando imágenes: {e}")
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IvsCommands(bot))