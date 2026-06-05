import aiohttp

async def obtener_datos_combate(nombre_pokemon):
    """
    Consulta la PokeAPI y devuelve un diccionario con los stats 
    necesarios para el simulador de combate (con tipos en lista).
    """
    url = f"https://pokeapi.co/api/v2/pokemon/{nombre_pokemon.lower()}"
    
    # Nota: Es mejor pasar la sesión como argumento, pero mantenemos tu lógica por ahora
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                # Mapeo de stats: attack, defense, speed
                stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
                
                # REVISIÓN: Extraer TODOS los tipos del Pokémon como una lista
                tipos = [t['type']['name'] for t in data['types']]
                
                return {
                    'nombre': nombre_pokemon.capitalize(),
                    'tipo': tipos,  # Ahora es una LISTA (ej: ['fuego', 'volador'])
                    'atk': stats.get('attack', 50),
                    'atk_esp': stats.get('special-attack', 50),
                    'def': stats.get('defense', 50),
                    'spd': stats.get('speed', 50),
                    'id': data['id'], # Añadido por si lo necesitas para imagencomb
                    'hp_base': stats.get('hp', 50)
                }
        except Exception as e:
            print(f"Error al obtener datos de {nombre_pokemon}: {e}")
            # Fallback seguro: tipo normal como lista
            return {
                'nombre': nombre_pokemon.capitalize(), 
                'tipo': ['normal'], 
                'atk': 50, 
                'def': 50, 
                'spd': 50
            }

async def preparar_equipos_completos(lista_nombres):
    """
    Toma una lista de nombres y devuelve la lista de diccionarios 
    procesados para pasárselos directamente a CombateSim.
    """
    equipo = []
    for nombre in lista_nombres:
        datos = await obtener_datos_combate(nombre)
        if datos:
            equipo.append(datos)
    return equipo