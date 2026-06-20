import random

from combate_calc import calcular_dano


class CombateSim:
    def __init__(self, equipo1, equipo2):
        self.equipos = {
            "Jugador 1": {
                "pokes": equipo1,
                "hp": [p.get("hp_max", 100) for p in equipo1],
                "hp_max": [p.get("hp_max", 100) for p in equipo1],
                "activo": 0,
            },
            "Jugador 2": {
                "pokes": equipo2,
                "hp": [p.get("hp_max", 100) for p in equipo2],
                "hp_max": [p.get("hp_max", 100) for p in equipo2],
                "activo": 0,
            },
        }

    def calcular_resultado_ataque(self, atacante, defensor):
        resultado = calcular_dano(atacante, defensor)
        return resultado.dano, resultado.mensaje

    def ejecutar_ronda(self):
        p1 = self.equipos["Jugador 1"]
        p2 = self.equipos["Jugador 2"]

        spd1 = p1["pokes"][p1["activo"]]["spd"]
        spd2 = p2["pokes"][p2["activo"]]["spd"]

        if spd1 > spd2:
            orden = ["Jugador 1", "Jugador 2"]
        elif spd2 > spd1:
            orden = ["Jugador 2", "Jugador 1"]
        else:
            orden = random.sample(
                ["Jugador 1", "Jugador 2"],
                2
            )
        historial = []
        activo_inicial_p1 = p1["activo"]
        activo_inicial_p2 = p2["activo"]

        for jug in orden:
            oponente = "Jugador 2" if jug == "Jugador 1" else "Jugador 1"
            idx_a = self.equipos[jug]["activo"]
            idx_d = self.equipos[oponente]["activo"]

            if jug == "Jugador 1" and self.equipos[jug]["activo"] != activo_inicial_p1:
                historial.append(
                    f"⏱️ {self.equipos[jug]['pokes'][idx_a]['nombre']} entró al campo y se prepara."
                )
                continue
            if jug == "Jugador 2" and self.equipos[jug]["activo"] != activo_inicial_p2:
                historial.append(
                    f"⏱️ {self.equipos[jug]['pokes'][idx_a]['nombre']} entró al campo y se prepara."
                )
                continue

            if self.equipos[jug]["hp"][idx_a] > 0 and self.equipos[oponente]["hp"][idx_d] > 0:
                p_atk = self.equipos[jug]["pokes"][idx_a]
                p_def = self.equipos[oponente]["pokes"][idx_d]

                dano, log = self.calcular_resultado_ataque(p_atk, p_def)
                self.equipos[oponente]["hp"][idx_d] -= dano
                historial.append(f"**{p_atk['nombre']}**: {log} (Daño: {dano} HP)")

                if self.equipos[oponente]["hp"][idx_d] <= 0:
                    self.equipos[oponente]["hp"][idx_d] = 0

                    if self.equipos[oponente]["activo"] + 1 < len(self.equipos[oponente]["pokes"]):
                        self.equipos[oponente]["activo"] += 1
                        nuevo = self.equipos[oponente]["pokes"][self.equipos[oponente]["activo"]]["nombre"]
                        historial.append(
                            f"⚠️ ¡{p_def['nombre']} se debilitó! {oponente} cambia a {nuevo}."
                        )
                    else:
                        historial.append(
                            f"💀 ¡{p_def['nombre']} se debilitó! ¡A {oponente} no le quedan más Pokémon!"
                        )

        return "\n".join(historial)

    def es_fin_del_juego(self):
        vida_j1 = sum(self.equipos["Jugador 1"]["hp"])
        vida_j2 = sum(self.equipos["Jugador 2"]["hp"])

        if vida_j1 <= 0:
            return "Jugador 2"
        if vida_j2 <= 0:
            return "Jugador 1"
        return None
