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

NATURALEZAS = {
    "Fuerte": {"atq": 1.0, "def": 1.0, "esp_atq": 1.0, "esp_def": 1.0, "vel": 1.0},
    "Dócil": {"atq": 1.0, "def": 1.0, "esp_atq": 1.0, "esp_def": 1.0, "vel": 1.0},
    "Seria": {"atq": 1.0, "def": 1.0, "esp_atq": 1.0, "esp_def": 1.0, "vel": 1.0},
    "Rara": {"atq": 1.0, "def": 1.0, "esp_atq": 1.0, "esp_def": 1.0, "vel": 1.0},
    "Agitada": {"atq": 1.0, "def": 1.0, "esp_atq": 1.0, "esp_def": 1.0, "vel": 1.0},
    "Huraña": {"atq": 1.1, "def": 0.9, "esp_atq": 1.0, "esp_def": 1.0, "vel": 1.0},
    "Firme": {"atq": 1.1, "def": 1.0, "esp_atq": 0.9, "esp_def": 1.0, "vel": 1.0},
    "Pícara": {"atq": 1.1, "def": 1.0, "esp_atq": 1.0, "esp_def": 0.9, "vel": 1.0},
    "Audaz": {"atq": 1.1, "def": 1.0, "esp_atq": 1.0, "esp_def": 1.0, "vel": 0.9},
    "Osada": {"atq": 0.9, "def": 1.1, "esp_atq": 1.0, "esp_def": 1.0, "vel": 1.0},
    "Floja": {"atq": 1.0, "def": 1.1, "esp_atq": 1.0, "esp_def": 0.9, "vel": 1.0},
    "Plácida": {"atq": 1.0, "def": 1.1, "esp_atq": 1.0, "esp_def": 1.0, "vel": 0.9},
    "Modesta": {"atq": 0.9, "def": 1.0, "esp_atq": 1.1, "esp_def": 1.0, "vel": 1.0},
    "Afable": {"atq": 1.0, "def": 0.9, "esp_atq": 1.1, "esp_def": 1.0, "vel": 1.0},
    "Mansa": {"atq": 1.0, "def": 1.0, "esp_atq": 1.1, "esp_def": 1.0, "vel": 0.9},
    "Alocada": {"atq": 1.0, "def": 1.0, "esp_atq": 1.1, "esp_def": 0.9, "vel": 1.0},
    "Serena": {"atq": 0.9, "def": 1.0, "esp_atq": 1.0, "esp_def": 1.1, "vel": 1.0},
    "Amable": {"atq": 1.0, "def": 0.9, "esp_atq": 1.0, "esp_def": 1.1, "vel": 1.0},
    "Cauta": {"atq": 1.0, "def": 1.0, "esp_atq": 0.9, "esp_def": 1.1, "vel": 1.0},
    "Grosera": {"atq": 1.0, "def": 1.0, "esp_atq": 1.0, "esp_def": 1.1, "vel": 0.9},
    "Tímida": {"atq": 0.9, "def": 1.0, "esp_atq": 1.0, "esp_def": 1.0, "vel": 1.1},
    "Activa": {"atq": 1.0, "def": 0.9, "esp_atq": 1.0, "esp_def": 1.0, "vel": 1.1},
    "Alegre": {"atq": 1.0, "def": 1.0, "esp_atq": 0.9, "esp_def": 1.0, "vel": 1.1},
    "Ingenua": {"atq": 1.0, "def": 1.0, "esp_atq": 1.0, "esp_def": 0.9, "vel": 1.1},
    "Quietud": {"atq": 1.0, "def": 0.9, "esp_atq": 1.1, "esp_def": 1.0, "vel": 1.0}
}

STAT_MAP = {
    'attack': 'atq',
    'defense': 'def',
    'special-attack': 'esp_atq',
    'special-defense': 'esp_def',
    'speed': 'vel'
}

class IvsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ivs")
    async def ver_ivs(self, ctx, id_pokemon: int):
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Obtenemos el tamano_factor de la base de datos
        cursor.execute("""
            SELECT pokemon_nombre, iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe, es_shiny, naturaleza, tamano_factor
            FROM capturas 
            WHERE id = %s AND user_id = %s
        """, (str(id_pokemon), str(ctx.author.id)))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            await ctx.send("❌ No existe ningún Pokémon con ese ID en **tu** inventario.")
            return

        # 2. Desempaquetamos incluyendo el tamano
        nombre, hp, atk, defs, spa, spd, spe, es_shiny, naturaleza, tamano = resultado
        
        # Lógica de etiqueta de tamaño
        tamano = float(tamano or 1.0) # Por si hay algún nulo antiguo
        if tamano < 0.7: etiqueta_tamano = "XXS 🤏"
        elif tamano > 1.3: etiqueta_tamano = "XXL 👑"
        else: etiqueta_tamano = "Normal"

        ivs_list = [hp, atk, defs, spa, spd, spe]
        total = sum(ivs_list)
        porcentaje = round((total / 186) * 100, 2)
        
        # Color dinámico
        if porcentaje >= 85: color, calidad = discord.Color.gold(), "💎 Épico"
        elif porcentaje >= 70: color, calidad = discord.Color.green(), "🔥 Excelente"
        else: color, calidad = discord.Color.blue(), "⏺️ Normal"

        emoji_shiny = "✨ " if es_shiny else ""
        embed = discord.Embed(title=f"{emoji_shiny}{nombre.capitalize()}", color=color)
        
        data, species = await servicios.obtener_pokemon(self.bot.session, nombre)
        nat_stats = NATURALEZAS.get(naturaleza.capitalize(), NATURALEZAS["Fuerte"])

        # (Mantén tu función format_stat_con_nat aquí adentro igual que antes)
        def format_stat_con_nat(base_lvl50, iv, stat_name):
            if stat_name == 'hp': return f"**{base_lvl50:>3}** | {iv:>2}/31"
            key = STAT_MAP.get(stat_name)
            mult = nat_stats.get(key, 1.0)
            val = math.floor(base_lvl50 * mult)
            flecha = " ⬆️" if mult > 1.0 else (" ⬇️" if mult < 1.0 else "")
            return f"**{val:>3}**{flecha} | {iv:>2}/31"

        if data:
            b = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            embed.add_field(name="📊 Estadísticas (Lvl 50 | IVs)", value="━━━━━━━━━━━━━━━━━━━━", inline=False)
            embed.add_field(name="❤️ HP",  value=format_stat_con_nat(calcular_hp_lvl50(b.get('hp',0), hp), hp, "hp"), inline=True)
            embed.add_field(name="⚔️ Atk", value=format_stat_con_nat(calcular_stat_lvl50(b.get('attack',0), atk), atk, "attack"), inline=True)
            embed.add_field(name="🛡️ Def", value=format_stat_con_nat(calcular_stat_lvl50(b.get('defense',0), defs), defs, "defense"), inline=True)
            embed.add_field(name="🔮 SpA", value=format_stat_con_nat(calcular_stat_lvl50(b.get('special-attack',0), spa), spa, "special-attack"), inline=True)
            embed.add_field(name="✨ SpD", value=format_stat_con_nat(calcular_stat_lvl50(b.get('special-defense',0), spd), spd, "special-defense"), inline=True)
            embed.add_field(name="⚡ Spe", value=format_stat_con_nat(calcular_stat_lvl50(b.get('speed',0), spe), spe, "speed"), inline=True)

        detalles = (
            f"🆔 **ID Único:** {id_pokemon}\n"
            f"📏 **Tamaño:** {etiqueta_tamano} ({tamano}x)\n"
            f"🍃 **Naturaleza:** {naturaleza.capitalize()}\n"
            f"⭐ **Calidad:** {calidad}\n"
            f"📈 **Potencial Total:** {total}/186 ({porcentaje}%)\n"
        )
        embed.add_field(name="📝 Detalles", value=detalles, inline=False)
        
        # 3. Escalado Visual con servicios.procesar_sprite_pokemon
        try:
            dex_id = await servicios.obtener_id_por_nombre(self.bot.session, nombre)
            if dex_id:
                path_s = "shiny/" if es_shiny else ""
                url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{path_s}{dex_id}.png"
                
                async with self.bot.session.get(url) as resp:
                    img_data = await resp.read()
                    img_base = Image.open(io.BytesIO(img_data)).convert("RGBA")
                    
                    # Llamada a la nueva función de servicios (que debes añadir abajo)
                    img_final = servicios.procesar_sprite_pokemon(img_base, tamano)
                    
                    buffer = io.BytesIO()
                    img_final.save(buffer, format="PNG")
                    buffer.seek(0)
                    
                    file = discord.File(buffer, filename="pokemon.png")
                    embed.set_image(url="attachment://pokemon.png")
                    await ctx.send(embed=embed, file=file)
                    return # Salimos para no enviar el embed dos veces
        except Exception as e:
            log.error(f"Error imagen: {e}")
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IvsCommands(bot))