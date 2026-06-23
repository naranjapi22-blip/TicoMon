import discord
from discord.ext import commands
import random
import aiohttp
from vistas import BotonCaptura
from logger_config import log
import servicios
from database import obtener_pokemon_local_nombre
import database
# DICCIONARIO PARA TRADUCCIONES DE TIPOS
TRADUCCIONES_TIPOS = {
    "fuego": "fire", "agua": "water", "planta": "grass", "electrico": "electric",
    "electridad": "electric", "veneno": "poison", "tierra": "ground", "roca": "rock",
    "bicho": "bug", "fantasma": "ghost", "acero": "steel", "psiquico": "psychic",
    "hielo": "ice", "dragon": "dragon", "siniestro": "dark", "hada": "fairy",
    "lucha": "fighting", "volador": "flying", "normal": "normal"
}

# DICCIONARIO DE REGIONES (RANGOS NACIONALES)
REGIONES = {
    "kanto": (1, 151), "johto": (152, 251), "hoenn": (252, 386),
    "sinnoh": (387, 493), "unova": (494, 649), "kalos": (650, 721),
    "alola": (722, 809), "galar": (810, 905), "paldea": (906, 1025)
}

async def setup(bot):

    print("ADMIN SETUP EJECUTADO")
    
# --- COMANDO SPAWNSHINY CORREGIDO ---
    @bot.command(name="spawnshiny")
    @commands.has_permissions(administrator=True)
    async def spawnshiny(ctx):
        """Fuerza la aparición de un Shiny con imagen: !spawnshiny"""
        try:
            log.info(f"🎯 [Admin] Comando spawnshiny ejecutado por {ctx.author}")
            random_id = random.randint(1, 1025)
            
            # Usamos servicios.obtener_pokemon para obtener data + species + capture_rate
            data, species = await servicios.obtener_pokemon(ctx.bot.session, random_id)
            
            if not data:
                return await ctx.send("❌ Error al obtener datos de la API.")
            
            nombre = data['name']
            url_imagen = data['sprites']['other']['official-artwork']['front_shiny']
            # Extraemos el rate desde species (la función de servicios ya lo prepara)
            rate = species.get('capture_rate', 45)
            
            embed = discord.Embed(
                title="✨ ¡Ha aparecido un Pokémon SHINY salvaje!",
                description=f"Un **{nombre.capitalize()} ✨** salvaje apareció.",
                color=discord.Color.gold()
            )
            embed.set_image(url=url_imagen)
            
            # PASAMOS LOS 4 ARGUMENTOS REQUERIDOS:
            # 1. data, 2. es_legendario, 3. es_shiny=True, 4. rate
            view = BotonCaptura(data, species.get('is_legendary', False), True, rate)
            
            await ctx.send(embed=embed, view=view)
            log.info(f"✅ Embed de shiny enviado exitosamente para {nombre}")
            
        except Exception as e:
            log.error(f"🚨 Error en comando spawnshiny: {e}", exc_info=True)
            await ctx.send("❌ Hubo un error al generar el Shiny.")

# --- COMANDO SPAWNLEGENDARY CORREGIDO ---
    @bot.command(name="spawnlegendary")
    @commands.has_permissions(administrator=True)
    async def spawnlegendary(ctx):
        """Fuerza la aparición de un Legendario: !spawnlegendary"""
        try:
            log.info(f"🎯 [Admin] Comando spawnlegendary por {ctx.author}")
            
            # Buscamos un legendario usando la función centralizada
            data, species = None, None
            while not species or not species.get('is_legendary'):
                random_id = random.randint(1, 1025)
                data, species = await servicios.obtener_pokemon(ctx.bot.session, random_id)
            
            # Extraemos los datos necesarios
            nombre = data['name']
            url_imagen = data['sprites']['other']['official-artwork']['front_default']
            rate = species.get('capture_rate', 3) # Los legendarios suelen tener rate 3
            
            embed = discord.Embed(
                title="👑 ¡Ha aparecido un Pokémon LEGENDARIO salvaje!",
                description=f"Un **{nombre.capitalize()}** legendario ha descendido al servidor.",
                color=discord.Color.gold()
            )
            embed.set_image(url=url_imagen)
            
            # CORRECCIÓN: Pasamos el objeto 'data' completo y el 'capture_rate'
            view = BotonCaptura(
                pokemon_data=data, 
                es_legendario=True, 
                es_shiny=False, 
                capture_rate=rate
            )
            
            await ctx.send(embed=embed, view=view)
            log.info(f"✅ Embed legendario enviado: {nombre}")
            
        except Exception as e:
            log.error(f"🚨 Error en comando spawnlegendary: {e}", exc_info=True)
            await ctx.send("❌ Hubo un error al generar el legendario.")

