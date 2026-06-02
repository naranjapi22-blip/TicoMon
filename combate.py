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
        self.equipos = {
            "Jugador 1": {
                "pokes": equipo1, 
                "hp": [p.get('hp_base', 50) for p in equipo1],
                "hp_max": [p.get('hp_base', 50) for p in equipo1],
                "activo": 0
            },
            "Jugador 2": {
                "pokes": equipo2, 
                "hp": [p.get('hp_base', 50) for p in equipo2],
                "hp_max": [p.get('hp_base', 50) for p in equipo2],
                "activo": 0
            }
        }

    def obtener_multiplicador(self, tipos_atk, tipos_def):
        """
        tipos_atk: El tipo del ataque (normalmente un string, ej: "fuego").
        tipos_def: Una lista con los tipos del defensor (ej: ["planta", "veneno"]).
        """
        # Aseguramos que tipos_atk sea el tipo único del ataque
        if isinstance(tipos_atk, list):
            tipo_atk = tipos_atk[0]
        else:
            tipo_atk = tipos_atk
            
        # Aseguramos que tipos_def sea una lista
        if isinstance(tipos_def, str):
            tipos_def = [tipos_def]
            
        if tipo_atk not in TABLA_TIPOS:
            return 1.0
        
        mult = 1.0
        # Multiplicamos la efectividad por cada tipo del defensor
        for t_def in tipos_def:
            efectos = TABLA_TIPOS[tipo_atk]
            if t_def in efectos["super"]:
                mult *= 2.0
            elif t_def in efectos["poca"]:
                mult *= 0.5
        
        return mult

    def calcular_resultado_ataque(self, atacante, defensor):
        # 1. Estadística ofensiva
        stat_ofensivo = max(atacante.get('atk', 50), atacante.get('atk_esp', 50))
        
        # 2. Factores de estrategia
        stab = 1.3 if atacante['tipo'][0] in atacante['tipo'] else 1.0
        mult = self.obtener_multiplicador(atacante['tipo'], defensor['tipo'])
        
        # 3. FÓRMULA DE DAÑO (Poder base ajustado a 25 para menos potencia)
        poder_base = 25 
        daño = int((stat_ofensivo / (defensor['def'] + 15)) * poder_base * mult * stab)
        
        # 4. Fallos y Críticos
        if random.random() < 0.10:
            return 0, f"💨 ¡{atacante['nombre']} falló!"

        es_critico = random.random() < 0.10
        if es_critico:
            daño = int(daño * 1.4)
            prefijo = "💥 ¡GOLPE CRÍTICO!"
        else:
            prefijo = "✨ ¡Ataque directo!"
            
        # 5. Variación
        daño = int(daño * random.uniform(0.8, 1.0))
        daño = max(3, daño)
        
        sufijo = " ¡Es súper efectivo!" if mult >= 2.0 else (" No es muy efectivo..." if mult <= 0.5 else "")
        mensaje = f"{prefijo} **{atacante['nombre']}** causa {daño} HP.{sufijo}"
        
        return daño, mensaje
    def ejecutar_ronda(self):
        p1 = self.equipos["Jugador 1"]
        p2 = self.equipos["Jugador 2"]
        
        spd1 = p1['pokes'][p1['activo']]['spd']
        spd2 = p2['pokes'][p2['activo']]['spd']
        
        # 1. Definimos quién ataca primero
        orden = ["Jugador 1", "Jugador 2"] if spd1 >= spd2 else ["Jugador 2", "Jugador 1"]
        
        historial = []
        
        # 2. Registramos quién está activo al inicio de la ronda
        # Si alguien cambia, este ID cambiará
        activo_inicial_p1 = p1['activo']
        activo_inicial_p2 = p2['activo']

        for jug in orden:
            oponente = "Jugador 2" if jug == "Jugador 1" else "Jugador 1"
            
            idx_a = self.equipos[jug]["activo"]
            idx_d = self.equipos[oponente]["activo"]
            
            # --- CORRECCIÓN CRÍTICA ---
            # Si el Pokémon que le toca atacar es el que entró en ESTA MISMA RONDA 
            # tras un cambio, no debería atacar.
            if jug == "Jugador 1" and self.equipos[jug]["activo"] != activo_inicial_p1:
                historial.append(f"⏱️ {self.equipos[jug]['pokes'][idx_a]['nombre']} entró al campo y se prepara.")
                continue
            if jug == "Jugador 2" and self.equipos[jug]["activo"] != activo_inicial_p2:
                historial.append(f"⏱️ {self.equipos[jug]['pokes'][idx_a]['nombre']} entró al campo y se prepara.")
                continue

            # Verificar si tienen vida y realizar ataque
            if self.equipos[jug]["hp"][idx_a] > 0 and self.equipos[oponente]["hp"][idx_d] > 0:
                p_atk = self.equipos[jug]["pokes"][idx_a]
                p_def = self.equipos[oponente]["pokes"][idx_d]
                
                daño, log = self.calcular_resultado_ataque(p_atk, p_def)
                
                # Lógica de Aguante
                vida_actual = self.equipos[oponente]["hp"][idx_d]
                if vida_actual - daño <= 0 and vida_actual > 50:
                    if random.random() < 0.20:
                        daño = vida_actual - 1
                        historial.append(f"🔥 ¡{p_def['nombre']} sobrevive a 1 HP!")
                
                self.equipos[oponente]["hp"][idx_d] -= daño
                historial.append(f"**{p_atk['nombre']}**: {log} (Daño: {daño} HP)")
                
                # Lógica de relevo
                if self.equipos[oponente]["hp"][idx_d] <= 0:
                    self.equipos[oponente]["hp"][idx_d] = 0
                    if self.equipos[oponente]["activo"] < 2:
                        self.equipos[oponente]["activo"] += 1
                        nuevo = self.equipos[oponente]['pokes'][self.equipos[oponente]['activo']]['nombre']
                        historial.append(f"⚠️ ¡{p_def['nombre']} se debilitó! {oponente} cambia a {nuevo}.")
        
        return "\n".join(historial)

    def es_fin_del_juego(self):
        """Verifica si alguno de los equipos ha perdido todos sus Pokémon."""
        vida_j1 = sum(self.equipos["Jugador 1"]["hp"])
        vida_j2 = sum(self.equipos["Jugador 2"]["hp"])
        
        if vida_j1 <= 0: return "Jugador 2"
        if vida_j2 <= 0: return "Jugador 1"
        return None