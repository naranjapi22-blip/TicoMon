import discord
from discord.ext import commands
import database
import servicios
import math
import io # Necesario para io.BytesIO
from PIL import Image # Necesario para Image.open
from logger_config import log # Necesario para el log
from datetime import datetime, timezone # Asegúrate de tener este también
from discord.ui import Button, View
import records
from mapeo_pokes import obtener_id_gif
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
class PaginatorView(View):
    def __init__(self, pages, user):
        super().__init__(timeout=60)
        self.pages = pages
        self.user = user
        self.current_page = 0

    def create_embed(self):
        embed = discord.Embed(title=f"🏆 Récords de {self.user.display_name}", color=discord.Color.gold())
        embed.description = self.pages[self.current_page]
        embed.set_footer(text=f"Página {self.current_page + 1} de {len(self.pages)}")
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def prev(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user != self.user: return
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.create_embed())

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user != self.user: return
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.create_embed())
class IvsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ivs")
    async def ver_ivs(self, ctx, id_pokemon: int):
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # 1. Obtenemos datos incluyendo nombre, tamaño y el dex_id de la tabla pokemon_data
        cursor.execute("""
            SELECT c.pokemon_nombre, c.iv_hp, c.iv_atk, c.iv_def, c.iv_spa, c.iv_spd, c.iv_spe, 
                   c.es_shiny, c.naturaleza, c.tamano_factor, p.id
            FROM capturas c
            LEFT JOIN pokemon_data p
            ON c.pokemon_nombre = p.nombre
            WHERE c.id = %s AND c.user_id = %s
        """, (str(id_pokemon), str(ctx.author.id)))
        
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            await ctx.send("❌ No existe ningún Pokémon con ese ID en **tu** inventario.")
            return

        nombre, hp, atk, defs, spa, spd, spe, es_shiny, naturaleza, tamano, dex_id = resultado
        
        # 2. Verificación de Récord para el Boost Visual
        estado_record = records.obtener_estado_record(cursor, nombre.lower(), id_pokemon)
        conn.close() 
        
        # Lógica de etiqueta de tamaño
        tamano = float(tamano or 1.0)
        if tamano <= 0.8: etiqueta_tamano = "XXS 🤏"
        elif tamano >= 1.2: etiqueta_tamano = "XXL 👑"
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
        
        try:
            if dex_id is not None:

                # Obtenemos el ID corregido usando tu archivo de mapeo
                id_final = obtener_id_gif(dex_id)

                path_folder = "shiny" if es_shiny else "regular"

                url_gif = (
                    f"https://www.shinyhunters.com/images/"
                    f"{path_folder}/{id_final}.gif"
                )

                embed.set_image(url=url_gif)

            await ctx.send(embed=embed)
            return

        except Exception as e:
            log.error(f"Error cargando GIF: {e}")
            await ctx.send(embed=embed)
        except Exception as e:
            log.error(f"Error cargando GIF: {e}")
            await ctx.send(embed=embed)
        except Exception as e:
            log.error(f"Error cargando GIF: {e}")
            await ctx.send(embed=embed)
    @commands.command(name="misrecords")
    async def ver_mis_records(self, ctx):
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # 1. Traemos los IDs además de los nombres y flags
        cursor.execute("""
            SELECT pokemon_nombre, id_pokemon_grande, id_pokemon_pequeno,
                   CASE WHEN user_id_grande = %s THEN '👑' ELSE '' END as es_grande,
                   CASE WHEN user_id_pequeno = %s THEN '🤏' ELSE '' END as es_pequeno
            FROM RECORDS_ESPECIE 
            WHERE user_id_grande = %s OR user_id_pequeno = %s
        """, (str(ctx.author.id), str(ctx.author.id), str(ctx.author.id), str(ctx.author.id)))
        
        registros = cursor.fetchall()
        conn.close()
        
        if not registros:
            await ctx.send("❌ Aún no posees ningún récord.")
            return

        # 2. Dividir en páginas (10 récords por página)
        items_por_pagina = 10
        chunks = [registros[i:i + items_por_pagina] for i in range(0, len(registros), items_por_pagina)]
        pages = []

        for chunk in chunks:
            text = ""
            for nombre, id_g, id_p, es_g, es_p in chunk:
                # Lista para almacenar los bloques de ID (Emoji + ID)
                ids_texto = []
                
                # Si es grande, añadimos su ID a la lista
                if es_g:
                    ids_texto.append(f"👑`{id_g}`")
                
                # Si es pequeño, añadimos su ID a la lista
                if es_p:
                    ids_texto.append(f"🤏`{id_p}`")
                
                # Unimos ambos elementos con un espacio
                text += f"• **{nombre.capitalize():<12}** {' '.join(ids_texto)}\n"
            pages.append(text)

        # 3. Enviar mensaje con el paginador
        view = PaginatorView(pages, ctx.author)
        await ctx.send(embed=view.create_embed(), view=view)
    @commands.command(name="records")
    async def ver_records(self, ctx, *, pokemon_nombre: str):
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id_pokemon_grande, user_id_grande, tamano_grande, fecha_grande,
                   id_pokemon_pequeno, user_id_pequeno, tamano_pequeno, fecha_pequeno
            FROM RECORDS_ESPECIE 
            WHERE pokemon_nombre = %s
        """, (pokemon_nombre.lower(),))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            await ctx.send(f"❌ No hay récords para **{pokemon_nombre.capitalize()}**. ¡Sé el primero!")
            return

        id_g, user_g, tam_g, fec_g, id_p, user_p, tam_p, fec_p = row
        
        # Diseño compacto
        embed = discord.Embed(title=f"🏆 Salón de la Fama: {pokemon_nombre.capitalize()}", color=discord.Color.gold())
        
        embed.add_field(
            name="👑 Récord XXL", 
            value=f"**Tamaño:** {tam_g}x | **ID:** {id_g}\n**Dueño:** <@{user_g}> | **Fecha:** {fec_g}", 
            inline=False
        )
        embed.add_field(
            name="🤏 Récord XXS", 
            value=f"**Tamaño:** {tam_p}x | **ID:** {id_p}\n**Dueño:** <@{user_p}> | **Fecha:** {fec_p}", 
            inline=False
        )
        
        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(IvsCommands(bot))
    