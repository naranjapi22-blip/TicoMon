import discord
import database
import servicios
from ivs_commands import calcular_stat_lvl50, calcular_hp_lvl50
from vistas_selector import SPRITE_URL, POR_PAGINA


def _etiqueta_captura(captura: dict) -> str:
    shiny = "✨ " if captura["es_shiny"] else ""
    return f"{shiny}{captura['nombre'].capitalize()} [#{captura['id']}] {captura['iv_pct']}%"


def _filtrar_capturas(capturas: list[dict], query: str) -> list[dict]:
    q = query.strip().lower()
    if q.startswith("#"):
        q = q[1:]
    if q.isdigit():
        captura_id = int(q)
        return [c for c in capturas if c["id"] == captura_id]
    return [c for c in capturas if q in c["nombre"].lower()]


def _lineas_equipo(slots: list) -> str:
    lineas = []
    for i, slot in enumerate(slots, 1):
        if slot:
            shiny = "✨ " if slot["es_shiny"] else ""
            lineas.append(f"**{i}.** {shiny}{slot['nombre'].capitalize()} `[#{slot['id']}]`")
        else:
            lineas.append(f"**{i}.** —")
    return "\n".join(lineas)


async def crear_embed_equipo(user: discord.Member, session, slots: list | None = None) -> discord.Embed:
    if slots is None:
        slots = database.obtener_equipo_detalle(user.id)
    ocupados = sum(1 for s in slots if s)
    embed = discord.Embed(
        title=f"🎒 Equipo de {user.display_name}",
        description=f"Slots **{ocupados}/9**\n\n{_lineas_equipo(slots)}",
        color=discord.Color.blue(),
    )
    for slot in slots:
        if slot:
            poke_id = await servicios.obtener_id_por_nombre(session, slot["nombre"])
            if poke_id:
                embed.set_thumbnail(url=SPRITE_URL.format(poke_id=poke_id))
                break
    return embed


def _format_stat(lvl50: int, iv: int) -> str:
    return f"**{lvl50:>3}** | {iv:>2}/31"


def _stats_desde_captura(b: dict, captura) -> tuple[str, float]:
    captura_id, hp, atk, defs, spa, spd, spe, es_shiny = captura
    ivs = [hp, atk, defs, spa, spd, spe]
    total = sum(ivs)
    pct = round((total / 186) * 100, 2)
    shiny = " ✨" if es_shiny else ""
    texto = (
        f"**`#{captura_id}`**{shiny} **{pct}%**\n"
        f"IVs `{hp}/{atk}/{defs}/{spa}/{spd}/{spe}`\n"
        f"❤️ {calcular_hp_lvl50(b.get('hp', 0), hp)} · "
        f"⚔️ {calcular_stat_lvl50(b.get('attack', 0), atk)} · "
        f"🛡️ {calcular_stat_lvl50(b.get('defense', 0), defs)}\n"
        f"🔮 {calcular_stat_lvl50(b.get('special-attack', 0), spa)} · "
        f"✨ {calcular_stat_lvl50(b.get('special-defense', 0), spd)} · "
        f"⚡ {calcular_stat_lvl50(b.get('speed', 0), spe)}"
    )
    return texto, pct


