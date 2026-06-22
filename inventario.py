import discord
from discord.ext import commands

import database
import servicios
from regiones import REGIONES

POR_PAGINA = 10

GENERACIONES = [
    (1, 151, 1),
    (152, 251, 2),
    (252, 386, 3),
    (387, 493, 4),
    (494, 649, 5),
    (650, 721, 6),
    (722, 809, 7),
    (810, 905, 8),
    (906, 1025, 9),
]

TIPOS_FILTRO = [
    ("todos", "Todos los tipos"),
    ("normal", "Normal"),
    ("fuego", "Fuego"),
    ("agua", "Agua"),
    ("planta", "Planta"),
    ("electrico", "Eléctrico"),
    ("hielo", "Hielo"),
    ("lucha", "Lucha"),
    ("veneno", "Veneno"),
    ("tierra", "Tierra"),
    ("volador", "Volador"),
    ("psiquico", "Psíquico"),
    ("bicho", "Bicho"),
    ("roca", "Roca"),
    ("fantasma", "Fantasma"),
    ("dragon", "Dragón"),
    ("siniestro", "Siniestro"),
    ("acero", "Acero"),
    ("hada", "Hada"),
]

TIPO_ALIASES = {
    "fuego": ("fuego", "fire"),
    "agua": ("agua", "water"),
    "planta": ("planta", "grass"),
    "electrico": ("electrico", "electric"),
    "hielo": ("hielo", "ice"),
    "lucha": ("lucha", "fighting"),
    "veneno": ("veneno", "poison"),
    "tierra": ("tierra", "ground"),
    "volador": ("volador", "flying"),
    "psiquico": ("psiquico", "psychic"),
    "bicho": ("bicho", "bug"),
    "roca": ("roca", "rock"),
    "fantasma": ("fantasma", "ghost"),
    "dragon": ("dragon",),
    "siniestro": ("siniestro", "dark"),
    "acero": ("acero", "steel"),
    "hada": ("hada", "fairy"),
    "normal": ("normal",),
}

ORDENES = {
    "nombre_asc": ("Nombre A → Z", lambda e: e["nombre"].lower()),
    "nombre_desc": ("Nombre Z → A", lambda e: e["nombre"].lower(), True),
    "id_asc": ("ID ↑ (antiguos)", lambda e: e["id"]),
    "id_desc": ("ID ↓ (recientes)", lambda e: e["id"], True),
    "iv_asc": ("IV% ↑ (menor)", lambda e: e["iv_pct"]),
    "iv_desc": ("IV% ↓ (mayor)", lambda e: e["iv_pct"], True),
}


def _generacion_desde_dex(dex_id: int | None) -> int | None:
    if not dex_id:
        return None
    for inicio, fin, gen in GENERACIONES:
        if inicio <= dex_id <= fin:
            return gen
    return None


def _region_desde_dex(dex_id: int | None) -> str | None:
    if not dex_id:
        return None
    for nombre, rango in REGIONES.items():
        if rango["inicio"] <= dex_id <= rango["fin"]:
            return nombre
    return None


def _coincide_tipo(tipos_raw: str, filtro: str) -> bool:
    if filtro == "todos":
        return True
    if not tipos_raw:
        return False
    tipos_db = [t.strip().lower() for t in tipos_raw.split(",")]
    aliases = TIPO_ALIASES.get(filtro, (filtro,))
    return any(alias in tipos_db for alias in aliases)


def _filtrar_entradas(entradas: list[dict], *, tipo, generacion, region) -> list[dict]:
    resultado = []
    for e in entradas:
        if not _coincide_tipo(e["tipos"], tipo):
            continue
        dex = e.get("dex_id")
        if generacion != "todas":
            if _generacion_desde_dex(dex) != int(generacion):
                continue
        if region != "todas":
            if _region_desde_dex(dex) != region:
                continue
        resultado.append(e)
    return resultado


def _ordenar_entradas(entradas: list[dict], orden: str) -> list[dict]:
    cfg = ORDENES.get(orden, ORDENES["id_desc"])
    key_fn = cfg[1]
    reverse = len(cfg) > 2 and cfg[2]
    return sorted(entradas, key=key_fn, reverse=reverse)


def _formatear_tipos(tipos_raw: str) -> str:
    if not tipos_raw:
        return "?"
    return ", ".join(t.strip().capitalize() for t in tipos_raw.split(",") if t.strip())


