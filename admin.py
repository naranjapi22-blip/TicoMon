import discord
from discord.ext import commands
import random
import aiohttp
from vistas import BotonCaptura

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
        random_id = random.randint(1, 1025)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pokeapi.co/api/v2/pokemon/{random_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    nombre = data['name']
                    url_imagen = data['sprites']['other']['official-artwork']['front_shiny']
                else:
                    nombre = "pikachu"
                    url_imagen = ""
        
        embed = discord.Embed(
            title="✨ ¡Ha aparecido un Pokémon SHINY salvaje!",
            description=f"Un **{nombre.capitalize()} ✨** salvaje apareció de la nada.",
            color=discord.Color.gold()
        )
        if url_imagen:
            embed.set_image(url=url_imagen)
        
        view = BotonCaptura(nombre, False, True)
        await ctx.send(embed=embed, view=view)

    # --- COMANDO SPAWNLEGENDARY ---
    @bot.command(name="spawnlegendary")
    @commands.has_permissions(administrator=True)
    async def spawnlegendary(ctx):
        """Fuerza la aparición de un Legendario: !spawnlegendary"""
        
        async with aiohttp.ClientSession() as session:
            es_legendario = False
            random_id = 0
            while not es_legendario:
                random_id = random.randint(1, 1025)
                async with session.get(f"https://pokeapi.co/api/v2/pokemon-species/{random_id}") as response:
                    if response.status == 200:
                        data_species = await response.json()
                        es_legendario = data_species['is_legendary']
            
            async with session.get(f"https://pokeapi.co/api/v2/pokemon/{random_id}") as response:
                data = await response.json()
                nombre = data['name']
                url_imagen = data['sprites']['other']['official-artwork']['front_default']

        embed = discord.Embed(
            title="👑 ¡Ha aparecido un Pokémon LEGENDARIO salvaje!",
            description=f"Un **{nombre.capitalize()}** legendario ha descendido al servidor.",
            color=discord.Color.gold()
        )
        
        if url_imagen:
            embed.set_image(url=url_imagen)
        
        view = BotonCaptura(nombre, True, False) 
        await ctx.send(embed=embed, view=view)

    # --- COMANDO SPAWNREGION ---
    @bot.command(name="spawnregion")
    @commands.has_permissions(administrator=True)
    async def spawnregion(ctx, region: str = None):
        """Hace aparecer un Pokémon de una región específica: !spawnregion <region>"""
        region = region.lower() if region else random.choice(list(REGIONES.keys()))
        
        if region not in REGIONES:
            return await ctx.send(f"❌ Región no válida. Usa: {', '.join(REGIONES.keys())}")

        rango = REGIONES[region]
        random_id = random.randint(rango[0], rango[1])
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pokeapi.co/api/v2/pokemon/{random_id}") as res:
                data = await res.json()
                nombre = data['name']
                url_imagen = data['sprites']['other']['official-artwork']['front_default']
        
        embed = discord.Embed(
            title=f"🌍 ¡Un Pokémon de {region.capitalize()} ha aparecido!",
            description=f"Un **{nombre.capitalize()}** salvaje apareció.",
            color=discord.Color.green()
        )
        embed.set_image(url=url_imagen)
        await ctx.send(embed=embed, view=BotonCaptura(nombre, False, False))

    # --- COMANDO SPAWNTYPE ---
    @bot.command(name="spawntype")
    @commands.has_permissions(administrator=True)
    async def spawntype(ctx, tipo: str = None):
        """Aparece un Pokémon de un tipo específico: !spawntype <tipo>"""
        if not tipo:
            return await ctx.send("❌ Debes especificar un tipo (ej: !spawntype fuego).")
        
        tipo_api = TRADUCCIONES_TIPOS.get(tipo.lower())
        if not tipo_api:
            return await ctx.send("❌ Tipo no encontrado. Asegúrate de escribirlo bien.")

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pokeapi.co/api/v2/type/{tipo_api}") as res:
                if res.status != 200:
                    return await ctx.send("❌ Error al buscar el tipo.")
                data_tipo = await res.json()
                poke_info = random.choice(data_tipo['pokemon'])
                
                async with session.get(poke_info['pokemon']['url']) as res_poke:
                    data = await res_poke.json()
                    nombre = data['name']
                    url_imagen = data['sprites']['other']['official-artwork']['front_default']

        embed = discord.Embed(
            title=f"🔥 ¡Un Pokémon de tipo {tipo.capitalize()}!",
            description=f"Un **{nombre.capitalize()}** salvaje apareció.",
            color=discord.Color.red()
        )
        if url_imagen:
            embed.set_image(url=url_imagen)
        
        await ctx.send(embed=embed, view=BotonCaptura(nombre, False, False))