import discord
from discord.ext import commands
import database
import servicios
import os
import random
import psycopg2
from logger_config import log
from servicios_gif import obtener_gif
# --- 1. CONFIGURACIÓN DE BASE DE DATOS DEL PERFIL ---
def init_db_perfil():
    """Prepara la tabla del perfil."""

    conn = database.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfiles (
                user_id BIGINT PRIMARY KEY,
                pokemon_destacado TEXT,
                es_shiny INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            ALTER TABLE perfiles
            ADD COLUMN IF NOT EXISTS es_shiny INTEGER DEFAULT 0
        """)

        conn.commit()

    finally:
        cursor.close()
        conn.close()

def guardar_destacado(user_id, pokemon_nombre, es_shiny):
    conn = database.get_connection()
    cursor = conn.cursor()

    try:
        query = """
            INSERT INTO perfiles (user_id, pokemon_destacado, es_shiny)
            VALUES (%s, %s, %s)
            ON CONFLICT(user_id)
            DO UPDATE SET
                pokemon_destacado = EXCLUDED.pokemon_destacado,
                es_shiny = EXCLUDED.es_shiny
        """

        cursor.execute(
            query,
            (str(user_id), pokemon_nombre, es_shiny)
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()

def obtener_destacado(user_id):
    conn = database.get_connection()
    cursor = conn.cursor()
    
    is_postgres = os.environ.get('DATABASE_URL') is not None
    
    if is_postgres:
        cursor.execute("SELECT pokemon_destacado, es_shiny FROM perfiles WHERE user_id = %s", (str(user_id),))
    else:
        cursor.execute("SELECT pokemon_destacado, es_shiny FROM perfiles WHERE user_id = ?", (user_id,))
    
    resultado = cursor.fetchone()
    conn.close()
    return resultado

# --- 2. MÓDULO PRINCIPAL DE COMANDOS ---
def iniciar_modulo_perfil(bot):
    init_db_perfil() # Prepara la tabla al encender el bot

    @bot.command(name="perfil")
    async def perfil(ctx, miembro: discord.Member = None):
        """Muestra la tarjeta de entrenador del usuario con su progreso y compañero."""
        usuario = miembro or ctx.author
        
        # Extraemos datos globales de capturas
        todas_las_capturas = database.obtener_capturas(usuario.id, solo_shiny=False)
        capturas_shinies = database.obtener_capturas(usuario.id, solo_shiny=True)
        
        total_capturados = len(todas_las_capturas)
        especies_unicas = len(set(todas_las_capturas))
        total_shinies = len(capturas_shinies)
        
        MAX_POKEDEX = 1077
        porcentaje_completado = (especies_unicas / MAX_POKEDEX) * 100 if MAX_POKEDEX > 0 else 0
        bloques_llenos = int(porcentaje_completado // 10)
        barra_visual = "🟩" * bloques_llenos + "⬛" * (10 - bloques_llenos)

        embed = discord.Embed(
            title=f"🎒 Tarjeta de Entrenador: {usuario.display_name}",
            color=discord.Color.from_rgb(46, 125, 50)
        )
        embed.set_thumbnail(url=usuario.display_avatar.url)
        
        embed.add_field(
            name="📊 Estadísticas de Colección",
            value=f"• **Total Capturas:** `{total_capturados}`\n"
                  f"• **Variocolores (Shiny) ✨:** `{total_shinies}`",
            inline=True
        )
        
        embed.add_field(
            name=f"📈 Progreso de la Pokédex",
            value=f"{barra_visual} ({porcentaje_completado:.1f}%)\n`{especies_unicas}` de `{MAX_POKEDEX}` registrados.",
            inline=False
        )

        # --- LÓGICA DE VISUALIZACIÓN DEL DESTACADO ---
        datos_destacado = obtener_destacado(usuario.id)

        if datos_destacado:

            destacado_nombre, es_shiny_db = datos_destacado
            es_shiny = bool(es_shiny_db)

            pokemon = database.obtener_pokemon_local_nombre(
                destacado_nombre
            )

            dex_id = None

            if pokemon:
                dex_id = pokemon.get(
                    "pokeapi_id",
                    pokemon["id"]
                )

                display_scale = float(
                    pokemon.get(
                        "display_scale",
                        1.0
                    )
                )
            if dex_id:

                try:

                    print(
                        f"DESTACADO={destacado_nombre} | "
                        f"DEX={dex_id}"
                    )

                    buffer = await obtener_gif(
                        dex_id,
                        es_shiny,
                        display_scale
                    )

                    file = discord.File(
                        buffer,
                        filename="pokemon.gif"
                    )

                    embed.set_image(
                        url="attachment://pokemon.gif"
                    )

                except Exception as e:

                    print(
                        f"Error cargando GIF "
                        f"{destacado_nombre}: {e}"
                    )

                titulo_destacado = (
                    f"**{destacado_nombre.capitalize()}** "
                    f"{'✨' if es_shiny else ''}"
                )

                embed.add_field(
                    name="🌟 Compañero Destacado",
                    value=titulo_destacado,
                    inline=False
                )

                if es_shiny:
                    embed.color = discord.Color.gold()

        else:

            embed.add_field(
                name="🌟 Compañero Destacado",
                value=(
                    "*No ha destacado ningún Pokémon.*\n"
                    "Usa `!destacar <nombre>`"
                ),
                inline=False
            )

            if es_shiny:
                embed.color = discord.Color.gold()
            else:
                embed.add_field(name="🌟 Compañero Destacado", value="*No ha destacado ningún Pokémon.*\nUsa `@Bot destacar <nombre> [shiny]`", inline=False)
            
        if datos_destacado and dex_id:

            await ctx.send(
                embed=embed,
                file=file
            )

        else:

            await ctx.send(
                embed=embed
            )

    @bot.command(name="destacar")
    async def destacar(ctx, *, argumentos: str):
        """Elige un Pokémon que hayas capturado para mostrarlo en tu perfil gigante."""
        argumentos = argumentos.lower().strip()
        
        # 1. Analizamos lo que escribió el usuario
        quiere_shiny = False
        if argumentos.endswith(" shiny"):
            quiere_shiny = True
            nombre = argumentos[:-6].strip() 
        else:
            nombre = argumentos

        # 2. Revisamos su inventario
        versiones = database.obtener_versiones_pokemon(ctx.author.id, nombre)
        
        # Filtros de validación
        if not versiones:
            return await ctx.send(f"❌ ¡Aún no has capturado a **{nombre.capitalize()}**!")
        
        if quiere_shiny and 1 not in versiones:
            return await ctx.send(f"❌ ¡Aún no has capturado a **{nombre.capitalize()}** en su versión ✨ Shiny!")
            
        if not quiere_shiny and 0 not in versiones:
            return await ctx.send(f"❌ Solo posees la versión ✨ Shiny de **{nombre.capitalize()}**. Usa el comando `destacar {nombre} shiny`.")
        
        # 3. Guardamos la selección
        es_shiny_int = 1 if quiere_shiny else 0
        guardar_destacado(ctx.author.id, nombre, es_shiny_int)
        
        texto_shiny = "✨ Shiny " if quiere_shiny else ""
        await ctx.send(f"🌟 ¡Excelente! **{nombre.capitalize()}** {texto_shiny}ahora es tu Pokémon compañero y aparecerá en grande en tu perfil.")