def _construir_embeds(entradas: list[dict], autor: discord.Member, pagina: int, filtros_activos: str) -> tuple[list[discord.Embed], int]:
    if not entradas:
        embed = discord.Embed(
            title=f"🎒 Inventario de {autor.display_name}",
            description="No hay Pokémon con los filtros seleccionados.",
            color=discord.Color.orange(),
        )
        embed.set_footer(text=filtros_activos)
        return [embed], 0

    paginas_datos = [entradas[i : i + POR_PAGINA] for i in range(0, len(entradas), POR_PAGINA)]
    total_paginas = len(paginas_datos)
    pagina = max(0, min(pagina, total_paginas - 1))
    embeds = []

    for i, bloque in enumerate(paginas_datos):
        lineas = []
        for e in bloque:
            shiny = "✨ " if e["es_shiny"] else ""
            tipos = _formatear_tipos(e.get("tipos", ""))
            dex = f"#{e['dex_id']}" if e.get("dex_id") else "?"
            lineas.append(
                f"{shiny}**{e['nombre'].capitalize()}** "
                f"`[{e['id']}]` · {tipos} · Dex {dex} · `{int(e['iv_pct'])}%`"
            )

        embed = discord.Embed(
            title=f"🎒 Inventario de {autor.display_name}",
            description="\n".join(lineas),
            color=discord.Color.green(),
        )
        embed.set_footer(
            text=f"Página {i + 1}/{total_paginas} · {filtros_activos} · !ivs [ID] para detalles"
        )
        embeds.append(embed)

    return embeds, pagina


