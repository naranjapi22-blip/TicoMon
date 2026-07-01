import re

import discord
from discord.ext import commands
import database
import math
from logger_config import log # Necesario para el log
from discord.ui import View
import records
from candy import add_candy_for_pokemon
from records import recalcular_record_liberado
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
class VistaConfirmarLiberacion(
    discord.ui.View
):

    def __init__(
        self,
        pokemon_id
    ):
        super().__init__(
            timeout=60
        )

        self.pokemon_id = pokemon_id
        self.confirmado = False

    @discord.ui.button(
        label="Liberar",
        style=discord.ButtonStyle.danger,
        emoji="🗑️"
    )
    async def liberar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.confirmado = True

        await interaction.response.defer()

        self.stop()

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.secondary,
        emoji="❌"
    )
    async def cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="❌ Liberación cancelada.",
            view=None
        )

        self.stop()


class VistaConfirmarLiberacionLote(discord.ui.View):
    def __init__(self, author: discord.Member, captura_ids: list[int]):
        super().__init__(timeout=60)
        self.author = author
        self.captura_ids = captura_ids
        self.confirmado = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(
                "❌ Solo quien ejecutó el comando puede confirmar.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="Confirmar liberación",
        style=discord.ButtonStyle.danger,
        emoji="🗑️",
    )
    async def confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.confirmado = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.secondary,
        emoji="❌",
    )
    async def cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.edit_message(
            content="❌ Liberación cancelada.",
            embed=None,
            view=None,
        )
        self.stop()


def _linea_preview_liberar(pokemon: dict, extra: str = "") -> str:
    shiny = "✨ " if pokemon.get("es_shiny") else ""
    sufijo = f" {extra}" if extra else ""
    return (
        f"• {shiny}**{_nombre_display(pokemon['nombre'])}** "
        f"`{pokemon['id']}` · `{int(pokemon['iv_pct'])}%` IV{sufijo}"
    )


def _embed_preview_liberar(preview: dict) -> discord.Embed:
    liberables = preview["liberables"]
    no_encontrados = preview["no_encontrados"]
    con_record = [p for p in liberables if p.get("tipo_record")]

    desc = "Revisa la lista antes de liberar. Esta acción no se puede deshacer."
    if con_record:
        desc += (
            "\n\n⚠️ Los Pokémon con récord de tamaño serán liberados y "
            "el sistema buscará automáticamente un nuevo récord."
        )

    embed = discord.Embed(
        title="🗑️ Confirmar liberación",
        description=desc,
        color=discord.Color.orange(),
    )

    if liberables:
        lineas = [
            _linea_preview_liberar(
                p,
                extra=(
                    f"· récord **{p['tipo_record']}**"
                    if p.get("tipo_record")
                    else ""
                ),
            )
            for p in liberables[:20]
        ]
        extra = len(liberables) - 20
        if extra > 0:
            lineas.append(f"_…y {extra} más_")
        embed.add_field(
            name=f"A liberar ({len(liberables)})",
            value="\n".join(lineas),
            inline=False,
        )

    if no_encontrados:
        ids_txt = ", ".join(f"`{i}`" for i in no_encontrados[:15])
        extra = len(no_encontrados) - 15
        if extra > 0:
            ids_txt += f" _…y {extra} más_"
        embed.add_field(
            name=f"No encontrados ({len(no_encontrados)})",
            value=ids_txt,
            inline=False,
        )

    if liberables:
        embed.set_footer(text="Pulsa Confirmar para liberar todos los de la lista.")
    else:
        embed.set_footer(text="No hay Pokémon liberables en esta selección.")

    return embed


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


_ID_SPLIT = re.compile(r"[\s,;]+")
_INVISIBLE = re.compile(
    r"[\u200b-\u200d\ufeff\u2060\u00ad\u200e\u200f\u202a-\u202e\u2066-\u2069"
    r"\u00a0\u202f\u205f\u3000"
    r"]+"
)
_HASH_ID = re.compile(r"#(\d+)")


def _parsear_ids_liberar(texto: str) -> list[int]:
    ids: list[int] = []
    vistos: set[int] = set()
    texto = _INVISIBLE.sub("", texto)
    for part in _ID_SPLIT.split(texto):
        part = _INVISIBLE.sub("", part).strip().strip("`[]#")
        if not part:
            continue
        hash_match = _HASH_ID.search(part)
        if hash_match:
            cap_id = int(hash_match.group(1))
        else:
            try:
                cap_id = int(part)
            except ValueError:
                continue
        if cap_id not in vistos:
            vistos.add(cap_id)
            ids.append(cap_id)
    return ids


def _texto_db(val, campo: str = "valor") -> str:
    """Normaliza valores de BD a str (p. ej. tipos array o composite)."""
    if val is None:
        return "?"
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    if isinstance(val, (list, tuple)):
        log.warning(
            f"[LIBERAR] Campo {campo} con tipo {type(val).__name__}: {val!r}"
        )
        return _texto_db(val[0], campo) if val else "?"
    return str(val)


