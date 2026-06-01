import requests

def generar_lista_base():
    base_ids = []
    print("Analizando los Pokémon... esto puede tardar unos minutos.")
    
    # 1025 es el número actual aproximado de especies
    for i in range(1, 1026): 
        url = f"https://pokeapi.co/api/v2/pokemon-species/{i}/"
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # Si 'evolves_from_species' es None, es forma base
                if data['evolves_from_species'] is None:
                    base_ids.append(str(i))
                    print(f"ID {i} ({data['name']}) añadido.")
            else:
                print(f"Error al obtener ID {i}")
        except Exception as e:
            print(f"Fallo en conexión: {e}")
    
    with open('lista_spawn.txt', 'w') as f:
        f.write('\n'.join(base_ids))
    print(f"¡Listo! Se guardaron {len(base_ids)} Pokémon base en 'lista_spawn.txt'.")

generar_lista_base()