class OrdenInventarioSelect(discord.ui.Select):
    def __init__(self, vista: "VistaInventario"):
        self.vista = vista
        options = [
            discord.SelectOption(label=label, value=key, default=(key == vista.orden))
            for key, (label, *_) in ORDENES.items()
        ]
        super().__init__(
            placeholder="📊 Ordenar por…",
            options=options,
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        self.vista.orden = self.values[0]
        self.vista.pagina = 0
        await self.vista.refrescar(interaction)


class TipoInventarioSelect(discord.ui.Select):
    def __init__(self, vista: "VistaInventario"):
        self.vista = vista
        options = [
            discord.SelectOption(
                label=label,
                value=valor,
                default=(valor == vista.filtro_tipo),
            )
            for valor, label in TIPOS_FILTRO
        ]
        super().__init__(
            placeholder="🧪 Filtrar por tipo…",
            options=options,
            min_values=1,
            max_values=1,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        self.vista.filtro_tipo = self.values[0]
        self.vista.pagina = 0
        await self.vista.refrescar(interaction)


class GeneracionInventarioSelect(discord.ui.Select):
    def __init__(self, vista: "VistaInventario"):
        self.vista = vista
        options = [discord.SelectOption(label="Todas las generaciones", value="todas", default=(vista.filtro_gen == "todas"))]
        for _, _, gen in GENERACIONES:
            options.append(
                discord.SelectOption(
                    label=f"Generación {gen}",
                    value=str(gen),
                    default=(vista.filtro_gen == str(gen)),
                )
            )
        super().__init__(
            placeholder="🔢 Filtrar por generación…",
            options=options,
            min_values=1,
            max_values=1,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction):
        self.vista.filtro_gen = self.values[0]
        self.vista.pagina = 0
        await self.vista.refrescar(interaction)


class RegionInventarioSelect(discord.ui.Select):
    def __init__(self, vista: "VistaInventario"):
        self.vista = vista
        options = [
            discord.SelectOption(
                label="Todas las regiones",
                value="todas",
                default=(vista.filtro_region == "todas"),
            )
        ]
        for nombre in REGIONES:
            options.append(
                discord.SelectOption(
                    label=nombre,
                    value=nombre,
                    default=(vista.filtro_region == nombre),
                )
            )
        super().__init__(
            placeholder="🗺️ Filtrar por región…",
            options=options,
            min_values=1,
            max_values=1,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction):
        self.vista.filtro_region = self.values[0]
        self.vista.pagina = 0
        await self.vista.refrescar(interaction)


class VistaInventario(discord.ui.View):
    def __init__(self, ctx, entradas: list[dict]):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.entradas_raw = entradas
        self.orden = "id_desc"
        self.filtro_tipo = "todos"
        self.filtro_gen = "todas"
        self.filtro_region = "todas"
        self.pagina = 0
        self.message: discord.Message | None = None

        self.add_item(OrdenInventarioSelect(self))
        self.add_item(TipoInventarioSelect(self))
        self.add_item(GeneracionInventarioSelect(self))
        self.add_item(RegionInventarioSelect(self))

    def _texto_filtros(self) -> str:
        partes = [ORDENES[self.orden][0]]
        if self.filtro_tipo != "todos":
            partes.append(f"Tipo: {dict(TIPOS_FILTRO).get(self.filtro_tipo, self.filtro_tipo)}")
        if self.filtro_gen != "todas":
            partes.append(f"Gen {self.filtro_gen}")
        if self.filtro_region != "todas":
            partes.append(self.filtro_region)
        return " · ".join(partes)

    def _entradas_visibles(self) -> list[dict]:
        filtradas = _filtrar_entradas(
            self.entradas_raw,
            tipo=self.filtro_tipo,
            generacion=self.filtro_gen,
            region=self.filtro_region,
        )
        return _ordenar_entradas(filtradas, self.orden)

    def embed_actual(self) -> discord.Embed:
        embeds, pagina = _construir_embeds(
            self._entradas_visibles(),
            self.ctx.author,
            self.pagina,
            self._texto_filtros(),
        )
        self.pagina = pagina
        return embeds[self.pagina]

    async def refrescar(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "❌ Solo el dueño puede usar estos filtros.",
                ephemeral=True,
            )
        self._reconstruir_selects()
        await interaction.response.edit_message(embed=self.embed_actual(), view=self)

    def _reconstruir_selects(self):
        for item in list(self.children):
            if isinstance(item, discord.ui.Select):
                self.remove_item(item)
        self.add_item(OrdenInventarioSelect(self))
        self.add_item(TipoInventarioSelect(self))
        self.add_item(GeneracionInventarioSelect(self))
        self.add_item(RegionInventarioSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "❌ Solo el dueño del inventario puede usar estos controles.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary, row=4)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        visibles = self._entradas_visibles()
        total = max(1, (len(visibles) + POR_PAGINA - 1) // POR_PAGINA)
        self.pagina = (self.pagina - 1) % total
        await interaction.response.edit_message(embed=self.embed_actual(), view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary, row=4)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        visibles = self._entradas_visibles()
        total = max(1, (len(visibles) + POR_PAGINA - 1) // POR_PAGINA)
        self.pagina = (self.pagina + 1) % total
        await interaction.response.edit_message(embed=self.embed_actual(), view=self)


class PaginadorInventario(discord.ui.View):
    def __init__(self, ctx, embeds):
        super().__init__(timeout=180)

        self.ctx = ctx
        self.embeds = embeds
        self.pagina_actual = 0
        self.message = None

        if len(self.embeds) <= 1:
            self.btn_anterior.disabled = True
            self.btn_siguiente.disabled = True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(
        label="◀️ Anterior",
        style=discord.ButtonStyle.secondary,
        custom_id="ant",
    )
    async def btn_anterior(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "❌ Solo el dueño puede cambiar de página.",
                ephemeral=True,
            )

        self.pagina_actual = (self.pagina_actual - 1) % len(self.embeds)

        await interaction.response.edit_message(
            embed=self.embeds[self.pagina_actual],
        )

    @discord.ui.button(
        label="Siguiente ▶️",
        style=discord.ButtonStyle.secondary,
        custom_id="sig",
    )
    async def btn_siguiente(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "❌ Solo el dueño puede cambiar de página.",
                ephemeral=True,
            )

        self.pagina_actual = (self.pagina_actual + 1) % len(self.embeds)

        await interaction.response.edit_message(
            embed=self.embeds[self.pagina_actual],
        )


class Inventario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="inventario")
    async def ver_inventario(self, ctx):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, pokemon_nombre, es_shiny,
                ((iv_hp + iv_atk + iv_def + iv_spa + iv_spd + iv_spe) * 100 / 186) as porcentaje
            FROM capturas
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (str(ctx.author.id),),
        )
        pokemones = cursor.fetchall()
        conn.close()

        if not pokemones:
            await ctx.send("🎒 Tu inventario está vacío.")
            return

        elementos_por_pagina = 10
        paginas = [
            pokemones[i : i + elementos_por_pagina]
            for i in range(0, len(pokemones), elementos_por_pagina)
        ]
        embeds = []

        for i, pagina in enumerate(paginas):
            lista = ""

            for p in pagina:
                id_p, nombre, shiny, porc = p

                emoji = "✨" if shiny else "⚪"

                if porc >= 85:
                    color_pc = "💎"
                elif porc >= 70:
                    color_pc = "🔥"
                else:
                    color_pc = "⏺️"

                lista += (
                    f"{emoji} **{nombre.capitalize()}** "
                    f"`[{id_p}]` | {color_pc} `{int(porc)}%`\n"
                )

            embed = discord.Embed(
                title=f"🎒 Inventario de {ctx.author.name}",
                color=discord.Color.green(),
            )

            embed.description = lista

            embed.set_footer(
                text=f"Página {i + 1}/{len(paginas)} | Usa !ivs [ID] para detalles."
            )

            embeds.append(embed)

        view = PaginadorInventario(ctx, embeds)

        mensaje = await ctx.send(embed=embeds[0], view=view)

        view.message = mensaje

    @commands.command(name="new-inventario")
    async def ver_new_inventario(self, ctx):
        pokemones = database.obtener_inventario_usuario(ctx.author.id)

        if not pokemones:
            await ctx.send("🎒 Tu inventario está vacío.")
            return

        vista = VistaInventario(ctx, pokemones)
        mensaje = await ctx.send(embed=vista.embed_actual(), view=vista)
        vista.message = mensaje

    @commands.command(name="top")
    async def ver_top(self, ctx, tipo=None):

        TIPOS_VALIDOS = {
            "normal",
            "fire",
            "water",
            "grass",
            "electric",
            "ice",
            "fighting",
            "poison",
            "ground",
            "flying",
            "psychic",
            "bug",
            "rock",
            "ghost",
            "dragon",
            "dark",
            "steel",
            "fairy",
        }

        if tipo:

            tipo = tipo.lower()

            if tipo not in TIPOS_VALIDOS:

                return await ctx.send(
                    f"❌ Tipo inválido: {tipo}"
                )

        conn = database.get_connection()
        cursor = conn.cursor()

        if tipo:

            cursor.execute(
                """
                SELECT
                    c.id,
                    c.pokemon_nombre,
                    c.es_shiny,
                    p.id AS dex_id,
                    ((c.iv_hp + c.iv_atk + c.iv_def +
                    c.iv_spa + c.iv_spd + c.iv_spe) * 100 / 186) AS porcentaje
                FROM capturas c
                LEFT JOIN pokemon_data p
                    ON c.pokemon_nombre = p.nombre
                WHERE c.user_id = %s
                AND LOWER(p.tipos) LIKE %s
                ORDER BY porcentaje DESC
                LIMIT 5
            """,
                (
                    str(ctx.author.id),
                    f"%{tipo}%",
                ),
            )

        else:

            cursor.execute(
                """
                SELECT
                    c.id,
                    c.pokemon_nombre,
                    c.es_shiny,
                    p.id AS dex_id,
                    ((c.iv_hp + c.iv_atk + c.iv_def +
                    c.iv_spa + c.iv_spd + c.iv_spe) * 100 / 186) AS porcentaje
                FROM capturas c
                LEFT JOIN pokemon_data p
                    ON c.pokemon_nombre = p.nombre
                WHERE c.user_id = %s
                ORDER BY porcentaje DESC
                LIMIT 5
            """,
                (str(ctx.author.id),),
            )

        top_pokemones = cursor.fetchall()
        conn.close()

        if not top_pokemones:

            if tipo:

                await ctx.send(
                    f"❌ No tienes Pokémon tipo **{tipo}**."
                )

            else:

                await ctx.send(
                    "❌ Aún no tienes Pokémon capturados."
                )

            return

        imagen_top = await servicios.generar_imagen_top(
            top_pokemones,
            tipo=tipo,
        )

        if not imagen_top:

            await ctx.send(
                "❌ Error generando imagen."
            )

            return

        archivo = discord.File(
            imagen_top,
            filename="top.png",
        )

        titulo = (
            f"🏆 Tus 5 mejores Pokémon tipo {tipo.capitalize()}"
            if tipo
            else "🏆 Tus 5 mejores Pokémon"
        )

        embed = discord.Embed(
            title=titulo,
            color=discord.Color.gold(),
        )

        embed.set_image(
            url="attachment://top.png",
        )

        await ctx.send(
            embed=embed,
            file=archivo,
        )


async def setup(bot):
    await bot.add_cog(Inventario(bot))