async def crear_embed_captura_stats(session, user_id, captura_id: int) -> discord.Embed:
    cap = database.obtener_captura(user_id, captura_id)
    if not cap:
        return discord.Embed(description="❌ Captura no encontrada.", color=discord.Color.red())

    cid, nombre, es_shiny, hp, atk, defs, spa, spd, spe = cap
    ivs = [hp, atk, defs, spa, spd, spe]
    total = sum(ivs)
    pct = round((total / 186) * 100, 2)

    if pct >= 85:
        color = discord.Color.gold()
        calidad = "Épico"
    elif pct >= 70:
        color = discord.Color.green()
        calidad = "Excelente"
    else:
        color = discord.Color.blue()
        calidad = "Normal"

    emoji_shiny = "✨ " if es_shiny else ""
    embed = discord.Embed(
        title=f"{emoji_shiny}{nombre.capitalize()} `[#{cid}]`",
        color=color,
    )
    embed.add_field(
        name="Detalles",
        value=(
            f"⭐ **Calidad:** {calidad}\n"
            f"📈 **Potencial:** {total}/186 ({pct}%)\n"
            f"✨ **Shiny:** {'Sí' if es_shiny else 'No'}"
        ),
        inline=False,
    )

    data, _ = await servicios.obtener_pokemon(session, nombre)
    if data:
        tipos = ", ".join(t["type"]["name"].capitalize() for t in data.get("types", []))
        b = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
        embed.insert_field_at(
            0,
            name="Tipos",
            value=tipos or "—",
            inline=True,
        )
        embed.add_field(name="Estadísticas (Lvl 50 | IVs)", value="━━━━━━━━━━━━━━━━━━━━", inline=False)
        embed.add_field(name="❤️ HP", value=_format_stat(calcular_hp_lvl50(b.get("hp", 0), hp), hp), inline=True)
        embed.add_field(name="⚔️ Atk", value=_format_stat(calcular_stat_lvl50(b.get("attack", 0), atk), atk), inline=True)
        embed.add_field(name="🛡️ Def", value=_format_stat(calcular_stat_lvl50(b.get("defense", 0), defs), defs), inline=True)
        embed.add_field(name="🔮 SpA", value=_format_stat(calcular_stat_lvl50(b.get("special-attack", 0), spa), spa), inline=True)
        embed.add_field(name="✨ SpD", value=_format_stat(calcular_stat_lvl50(b.get("special-defense", 0), spd), spd), inline=True)
        embed.add_field(name="⚡ Spe", value=_format_stat(calcular_stat_lvl50(b.get("speed", 0), spe), spe), inline=True)

        poke_id = data.get("id") or await servicios.obtener_id_por_nombre(session, nombre)
        if poke_id:
            embed.set_thumbnail(url=SPRITE_URL.format(poke_id=poke_id))

    return embed


def _resumen_captura(b: dict, captura) -> str:
    texto, _ = _stats_desde_captura(b, captura)
    return texto


def _stats_todas_capturas(data, capturas: list) -> str:
    if not capturas:
        return "Sin capturas de esta especie."
    if not data:
        return "Sin datos de PokeAPI."
    b = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    tipos = ", ".join(t["type"]["name"].capitalize() for t in data.get("types", []))
    bloques = [f"**Tipos:** {tipos or '—'}"]
    for i, captura in enumerate(capturas):
        if i > 0:
            bloques.append("─────────────")
        bloques.append(_resumen_captura(b, captura))
    texto = "\n".join(bloques)
    if len(texto) > 1024:
        texto = texto[:1020] + "…"
    return texto


async def crear_embed_comparacion(session, user_id, nombre_a: str, nombre_b: str) -> discord.Embed:
    data_a, _ = await servicios.obtener_pokemon(session, nombre_a)
    data_b, _ = await servicios.obtener_pokemon(session, nombre_b)
    caps_a = database.listar_capturas_por_especie(user_id, nombre_a)
    caps_b = database.listar_capturas_por_especie(user_id, nombre_b)

    embed = discord.Embed(
        title="📊 Comparación (Lvl 50 · todas tus capturas)",
        color=discord.Color.gold(),
    )
    embed.add_field(
        name=f"{nombre_a.capitalize()} ({len(caps_a)})",
        value=_stats_todas_capturas(data_a, caps_a),
        inline=True,
    )
    embed.add_field(
        name=f"{nombre_b.capitalize()} ({len(caps_b)})",
        value=_stats_todas_capturas(data_b, caps_b),
        inline=True,
    )
    poke_id = await servicios.obtener_id_por_nombre(session, nombre_a)
    if poke_id:
        embed.set_thumbnail(url=SPRITE_URL.format(poke_id=poke_id))
    return embed


