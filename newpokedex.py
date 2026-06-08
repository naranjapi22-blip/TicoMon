import discord
from discord.ext import commands
import aiohttp
from cache_service import db_cache
from vistas import PokedexView
import database  # Asegúrate de importar tu módulo de base de datos

REGIONES = {
    "1": (1, 151), "2": (152, 251), "3": (252, 386),
    "4": (387, 493), "5": (494, 649), "6": (650, 721),
    "7": (722, 809), "8": (810, 905), "9": (906, 1025)
}

@commands.command()
@canal_restringido()
async def pokedex(ctx, *, filtro: str = None):
    """
    Comando optimizado usando caché local para filtrado instantáneo.
    """
    if not hasattr(ctx.bot, 'session') or ctx.bot.session.closed:
        ctx.bot.session = aiohttp.ClientSession()

    async with ctx.typing():
        # 1. Obtener nombres de capturas
        es_shiny_mode = (filtro == "shiny")
        # Nota: Si tu base de datos principal es síncrona, esto bloquea un instante.
        # Si puedes, intenta que obtener_capturas sea una corrutina en el futuro.
        nombres_capturados = database.obtener_capturas(ctx.author.id, solo_shiny=es_shiny_mode)
        
        if not nombres_capturados:
            return await ctx.send("No tienes Pokémon registrados en tu colección.")

        # 2. Convertir nombres a IDs de Pokédex eficientemente
        ids_usuario = set()
        # Cache local para no preguntar 10 veces por el mismo nombre si el usuario tiene repetidos
        cache_temporal = {} 
        
        for nombre in nombres_capturados:
            if nombre not in cache_temporal:
                cache_temporal[nombre] = await db_cache.obtener_id_pokedex_por_nombre(nombre)
            
            id_pokedex = cache_temporal[nombre]
            if id_pokedex:
                ids_usuario.add(id_pokedex)

        # 3. Preparar variables de filtrado
        inicio, fin = 1, 1025
        region_label = "Colección"
        es_coleccion_personal = True
        ids_finales = ids_usuario

        # 4. Aplicar lógica de filtros
        if filtro:
            if filtro.isdigit() and filtro in REGIONES:
                inicio, fin = REGIONES[filtro]
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

    # 5. Lanzar la vista
    view = PokedexView(
        region=region_label,
        inicio=inicio,
        fin=fin,
        tenidos=ids_finales,
        es_coleccion_personal=es_coleccion_personal,
        modo_shiny=es_shiny_mode
    )
    
    await view.generar_vista_pokedex(ctx, ctx.bot.session)