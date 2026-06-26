from combate_calc import (
    calcular_dano,
    elegir_movimiento_alpha
)

import random


class CombateRaidSim:

    def __init__(self, jugadores, alpha):

        self.jugadores = jugadores

        self.hp_jugadores = [
            p["hp_max"]
            for p in jugadores
        ]

        self.alpha = alpha[0]

        self.hp_alpha = self.alpha["hp_max"]
        self.hp_alpha_max = self.alpha["hp_max"]

    def es_fin_del_juego(self):

        if self.hp_alpha <= 0:
            return "Jugadores"

        if all(hp <= 0 for hp in self.hp_jugadores):
            return "Alpha"

        return None

    def jugadores_vivos(self):

        return [
            i
            for i, hp in enumerate(self.hp_jugadores)
            if hp > 0
        ]

    def calcular_resultado_ataque(
        self,
        atacante,
        defensor
    ):

        resultado = calcular_dano(
            atacante,
            defensor
        )

        return (
            resultado.dano,
            resultado.mensaje
        )

    def ejecutar_ronda(self):

        historial = []

        # Turno de los jugadores
        for i in self.jugadores_vivos():

            atacante = self.jugadores[i]

            dano, log = self.calcular_resultado_ataque(
                atacante,
                self.alpha
            )

            dano = int(
                dano *
                self.alpha.get(
                    "defense_multiplier",
                    1.0
                )
            )

            self.hp_alpha -= dano

            if self.hp_alpha < 0:
                self.hp_alpha = 0

            historial.append(log)

            if self.hp_alpha <= 0:
                break

        vivos = self.jugadores_vivos()

        # Turno del Alpha
        if vivos and self.hp_alpha > 0:

            movimiento, movimiento_nombre = (
                elegir_movimiento_alpha(
                    self.alpha["species_showdown"],
                    {
                        "atk": self.alpha["atk"],
                        "spa": self.alpha["atk_esp"]
                    }
                )
            )

            self.alpha["movimiento"] = movimiento
            self.alpha["movimiento_nombre"] = movimiento_nombre

            objetivo = random.choice(vivos)

            dano, log = self.calcular_resultado_ataque(
                self.alpha,
                self.jugadores[objetivo]
            )

            dano = int(
                dano *
                self.alpha.get(
                    "damage_multiplier",
                    1.0
                )
            )

            self.hp_jugadores[objetivo] -= dano

            if self.hp_jugadores[objetivo] < 0:
                self.hp_jugadores[objetivo] = 0

            historial.append(log)

            if self.hp_jugadores[objetivo] == 0:

                historial.append(
                    f"💀 {self.jugadores[objetivo]['nombre']} se debilitó"
                )

        return historial