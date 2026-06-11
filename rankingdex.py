import discord
from discord.ext import commands

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
                    COUNT(DISTINCT pokemon_nombre) AS especies
                FROM capturas
                GROUP BY user_id
                ORDER BY especies DESC
            """)

            ranking = cursor.fetchall()

            if not ranking:
                await ctx.send("❌ No hay datos suficientes para generar el ranking.")
                return

            embed = discord.Embed(
                title="🏆 Ranking Global de Pokédex",
                color=discord.Color.gold()
            )

            top_texto = ""
            posicion_usuario = None
            especies_usuario = 0

            for posicion, fila in enumerate(ranking, start=1):

                user_id = int(fila[0])
                especies = fila[1]

                if posicion == 1:
                    emoji = "🥇"
                elif posicion == 2:
                    emoji = "🥈"
                elif posicion == 3:
                    emoji = "🥉"
                else:
                    emoji = f"{posicion}️⃣"

                if posicion <= 10:
                    usuario = bot.get_user(user_id)

                    if usuario:
                        nombre = usuario.display_name
                    else:
                        try:
                            usuario = await bot.fetch_user(user_id)
                            nombre = usuario.name
                        except:
                            nombre = f"Usuario {user_id}"

                    porcentaje = (especies / MAX_POKEDEX) * 100

                    top_texto += (
                        f"{emoji} **{nombre}**\n"
                        f"📚 {especies} especies • "
                        f"📈 {porcentaje:.1f}%\n\n"
                    )

                if user_id == ctx.author.id:
                    posicion_usuario = posicion
                    especies_usuario = especies

            embed.add_field(
                name="🌟 Top Entrenadores",
                value=top_texto,
                inline=False
            )

            if posicion_usuario:
                porcentaje_usuario = (
                    especies_usuario / MAX_POKEDEX
                ) * 100

                embed.add_field(
                    name="📍 Tu Posición",
                    value=(
                        f"**#{posicion_usuario}**\n"
                        f"📚 {especies_usuario} especies\n"
                        f"📈 {porcentaje_usuario:.1f}% completado"
                    ),
                    inline=False
                )

            embed.set_footer(
                text=f"Total de entrenadores clasificados: {len(ranking)}"
            )

            await ctx.send(embed=embed)

        finally:
            conn.close()