class ConfirmarCapturaView(discord.ui.View):
    def __init__(self, vista_equipo: "VistaEquipo", captura_id: int, *, slot: int | None = None):
        super().__init__(timeout=120)
        self.vista_equipo = vista_equipo
        self.captura_id = captura_id
        self.slot = slot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.vista_equipo.user.id:
            await interaction.response.send_message("❌ No es tu equipo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.slot is None:
                slot = database.agregar_a_equipo(self.vista_equipo.user.id, self.captura_id)
                cap = database.obtener_captura(self.vista_equipo.user.id, self.captura_id)
                nombre = cap[1].capitalize() if cap else "?"
                mensaje = f"✅ **{nombre}** `[#{self.captura_id}]` añadido al slot **{slot}**."
            else:
                database.reemplazar_en_equipo(self.vista_equipo.user.id, self.slot, self.captura_id)
                cap = database.obtener_captura(self.vista_equipo.user.id, self.captura_id)
                nombre = cap[1].capitalize() if cap else "?"
                mensaje = f"✅ Slot **{self.slot}** → **{nombre}** `[#{self.captura_id}]`."
        except database.EquipoError as e:
            return await interaction.response.send_message(f"❌ {e}", ephemeral=True)

        self.stop()
        await interaction.response.edit_message(content=mensaje, embed=None, view=None)
        await self.vista_equipo._refrescar_mensaje_principal()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="❌ Acción cancelada.", embed=None, view=None)


class EleccionCapturaView(discord.ui.View):
    def __init__(self, vista_equipo: "VistaEquipo", capturas: list[dict], *, slot: int | None = None):
        super().__init__(timeout=120)
        self.vista_equipo = vista_equipo
        self.capturas = {str(c["id"]): c for c in capturas}
        self.slot = slot

        opciones = [
            discord.SelectOption(label=_etiqueta_captura(c)[:100], value=str(c["id"]))
            for c in capturas[:25]
        ]
        self.select = discord.ui.Select(placeholder="Elige una captura", options=opciones)
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.vista_equipo.user.id:
            await interaction.response.send_message("❌ No es tu equipo.", ephemeral=True)
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        captura_id = int(interaction.data["values"][0])
        embed = await crear_embed_captura_stats(
            self.vista_equipo.session,
            self.vista_equipo.user.id,
            captura_id,
        )
        view = ConfirmarCapturaView(self.vista_equipo, captura_id, slot=self.slot)
        await interaction.response.edit_message(
            content="Revisa las estadísticas y confirma:",
            embed=embed,
            view=view,
        )


class BuscarCapturaModal(discord.ui.Modal, title="Buscar captura"):
    buscar = discord.ui.TextInput(
        label="Buscar",
        placeholder="nombre o #id (ej. pikachu, 42)",
        max_length=50,
        required=True,
    )

    def __init__(self, vista_equipo: "VistaEquipo", *, slot: int | None = None):
        super().__init__()
        self.vista_equipo = vista_equipo
        self.slot = slot

    async def on_submit(self, interaction: discord.Interaction):
        if self.slot is None:
            candidatos = self.vista_equipo._capturas_disponibles_para_anadir()
        else:
            candidatos = self.vista_equipo._capturas_para_reemplazo(self.slot)

        if not candidatos:
            return await interaction.response.send_message(
                "❌ No hay capturas disponibles para esa acción.",
                ephemeral=True,
            )

        coincidencias = _filtrar_capturas(candidatos, self.buscar.value)
        if not coincidencias:
            return await interaction.response.send_message(
                "❌ No tienes ninguna captura que coincida con esa búsqueda.",
                ephemeral=True,
            )
        if len(coincidencias) > 25:
            return await interaction.response.send_message(
                "❌ Demasiados resultados. Sé más específico (usa el ID `#123`).",
                ephemeral=True,
            )

        if len(coincidencias) == 1:
            captura_id = coincidencias[0]["id"]
            embed = await crear_embed_captura_stats(
                self.vista_equipo.session,
                self.vista_equipo.user.id,
                captura_id,
            )
            view = ConfirmarCapturaView(self.vista_equipo, captura_id, slot=self.slot)
            return await interaction.response.send_message(
                content="Revisa las estadísticas y confirma:",
                embed=embed,
                view=view,
                ephemeral=True,
            )

        view = EleccionCapturaView(self.vista_equipo, coincidencias, slot=self.slot)
        await interaction.response.send_message(
            content=f"**{len(coincidencias)}** capturas encontradas. Elige una:",
            view=view,
            ephemeral=True,
        )


