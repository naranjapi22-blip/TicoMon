import discord

import database

MAX_POKEDEX = 1025


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