def _nombre_display(val) -> str:
    return _texto_db(val, "nombre").capitalize()


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
        embed = discord.Embed(
            title=f"{emoji_shiny}{nombre.capitalize()}",
            color=color
        )

        # Intentamos obtener la información del Pokémon
        pokemon = database.obtener_pokemon_local_nombre(nombre)

        # Si no existe exactamente, buscamos la especie base
        if not pokemon and "-" in nombre:
            nombre_base = nombre.split("-", 1)[0]
            pokemon = database.obtener_pokemon_local_nombre(nombre_base)

        # Siempre usamos el ID del caché en lugar del LEFT JOIN
        gif_id = None

        if pokemon:
            dex_id = pokemon.get(
                "pokeapi_id",
                pokemon["id"]
            )

            gif_id = obtener_id_gif(dex_id)
        nat_stats = NATURALEZAS.get(
            naturaleza.capitalize(),
            NATURALEZAS["Fuerte"]
        )

        def format_stat_con_nat(base_lvl50, iv, stat_name):
            if stat_name == 'hp': return f"**{base_lvl50:>3}** | {iv:>2}/31"
            key = STAT_MAP.get(stat_name)
            mult = nat_stats.get(key, 1.0)
            val = math.floor(base_lvl50 * mult)
            flecha = " ⬆️" if mult > 1.0 else (" ⬇️" if mult < 1.0 else "")
            return f"**{val:>3}**{flecha} | {iv:>2}/31"

        if pokemon:

            b = {
                "hp": pokemon["hp"],
                "attack": pokemon["attack"],
                "defense": pokemon["defense"],
                "special-attack": pokemon["special_attack"],
                "special-defense": pokemon["special_defense"],
                "speed": pokemon["speed"]
            }
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

                path_folder = "shiny" if es_shiny else "regular"

                url_gif = (
                    "https://pub-23cb564f6c174627926c1ac0409563d4.r2.dev/"
                    f"gifs_calidad/{path_folder}/{gif_id}.gif?v=2"
                )

                embed.set_image(url=url_gif)

            await ctx.send(embed=embed, ephemeral=True)
            return

        except Exception as e:
            import traceback

            print("=== ERROR GIF IVS ===")
            traceback.print_exc()

            log.error(f"Error cargando GIF: {e}", exc_info=True)

            await ctx.send(embed=embed, ephemeral=True)
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

    @commands.command(name="liberar")
    async def liberar(self, ctx, id_pokemon: int):

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT
                    pokemon_nombre,
                    es_shiny,
                    iv_hp,
                    iv_atk,
                    iv_def,
                    iv_spa,
                    iv_spd,
                    iv_spe
                FROM capturas
                WHERE id = %s
                AND user_id = %s
            """, (
                str(id_pokemon),
                str(ctx.author.id)
            ))

            resultado = cursor.fetchone()

            if not resultado:

                await ctx.send(
                    "❌ No existe ningún Pokémon con ese ID en tu inventario."
                )

                return

            nombre, shiny, hp, atk, de, spa, spd, spe = resultado
            nombre = _texto_db(nombre, "pokemon_nombre")

            cursor.execute("""
                SELECT
                    pokemon_nombre,
                    id_pokemon_grande,
                    id_pokemon_pequeno
                FROM RECORDS_ESPECIE
                WHERE id_pokemon_grande = %s
                OR id_pokemon_pequeno = %s
            """, (
                str(id_pokemon),
                str(id_pokemon)
            ))

            record = cursor.fetchone()

            tipo_record = None

            vista = VistaConfirmarLiberacion(id_pokemon)
            
            if record:

                if str(record[1]) == str(id_pokemon):

                    tipo_record = "XXL"

                elif str(record[2]) == str(id_pokemon):

                    tipo_record = "XXS"

                await ctx.send(
                    f"⚠️ **{_nombre_display(nombre)}** posee un récord "
                    f"de tamaño **{tipo_record}**.\n\n"
                    f"Si lo liberas, el sistema buscará "
                    f"automáticamente un nuevo récord.\n\n"
                    f"¿Deseas continuar?",
                    view=vista
                )

                await vista.wait()

                if not vista.confirmado:

                    return

                recalcular_record_liberado(
                    cursor,
                    nombre.lower(),
                    id_pokemon,
                    tipo_record
                )
            else:
                await ctx.send(
                    f"**{nombre.capitalize()}** será liberado."
                    f"(ID `{id_pokemon}`)\n"
                    f"¿Deseas continuar?",
                    view=vista
                )

                await vista.wait()

                if not vista.confirmado:

                    return

            # Eliminar Pokémon
            cursor.execute("""
                DELETE FROM capturas
                WHERE id = %s
                AND user_id = %s
            """, (
                str(id_pokemon),
                str(ctx.author.id)
            ))

            conn.commit()

            # Dar caramelo
            add_candy_for_pokemon(
                ctx.author.id,
                nombre,
                1
            )

            emoji = "✨" if shiny else ""

            cursor.execute(
                """
                SELECT tipos
                FROM pokemon_data
                WHERE nombre = %s
                """,
                (nombre.lower(),)
            )

            row = cursor.fetchone()

            if not row:

                return

            tipo_primario = database.tipo_primario_desde_tipos(row[0] if row else None)

            await ctx.send(
                f"🗑️ Liberaste a {emoji} **{_nombre_display(nombre)}** "
                f"(ID `{id_pokemon}`)\n"
                f"🍬 Recibiste 1 caramelo {tipo_primario}."
            )

        except Exception as e:

            conn.rollback()

            await ctx.send(
                "❌ Ocurrió un error al liberar el Pokémon."
            )

            print(
                f"[LIBERAR ERROR] {e}"
            )
            log.error(f"[LIBERAR ERROR] user_id={ctx.author.id} id={id_pokemon}: {e}", exc_info=True)

        finally:

            cursor.close()
            conn.close()

    @commands.command(name="new-liberar")
    async def new_liberar(self, ctx, *, ids: str):
        captura_ids = _parsear_ids_liberar(ids)

        if not captura_ids:
            return await ctx.send(
                "❌ Indica al menos un ID. Ejemplo: `!new-liberar 101, 202, 303`"
            )

        log.info(
            f"[NEW-LIBERAR] Preview solicitado por user_id={ctx.author.id} "
            f"ids={captura_ids}"
        )

        try:
            preview = database.preview_liberar_capturas(ctx.author.id, captura_ids)
        except Exception as e:
            log.error(f"[NEW-LIBERAR ERROR] Preview falló: {e}", exc_info=True)
            return await ctx.send("❌ Ocurrió un error al consultar los Pokémon.")

        liberables = preview["liberables"]
        no_encontrados = preview["no_encontrados"]
        con_record = sum(1 for p in liberables if p.get("tipo_record"))

        log.info(
            f"[NEW-LIBERAR] Preview user_id={ctx.author.id} "
            f"liberables={len(liberables)} con_record={con_record} "
            f"no_encontrados={len(no_encontrados)}"
        )

        if not liberables and not no_encontrados:
            return await ctx.send("❌ No se encontraron Pokémon para esos IDs.")

        embed = _embed_preview_liberar(preview)

        if not liberables:
            return await ctx.send(embed=embed)

        ids_a_liberar = [p["id"] for p in liberables]
        vista = VistaConfirmarLiberacionLote(ctx.author, ids_a_liberar)
        mensaje = await ctx.send(embed=embed, view=vista)
        await vista.wait()

        if not vista.confirmado:
            log.info(
                f"[NEW-LIBERAR] Cancelado por user_id={ctx.author.id} "
                f"ids={ids_a_liberar}"
            )
            return

        try:
            liberados = database.liberar_capturas_usuario(
                ctx.author.id,
                ids_a_liberar,
            )
        except Exception as e:
            log.error(f"[NEW-LIBERAR ERROR] Liberación falló: {e}", exc_info=True)
            await mensaje.edit(
                content="❌ Ocurrió un error al liberar los Pokémon.",
                embed=None,
                view=None,
            )
            return

        if not liberados:
            await mensaje.edit(
                content="No se liberó ningún Pokémon.",
                embed=None,
                view=None,
            )
            return

        lineas = []
        max_detalle = 15
        for pokemon in liberados[:max_detalle]:
            emoji = "✨ " if pokemon["es_shiny"] else ""
            lineas.append(
                f"• {emoji}**{_nombre_display(pokemon['nombre'])}** "
                f"`{pokemon['id']}` → 🍬 {pokemon['tipo_caramelo']}"
            )
        extra = len(liberados) - max_detalle
        if extra > 0:
            lineas.append(f"_…y {extra} más_")

        log.info(
            f"[NEW-LIBERAR] Completado user_id={ctx.author.id} "
            f"liberados={len(liberados)} ids={[p['id'] for p in liberados]}"
        )

        resumen = (
            f"🗑️ Liberaste **{len(liberados)}** Pokémon. "
            f"🍬 Recibiste **{len(liberados)}** caramelos.\n"
            + "\n".join(lineas)
        )
        if no_encontrados:
            resumen += (
                "\n\n⚠️ IDs ignorados: "
                + ", ".join(map(str, no_encontrados))
            )

        await mensaje.edit(
            content=resumen,
            embed=None,
            view=None,
        )


async def setup(bot):
    await bot.add_cog(IvsCommands(bot))
    