class AgregarPorIdModal(discord.ui.Modal, title="Añadir por ID"):
    captura_id_input = discord.ui.TextInput(
        label="ID de captura",
        placeholder="ej. 42",
        max_length=10,
        required=True,
    )

    def __init__(self, vista_equipo: "VistaEquipo"):
        super().__init__()
        self.vista_equipo = vista_equipo

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.captura_id_input.value.strip().lstrip("#")
        if not raw.isdigit():
            return await interaction.response.send_message("❌ ID inválido.", ephemeral=True)

        captura_id = int(raw)
        cap = database.obtener_captura(self.vista_equipo.user.id, captura_id)
        if not cap:
            return await interaction.response.send_message(
                "❌ No tienes ninguna captura con ese ID.",
                ephemeral=True,
            )
        if captura_id in self.vista_equipo._ids_en_equipo():
            return await interaction.response.send_message(
                "❌ Esa captura ya está en tu equipo.",
                ephemeral=True,
            )

        try:
            slot = database.agregar_a_equipo(self.vista_equipo.user.id, captura_id)
        except database.EquipoError as e:
            return await interaction.response.send_message(f"❌ {e}", ephemeral=True)

        nombre = cap[1].capitalize()
        await interaction.response.send_message(
            f"✅ **{nombre}** `[#{captura_id}]` añadido al slot **{slot}**.",
            ephemeral=True,
        )
        await self.vista_equipo._refrescar_mensaje_principal()


class PuertaEquipoPrivada(discord.ui.View):
    """Mensaje público con botón que abre el panel de equipo solo para el jugador."""

    def __init__(self, jugador: discord.Member, session):
        super().__init__(timeout=180)
        self.jugador = jugador
        self.session = session

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.jugador.id

    @discord.ui.button(label="📋 Abrir mi equipo (privado)", style=discord.ButtonStyle.primary)
    async def abrir_equipo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        button.disabled = True
        await interaction.edit_original_response(view=self)

        vista = VistaEquipo(self.jugador, self.session)
        embed = await vista.crear_embed()
        msg = await interaction.followup.send(embed=embed, view=vista, ephemeral=True)
        vista.message = msg

        try:
            await interaction.message.delete()
        except discord.HTTPException:
            pass


async def abrir_equipo_en_privado(ctx, jugador: discord.Member, session):
    puerta = PuertaEquipoPrivada(jugador, session)
    await ctx.send(
        f"🎒 {jugador.mention}, pulsa **Abrir mi equipo (privado)**. Solo tú verás tu equipo.",
        view=puerta,
    )


class CompararBuscarModal(discord.ui.Modal, title="Buscar especie"):
    def __init__(self, picker: "CompararPickerView"):
        super().__init__()
        self.picker = picker
        self.campo = discord.ui.TextInput(
            label="Nombre",
            placeholder="ej. pikachu, char…",
            max_length=50,
            required=True,
        )
        self.add_item(self.campo)

    async def on_submit(self, interaction: discord.Interaction):
        self.picker.filtro = self.campo.value.strip().lower()
        self.picker.pagina_actual = 0
        if not self.picker.lista_visible:
            return await interaction.response.send_message(
                "❌ No tienes ninguna especie que coincida con esa búsqueda.",
                ephemeral=True,
            )
        self.picker._reconstruir_componentes()
        await interaction.response.edit_message(
            embed=self.picker.crear_embed(),
            view=self.picker,
        )


