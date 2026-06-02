
class GestorEquipo:
    def __init__(self):
        # Esta es tu "Pokédex" personal
        self.coleccion = []

    def agregar_pokemon(self, pokemon):
        self.coleccion.append(pokemon)
        print(f"¡{pokemon['nombre']} añadido a tu colección!")

    def mostrar_coleccion(self):
        print("\n--- Tu Colección ---")
        for i, p in enumerate(self.coleccion):
            print(f"{i}. {p['nombre']} | Tipos: {', '.join(p['tipo'])}")

    def armar_equipo(self, indices):
        if len(indices) != 3:
            print("Error: Debes seleccionar exactamente 3 Pokémon.")
            return None
        return [self.coleccion[i] for i in indices]