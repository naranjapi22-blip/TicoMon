import random

from combate_v2.motor import MotorCombate
from combate_calc import calcular_dano


class CombateSim:

    def __init__(self, equipo1, equipo2):

        self.motor = MotorCombate()
        self.turno = 0

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

    def ejecutar_ronda(self):

        self.turno += 1

        p1 = self.equipos["Jugador 1"]
        p2 = self.equipos["Jugador 2"]

        if self.turno == 1:

            self.motor.inicio(
                self.equipos,
                p1["pokes"][0]["nombre"],
                p2["pokes"][0]["nombre"]
            )

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

            oponente = (
                "Jugador 2"
                if jug == "Jugador 1"
                else "Jugador 1"
            )

            idx_a = self.equipos[jug]["activo"]
            idx_d = self.equipos[oponente]["activo"]

            if (
                jug == "Jugador 1"
                and self.equipos[jug]["activo"] != activo_inicial_p1
            ):
                historial.append(
                    f"⏱️ {self.equipos[jug]['pokes'][idx_a]['nombre']} entró al campo y se prepara."
                )
                continue

            if (
                jug == "Jugador 2"
                and self.equipos[jug]["activo"] != activo_inicial_p2
            ):
                historial.append(
                    f"⏱️ {self.equipos[jug]['pokes'][idx_a]['nombre']} entró al campo y se prepara."
                )
                continue

            if (
                self.equipos[jug]["hp"][idx_a] > 0
                and
                self.equipos[oponente]["hp"][idx_d] > 0
            ):

                p_atk = self.equipos[jug]["pokes"][idx_a]
                p_def = self.equipos[oponente]["pokes"][idx_d]

                resultado = calcular_dano(
                    p_atk,
                    p_def
                )

                dano = resultado.dano

                self.equipos[oponente]["hp"][idx_d] -= dano

                hp_actual = max(
                    0,
                    self.equipos[oponente]["hp"][idx_d]
                )

                self.motor.ataque(

                    equipos=self.equipos,

                    turno=self.turno,

                    atacante=p_atk["nombre"],

                    defensor=p_def["nombre"],

                    movimiento=p_atk["movimiento_nombre"],

                    dano=dano,

                    hp_actual=hp_actual,

                    hp_max=self.equipos[oponente]["hp_max"][idx_d],

                    critico=resultado.critico,

                    debilitado=hp_actual <= 0

                )

                historial.append(
                    f"**{p_atk['nombre']}**: {resultado.mensaje} (Daño: {dano} HP)"
                )

                if self.equipos[oponente]["hp"][idx_d] <= 0:

                    self.equipos[oponente]["hp"][idx_d] = 0

                    if (
                        self.equipos[oponente]["activo"] + 1
                        <
                        len(self.equipos[oponente]["pokes"])
                    ):

                        self.equipos[oponente]["activo"] += 1

                        nuevo = self.equipos[oponente]["pokes"][
                            self.equipos[oponente]["activo"]
                        ]["nombre"]

                        self.motor.cambio(
                            self.equipos,

                            turno=self.turno,

                            entrenador=oponente,

                            sale=p_def["nombre"],

                            entra=nuevo

                        )

                        historial.append(
                            f"⚠️ ¡{p_def['nombre']} se debilitó! {oponente} cambia a {nuevo}."
                        )

                    else:

                        ganador = (
                            "Jugador 1"
                            if oponente == "Jugador 2"
                            else "Jugador 2"
                        )

                        self.motor.victoria(
                            self.equipos,

                            turno=self.turno,

                            ganador=ganador

                        )

                        historial.append(
                            f"💀 ¡{p_def['nombre']} se debilitó! ¡A {oponente} no le quedan más Pokémon!"
                        )
        self.motor.snapshot(
            self.equipos
        )
        return "\n".join(historial)

    def obtener_eventos(self):

        return self.motor.obtener_eventos()

    def es_fin_del_juego(self):

        vida_j1 = sum(
            self.equipos["Jugador 1"]["hp"]
        )

        vida_j2 = sum(
            self.equipos["Jugador 2"]["hp"]
        )

        if vida_j1 <= 0:
            return "Jugador 2"

        if vida_j2 <= 0:
            return "Jugador 1"

        return None

    def simular(self):

        self.motor.limpiar()

        self.turno = 0

        while not self.es_fin_del_juego():

            self.ejecutar_ronda()

        return self.motor.obtener_pasos()

    def obtener_snapshots(self):

        return self.motor.snapshots
    def obtener_pasos(self):

        return self.motor.obtener_pasos()