import discord

import database

MAX_POKEDEX = 1077
COMPARE_POR_PAGINA = 5


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
    return (
        f"**{grupo['nombre'].capitalize()}** · x{grupo['cantidad']}\n"
        f"{_formatear_capturas_compare(grupo['capturas'])}\n"
    )


def _paginas_compare(grupos: list[dict]) -> list[str]:
    paginas = []
    for inicio in range(0, len(grupos), COMPARE_POR_PAGINA):
        bloque = grupos[inicio : inicio + COMPARE_POR_PAGINA]
        paginas.append("".join(_bloque_compare(g) for g in bloque))
    return paginas


class VistaCompare(discord.ui.View):
    def __init__(self, user, paginas: list[str], titulo: str):
        super().__init__(timeout=120)
        self.user = user
        self.paginas = paginas
        self.titulo = titulo
        self.pagina_actual = 0
        if len(paginas) <= 1:
            for item in self.children:
                item.disabled = True

    def embed_actual(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.titulo,
            description=self.paginas[self.pagina_actual],
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text=f"Página {self.pagina_actual + 1}/{len(self.paginas)} · !ivs [ID] para detalles"
        )
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(
                "❌ Solo el dueño puede cambiar de página.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina_actual = (self.pagina_actual - 1) % len(self.paginas)
        await interaction.response.edit_message(embed=self.embed_actual(), view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina_actual = (self.pagina_actual + 1) % len(self.paginas)
        await interaction.response.edit_message(embed=self.embed_actual(), view=self)


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

    @bot.command(name="comprar-pokemon")
    async def comprar_pokemon(ctx, miembro: discord.Member):
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
        paginas = _paginas_compare(grupos)
        vista = VistaCompare(ctx.author, paginas, titulo)
        await ctx.send(embed=vista.embed_actual(), view=vista)