# --- COMANDO SPAWNREGION CORREGIDO ---
    @bot.command(name="spawnregion")
    @commands.has_permissions(administrator=True)
    async def spawnregion(ctx, region: str = None):
        """Hace aparecer un Pokémon de una región específica (No legendario): !spawnregion <region>"""
        try:
            region = region.lower() if region else random.choice(list(REGIONES.keys()))
            log.info(f"🎯 [Admin] Comando spawnregion ejecutado por {ctx.author} - Región: {region}")
            
            if region not in REGIONES:
                return await ctx.send(f"❌ Región no válida. Usa: {', '.join(REGIONES.keys())}")

            data, species = None, None
            es_legendario = True
            
            # FILTRO: Buscamos hasta encontrar uno que no sea legendario
            while es_legendario:
                rango = REGIONES[region]
                random_id = random.randint(rango[0], rango[1])
                data, species = await servicios.obtener_pokemon(ctx.bot.session, random_id)
                if data and species:
                    es_legendario = species.get('is_legendary', False)
            
            nombre = data['name']
            url_imagen = data['sprites']['other']['official-artwork']['front_default']
            rate = species.get('capture_rate', 45)
            
            embed = discord.Embed(
                title=f"🌍 ¡Un Pokémon de {region.capitalize()} ha aparecido!", 
                description=f"Un **{nombre.capitalize()}** salvaje apareció.", 
                color=discord.Color.green()
            )
            embed.set_image(url=url_imagen)
            
            # CORRECCIÓN: Pasamos el objeto completo 'data' y el 'rate' extraído
            view = BotonCaptura(
                pokemon_data=data, 
                es_legendario=False, 
                es_shiny=False, 
                capture_rate=rate
            )
            
            await ctx.send(embed=embed, view=view)
            log.info(f"✅ Embed de región enviado exitosamente: {nombre}")
            
        except Exception as e:
            log.error(f"🚨 Error en comando spawnregion: {e}", exc_info=True)
            await ctx.send("❌ Hubo un error al generar el Pokémon regional.")

# --- COMANDO SPAWNTYPE CORREGIDO ---
    @bot.command(name="spawntype")
    @commands.has_permissions(administrator=True)
    async def spawntype(ctx, tipo: str = None):
        """Aparece un Pokémon de un tipo específico (No legendario): !spawntype <tipo>"""
        try:
            if not tipo: return await ctx.send("❌ Debes especificar un tipo (ej: !spawntype fuego).")
            
            tipo_api = TRADUCCIONES_TIPOS.get(tipo.lower())
            if not tipo_api: return await ctx.send("❌ Tipo no encontrado.")

            log.info(f"🎯 [Admin] Comando spawntype ejecutado por {ctx.author} - Tipo: {tipo}")

            # Obtenemos la lista de Pokémon del tipo
            async with ctx.bot.session.get(f"https://pokeapi.co/api/v2/type/{tipo_api}") as res:
                data_tipo = await res.json()
                
                data, species = None, None
                is_leg = True
                
                # FILTRO: Buscamos hasta encontrar uno que no sea legendario
                while is_leg:
                    poke_info = random.choice(data_tipo['pokemon'])
                    poke_id = poke_info['pokemon']['url'].split('/')[-2]
                    data, species = await servicios.obtener_pokemon(ctx.bot.session, poke_id)
                    is_leg = species.get('is_legendary', False)

            rate = species.get('capture_rate', 45)
            
            embed = discord.Embed(
                title=f"🔥 ¡Un Pokémon de tipo {tipo.capitalize()}!", 
                description=f"Un **{data['name'].capitalize()}** salvaje apareció.", 
                color=discord.Color.red()
            )
            embed.set_image(url=data['sprites']['other']['official-artwork']['front_default'])
            
            # CORRECCIÓN: Pasamos el objeto 'data' y el 'rate' extraído
            view = BotonCaptura(
                pokemon_data=data, 
                es_legendario=False, 
                es_shiny=False, 
                capture_rate=rate
            )
            
            await ctx.send(embed=embed, view=view)
            log.info(f"✅ Embed de tipo enviado exitosamente: {data['name']}")
            
        except Exception as e:
            log.error(f"🚨 Error en comando spawntype: {e}", exc_info=True)
            await ctx.send("❌ Hubo un error al generar el Pokémon de ese tipo.")
    @bot.command(name="spawnpokemon")
    @commands.has_permissions(administrator=True)
    async def spawnpokemon(ctx, *, nombre):

        pokemon = database.obtener_pokemon_local_nombre(
            nombre.lower()
        )

        if not pokemon:
            return await ctx.send(
                "❌ Pokémon no encontrado."
            )

        await ctx.send(
            f"ID BD: {pokemon['id']}\n"
            f"Nombre: {pokemon['nombre']}"
        )