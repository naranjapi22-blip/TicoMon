import discord
from discord.ext import commands
import sqlite3
import database
import servicios

# --- 1. CONFIGURACIÓN DE BASE DE DATOS DEL PERFIL ---
def init_db_perfil():
    """Prepara la tabla del perfil y la actualiza si es necesario."""
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfiles (
            user_id INTEGER PRIMARY KEY,
            pokemon_destacado TEXT,
            es_shiny INTEGER DEFAULT 0
        )
    ''')
    # Actualización silenciosa: si la tabla ya existía sin la columna 'es_shiny', la añade
    try:
        cursor.execute("ALTER TABLE perfiles ADD COLUMN es_shiny INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # La columna ya existe, continuamos con normalidad
        
    conn.commit()
    conn.close()

def guardar_destacado(user_id, pokemon_nombre, es_shiny):
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        REPLACE INTO perfiles (user_id, pokemon_destacado, es_shiny) 
        VALUES (?, ?, ?)
    ''', (user_id, pokemon_nombre, es_shiny))
    conn.commit()
    conn.close()

def obtener_destacado(user_id):
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT pokemon_destacado, es_shiny FROM perfiles WHERE user_id = ?", (user_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado # Devuelve (nombre, es_shiny) o None

# --- 2. MÓDULO PRINCIPAL DE COMANDOS ---
def iniciar_modulo_perfil(bot):
    init_db_perfil() # Prepara la tabla al encender el bot

    @bot.command(name="perfil")
    async def perfil(ctx, miembro: discord.Member = None):
        """Muestra la tarjeta de entrenador del usuario con su progreso y compañero."""
        usuario = miembro or ctx.author
        
        # Extraemos datos
        todas_las_capturas = database.obtener_capturas(usuario.id, solo_shiny=False)
        capturas_shinies = database.obtener_capturas(usuario.id, solo_shiny=True)
        
        total_capturados = len(todas_las_capturas)
        especies_unicas = len(set(todas_las_capturas))
        total_shinies = len(capturas_shinies)
        
        MAX_POKEDEX = 1025
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
            es_shiny = bool(es_shiny_db) # Convierte el 0/1 a False/True
            
            data, _ = await servicios.obtener_pokemon(bot.session, destacado_nombre)
            if data:
                try:
                    if es_shiny:
                        url_imagen = data['sprites']['other']['official-artwork']['front_shiny']
                    else:
                        url_imagen = data['sprites']['other']['official-artwork']['front_default']
                except KeyError:
                    url_imagen = data['sprites']['front_default'] 
                
                embed.set_image(url=url_imagen)
                titulo_destacado = f"**{destacado_nombre.capitalize()}** {'✨' if es_shiny else ''}"
                embed.add_field(name="🌟 Compañero Destacado", value=titulo_destacado, inline=False)
                
                if es_shiny:
                    embed.color = discord.Color.gold()
        else:
            embed.add_field(name="🌟 Compañero Destacado", value="*No ha destacado ningún Pokémon.*\nUsa `@Bot destacar <nombre> [shiny]`", inline=False)
            
        await ctx.send(embed=embed)

    @bot.command(name="destacar")
    async def destacar(ctx, *, argumentos: str):
        """Elige un Pokémon que hayas capturado para mostrarlo en tu perfil gigante."""
        argumentos = argumentos.lower().strip()
        
        # 1. Analizamos lo que escribió el usuario
        quiere_shiny = False
        if argumentos.endswith(" shiny"):
            quiere_shiny = True
            # Le quitamos la palabra " shiny" al final para quedarnos solo con el nombre
            nombre = argumentos[:-6].strip() 
        else:
            nombre = argumentos

        # 2. Revisamos su inventario
        versiones = database.obtener_versiones_pokemon(ctx.author.id, nombre)
        
        # Filtro 1: No lo ha capturado en absoluto
        if not versiones:
            return await ctx.send(f"❌ ¡Aún no has capturado a **{nombre.capitalize()}**!")
        
        # Filtro 2: Pide shiny pero no lo tiene
        if quiere_shiny and 1 not in versiones:
            return await ctx.send(f"❌ ¡Aún no has capturado a **{nombre.capitalize()}** en su versión ✨ Shiny!")
            
        # Filtro 3: Pide normal pero solo tiene el shiny
        if not quiere_shiny and 0 not in versiones:
            return await ctx.send(f"❌ Solo posees la versión ✨ Shiny de **{nombre.capitalize()}**. Usa el comando `destacar {nombre} shiny`.")
        
        # 3. Guardamos la selección exacta en la base de datos
        es_shiny_int = 1 if quiere_shiny else 0
        guardar_destacado(ctx.author.id, nombre, es_shiny_int)
        
        texto_shiny = "✨ Shiny " if quiere_shiny else ""
        await ctx.send(f"🌟 ¡Excelente! **{nombre.capitalize()}** {texto_shiny}ahora es tu Pokémon compañero y aparecerá en grande en tu perfil.")