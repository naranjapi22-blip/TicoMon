import asyncio
import aiohttp
from cache_service import db_cache

async def prellenar_cache():
    await db_cache.inicializar_bd()
    async with aiohttp.ClientSession() as session:
        print("Iniciando carga masiva de datos a la caché...")
        for i in range(1, 1026): # IDs del 1 al 1025
            async with session.get(f"https://pokeapi.co/api/v2/pokemon-species/{i}/") as resp:
                data = await resp.json()
                
                # Extraemos datos
                nombre = data['name']
                is_legendary = data.get('is_legendary', False)
                is_mythical = data.get('is_mythical', False)
                
                # Necesitamos también los tipos, esto requiere otra llamada a /pokemon/
                async with session.get(f"https://pokeapi.co/api/v2/pokemon/{i}/") as resp_p:
                    p_data = await resp_p.json()
                    tipos = [t['type']['name'] for t in p_data['types']]
                
                # Guardamos en caché
                await db_cache.guardar_pokemon(i, nombre, tipos, is_legendary, is_mythical)
                print(f"[{i}/1025] Guardado: {nombre}")

if __name__ == "__main__":
    asyncio.run(prellenar_cache())