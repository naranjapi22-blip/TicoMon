import discord
import database
import servicios
from ivs_commands import calcular_stat_lvl50, calcular_hp_lvl50
from vistas_selector import SelectorPokemon, SPRITE_URL, POR_PAGINA


def _etiqueta_captura(captura: dict) -> str:
    shiny = "✨ " if captura["es_shiny"] else ""
    return f"{shiny}{captura['nombre'].capitalize()} [#{captura['id']}] {captura['iv_pct']}%"


def _datos_selector(capturas: list[dict]) -> tuple[list[str], dict[str, str], dict[str, str]]:
    valores = [str(c["id"]) for c in capturas]
    etiquetas = {str(c["id"]): _etiqueta_captura(c) for c in capturas}
    nombres = {str(c["id"]): c["nombre"] for c in capturas}
    return valores, etiquetas, nombres


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


def _resumen_captura(b: dict, captura) -> str:
    captura_id, hp, atk, defs, spa, spd, spe, es_shiny = captura
    total = hp + atk + defs + spa + spd + spe
    pct = round((total / 186) * 100, 2)
    shiny = " ✨" if es_shiny else ""
    return (
        f"**`#{captura_id}`**{shiny} **{pct}%**\n"
        f"IVs `{hp}/{atk}/{defs}/{spa}/{spd}/{spe}`\n"
        f"❤️ {calcular_hp_lvl50(b.get('hp', 0), hp)} · "
        f"⚔️ {calcular_stat_lvl50(b.get('attack', 0), atk)} · "
        f"🛡️ {calcular_stat_lvl50(b.get('defense', 0), defs)}\n"
        f"🔮 {calcular_stat_lvl50(b.get('special-attack', 0), spa)} · "
        f"✨ {calcular_stat_lvl50(b.get('special-defense', 0), spd)} · "
        f"⚡ {calcular_stat_lvl50(b.get('speed', 0), spe)}"
    )


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


class CompararView(discord.ui.View):
    """Dos selects cuando hay ≤25 especies distintas."""

    def __init__(self, user: discord.Member, session, especies: list[str]):
        super().__init__(timeout=120)
        self.user = user
        self.session = session
        self.especies = sorted(especies, key=str.lower)
        opts = [
            discord.SelectOption(label=e.capitalize()[:100], value=e)
            for e in self.especies[:25]
        ]
        self.select_a = discord.ui.Select(placeholder="Pokémon A", options=opts, row=0)
        self.select_b = discord.ui.Select(placeholder="Pokémon B", options=opts, row=1)
        self.select_a.callback = self._noop
        self.select_b.callback = self._noop
        self.add_item(self.select_a)
        self.add_item(self.select_b)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ No es tu comparación.", ephemeral=True)
            return False
        return True

    async def _noop(self, interaction: discord.Interaction):
        await interaction.response.defer()

    @discord.ui.button(label="📊 Comparar", style=discord.ButtonStyle.primary, row=2)
    async def comparar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.select_a.values or not self.select_b.values:
            return await interaction.response.send_message(
                "❌ Elige ambos Pokémon.",
                ephemeral=True,
            )
        a, b = self.select_a.values[0], self.select_b.values[0]
        if a == b:
            return await interaction.response.send_message(
                "❌ Elige dos especies distintas.",
                ephemeral=True,
            )
        embed = await crear_embed_comparacion(self.session, self.user.id, a, b)
        self.stop()
        await interaction.response.send_message(embed=embed, ephemeral=True, view=None)


