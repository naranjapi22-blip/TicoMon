import discord
from vistas_selector import SelectorPokemon


class SelectorBatalla(SelectorPokemon):
    """Selector de equipo para !batalla: 3 Pokémon con confirmación."""

    def __init__(self, user: discord.Member, lista_o_datos, session):
        if isinstance(lista_o_datos, dict):
            lista = lista_o_datos["valores"]
            etiquetas = lista_o_datos.get("etiquetas")
            nombres = lista_o_datos.get("nombres")
        else:
            lista = lista_o_datos
            etiquetas = None
            nombres = None
        super().__init__(
            user,
            lista,
            session,
            max_seleccion=3,
            titulo="⚔️ Arma tu equipo",
            descripcion_extra="Elige del menú, busca por nombre o confirma cuando tengas 3.",
            placeholder_select="➕ Añadir un Pokémon al equipo",
            etiqueta_campo="Tu equipo",
            auto_confirmar_uno=False,
            etiquetas=etiquetas,
            nombre_por_valor=nombres,
        )

    async def _finalizar_seleccion(self, interaction: discord.Interaction, vista_previa: str | None = None):
        self.stop()
        embed = await self.crear_embed(vista_previa=vista_previa)
        embed.title = "✅ Equipo listo"
        embed.color = discord.Color.green()
        await interaction.response.edit_message(embed=embed, view=None)


class PuertaSeleccionPrivada(discord.ui.View):
    """Mensaje público con un botón que abre el selector solo para el jugador (ephemeral)."""

    def __init__(self, jugador: discord.Member, lista: list[str], crear_selector):
        super().__init__(timeout=180)
        self.jugador = jugador
        self.lista = lista
        self.crear_selector = crear_selector
        self.seleccionados: list[str] = []

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.jugador.id:
            return False
        return True

    @discord.ui.button(
        label="📋 Elegir mi equipo (privado)",
        style=discord.ButtonStyle.primary,
    )
    async def abrir_selector(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        button.disabled = True
        await interaction.edit_original_response(view=self)

        selector = self.crear_selector(self.jugador, self.lista)

        if isinstance(selector, SelectorPokemon):
            embed = await selector.crear_embed()
            await interaction.followup.send(
                embed=embed,
                view=selector,
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "⚔️ Elige tus 3 Pokémon (solo tú ves este mensaje):",
                view=selector,
                ephemeral=True,
            )

        selector.message = await interaction.original_response()
        await selector.wait()
        self.seleccionados = list(selector.seleccionados)
        self.stop()

        if len(self.seleccionados) >= 3:
            await interaction.followup.send(
                "✅ Equipo registrado. Nadie más pudo ver tus elecciones.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "❌ No completaste la selección a tiempo.",
                ephemeral=True,
            )

    async def on_timeout(self):
        self.stop()


async def elegir_equipo_en_privado(ctx, jugador: discord.Member, lista: list[str], crear_selector):
    """
    Pide equipo sin mostrar picks en el canal: botón público → UI ephemeral.
    """
    puerta = PuertaSeleccionPrivada(jugador, lista, crear_selector)
    msg = await ctx.send(
        f"⚔️ {jugador.mention}, pulsa **Elegir mi equipo (privado)**. "
        "Solo tú verás tu lista y tus 3 Pokémon.",
        view=puerta,
    )
    await puerta.wait()
    try:
        await msg.delete()
    except discord.HTTPException:
        pass
    return puerta.seleccionados
