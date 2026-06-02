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
        {'nombre': str, 'tipo': list, 'atk': int, 'sp_atk': int, 'def': int, 'spd': int}
        """
        self.equipos = {
            "Jugador 1": {"pokes": equipo1, "hp": [100, 100, 100], "activo": 0},
            "Jugador 2": {"pokes": equipo2, "hp": [100, 100, 100], "activo": 0}
        }

    def obtener_multiplicador(self, tipo_atk, tipos_def):
        """Calcula el multiplicador considerando tipos simples o dobles."""
        mult_total = 1.0
        if tipo_atk not in TABLA_TIPOS:
            return 1.0
        
        efectos = TABLA_TIPOS[tipo_atk]
        for t_def in tipos_def:
            if t_def in efectos["super"]:
                mult_total *= 2.0
            elif t_def in efectos["poca"]:
                mult_total *= 0.5
        return mult_total

    def calcular_daño(self, atacante, defensor):
            """Calcula el daño basado en estadísticas de ataque vs defensa."""
            
            # 1. Obtener efectividad de tipo
            mult = self.obtener_multiplicador(atacante['tipo'][0], defensor['tipo'])
            
            # 2. Determinar la mejor estadística ofensiva y la defensa del rival
            ofensiva = max(atacante.get('atk', 50), atacante.get('sp_atk', 50))
            defensa_rival = defensor.get('def', 50)
            
            # 3. Fórmula de daño: (Ataque * 0.3) - (Defensa * 0.15)
            # Esto hace que un Pokémon con mucha defensa realmente reduzca el daño recibido.
            # Añadimos un pequeño componente aleatorio (random.randint) para variedad.
            daño_base = (ofensiva * 0.3) - (defensa_rival * 0.15) + random.randint(5, 15)
            
            # Aseguramos que el daño base no sea negativo si la defensa es muy alta
            daño_base = max(5, daño_base) * mult
            
            # 4. Lógica de Crítico: 20% de probabilidad, daño x1.5
            es_critico = random.random() < 0.20
            if es_critico:
                daño_base *= 1.5
                
            # 5. Aplicar variación aleatoria final
            daño_final = int(daño_base * random.uniform(0.85, 1.0))
            
            # 6. Textos de feedback
            mensajes = []
            if mult > 1.0: mensajes.append("¡Es súper efectivo!")
            elif mult < 1.0: mensajes.append("No es muy efectivo...")
            if es_critico: mensajes.append("¡Un golpe crítico!")
            
            # Retornamos el daño (mínimo 10 para que siempre haya progreso)
            return max(10, daño_final), " ".join(mensajes)

    def ejecutar_ronda(self):
        """Ejecuta una ronda donde ambos atacan (primero el más rápido)."""
        historial = []
        p1 = self.equipos["Jugador 1"]
        p2 = self.equipos["Jugador 2"]
        
        # Determinar orden basado en velocidad
        spd1 = p1['pokes'][p1['activo']]['spd']
        spd2 = p2['pokes'][p2['activo']]['spd']
        orden = ["Jugador 1", "Jugador 2"] if spd1 >= spd2 else ["Jugador 2", "Jugador 1"]
        
        for atacante in orden:
            defensor = "Jugador 2" if atacante == "Jugador 1" else "Jugador 1"
            
            # Verificar si el atacante sigue vivo antes de golpear
            if self.equipos[atacante]["hp"][self.equipos[atacante]["activo"]] > 0:
                p_atk = self.equipos[atacante]["pokes"][self.equipos[atacante]["activo"]]
                p_def = self.equipos[defensor]["pokes"][self.equipos[defensor]["activo"]]
                
                # Verificar si el defensor está vivo (puede haber sido derrotado antes en esta misma ronda)
                if self.equipos[defensor]["hp"][self.equipos[defensor]["activo"]] > 0:
                    daño, mensaje = self.calcular_daño(p_atk, p_def)
                    
                    # Aplicar daño
                    self.equipos[defensor]["hp"][self.equipos[defensor]["activo"]] -= daño
                    historial.append(f"**{p_atk['nombre']}** atacó a {p_def['nombre']} (-{daño} HP). {mensaje}")
                    
                    # Lógica de relevo si el defensor cae durante la ronda
                    if self.equipos[defensor]["hp"][self.equipos[defensor]["activo"]] <= 0:
                        self.equipos[defensor]["hp"][self.equipos[defensor]["activo"]] = 0
                        historial.append(f"¡{p_def['nombre']} se debilitó!")
                        if self.equipos[defensor]["activo"] < 2:
                            self.equipos[defensor]["activo"] += 1
                            nuevo = self.equipos[defensor]["pokes"][self.equipos[defensor]["activo"]]
                            historial.append(f"Sale {nuevo['nombre']} al combate.")
        
        return "\n".join(historial)

    def es_fin_del_juego(self):
        """Verifica si alguno de los equipos ha perdido todos sus Pokémon."""
        vida_j1 = sum(self.equipos["Jugador 1"]["hp"])
        vida_j2 = sum(self.equipos["Jugador 2"]["hp"])
        
        if vida_j1 <= 0: return "Jugador 2"
        elif vida_j2 <= 0: return "Jugador 1"
        return None