class CompararModal(discord.ui.Modal, title="Comparar Pokémon"):
    """Modal con selects cuando discord.py soporta Label (≤25 especies)."""

    def __init__(self, user: discord.Member, session, especies: list[str]):
        super().__init__()
        self.user = user
        self.session = session
        self.especies = sorted(especies, key=str.lower)
        opts = [
            discord.SelectOption(label=e.capitalize()[:100], value=e)
            for e in self.especies[:25]
        ]
        self._select_a = discord.ui.Select(placeholder="Pokémon A", options=opts)
        self._select_b = discord.ui.Select(placeholder="Pokémon B", options=opts)
        self.add_item(discord.ui.Label(text="Pokémon A", component=self._select_a))
        self.add_item(discord.ui.Label(text="Pokémon B", component=self._select_b))

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ No es tu comparación.", ephemeral=True)
        if not self._select_a.values or not self._select_b.values:
            return await interaction.response.send_message("❌ Elige ambos Pokémon.", ephemeral=True)
        a, b = self._select_a.values[0], self._select_b.values[0]
        if a == b:
            return await interaction.response.send_message("❌ Elige dos especies distintas.", ephemeral=True)
        embed = await crear_embed_comparacion(self.session, self.user.id, a, b)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def _comparar_dos_pasos(interaction: discord.Interaction, user: discord.Member, session, especies: list[str]):
    await interaction.response.defer(ephemeral=True)

    selector_a = SelectorPokemon(
        user,
        especies,
        session,
        max_seleccion=1,
        titulo="📊 Comparar — elige Pokémon A",
        placeholder_select="Elige el primer Pokémon",
        etiqueta_campo="Pokémon A",
    )
    msg = await interaction.followup.send(
        embed=await selector_a.crear_embed(),
        view=selector_a,
        ephemeral=True,
    )
    selector_a.message = msg
    await selector_a.wait()
    if not selector_a.seleccionados:
        return
    nombre_a = selector_a.seleccionados[0]
    restantes = [e for e in especies if e.lower() != nombre_a.lower()]

    selector_b = SelectorPokemon(
        user,
        restantes,
        session,
        max_seleccion=1,
        titulo="📊 Comparar — elige Pokémon B",
        placeholder_select="Elige el segundo Pokémon",
        etiqueta_campo="Pokémon B",
    )
    embed_b = await selector_b.crear_embed()
    await msg.edit(embed=embed_b, view=selector_b)
    selector_b.message = msg
    await selector_b.wait()
    if not selector_b.seleccionados:
        return
    nombre_b = selector_b.seleccionados[0]
    embed = await crear_embed_comparacion(session, user.id, nombre_a, nombre_b)
    await msg.edit(embed=embed, view=None)


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

    async def _ejecutar_selector_ephemeral(
        self,
        interaction: discord.Interaction,
        capturas: list[dict],
        titulo: str,
        on_pick,
        *,
        ya_respondido: bool = False,
    ):
        if not capturas:
            if ya_respondido:
                return await interaction.followup.send(
                    "❌ No hay capturas disponibles para esa acción.",
                    ephemeral=True,
                )
            return await interaction.response.send_message(
                "❌ No hay capturas disponibles para esa acción.",
                ephemeral=True,
            )
        if not ya_respondido:
            await interaction.response.defer(ephemeral=True)

        valores, etiquetas, nombres = _datos_selector(capturas)
        selector = SelectorPokemon(
            self.user,
            valores,
            self.session,
            max_seleccion=1,
            titulo=titulo,
            placeholder_select="Elige una captura",
            etiqueta_campo="Selección",
            etiquetas=etiquetas,
            nombre_por_valor=nombres,
        )
        msg = await interaction.followup.send(
            embed=await selector.crear_embed(),
            view=selector,
            ephemeral=True,
        )
        selector.message = msg
        await selector.wait()
        if not selector.seleccionados:
            return
        captura_id = int(selector.seleccionados[0])
        try:
            mensaje = on_pick(captura_id)
        except database.EquipoError as e:
            await interaction.followup.send(f"❌ {e}", ephemeral=True)
            return
        await interaction.followup.send(mensaje, ephemeral=True)
        await self._refrescar_mensaje_principal()

    @discord.ui.button(label="➕ Añadir", style=discord.ButtonStyle.success, row=0)
    async def anadir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if database.contar_equipo(self.user.id) >= 9:
            return await interaction.response.send_message(
                "❌ Tu equipo está completo (9/9).",
                ephemeral=True,
            )
        capturas = self._capturas_disponibles_para_anadir()

        def on_pick(captura_id: int) -> str:
            slot = database.agregar_a_equipo(self.user.id, captura_id)
            cap = database.obtener_captura(self.user.id, captura_id)
            nombre = cap[1].capitalize() if cap else "?"
            return f"✅ **{nombre}** `[#{captura_id}]` añadido al slot **{slot}**."

        await self._ejecutar_selector_ephemeral(
            interaction, capturas, "➕ Añadir al equipo", on_pick
        )

    @discord.ui.button(label="🔄 Reemplazar", style=discord.ButtonStyle.primary, row=0)
    async def reemplazar(self, interaction: discord.Interaction, button: discord.ui.Button):
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
            slot = int(sel_inter.data["values"][0])
            capturas = self._capturas_para_reemplazo(slot)
            await sel_inter.response.edit_message(
                content=f"Slot **{slot}** — elige la captura:",
                view=None,
            )

            def on_pick(captura_id: int) -> str:
                database.reemplazar_en_equipo(self.user.id, slot, captura_id)
                cap = database.obtener_captura(self.user.id, captura_id)
                nombre = cap[1].capitalize() if cap else "?"
                return f"✅ Slot **{slot}** → **{nombre}** `[#{captura_id}]`."

            await self._ejecutar_selector_ephemeral(
                sel_inter,
                capturas,
                f"🔄 Reemplazar slot {slot}",
                on_pick,
                ya_respondido=True,
            )

        select.callback = callback
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        await interaction.response.send_message(
            "Elige el slot que quieres reemplazar:",
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="➖ Quitar", style=discord.ButtonStyle.secondary, row=0)
    async def quitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        equipo = database.obtener_equipo_detalle(self.user.id)
        llenos = [(i, s) for i, s in enumerate(equipo, 1) if s]
        if not llenos:
            return await interaction.response.send_message("❌ Tu equipo está vacío.", ephemeral=True)

        opciones = [
            discord.SelectOption(
                label=f"Slot {i}: {s['nombre'].capitalize()} [#{s['id']}]"[:100],
                value=str(i),
            )
            for i, s in llenos
        ]
        select = discord.ui.Select(placeholder="Elige qué quitar", options=opciones)

        async def callback(sel_inter: discord.Interaction):
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
        await interaction.response.send_message("Elige el Pokémon a quitar:", view=view, ephemeral=True)

    @discord.ui.button(label="📊 Comparar", style=discord.ButtonStyle.primary, row=1)
    async def comparar(self, interaction: discord.Interaction, button: discord.ui.Button):
        especies = database.obtener_lista_capturas(self.user.id)
        if len(especies) < 2:
            return await interaction.response.send_message(
                "❌ Necesitas al menos 2 especies distintas capturadas.",
                ephemeral=True,
            )
        if len(especies) <= POR_PAGINA:
            try:
                modal = CompararModal(self.user, self.session, especies)
                return await interaction.response.send_modal(modal)
            except (TypeError, AttributeError):
                view = CompararView(self.user, self.session, especies)
                return await interaction.response.send_message(
                    "Elige dos Pokémon y pulsa Comparar:",
                    view=view,
                    ephemeral=True,
                )
        await _comparar_dos_pasos(interaction, self.user, self.session, especies)

    async def on_timeout(self):
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True
