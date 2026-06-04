import discord
from discord.ext import commands
from database import get_connection
import servicios
import math

# Fórmulas oficiales de Pokémon (siempre redondean hacia abajo)
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
        ivs_list = [hp, atk, defs, spa, spd, spe]
        total = sum(ivs_list)
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
        
        embed = discord.Embed(title=f"{emoji_shiny}{nombre.capitalize()}", color=color)
        
        # 1. Detalles Generales
        detalles = (
            f"🆔 **ID Único:** {id_pokemon}\n"
            f"⭐ **Calidad:** {calidad}\n"
            f"📈 **Potencial Total:** {total}/186 ({porcentaje}%)\n"
            f"✨ **Variocolor:** {'Sí' if es_shiny else 'No'}"
        )
        embed.add_field(name="📝 Detalles de Captura", value=detalles, inline=False)
        
        # 2. Estadísticas Detalladas (Base + IVs + Lvl 50)
        try:
            data, _ = await servicios.obtener_pokemon(self.bot.session, nombre)
            if data:
                b = {s['stat']['name']: s['base_stat'] for s in data['stats']}
                stats_final_format = f"""```yaml
                Stat    Base   IVs     Lvl50
                ❤️ HP : {b.get('hp',0):>3}   {hp:>2}/31   {calcular_hp_lvl50(b.get('hp',0), hp):>3}
                ⚔️ Atk: {b.get('attack',0):>3}   {atk:>2}/31   {calcular_stat_lvl50(b.get('attack',0), atk):>3}
                🛡️ Def: {b.get('defense',0):>3}   {defs:>2}/31   {calcular_stat_lvl50(b.get('defense',0), defs):>3}
                🔮 SpA: {b.get('special-attack',0):>3}   {spa:>2}/31   {calcular_stat_lvl50(b.get('special-attack',0), spa):>3}
                ✨ SpD: {b.get('special-defense',0):>3}   {spd:>2}/31   {calcular_stat_lvl50(b.get('special-defense',0), spd):>3}
                ⚡ Spe: {b.get('speed',0):>3}   {spe:>2}/31   {calcular_stat_lvl50(b.get('speed',0), spe):>3}
                ```"""
                embed.add_field(name="📊 Estadísticas Detalladas", value=stats_final_format, inline=False)
        except Exception as e:
            print(f"Error cargando stats: {e}")
        
        # 3. Imágenes
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