import discord

import database
from inventario import (
    GENERACIONES,
    TIPOS_FILTRO,
    _coincide_tipo,
    _formatear_tipos,
    _generacion_desde_dex,
    _region_desde_dex,
)
from regiones import REGIONES

MAX_POKEDEX = 1077
COMPARE_POR_PAGINA = 5
VIEW_TIMEOUT = 600

ORDENES_COMPARE = {
    "cantidad_desc": ("Copias ↓ (más)", lambda g: g["cantidad"], True),
    "cantidad_asc": ("Copias ↑ (menor)", lambda g: g["cantidad"]),
    "nombre_asc": ("Nombre A → Z", lambda g: g["nombre"].lower()),
    "nombre_desc": ("Nombre Z → A", lambda g: g["nombre"].lower(), True),
    "iv_desc": ("Mejor IV% ↓", lambda g: max(c["iv_pct"] for c in g["capturas"]), True),
    "iv_asc": ("Mejor IV% ↑", lambda g: max(c["iv_pct"] for c in g["capturas"])),
}


def _filtrar_grupos(grupos: list[dict], *, tipo, generacion, region) -> list[dict]:
    resultado = []
    for g in grupos:
        if not _coincide_tipo(g.get("tipos", ""), tipo):
            continue
        dex = g.get("dex_id")
        if generacion != "todas":
            if _generacion_desde_dex(dex) != int(generacion):
                continue
        if region != "todas":
            if _region_desde_dex(dex) != region:
                continue
        resultado.append(g)
    return resultado


def _ordenar_grupos(grupos: list[dict], orden: str) -> list[dict]:
    cfg = ORDENES_COMPARE.get(orden, ORDENES_COMPARE["cantidad_desc"])
    key_fn = cfg[1]
    reverse = len(cfg) > 2 and cfg[2]
    return sorted(grupos, key=key_fn, reverse=reverse)


def _formatear_capturas_compare(capturas: list[dict], max_mostrar: int = 10) -> str:
    partes = []
    for captura in capturas[:max_mostrar]:
        shiny = " ✨" if captura["es_shiny"] else ""
        partes.append(f"`#{captura['id']}` {int(captura['iv_pct'])}%{shiny}")
    texto = " · ".join(partes)
    restantes = len(capturas) - max_mostrar
    if restantes > 0:
        texto += f"\n_…y {restantes} copia(s) más_"
    return texto


def _bloque_compare(grupo: dict) -> str:
    tipos = _formatear_tipos(grupo.get("tipos", ""))
    dex = f"#{grupo['dex_id']}" if grupo.get("dex_id") else "?"
    return (
        f"**{grupo['nombre'].capitalize()}** · x{grupo['cantidad']} · {tipos} · Dex {dex}\n"
        f"{_formatear_capturas_compare(grupo['capturas'])}\n"
    )


