import random

# Tabla de efectividades
TABLA_TIPOS = {
    "normal": {"super": [], "poca": ["roca", "acero"]},
    "fuego": {"super": ["planta", "hielo", "bicho", "acero"], "poca": ["fuego", "agua", "roca", "dragon"]},
    "agua": {"super": ["fuego", "tierra", "roca"], "poca": ["agua", "planta", "dragon"]},
    "planta": {"super": ["agua", "tierra", "roca"], "poca": ["fuego", "planta", "veneno", "volador", "bicho", "acero", "dragon"]},
    "electrico": {"super": ["agua", "volador"], "poca": ["planta", "electrico", "dragon"]},
    "tierra": {"super": ["fuego", "electrico", "veneno", "roca", "acero"], "poca": ["planta", "bicho"]},
    "volador": {"super": ["planta", "lucha", "bicho"], "poca": ["electrico", "roca", "acero"]},
    "lucha": {"super": ["normal", "hielo", "roca", "acero", "siniestro"], "poca": ["veneno", "volador", "psiquico", "bicho", "hada"]},
    "roca": {"super": ["fuego", "hielo", "volador", "bicho"], "poca": ["lucha", "tierra", "acero"]},
    "veneno": {"super": ["planta", "hada"], "poca": ["veneno", "tierra", "roca", "fantasma"]},
    "psiquico": {"super": ["lucha", "veneno"], "poca": ["psiquico", "acero"]},
    "hielo": {"super": ["planta", "tierra", "volador", "dragon"], "poca": ["fuego", "agua", "hielo", "acero"]},
    "bicho": {"super": ["planta", "psiquico", "siniestro"], "poca": ["fuego", "lucha", "veneno", "volador", "fantasma", "acero", "hada"]},
    "fantasma": {"super": ["psiquico", "fantasma"], "poca": ["siniestro"]},
    "dragon": {"super": ["dragon"], "poca": ["acero"]},
    "siniestro": {"super": ["psiquico", "fantasma"], "poca": ["lucha", "siniestro", "hada"]},
    "acero": {"super": ["hielo", "roca", "hada"], "poca": ["fuego", "agua", "electrico", "acero"]},
    "hada": {"super": ["lucha", "dragon", "siniestro"], "poca": ["fuego", "veneno", "acero"]}
}

class CombateSim:
    def __init__(self, equipo1, equipo2):
        """
        equipo1/2 son listas de diccionarios:
        {'nombre': str, 'tipo': str, 'atk': int, 'def': int, 'spd': int}
        """
        self.equipos = {
            "Jugador 1": {"pokes": equipo1, "hp": [100, 100, 100], "activo": 0},
            "Jugador 2": {"pokes": equipo2, "hp": [100, 100, 100], "activo": 0}
        }

    def obtener_multiplicador(self, tipo_atk, tipo_def):
        """Calcula el multiplicador de daño según la tabla de tipos."""
        if tipo_atk not in TABLA_TIPOS:
            return 1.0
        
        efectos = TABLA_TIPOS[tipo_atk]
        if tipo_def in efectos["super"]:
            return 2.0
        elif tipo_def in efectos["poca"]:
            return 0.5
        return 1.0

    def calcular_daño(self, atacante, defensor):
            # Asegúrate de que defensor['tipo'] sea siempre una lista, 
            # incluso si solo tiene un tipo, ej: ['fuego']
            mult = self.obtener_multiplicador(atacante['tipo'], defensor['tipo'])
            
            ratio = atacante['atk'] / (defensor['def'] + 1)
            daño_base = (ratio * 10) * mult
            daño_final = int(daño_base * random.uniform(0.85, 1.15))
            
            # Mensaje dinámico según el multiplicador total
            texto = ""
            if mult > 1.0: texto = "¡Es súper efectivo!"
            elif mult < 1.0: texto = "No es muy efectivo..."
            
            return max(5, daño_final), texto

    def ejecutar_ronda(self):
        """Ejecuta una ronda donde ambos atacan (primero el más rápido)."""
        p1 = self.equipos["Jugador 1"]
        p2 = self.equipos["Jugador 2"]
        
        # Determinar orden basado en velocidad
        spd1 = p1['pokes'][p1['activo']]['spd']
        spd2 = p2['pokes'][p2['activo']]['spd']
        orden = ["Jugador 1", "Jugador 2"] if spd1 >= spd2 else ["Jugador 2", "Jugador 1"]
        
        historial = []
        for atacante in orden:
            defensor = "Jugador 2" if atacante == "Jugador 1" else "Jugador 1"
            
            # Verificar si el atacante sigue vivo antes de golpear
            if self.equipos[atacante]["hp"][self.equipos[atacante]["activo"]] > 0:
                p_atk = self.equipos[atacante]["pokes"][self.equipos[atacante]["activo"]]
                p_def = self.equipos[defensor]["pokes"][self.equipos[defensor]["activo"]]
                daño, mensaje = self.calcular_daño(p_atk, p_def)
                
                # Aplicar daño
                self.equipos[defensor]["hp"][self.equipos[defensor]["activo"]] -= daño
                historial.append(f"**{p_atk['nombre']}** atacó a {p_def['nombre']} (-{daño} HP). {mensaje}")
                
                # Lógica de relevo si el defensor cae durante la ronda
                if self.equipos[defensor]["hp"][self.equipos[defensor]["activo"]] <= 0:
                    if self.equipos[defensor]["activo"] < 2:
                        self.equipos[defensor]["activo"] += 1
        
        return "\n".join(historial)

    def es_fin_del_juego(self):
        """Verifica si alguno de los equipos ha perdido todos sus Pokémon."""
        vida_j1 = sum(self.equipos["Jugador 1"]["hp"])
        vida_j2 = sum(self.equipos["Jugador 2"]["hp"])
        
        if vida_j1 <= 0:
            return "Jugador 2" # Gana el jugador 2
        elif vida_j2 <= 0:
            return "Jugador 1" # Gana el jugador 1
            
        return None # El combate continúa
    def obtener_multiplicador(self, tipo_atk, tipos_def):
            """
            tipo_atk: string (ej: 'fuego')
            tipos_def: lista (ej: ['planta', 'volador'])
            """
            mult_total = 1.0
            for t_def in tipos_def:
                if tipo_atk not in TABLA_TIPOS:
                    continue
                    
                efectos = TABLA_TIPOS[tipo_atk]
                if t_def in efectos["super"]:
                    mult_total *= 2.0
                elif t_def in efectos["poca"]:
                    mult_total *= 0.5
            return mult_total