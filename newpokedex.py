import discord
from discord.ext import commands
import aiohttp
from cache_service import db_cache
from vistas import PokedexView
import database 

class PokedexCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.regiones = {
            "1": (1, 151), "2": (152, 251), "3": (252, 386),
            "4": (387, 493), "5": (494, 649), "6": (650, 721),
            "7": (722, 809), "8": (810, 905), "9": (906, 1025)
        }

    @commands.command(name="pokedex")
    # @canal_restringido() # Descomenta si tienes tu decorador personalizado
    async def pokedex(self, ctx, *, filtro: str = None):
        """Comando optimizado usando caché local para filtrado instantáneo."""
        
        if not hasattr(self.bot, 'session') or self.bot.session.closed:
            self.bot.session = aiohttp.ClientSession()

        async with ctx.typing():
            # 1. Obtener nombres de capturas
            es_shiny_mode = (filtro == "shiny")
            nombres_capturados = database.obtener_capturas(ctx.author.id, solo_shiny=es_shiny_mode)
            
            if not nombres_capturados:
                return await ctx.send("No tienes Pokémon registrados en tu colección.")

            # 2. Convertir nombres a IDs usando la caché
            ids_usuario = set()
            cache_temporal = {} 
            
            for nombre in nombres_capturados:
                if nombre not in cache_temporal:
                    cache_temporal[nombre] = await db_cache.obtener_id_pokedex_por_nombre(nombre)
                
                id_pokedex = cache_temporal[nombre]
                if id_pokedex:
                    ids_usuario.add(id_pokedex)

            # 3. Preparar variables
            inicio, fin = 1, 1025
            region_label = "Colección"
            es_coleccion_personal = True
            ids_finales = ids_usuario

            # 4. Lógica de filtros
            if filtro:
                if filtro.isdigit() and filtro in self.regiones:
                    inicio, fin = self.regiones[filtro]
                    region_label = f"Región {filtro}"
                    es_coleccion_personal = False
                
                elif filtro.lower() == "legendarios":
                    ids_filtrados = await db_cache.obtener_ids_por_filtro(legendarios=True)
                    ids_finales = ids_usuario.intersection(ids_filtrados)
                    region_label = "Legendarios y Míticos"
                
                elif not es_shiny_mode:
                    ids_filtrados = await db_cache.obtener_ids_por_filtro(filtro_tipo=filtro.lower())
                    ids_finales = ids_usuario.intersection(ids_filtrados)
                    region_label = f"Tipo {filtro.capitalize()}"

            if not ids_finales and not (filtro and filtro.isdigit()):
                return await ctx.send(f"No tienes Pokémon que coincidan con: **{filtro}**.")

        # 5. Lanzar vista
        view = PokedexView(
            region=region_label,
            inicio=inicio,
            fin=fin,
            tenidos=ids_finales,
            es_coleccion_personal=es_coleccion_personal,
            modo_shiny=es_shiny_mode
        )
        await view.generar_vista_pokedex(ctx, self.bot.session)

async def setup(bot):
    await bot.add_cog(PokedexCog(bot))