def _embed_compare_pagina(
    grupos: list[dict],
    titulo: str,
    pagina: int,
    filtros_activos: str,
) -> tuple[discord.Embed, int]:
    if not grupos:
        embed = discord.Embed(
            title=titulo,
            description="No hay especies con los filtros seleccionados.",
            color=discord.Color.orange(),
        )
        embed.set_footer(text=filtros_activos)
        return embed, 0

    total_paginas = max(1, (len(grupos) + COMPARE_POR_PAGINA - 1) // COMPARE_POR_PAGINA)
    pagina = max(0, min(pagina, total_paginas - 1))
    bloque = grupos[pagina * COMPARE_POR_PAGINA : (pagina + 1) * COMPARE_POR_PAGINA]

    embed = discord.Embed(
        title=titulo,
        description="".join(_bloque_compare(g) for g in bloque),
        color=discord.Color.blue(),
    )
    embed.set_footer(
        text=f"Página {pagina + 1}/{total_paginas} · {filtros_activos} · !ivs [ID] para detalles"
    )
    return embed, pagina


class OrdenCompareSelect(discord.ui.Select):
    def __init__(self, vista: "VistaCompararPokemon"):
        self.vista = vista
        options = [
            discord.SelectOption(label=label, value=key, default=(key == vista.orden))
            for key, (label, *_) in ORDENES_COMPARE.items()
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


class TipoCompareSelect(discord.ui.Select):
    def __init__(self, vista: "VistaCompararPokemon"):
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


class GeneracionCompareSelect(discord.ui.Select):
    def __init__(self, vista: "VistaCompararPokemon"):
        self.vista = vista
        options = [
            discord.SelectOption(
                label="Todas las generaciones",
                value="todas",
                default=(vista.filtro_gen == "todas"),
            )
        ]
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


class RegionCompareSelect(discord.ui.Select):
    def __init__(self, vista: "VistaCompararPokemon"):
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


class VistaCompararPokemon(discord.ui.View):
    def __init__(self, ctx, grupos: list[dict], titulo: str):
        super().__init__(timeout=VIEW_TIMEOUT)
        self.ctx = ctx
        self.grupos_raw = grupos
        self.titulo = titulo
        self.orden = "cantidad_desc"
        self.filtro_tipo = "todos"
        self.filtro_gen = "todas"
        self.filtro_region = "todas"
        self.pagina = 0
        self.message: discord.Message | None = None

        self.add_item(OrdenCompareSelect(self))
        self.add_item(TipoCompareSelect(self))
        self.add_item(GeneracionCompareSelect(self))
        self.add_item(RegionCompareSelect(self))

    def _texto_filtros(self) -> str:
        partes = [ORDENES_COMPARE[self.orden][0]]
        if self.filtro_tipo != "todos":
            partes.append(f"Tipo: {dict(TIPOS_FILTRO).get(self.filtro_tipo, self.filtro_tipo)}")
        if self.filtro_gen != "todas":
            partes.append(f"Gen {self.filtro_gen}")
        if self.filtro_region != "todas":
            partes.append(self.filtro_region)
        return " · ".join(partes)

    def _grupos_visibles(self) -> list[dict]:
        filtrados = _filtrar_grupos(
            self.grupos_raw,
            tipo=self.filtro_tipo,
            generacion=self.filtro_gen,
            region=self.filtro_region,
        )
        return _ordenar_grupos(filtrados, self.orden)

    def embed_actual(self) -> discord.Embed:
        embed, pagina = _embed_compare_pagina(
            self._grupos_visibles(),
            self.titulo,
            self.pagina,
            self._texto_filtros(),
        )
        self.pagina = pagina
        return embed

    async def _editar_mensaje(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            await interaction.edit_original_response(embed=self.embed_actual(), view=self)
        except discord.NotFound:
            pass

    async def refrescar(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "❌ Solo el dueño puede usar estos filtros.",
                ephemeral=True,
            )
        self._reconstruir_selects()
        await self._editar_mensaje(interaction)

    def _reconstruir_selects(self):
        for item in list(self.children):
            if isinstance(item, discord.ui.Select):
                self.remove_item(item)
        self.add_item(OrdenCompareSelect(self))
        self.add_item(TipoCompareSelect(self))
        self.add_item(GeneracionCompareSelect(self))
        self.add_item(RegionCompareSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "❌ Solo el dueño puede usar estos controles.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message and self.message.embeds:
                embed = self.message.embeds[0].copy()
                embed.set_footer(
                    text="⏱️ Sesión expirada — usa !comparar-pokemon para abrir de nuevo"
                )
                await self.message.edit(embed=embed, view=self)
            elif self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary, row=4)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        visibles = self._grupos_visibles()
        total = max(1, (len(visibles) + COMPARE_POR_PAGINA - 1) // COMPARE_POR_PAGINA)
        self.pagina = (self.pagina - 1) % total
        await self._editar_mensaje(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary, row=4)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        visibles = self._grupos_visibles()
        total = max(1, (len(visibles) + COMPARE_POR_PAGINA - 1) // COMPARE_POR_PAGINA)
        self.pagina = (self.pagina + 1) % total
        await self._editar_mensaje(interaction)


def iniciar_modulo_ranking(bot):

    @bot.command(name="rankingdex")
    async def rankingdex(ctx):
        """Muestra el ranking global de Pokédex."""

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT
                    user_id,
                    COUNT(DISTINCT pokemon_nombre) AS especies,
                    SUM(CASE WHEN es_shiny = 1 THEN 1 ELSE 0 END) AS shinies,
                    COUNT(*) AS capturas
                FROM capturas
                GROUP BY user_id
                ORDER BY especies DESC
            """)

            ranking = cursor.fetchall()

            usuarios_servidor = {
                str(m.id)
                for m in ctx.guild.members
                if not m.bot
            }

            ranking = [
                fila
                for fila in ranking
                if str(fila[0]) in usuarios_servidor
            ]
            if not ranking:
                await ctx.send(
                    "❌ No hay datos suficientes para generar el ranking."
                )
                return

            embed = discord.Embed(
                title="🏆 Ranking Global de Pokédex",
                description="¡Compite para convertirte en el mejor entrenador!",
                color=discord.Color.gold()
            )

            top_texto = ""

            posicion_usuario = None
            especies_usuario = 0
            shinies_usuario = 0
            capturas_usuario = 0

            for posicion, fila in enumerate(ranking, start=1):

                user_id = int(fila[0])
                especies = fila[1]
                shinies = fila[2] or 0
                capturas = fila[3] or 0

                if posicion == 1:
                    emoji = "🥇"
                elif posicion == 2:
                    emoji = "🥈"
                elif posicion == 3:
                    emoji = "🥉"
                elif posicion == 4:
                    emoji = "4️⃣"
                elif posicion == 5:
                    emoji = "5️⃣"
                else:
                    emoji = f"#{posicion}"

                # Mostrar Top 5
                if posicion <= 5:

                    usuario = bot.get_user(user_id)

                    if usuario:
                        nombre = usuario.display_name
                    else:
                        try:
                            usuario = await bot.fetch_user(user_id)
                            nombre = usuario.name
                        except Exception:
                            nombre = f"Usuario {user_id}"

                    porcentaje = (especies / MAX_POKEDEX) * 100

                    top_texto += (
                        f"{emoji} **{nombre}**\n"
                        f"📚 {especies} especies • 📈 {porcentaje:.1f}%\n"
                        f"✨ {shinies} shinies • 🎯 {capturas} capturas\n\n"
                    )

                # Datos del usuario actual
                if user_id == ctx.author.id:
                    posicion_usuario = posicion
                    especies_usuario = especies
                    shinies_usuario = shinies
                    capturas_usuario = capturas

            embed.add_field(
                name="🏆 Top 5 Pokédex",
                value=top_texto,
                inline=False
            )

            if posicion_usuario:

                porcentaje_usuario = (
                    especies_usuario / MAX_POKEDEX
                ) * 100

                diferencia_texto = ""

                if posicion_usuario > 1:
                    especies_superior = ranking[posicion_usuario - 2][1]
                    diferencia = especies_superior - especies_usuario

                    diferencia_texto = (
                        f"\n⬆️ Te faltan **{diferencia}** especies "
                        f"para alcanzar el puesto superior."
                    )

                embed.add_field(
                    name="📍 Tu Posición",
                    value=(
                        f"**#{posicion_usuario}**\n"
                        f"📚 {especies_usuario} especies\n"
                        f"📈 {porcentaje_usuario:.1f}% completado\n"
                        f"✨ Shinies capturados: **{shinies_usuario}**\n"
                        f"🎯 Capturas totales: **{capturas_usuario}**"
                        f"{diferencia_texto}"
                    ),
                    inline=False
                )

            embed.set_footer(
                text=f"Total de entrenadores clasificados: {len(ranking)}"
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error al generar el ranking: {e}")

        finally:
            conn.close()

    @bot.command(name="comparar")
    async def comparar(ctx, miembro: discord.Member):

        if miembro.bot:
            await ctx.send("❌ No puedes comparar con un bot.")
            return

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            # Pokémon del usuario actual
            cursor.execute("""
                SELECT DISTINCT pokemon_nombre
                FROM capturas
                WHERE user_id = %s
            """, (str(ctx.author.id),))

            mis_pokemon = {
                fila[0]
                for fila in cursor.fetchall()
            }

            # Pokémon del usuario objetivo
            cursor.execute("""
                SELECT DISTINCT pokemon_nombre
                FROM capturas
                WHERE user_id = %s
            """, (str(miembro.id),))

            sus_pokemon = {
                fila[0]
                for fila in cursor.fetchall()
            }

            compartidos = mis_pokemon & sus_pokemon
            solo_mios = mis_pokemon - sus_pokemon
            solo_suyos = sus_pokemon - mis_pokemon
            embed = discord.Embed(
                title="📊 Comparación de Pokédex",
                color=discord.Color.blue()
            )

            embed.add_field(
                name=f"📖 {ctx.author.display_name}",
                value=f"{len(mis_pokemon)} especies",
                inline=True
            )

            embed.add_field(
                name=f"📖 {miembro.display_name}",
                value=f"{len(sus_pokemon)} especies",
                inline=True
            )

            embed.add_field(
                name="🤝 Compartidos",
                value=str(len(compartidos)),
                inline=False
            )

            embed.add_field(
                name="✅ Tú tienes y él no",
                value=str(len(solo_mios)),
                inline=True
            )

            embed.add_field(
                name="❌ Él tiene y tú no",
                value=str(len(solo_suyos)),
                inline=True
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

        finally:
            conn.close()

    @bot.command(name="comparar-pokemon")
    async def comparar_pokemon(ctx, miembro: discord.Member):
        if miembro.bot:
            return await ctx.send("❌ No puedes comparar con un bot.")
        if miembro.id == ctx.author.id:
            return await ctx.send("❌ No puedes compararte contigo mismo.")

        grupos = database.obtener_exclusivos_vs_usuario(ctx.author.id, miembro.id)
        if not grupos:
            return await ctx.send(
                f"No hay especies que **{miembro.display_name}** tenga y tú no."
            )

        titulo = f"Especies de {miembro.display_name} que tú no tienes"
        vista = VistaCompararPokemon(ctx, grupos, titulo)
        mensaje = await ctx.send(embed=vista.embed_actual(), view=vista)
        vista.message = mensaje
