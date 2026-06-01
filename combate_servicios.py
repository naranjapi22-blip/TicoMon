import aiohttp

async def obtener_datos_combate(nombre_pokemon):
    """
    Consulta la PokeAPI y devuelve un diccionario con los stats 
    necesarios para el simulador de combate.
    """
    url = f"https://pokeapi.co/api/v2/pokemon/{nombre_pokemon.lower()}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                # Mapeo de stats: atacante, defensa y velocidad
                stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
                
                # Tipo principal (para la tabla de tipos)
                tipo = data['types'][0]['type']['name']
                
                return {
                    'nombre': nombre_pokemon.capitalize(),
                    'tipo': tipo,
                    'atk': stats.get('attack', 50),
                    'def': stats.get('defense', 50),
                    'spd': stats.get('speed', 50)
                }
        except:
            # Fallback en caso de error de conexión
            return {'nombre': nombre_pokemon.capitalize(), 'tipo': 'normal', 'atk': 50, 'def': 50, 'spd': 50}

async def preparar_equipos_completos(lista_nombres):
    """
    Toma una lista de nombres y devuelve la lista de diccionarios 
    procesados para pasárselos directamente a CombateSim.
    """
    equipo = []
    for nombre in lista_nombres:
        datos = await obtener_datos_combate(nombre)
        equipo.append(datos)
    return equipo