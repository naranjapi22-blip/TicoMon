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
            color, calidad = discord.Color.gold(), "💎 Épico"
        elif porcentaje >= 70: 
            color, calidad = discord.Color.green(), "🔥 Excelente"
        else: 
            color, calidad = discord.Color.blue(), "⏺️ Normal"

        emoji_shiny = "✨ " if es_shiny else ""
        embed = discord.Embed(title=f"{emoji_shiny}{nombre.capitalize()}", color=color)
        
        data, species = await servicios.obtener_pokemon(self.bot.session, nombre)
        nat_stats = NATURALEZAS.get(naturaleza.capitalize(), NATURALEZAS["Fuerte"])

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

        gen_url = species.get('generation', {}).get('url', '')
        gen_id = gen_url.split('/')[-2] if gen_url else "Desconocida"
        regiones = {'1': 'Kanto', '2': 'Johto', '3': 'Hoenn', '4': 'Sinnoh', '5': 'Teselia', '6': 'Kalos', '7': 'Alola', '8': 'Galar', '9': 'Paldea'}
        
        detalles = (
            f"🆔 **ID Único:** {id_pokemon}\n"
            f"🗺️ **Región:** {regiones.get(gen_id, 'Desconocida')}\n"
            f"🍃 **Naturaleza:** {naturaleza.capitalize()}\n"
            f"⭐ **Calidad:** {calidad}\n"
            f"📈 **Potencial Total:** {total}/186 ({porcentaje}%)\n"
            f"✨ **Variocolor:** {'Sí' if es_shiny else 'No'}"
        )
        embed.add_field(name="📝 Detalles de Captura", value=detalles, inline=False)
        
        try:
            dex_id = await servicios.obtener_id_por_nombre(self.bot.session, nombre)
            if dex_id:
                path_s = "shiny/" if es_shiny else ""
                url_base = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
                embed.set_image(url=f"{url_base}other/official-artwork/{path_s}{dex_id}.png")
                embed.set_thumbnail(url=f"{url_base}{path_s}{dex_id}.png")
        except Exception: pass
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IvsCommands(bot))