class CompararPickerView(discord.ui.View):
    """Elige dos especies con select paginado (25 por página)."""

    def __init__(self, user: discord.Member, session, especies: list[str]):
        super().__init__(timeout=180)
        self.user = user
        self.session = session
        self.especies = sorted(especies, key=str.lower)
        self.filtro: str | None = None
        self.pagina_actual = 0
        self.nombre_a: str | None = None
        self.nombre_b: str | None = None
        self._reconstruir_componentes()

    @property
    def eligiendo_b(self) -> bool:
        return self.nombre_a is not None and self.nombre_b is None

    @property
    def lista_visible(self) -> list[str]:
        base = self.especies
        if self.eligiendo_b:
            base = [e for e in base if e.lower() != self.nombre_a.lower()]
        if self.filtro:
            return [e for e in base if self.filtro in e.lower()]
        return base

    @property
    def paginas(self) -> list[list[str]]:
        visible = self.lista_visible
        if not visible:
            return [[]]
        return [visible[i : i + POR_PAGINA] for i in range(0, len(visible), POR_PAGINA)]

    def crear_embed(self) -> discord.Embed:
        total_pag = max(1, len(self.paginas))
        fase = "B" if self.eligiendo_b else "A"
        busqueda = f"\n🔎 Filtro: `{self.filtro}`" if self.filtro else ""
        desc = f"Elige **Pokémon {fase}** del menú.{busqueda}\n📄 Página **{self.pagina_actual + 1}/{total_pag}**"
        if self.nombre_a:
            desc += f"\n\n**A:** {self.nombre_a.capitalize()}"
        if self.nombre_b:
            desc += f"\n**B:** {self.nombre_b.capitalize()}"
        return discord.Embed(
            title="📊 Comparar especies",
            description=desc,
            color=discord.Color.gold(),
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ No es tu comparación.", ephemeral=True)
            return False
        return True

    def _reconstruir_componentes(self):
        self.clear_items()
        paginas = self.paginas
        if self.pagina_actual >= len(paginas):
            self.pagina_actual = max(0, len(paginas) - 1)

        opciones_pagina = paginas[self.pagina_actual]
        fase = "B" if self.eligiendo_b else "A"

        if opciones_pagina and self.nombre_b is None:
            opciones = [
                discord.SelectOption(label=n.capitalize()[:100], value=n)
                for n in opciones_pagina
            ]
            select = discord.ui.Select(
                placeholder=f"Elige Pokémon {fase}",
                min_values=1,
                max_values=1,
                options=opciones,
            )
            select.callback = self._callback_select
            self.add_item(select)

        if len(paginas) > 1:
            btn_atras = discord.ui.Button(label="◀️", style=discord.ButtonStyle.secondary)
            btn_atras.callback = self._callback_atras
            self.add_item(btn_atras)
            btn_adelante = discord.ui.Button(label="▶️", style=discord.ButtonStyle.secondary)
            btn_adelante.callback = self._callback_adelante
            self.add_item(btn_adelante)

        btn_buscar = discord.ui.Button(label="🔍 Buscar", style=discord.ButtonStyle.primary)
        btn_buscar.callback = self._callback_buscar
        self.add_item(btn_buscar)

        if self.filtro:
            btn_todos = discord.ui.Button(label="Ver todos", style=discord.ButtonStyle.secondary)
            btn_todos.callback = self._callback_ver_todos
            self.add_item(btn_todos)

        if self.eligiendo_b:
            btn_cambiar = discord.ui.Button(label="↩ Cambiar A", style=discord.ButtonStyle.secondary)
            btn_cambiar.callback = self._callback_cambiar_a
            self.add_item(btn_cambiar)

        if self.nombre_b:
            btn_cambiar_b = discord.ui.Button(label="↩ Cambiar B", style=discord.ButtonStyle.secondary)
            btn_cambiar_b.callback = self._callback_cambiar_b
            self.add_item(btn_cambiar_b)

        if self.nombre_a and self.nombre_b:
            btn_ok = discord.ui.Button(label="📊 Comparar", style=discord.ButtonStyle.success)
            btn_ok.callback = self._callback_comparar
            self.add_item(btn_ok)

    async def _editar(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.crear_embed(), view=self)

    async def _callback_select(self, interaction: discord.Interaction):
        nombre = interaction.data["values"][0]
        if not self.nombre_a:
            self.nombre_a = nombre
            self.pagina_actual = 0
            self.filtro = None
        else:
            if nombre.lower() == self.nombre_a.lower():
                return await interaction.response.send_message(
                    "❌ Elige una especie distinta a Pokémon A.",
                    ephemeral=True,
                )
            self.nombre_b = nombre
        self._reconstruir_componentes()
        await self._editar(interaction)

    async def _callback_atras(self, interaction: discord.Interaction):
        self.pagina_actual = max(0, self.pagina_actual - 1)
        self._reconstruir_componentes()
        await self._editar(interaction)

    async def _callback_adelante(self, interaction: discord.Interaction):
        self.pagina_actual = min(len(self.paginas) - 1, self.pagina_actual + 1)
        self._reconstruir_componentes()
        await self._editar(interaction)

    async def _callback_buscar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CompararBuscarModal(self))

    async def _callback_ver_todos(self, interaction: discord.Interaction):
        self.filtro = None
        self.pagina_actual = 0
        self._reconstruir_componentes()
        await self._editar(interaction)

    async def _callback_cambiar_a(self, interaction: discord.Interaction):
        self.nombre_a = None
        self.nombre_b = None
        self.pagina_actual = 0
        self.filtro = None
        self._reconstruir_componentes()
        await self._editar(interaction)

    async def _callback_cambiar_b(self, interaction: discord.Interaction):
        self.nombre_b = None
        self.pagina_actual = 0
        self.filtro = None
        self._reconstruir_componentes()
        await self._editar(interaction)

    async def _callback_comparar(self, interaction: discord.Interaction):
        embed = await crear_embed_comparacion(
            self.session, self.user.id, self.nombre_a, self.nombre_b
        )
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)


