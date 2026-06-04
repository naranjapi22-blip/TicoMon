import discord
import servicios

SPRITE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{poke_id}.png"
POR_PAGINA = 25


class BuscarPokemonModal(discord.ui.Modal, title="Buscar Pokémon"):
    def __init__(self, selector: "SelectorBatalla"):
        super().__init__()
        self.selector = selector
        self.campo_nombre = discord.ui.TextInput(
            label="Nombre",
            placeholder="ej. pikachu, charizard…",
            max_length=50,
            required=True,
        )
        self.add_item(self.campo_nombre)

    async def on_submit(self, interaction: discord.Interaction):
        self.selector.filtro = self.campo_nombre.value.strip().lower()
        self.selector.pagina_actual = 0
        if not self.selector.lista_visible:
            return await interaction.response.send_message(
                "❌ No tienes ningún Pokémon que coincida con esa búsqueda.",
                ephemeral=True,
            )
        self.selector._reconstruir_componentes()
        embed = await self.selector.crear_embed()
        await interaction.response.edit_message(embed=embed, view=self.selector)


class SelectorBatalla(discord.ui.View):
    """Selector de equipo para !batalla: miniaturas, búsqueda y confirmación."""

    def __init__(self, user: discord.Member, lista_completa: list[str], session):
        super().__init__(timeout=180)
        self.user = user
        self.session = session
        self.lista_completa = sorted(lista_completa, key=str.lower)
        self.filtro: str | None = None
        self.pagina_actual = 0
        self.seleccionados: list[str] = []
        self.nombre_a_id: dict[str, int] = {}
        self.message: discord.Message | None = None
        self._reconstruir_componentes()

    @property
    def lista_visible(self) -> list[str]:
        if self.filtro:
            return [n for n in self.lista_completa if self.filtro in n.lower()]
        return self.lista_completa

    @property
    def paginas(self) -> list[list[str]]:
        visible = self.lista_visible
        if not visible:
            return [[]]
        return [visible[i : i + POR_PAGINA] for i in range(0, len(visible), POR_PAGINA)]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "❌ Esta selección no es tuya.",
                ephemeral=True,
            )
            return False
        return True

    async def id_de(self, nombre: str) -> int | None:
        clave = nombre.lower()
        if clave not in self.nombre_a_id:
            poke_id = await servicios.obtener_id_por_nombre(self.session, nombre)
            if poke_id:
                self.nombre_a_id[clave] = poke_id
        return self.nombre_a_id.get(clave)

    def _texto_equipo(self) -> str:
        if not self.seleccionados:
            return "— vacío —"
        lineas = []
        for i, nombre in enumerate(self.seleccionados, 1):
            lineas.append(f"**{i}.** {nombre.capitalize()}")
        for i in range(len(self.seleccionados) + 1, 4):
            lineas.append(f"**{i}.** —")
        return "\n".join(lineas)

    async def crear_embed(self, vista_previa: str | None = None) -> discord.Embed:
        busqueda = f"\n🔎 Filtro: `{self.filtro}`" if self.filtro else ""
        total_pag = max(1, len(self.paginas))
        embed = discord.Embed(
            title=f"⚔️ Arma tu equipo ({len(self.seleccionados)}/3)",
            description=(
                f"Elige del menú, busca por nombre o confirma cuando tengas 3.{busqueda}\n"
                f"📄 Página **{self.pagina_actual + 1}/{total_pag}**"
            ),
            color=discord.Color.dark_teal(),
        )
        embed.add_field(name="Tu equipo", value=self._texto_equipo(), inline=False)

        preview = vista_previa or (self.seleccionados[-1] if self.seleccionados else None)
        if preview:
            poke_id = await self.id_de(preview)
            if poke_id:
                embed.set_thumbnail(url=SPRITE_URL.format(poke_id=poke_id))

        return embed

    def _reconstruir_componentes(self):
        self.clear_items()
        paginas = self.paginas
        if self.pagina_actual >= len(paginas):
            self.pagina_actual = max(0, len(paginas) - 1)

        opciones_pagina = paginas[self.pagina_actual]
        equipo_lleno = len(self.seleccionados) >= 3

        if opciones_pagina and not equipo_lleno:
            opciones = []
            for nombre in opciones_pagina:
                kwargs = {
                    "label": nombre.capitalize()[:100],
                    "value": nombre,
                }
                if nombre in self.seleccionados:
                    kwargs["description"] = "Ya en el equipo"
                opciones.append(discord.SelectOption(**kwargs))
            select = discord.ui.Select(
                placeholder="➕ Añadir un Pokémon al equipo",
                min_values=1,
                max_values=1,
                options=opciones,
            )
            select.callback = self._callback_anadir
            self.add_item(select)

        # Botones en View clásico (sin ActionRow — eso es solo Components V2)
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

        if self.seleccionados:
            btn_quitar = discord.ui.Button(label="↩ Quitar último", style=discord.ButtonStyle.secondary)
            btn_quitar.callback = self._callback_quitar
            self.add_item(btn_quitar)

        btn_confirmar = discord.ui.Button(
            label="✅ Confirmar equipo",
            style=discord.ButtonStyle.success,
            disabled=len(self.seleccionados) < 3,
        )
        btn_confirmar.callback = self._callback_confirmar
        self.add_item(btn_confirmar)

    async def _editar_vista(self, interaction: discord.Interaction, vista_previa: str | None = None):
        embed = await self.crear_embed(vista_previa=vista_previa)
        await interaction.response.edit_message(embed=embed, view=self)

    async def _callback_anadir(self, interaction: discord.Interaction):
        nombre = interaction.data["values"][0]
        if nombre in self.seleccionados:
            return await interaction.response.send_message(
                "❌ Ese Pokémon ya está en tu equipo.",
                ephemeral=True,
            )
        if len(self.seleccionados) >= 3:
            return await interaction.response.send_message(
                "❌ Ya tienes 3 Pokémon. Confirma o quita uno.",
                ephemeral=True,
            )
        self.seleccionados.append(nombre)
        self._reconstruir_componentes()
        await self._editar_vista(interaction, vista_previa=nombre)

    async def _callback_atras(self, interaction: discord.Interaction):
        self.pagina_actual = max(0, self.pagina_actual - 1)
        self._reconstruir_componentes()
        await self._editar_vista(interaction)

    async def _callback_adelante(self, interaction: discord.Interaction):
        self.pagina_actual = min(len(self.paginas) - 1, self.pagina_actual + 1)
        self._reconstruir_componentes()
        await self._editar_vista(interaction)

    async def _callback_buscar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BuscarPokemonModal(self))

    async def _callback_ver_todos(self, interaction: discord.Interaction):
        self.filtro = None
        self.pagina_actual = 0
        self._reconstruir_componentes()
        await self._editar_vista(interaction)

    async def _callback_quitar(self, interaction: discord.Interaction):
        if not self.seleccionados:
            return await interaction.response.send_message("No hay Pokémon que quitar.", ephemeral=True)
        self.seleccionados.pop()
        self._reconstruir_componentes()
        await self._editar_vista(interaction)

    async def _callback_confirmar(self, interaction: discord.Interaction):
        if len(self.seleccionados) < 3:
            return await interaction.response.send_message(
                "❌ Necesitas exactamente 3 Pokémon.",
                ephemeral=True,
            )
        self.stop()
        embed = await self.crear_embed()
        embed.title = "✅ Equipo listo"
        embed.color = discord.Color.green()
        await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self):
        self.stop()
