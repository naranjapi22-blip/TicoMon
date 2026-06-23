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
            "7": (722, 809), "8": (810, 905), "9": (906, 1077)
        }

    @commands.command(name="pokedex")
    async def pokedex(self, ctx, *args):
        # 1. Preparar sesión
        if not hasattr(self.bot, 'session') or self.bot.session.closed:
            self.bot.session = aiohttp.ClientSession()

        async with ctx.typing():
            # Procesar argumentos: extraer si es shiny y el resto de filtros
            args_lower = [a.lower() for a in args]
            es_shiny_mode = "shiny" in args_lower
            
            # Obtener todos los Pokémon que el usuario tiene (shiny o normales según el modo)
            nombres_capturados = database.obtener_capturas(ctx.author.id, solo_shiny=es_shiny_mode)
            
            if not nombres_capturados:
                return await ctx.send("No tienes Pokémon registrados en tu colección.")

            mapping = await db_cache.obtener_ids_por_nombres(nombres_capturados)
            ids_usuario = {id_p for id_p in mapping.values() if id_p}

            # Preparar variables iniciales
            inicio, fin = 1, 1077
            region_label = "Colección"
            es_coleccion_personal = True
            ids_finales = ids_usuario
            tipo_filtro = None

            # 2. Lógica de filtros acumulativos
            for filtro in args:
                f_lower = filtro.lower()
                if f_lower == "shiny":
                    continue # Ya lo procesamos arriba
                
                if f_lower.isdigit() and f_lower in self.regiones:
                    inicio, fin = self.regiones[f_lower]
                    region_label = f"Región {f_lower}"
                    es_coleccion_personal = False
                
                elif f_lower == "legendarios":
                    ids_filtrados = await db_cache.obtener_ids_por_filtro(legendarios=True)
                    ids_finales = ids_finales.intersection(ids_filtrados)
                    region_label = "Legendarios y Míticos"
                
                else:
                    # Asumimos que es un tipo
                    ids_filtrados = await db_cache.obtener_ids_por_filtro(filtro_tipo=f_lower)
                    ids_finales = ids_finales.intersection(ids_filtrados)
                    tipo_filtro = f_lower.capitalize()
                    region_label = f"Tipo {tipo_filtro}"

            # 3. Validación de resultados
            if not ids_finales and not (any(a.isdigit() for a in args)):
                return await ctx.send(f"No tienes Pokémon que coincidan con esos filtros.")

            # 4. Lanzar vista
            view = PokedexView(
                region=region_label,
                inicio=inicio,
                fin=fin,
                tenidos=ids_finales,
                es_coleccion_personal=es_coleccion_personal,
                modo_shiny=es_shiny_mode
            )
            # Pasamos el filtro para que el embed sepa qué tipo mostrar
            view.filtro_actual = tipo_filtro if tipo_filtro else "All"
            await view.generar_vista_pokedex(ctx, self.bot.session)

async def setup(bot):
    await bot.add_cog(PokedexCog(bot))