class VistaEquipo(discord.ui.View):
    def __init__(self, user: discord.Member, session):
        super().__init__(timeout=300)
        self.user = user
        self.session = session
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ Este equipo no es tuyo.", ephemeral=True)
            return False
        return True

    async def crear_embed(self) -> discord.Embed:
        return await crear_embed_equipo(self.user, self.session)

    def _ids_en_equipo(self) -> set[int]:
        return {c for c in database.obtener_equipo(self.user.id) if c is not None}

    def _capturas_disponibles_para_anadir(self) -> list[dict]:
        return database.listar_capturas_usuario(self.user.id, excluir_ids=self._ids_en_equipo())

    def _capturas_para_reemplazo(self, slot: int) -> list[dict]:
        ids_equipo = self._ids_en_equipo()
        equipo = database.obtener_equipo(self.user.id)
        actual_id = equipo[slot - 1]
        excluir = ids_equipo - ({actual_id} if actual_id else set())
        return database.listar_capturas_usuario(self.user.id, excluir_ids=excluir)

    async def _refrescar_mensaje_principal(self):
        if self.message:
            embed = await self.crear_embed()
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="➕ Añadir", style=discord.ButtonStyle.success, row=0)
    async def anadir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if database.contar_equipo(self.user.id) >= 9:
            return await interaction.response.send_message(
                "❌ Tu equipo está completo (9/9).",
                ephemeral=True,
            )
        if not self._capturas_disponibles_para_anadir():
            return await interaction.response.send_message(
                "❌ No tienes capturas disponibles para añadir.",
                ephemeral=True,
            )
        await interaction.response.send_modal(BuscarCapturaModal(self))

    @discord.ui.button(label="🔄 Reemplazar", style=discord.ButtonStyle.primary, row=0)
    async def reemplazar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        equipo = database.obtener_equipo_detalle(self.user.id)
        opciones = []
        for i, slot in enumerate(equipo, 1):
            if slot:
                label = f"Slot {i}: {slot['nombre'].capitalize()} [#{slot['id']}]"
            else:
                label = f"Slot {i}: — vacío —"
            opciones.append(discord.SelectOption(label=label[:100], value=str(i)))
        select = discord.ui.Select(placeholder="Elige el slot a reemplazar", options=opciones)

        async def callback(sel_inter: discord.Interaction):
            if sel_inter.user.id != self.user.id:
                return await sel_inter.response.send_message(
                    "❌ Este menú no es tuyo.",
                    ephemeral=True,
                )
            slot = int(sel_inter.data["values"][0])
            if not self._capturas_para_reemplazo(slot):
                return await sel_inter.response.send_message(
                    "❌ No hay capturas disponibles para ese slot.",
                    ephemeral=True,
                )
            await sel_inter.response.send_modal(BuscarCapturaModal(self, slot=slot))

        select.callback = callback
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        await interaction.followup.send(
            "Elige el slot que quieres reemplazar:",
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="➖ Quitar", style=discord.ButtonStyle.secondary, row=0)
    async def quitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        equipo = database.obtener_equipo_detalle(self.user.id)
        llenos = [(i, s) for i, s in enumerate(equipo, 1) if s]
        if not llenos:
            return await interaction.followup.send("❌ Tu equipo está vacío.", ephemeral=True)

        opciones = [
            discord.SelectOption(
                label=f"Slot {i}: {s['nombre'].capitalize()} [#{s['id']}]"[:100],
                value=str(i),
            )
            for i, s in llenos
        ]
        select = discord.ui.Select(placeholder="Elige qué quitar", options=opciones)

        async def callback(sel_inter: discord.Interaction):
            if sel_inter.user.id != self.user.id:
                return await sel_inter.response.send_message(
                    "❌ Este menú no es tuyo.",
                    ephemeral=True,
                )
            slot = int(sel_inter.data["values"][0])
            slot_data = equipo[slot - 1]
            database.quitar_de_equipo(self.user.id, slot)
            await sel_inter.response.edit_message(
                content=f"✅ Quitado **{slot_data['nombre'].capitalize()}** `[#{slot_data['id']}]` del slot **{slot}**.",
                view=None,
            )
            await self._refrescar_mensaje_principal()

        select.callback = callback
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        await interaction.followup.send("Elige el Pokémon a quitar:", view=view, ephemeral=True)

    @discord.ui.button(label="🆔 Agregar por ID", style=discord.ButtonStyle.success, row=1)
    async def anadir_por_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        if database.contar_equipo(self.user.id) >= 9:
            return await interaction.response.send_message(
                "❌ Tu equipo está completo (9/9).",
                ephemeral=True,
            )
        await interaction.response.send_modal(AgregarPorIdModal(self))

    @discord.ui.button(label="📊 Comparar", style=discord.ButtonStyle.primary, row=1)
    async def comparar(self, interaction: discord.Interaction, button: discord.ui.Button):
        especies = database.obtener_lista_capturas(self.user.id)
        if len(especies) < 2:
            return await interaction.response.send_message(
                "❌ Necesitas al menos 2 especies distintas capturadas.",
                ephemeral=True,
            )
        view = CompararPickerView(self.user, self.session, especies)
        await interaction.response.send_message(
            embed=view.crear_embed(),
            view=view,
            ephemeral=True,
        )

    async def on_timeout(self):
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True
