import discord
import servicios
from database import obtener_id_pokemon
SPRITE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{poke_id}.png"
POR_PAGINA = 25


class BuscarPokemonModal(discord.ui.Modal, title="Buscar Pokémon"):
    def __init__(self, selector: "SelectorPokemon"):
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


class SelectorPokemon(discord.ui.View):
    """Selector reutilizable: paginación, búsqueda y hasta N Pokémon."""

    def __init__(
        self,
        user: discord.Member,
        lista_completa: list[str],
        session,
        *,
        max_seleccion: int = 3,
        titulo: str = "Elige Pokémon",
        descripcion_extra: str = "",
        placeholder_select: str = "➕ Añadir un Pokémon",
        etiqueta_campo: str = "Tu selección",
        auto_confirmar_uno: bool = True,
        etiquetas: dict[str, str] | None = None,
        nombre_por_valor: dict[str, str] | None = None,
    ):
        super().__init__(timeout=180)
        self.user = user
        self.session = session
        self.etiquetas = etiquetas or {}
        self.nombre_por_valor = nombre_por_valor or {}
        self.lista_completa = sorted(
            lista_completa,
            key=lambda v: self.etiquetas.get(v, v).lower(),
        )
        self.max_seleccion = max_seleccion
        self.titulo = titulo
        self.descripcion_extra = descripcion_extra
        self.placeholder_select = placeholder_select
        self.etiqueta_campo = etiqueta_campo
        self.auto_confirmar_uno = auto_confirmar_uno
        self.filtro: str | None = None
        self.pagina_actual = 0
        self.seleccionados: list[str] = []
        self.nombre_a_id: dict[str, int] = {}
        self.message: discord.Message | None = None
        self._reconstruir_componentes()

    def _etiqueta(self, valor: str) -> str:
        return self.etiquetas.get(valor, valor.capitalize())

    def _nombre_especie(self, valor: str) -> str:
        return self.nombre_por_valor.get(valor, valor)

    @property
    def lista_visible(self) -> list[str]:
        if self.filtro:
            return [
                v for v in self.lista_completa
                if self.filtro in v.lower()
                or self.filtro in self._etiqueta(v).lower()
                or self.filtro in self._nombre_especie(v).lower()
            ]
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
            poke_id = database.obtener_id_pokemon(
                nombre
            )
            if poke_id:
                self.nombre_a_id[clave] = poke_id
        return self.nombre_a_id.get(clave)

    def _texto_seleccion(self) -> str:
        if not self.seleccionados:
            return "— vacío —"
        lineas = []
        for i, valor in enumerate(self.seleccionados, 1):
            lineas.append(f"**{i}.** {self._etiqueta(valor)}")
        for i in range(len(self.seleccionados) + 1, self.max_seleccion + 1):
            lineas.append(f"**{i}.** —")
        return "\n".join(lineas)

    async def crear_embed(self, vista_previa: str | None = None) -> discord.Embed:
        busqueda = f"\n🔎 Filtro: `{self.filtro}`" if self.filtro else ""
        total_pag = max(1, len(self.paginas))
        desc = self.descripcion_extra or (
            f"Elige del menú, busca por nombre o confirma cuando tengas {self.max_seleccion}."
        )
        embed = discord.Embed(
            title=f"{self.titulo} ({len(self.seleccionados)}/{self.max_seleccion})",
            description=f"{desc}{busqueda}\n📄 Página **{self.pagina_actual + 1}/{total_pag}**",
            color=discord.Color.dark_teal(),
        )
        embed.add_field(name=self.etiqueta_campo, value=self._texto_seleccion(), inline=False)

        preview = vista_previa or (self.seleccionados[-1] if self.seleccionados else None)
        if preview:
            poke_id = await self.id_de(self._nombre_especie(preview))
            if poke_id:
                embed.set_thumbnail(url=SPRITE_URL.format(poke_id=poke_id))

        return embed

    def _reconstruir_componentes(self):
        self.clear_items()
        paginas = self.paginas
        if self.pagina_actual >= len(paginas):
            self.pagina_actual = max(0, len(paginas) - 1)

        opciones_pagina = paginas[self.pagina_actual]
        seleccion_llena = len(self.seleccionados) >= self.max_seleccion

        if opciones_pagina and not seleccion_llena:
            opciones = []
            for valor in opciones_pagina:
                kwargs = {
                    "label": self._etiqueta(valor)[:100],
                    "value": valor,
                }
                if valor in self.seleccionados:
                    kwargs["description"] = "Ya seleccionado"
                opciones.append(discord.SelectOption(**kwargs))
            select = discord.ui.Select(
                placeholder=self.placeholder_select,
                min_values=1,
                max_values=1,
                options=opciones,
            )
            select.callback = self._callback_anadir
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

        if self.seleccionados and self.max_seleccion > 1:
            btn_quitar = discord.ui.Button(label="↩ Quitar último", style=discord.ButtonStyle.secondary)
            btn_quitar.callback = self._callback_quitar
            self.add_item(btn_quitar)

        if self.max_seleccion > 1 or not self.auto_confirmar_uno:
            btn_confirmar = discord.ui.Button(
                label="✅ Confirmar",
                style=discord.ButtonStyle.success,
                disabled=len(self.seleccionados) < self.max_seleccion,
            )
            btn_confirmar.callback = self._callback_confirmar
            self.add_item(btn_confirmar)

    async def _editar_vista(self, interaction: discord.Interaction, vista_previa: str | None = None):
        embed = await self.crear_embed(vista_previa=vista_previa)
        await interaction.response.edit_message(embed=embed, view=self)

    async def _finalizar_seleccion(self, interaction: discord.Interaction, vista_previa: str | None = None):
        self.stop()
        embed = await self.crear_embed(vista_previa=vista_previa)
        embed.title = "✅ Selección lista"
        embed.color = discord.Color.green()
        await interaction.response.edit_message(embed=embed, view=None)

    async def _callback_anadir(self, interaction: discord.Interaction):
        nombre = interaction.data["values"][0]
        if nombre in self.seleccionados:
            return await interaction.response.send_message(
                "❌ Ese Pokémon ya está seleccionado.",
                ephemeral=True,
            )
        if len(self.seleccionados) >= self.max_seleccion:
            return await interaction.response.send_message(
                f"❌ Ya tienes {self.max_seleccion} Pokémon. Confirma o quita uno.",
                ephemeral=True,
            )
        self.seleccionados.append(nombre)
        if self.max_seleccion == 1 and self.auto_confirmar_uno:
            return await self._finalizar_seleccion(interaction, vista_previa=nombre)
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
        if len(self.seleccionados) < self.max_seleccion:
            return await interaction.response.send_message(
                f"❌ Necesitas exactamente {self.max_seleccion} Pokémon.",
                ephemeral=True,
            )
        await self._finalizar_seleccion(interaction)

    async def on_timeout(self):
        self.stop()
