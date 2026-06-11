import discord

import database


def iniciar_modulo_ranking_shiny(bot):

    @bot.command(name="rankingshiny")
    async def rankingshiny(ctx):
        """Muestra el ranking de shinies."""

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT
                    user_id,
                    COUNT(*) AS shinies
                FROM capturas
                WHERE es_shiny = 1
                GROUP BY user_id
                ORDER BY shinies DESC
            """)

            ranking = cursor.fetchall()

            if not ranking:
                await ctx.send(
                    "❌ No hay suficientes shinies para generar el ranking."
                )
                return

            embed = discord.Embed(
                title="✨ Ranking Shiny Hunter",
                description="Los mejores cazadores de shinies.",
                color=discord.Color.gold()
            )

            top_texto = ""

            posicion_usuario = None
            shinies_usuario = 0

            for posicion, fila in enumerate(ranking, start=1):

                user_id = int(fila[0])
                shinies = fila[1]

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
                        f"✨ {shinies} shinies\n\n"
                    )

                if user_id == ctx.author.id:
                    posicion_usuario = posicion
                    shinies_usuario = shinies

            embed.add_field(
                name="✨ Top 5 Shiny Hunters",
                value=top_texto,
                inline=False
            )

            if posicion_usuario:

                diferencia_texto = ""

                if posicion_usuario > 1:
                    shinies_superior = ranking[posicion_usuario - 2][1]
                    diferencia = shinies_superior - shinies_usuario

                    diferencia_texto = (
                        f"\n⬆️ Te faltan **{diferencia}** "
                        f"shinies para alcanzar el puesto superior."
                    )

                embed.add_field(
                    name="📍 Tu Posición",
                    value=(
                        f"**#{posicion_usuario}**\n"
                        f"✨ Shinies capturados: **{shinies_usuario}**"
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
                f"❌ Error al generar el ranking shiny: {e}"
            )

        finally:
            conn.close()