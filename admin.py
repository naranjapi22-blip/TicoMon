import discord
from discord.ext import commands
import random
import aiohttp
from vistas import BotonCaptura
from logger_config import log

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

def setup(bot):
    
    # --- COMANDO SPAWNSHINY ---
    @bot.command(name="spawnshiny")
    @commands.has_permissions(administrator=True)
    async def spawnshiny(ctx):
        """Fuerza la aparición de un Shiny con imagen: !spawnshiny"""
        try:
            log.info(f"🎯 [Admin] Comando spawnshiny ejecutado por {ctx.author} (ID: {ctx.author.id})")
            
            random_id = random.randint(1, 1025)
            log.debug(f"Pokémon ID seleccionado: {random_id}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://pokeapi.co/api/v2/pokemon/{random_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        nombre = data['name']
                        url_imagen = data['sprites']['other']['official-artwork']['front_shiny']
                        log.info(f"✅ Shiny generado: {nombre.capitalize()}")
                    else:
                        nombre = "pikachu"
                        url_imagen = ""
                        log.warning(f"❌ Error en API para ID {random_id}, usando default: pikachu")
            
            embed = discord.Embed(
                title="✨ ¡Ha aparecido un Pokémon SHINY salvaje!",
                description=f"Un **{nombre.capitalize()} ✨** salvaje apareció de la nada.",
                color=discord.Color.gold()
            )
            if url_imagen:
                embed.set_image(url=url_imagen)
            
            view = BotonCaptura(nombre, False, True)
            await ctx.send(embed=embed, view=view)
            log.info(f"✅ Embed de shiny enviado exitosamente")
            
        except Exception as e:
            log.error(f"🚨 Error en comando spawnshiny: {e}", exc_info=True)
            await ctx.send("❌ Hubo un error al generar el Shiny.")

    # --- COMANDO SPAWNLEGENDARY ---
    @bot.command(name="spawnlegendary")
    @commands.has_permissions(administrator=True)
    async def spawnlegendary(ctx):
        """Fuerza la aparición de un Legendario: !spawnlegendary"""
        try:
            log.info(f"🎯 [Admin] Comando spawnlegendary ejecutado por {ctx.author} (ID: {ctx.author.id})")
            
            async with aiohttp.ClientSession() as session:
                es_legendario = False
                random_id = 0
                intentos = 0
                while not es_legendario and intentos < 50:
                    random_id = random.randint(1, 1025)
                    async with session.get(f"https://pokeapi.co/api/v2/pokemon-species/{random_id}") as response:
                        if response.status == 200:
                            data_species = await response.json()
                            es_legendario = data_species['is_legendary']
                            intentos += 1
                
                if not es_legendario:
                    log.warning(f"⚠️ No se encontró legendario después de {intentos} intentos")
                
                log.debug(f"Legendario encontrado: ID {random_id}")
                
                async with session.get(f"https://pokeapi.co/api/v2/pokemon/{random_id}") as response:
                    data = await response.json()
                    nombre = data['name']
                    url_imagen = data['sprites']['other']['official-artwork']['front_default']
                    log.info(f"✅ Legendario obtenido: {nombre.capitalize()}")

            embed = discord.Embed(
                title="👑 ¡Ha aparecido un Pokémon LEGENDARIO salvaje!",
                description=f"Un **{nombre.capitalize()}** legendario ha descendido al servidor.",
                color=discord.Color.gold()
            )
            
            if url_imagen:
                embed.set_image(url=url_imagen)
            
            view = BotonCaptura(nombre, True, False)
            await ctx.send(embed=embed, view=view)
            log.info(f"✅ Embed legendario enviado exitosamente")
            
        except Exception as e:
            log.error(f"🚨 Error en comando spawnlegendary: {e}", exc_info=True)
            await ctx.send("❌ Hubo un error al generar el legendario.")

    # --- COMANDO SPAWNREGION (Sin Legendarios) ---
    @bot.command(name="spawnregion")
    @commands.has_permissions(administrator=True)
    async def spawnregion(ctx, region: str = None):
        """Hace aparecer un Pokémon de una región específica (No legendario): !spawnregion <region>"""
        try:
            region = region.lower() if region else random.choice(list(REGIONES.keys()))
            log.info(f"🎯 [Admin] Comando spawnregion ejecutado por {ctx.author} (ID: {ctx.author.id}) - Región: {region}")
            
            if region not in REGIONES:
                log.warning(f"⚠️ Región inválida solicitada: {region}")
                return await ctx.send(f"❌ Región no válida. Usa: {', '.join(REGIONES.keys())}")

            async with aiohttp.ClientSession() as session:
                es_legendario = True
                nombre, url_imagen = "", ""
                intentos = 0
                while es_legendario and intentos < 50:
                    rango = REGIONES[region]
                    random_id = random.randint(rango[0], rango[1])
                    # Verificamos si es legendario
                    async with session.get(f"https://pokeapi.co/api/v2/pokemon-species/{random_id}") as res_sp:
                        if res_sp.status == 200:
                            data_sp = await res_sp.json()
                            es_legendario = data_sp['is_legendary']
                    
                    if not es_legendario:
                        async with session.get(f"https://pokeapi.co/api/v2/pokemon/{random_id}") as res_pk:
                            data = await res_pk.json()
                            nombre = data['name']
                            url_imagen = data['sprites']['other']['official-artwork']['front_default']
                            log.info(f"✅ Pokémon de región {region} obtenido: {nombre.capitalize()}")
                    intentos += 1
            
            embed = discord.Embed(title=f"🌍 ¡Un Pokémon de {region.capitalize()} ha aparecido!", description=f"Un **{nombre.capitalize()}** salvaje apareció.", color=discord.Color.green())
            embed.set_image(url=url_imagen)
            await ctx.send(embed=embed, view=BotonCaptura(nombre, False, False))
            log.info(f"✅ Embed de región enviado exitosamente")
            
        except Exception as e:
            log.error(f"🚨 Error en comando spawnregion: {e}", exc_info=True)
            await ctx.send("❌ Hubo un error al generar el Pokémon regional.")

    # --- COMANDO SPAWNTYPE (Sin Legendarios) ---
    @bot.command(name="spawntype")
    @commands.has_permissions(administrator=True)
    async def spawntype(ctx, tipo: str = None):
        """Aparece un Pokémon de un tipo específico (No legendario): !spawntype <tipo>"""
        try:
            if not tipo:
                log.warning(f"⚠️ Comando spawntype sin tipo especificado")
                return await ctx.send("❌ Debes especificar un tipo (ej: !spawntype fuego).")
            
            log.info(f"🎯 [Admin] Comando spawntype ejecutado por {ctx.author} (ID: {ctx.author.id}) - Tipo: {tipo}")
            
            tipo_api = TRADUCCIONES_TIPOS.get(tipo.lower())
            if not tipo_api:
                log.warning(f"⚠️ Tipo inválido solicitado: {tipo}")
                return await ctx.send("❌ Tipo no encontrado.")

            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://pokeapi.co/api/v2/type/{tipo_api}") as res:
                    data_tipo = await res.json()
                    is_leg = True
                    intentos = 0
                    while is_leg and intentos < 50:
                        poke_info = random.choice(data_tipo['pokemon'])
                        async with session.get(poke_info['pokemon']['url']) as res_pk:
                            data = await res_pk.json()
                            poke_id = data['id']
                            # Verificar si es legendario
                            async with session.get(f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}") as res_sp:
                                data_sp = await res_sp.json()
                                is_leg = data_sp['is_legendary']
                                if not is_leg:
                                    nombre = data['name']
                                    url_imagen = data['sprites']['other']['official-artwork']['front_default']
                                    log.info(f"✅ Pokémon de tipo {tipo} obtenido: {nombre.capitalize()}")
                        intentos += 1

            embed = discord.Embed(title=f"🔥 ¡Un Pokémon de tipo {tipo.capitalize()}!", description=f"Un **{nombre.capitalize()}** salvaje apareció.", color=discord.Color.red())
            embed.set_image(url=url_imagen)
            await ctx.send(embed=embed, view=BotonCaptura(nombre, False, False))
            log.info(f"✅ Embed de tipo enviado exitosamente")
            
        except Exception as e:
            log.error(f"🚨 Error en comando spawntype: {e}", exc_info=True)
            await ctx.send("❌ Hubo un error al generar el Pokémon de ese tipo.")
