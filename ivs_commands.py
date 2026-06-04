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
        
        # --- CORRECCIÓN DE SEGURIDAD APLICADA AQUÍ ---
        # Filtramos por ID de captura Y por el ID del usuario que envió el comando
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
        
        # Color dinámico y etiqueta de calidad general
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
        
        # 3. Estadísticas Base
        try:
            data, _ = await servicios.obtener_pokemon(self.bot.session, nombre)
            if data:
                b_stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
                base_format = f"""```yaml
Hp             : {b_stats.get('hp', 0)}
Attack         : {b_stats.get('attack', 0)}
Defense        : {b_stats.get('defense', 0)}
Special-attack : {b_stats.get('special-attack', 0)}
Special-defense: {b_stats.get('special-defense', 0)}
Speed          : {b_stats.get('speed', 0)}
```"""
                embed.add_field(name="📊 Estadísticas Base", value=base_format, inline=False)
        except Exception as e:
            print(f"Error cargando stats base en ivs: {e}")

        # 4. Bloque de Valores Individuales (IVs)
        stats_format = f"""```yaml
Hp             : {hp:>2}/31 [{evaluar_iv(hp)}]
Attack         : {atk:>2}/31 [{evaluar_iv(atk)}]
Defense        : {defs:>2}/31 [{evaluar_iv(defs)}]
Special-attack : {spa:>2}/31 [{evaluar_iv(spa)}]
Special-defense: {spd:>2}/31 [{evaluar_iv(spd)}]
Speed          : {spe:>2}/31 [{evaluar_iv(spe)}]
```"""
        embed.add_field(name="🧬 Valores Individuales (IVs)", value=stats_format, inline=False)
        
        # 5. Obtener IDs y URLs de imágenes
        try:
            dex_id = await servicios.obtener_id_por_nombre(self.bot.session, nombre)
            if dex_id:
                path_shiny = "shiny/" if es_shiny else ""
                
                # Imagen grande (Official Artwork)
                img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{path_shiny}{dex_id}.png"
                embed.set_image(url=img_url)
                
                # Miniatura arriba a la derecha
                thumb_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{path_shiny}{dex_id}.png"
                embed.set_thumbnail(url=thumb_url)
        except Exception as e:
            print(f"Error cargando imágenes para IVs: {e}")
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IvsCommands(bot))