import discord
from discord.ext import commands
import random
import aiohttp
from vistas import BotonCaptura

# UNA SOLA FUNCIÓN SETUP PARA TODO EL ARCHIVO
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
        
        # Corregido: (nombre, es_legendario=False, es_shiny=True)
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
        
        # Corregido: (nombre, es_legendario=True, es_shiny=False)
        view = BotonCaptura(nombre, True, False) 
        await ctx.send(embed=embed, view=view)