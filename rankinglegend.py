import discord

import database


def iniciar_modulo_ranking_legend(bot):

    @bot.command(name="rankinglegend")
    async def rankinglegend(ctx):
        """Muestra el ranking de legendarios y míticos."""

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT
                    c.user_id,
                    COUNT(*) AS legendarios
                FROM capturas c
                JOIN pokemon_data p
                    ON LOWER(c.pokemon_nombre) = LOWER(p.nombre)
                WHERE p.es_legendario = TRUE
                   OR p.es_mitico = TRUE
                GROUP BY c.user_id
                ORDER BY legendarios DESC
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
                    "❌ No hay suficientes legendarios para generar el ranking."
                )
                return

            embed = discord.Embed(
                title="👑 Ranking Legendario",
                description="Entrenadores con más Pokémon Legendarios y Míticos.",
                color=discord.Color.purple()
            )

            top_texto = ""

            posicion_usuario = None
            legendarios_usuario = 0

            for posicion, fila in enumerate(ranking, start=1):

                user_id = int(fila[0])
                legendarios = fila[1]

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

                    top_texto += (
                        f"{emoji} **{nombre}**\n"
                        f"👑 {legendarios} legendarios/míticos\n\n"
                    )

                if user_id == ctx.author.id:
                    posicion_usuario = posicion
                    legendarios_usuario = legendarios

            embed.add_field(
                name="👑 Top 5 Legendario",
                value=top_texto,
                inline=False
            )

            if posicion_usuario:

                diferencia_texto = ""

                if posicion_usuario > 1:
                    legendarios_superior = ranking[posicion_usuario - 2][1]
                    diferencia = legendarios_superior - legendarios_usuario

                    diferencia_texto = (
                        f"\n⬆️ Te faltan **{diferencia}** "
                        f"para alcanzar el puesto superior."
                    )

                embed.add_field(
                    name="📍 Tu Posición",
                    value=(
                        f"**#{posicion_usuario}**\n"
                        f"👑 Legendarios/Míticos: **{legendarios_usuario}**"
                        f"{diferencia_texto}"
                    ),
                    inline=False
                )

            embed.set_footer(
                text=f"Total de entrenadores clasificados: {len(ranking)}"
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(
                f"❌ Error al generar el ranking legendario: {e}"
            )

        finally:
            conn.close()