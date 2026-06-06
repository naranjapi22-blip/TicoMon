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
        
        # SQL actualizado para incluir la columna 'naturaleza'
        cursor.execute("""
            SELECT pokemon_nombre, iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe, es_shiny, naturaleza
            FROM capturas 
            WHERE id = %s AND user_id = %s
        """, (str(id_pokemon), str(ctx.author.id)))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            await ctx.send("❌ No existe ningún Pokémon con ese ID en **tu** inventario.")
            return

        nombre, hp, atk, defs, spa, spd, spe, es_shiny, naturaleza = resultado
        ivs_list = [hp, atk, defs, spa, spd, spe]
        total = sum(ivs_list)
        porcentaje = round((total / 186) * 100, 2)
        
        # Color dinámico
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
        
        # Obtener datos de la PokeAPI
        data, species = await servicios.obtener_pokemon(self.bot.session, nombre)
        
        # 1. Estadísticas Detalladas
        if data:
            b = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            def format_stat(lvl50, iv):
                return f"**{lvl50:>3}** | {iv:>2}/31"

            embed.add_field(name="📊 Estadísticas (Lvl 50 | IVs)", value="━━━━━━━━━━━━━━━━━━━━", inline=False)
            embed.add_field(name="❤️ HP",  value=format_stat(calcular_hp_lvl50(b.get('hp',0), hp), hp), inline=True)
            embed.add_field(name="⚔️ Atk", value=format_stat(calcular_stat_lvl50(b.get('attack',0), atk), atk), inline=True)
            embed.add_field(name="🛡️ Def", value=format_stat(calcular_stat_lvl50(b.get('defense',0), defs), defs), inline=True)
            embed.add_field(name="🔮 SpA", value=format_stat(calcular_stat_lvl50(b.get('special-attack',0), spa), spa), inline=True)
            embed.add_field(name="✨ SpD", value=format_stat(calcular_stat_lvl50(b.get('special-defense',0), spd), spd), inline=True)
            embed.add_field(name="⚡ Spe", value=format_stat(calcular_stat_lvl50(b.get('speed',0), spe), spe), inline=True)

        # 2. Lógica de Región
        gen_url = species.get('generation', {}).get('url', '')
        gen_id = gen_url.split('/')[-2] if gen_url else "Desconocida"
        regiones = {
            '1': 'Kanto', '2': 'Johto', '3': 'Hoenn', '4': 'Sinnoh', 
            '5': 'Teselia', '6': 'Kalos', '7': 'Alola', '8': 'Galar', '9': 'Paldea'
        }
        nombre_region = regiones.get(gen_id, "Desconocida")

        # 3. Detalles Generales
        detalles = (
            f"🆔 **ID Único:** {id_pokemon}\n"
            f"🗺️ **Región:** {nombre_region}\n"
            f"🍃 **Naturaleza:** {naturaleza.capitalize()}\n"
            f"⭐ **Calidad:** {calidad}\n"
            f"📈 **Potencial Total:** {total}/186 ({porcentaje}%)\n"
            f"✨ **Variocolor:** {'Sí' if es_shiny else 'No'}"
        )
        embed.add_field(name="📝 Detalles de Captura", value=detalles, inline=False)
        
        # 4. Imágenes
        try:
            dex_id = await servicios.obtener_id_por_nombre(self.bot.session, nombre)
            if dex_id:
                path_s = "shiny/" if es_shiny else ""
                url_base = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
                embed.set_image(url=f"{url_base}other/official-artwork/{path_s}{dex_id}.png")
                embed.set_thumbnail(url=f"{url_base}{path_s}{dex_id}.png")
        except Exception as e:
            print(f"Error cargando imágenes: {e}")
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IvsCommands(bot))