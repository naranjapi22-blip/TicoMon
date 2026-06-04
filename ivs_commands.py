import discord
from discord.ext import commands
from database import get_connection
import servicios

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
            WHERE id = %s
        """, (str(id_pokemon),))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            await ctx.send("❌ No existe ningún Pokémon con ese ID.")
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
        
        # 2. Detalles Generales (adaptados a la captura)
        detalles = (
            f"🆔 **ID Único:** {id_pokemon}\n"
            f"⭐ **Calidad:** {calidad}\n"
            f"📈 **Potencial Total:** {total}/186 ({porcentaje}%)\n"
            f"✨ **Variocolor:** {'Sí' if es_shiny else 'No'}"
        )
        embed.add_field(name="📝 Detalles de Captura", value=detalles, inline=False)
        
        # 3. Bloque de estadísticas alineado (estilo consola/código)
        # Usamos yaml para que los números resalten un poco en Discord
        stats_format = f"""```yaml
Hp             : {hp}/31
Attack         : {atk}/31
Defense        : {defs}/31
Special-attack : {spa}/31
Special-defense: {spd}/31
Speed          : {spe}/31
```"""
        embed.add_field(name="📊 Valores Individuales (IVs)", value=stats_format, inline=False)
        
        # 4. Obtener IDs y URLs de imágenes
        try:
            dex_id = await servicios.obtener_id_por_nombre(self.bot.session, nombre)
            if dex_id:
                path_shiny = "shiny/" if es_shiny else ""
                
                # Imagen grande (Official Artwork)
                img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{path_shiny}{dex_id}.png"
                embed.set_image(url=img_url)
                
                # Miniatura arriba a la derecha (Sprite pequeño)
                thumb_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{path_shiny}{dex_id}.png"
                embed.set_thumbnail(url=thumb_url)
        except Exception as e:
            print(f"Error cargando imágenes para IVs: {e}")
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IvsCommands(bot))