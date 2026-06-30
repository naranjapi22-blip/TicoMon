import random


class NarradorCombate:

    def __init__(self):

        self.ataques = {}
        self.ko = {}

    def narrar(self, escena):

        lineas = []

        for evento in escena["eventos"]:

            texto = self._narrar_evento(evento)

            if texto:
                lineas.append(texto)

        return "\n".join(lineas)

    def _narrar_evento(self, evento):

        if evento.tipo == "inicio":

            self.ataques.clear()
            self.ko.clear()

            return random.choice([

                f"⚔️ ¡Comienza el combate entre {evento.pokemon1} y {evento.pokemon2}!",

                f"⚔️ {evento.pokemon1} y {evento.pokemon2} están listos para luchar.",

                f"⚔️ ¡Empieza una nueva batalla!",

            ])

        if evento.tipo == "ataque":

            nombre = evento.atacante

            self.ataques[nombre] = (
                self.ataques.get(nombre, 0) + 1
            )

            veces = self.ataques[nombre]

            if evento.debilitado:

                self.ko[nombre] = (
                    self.ko.get(nombre, 0) + 1
                )

                if self.ko[nombre] >= 2:

                    return (
                        f"👑 {nombre} sigue imparable y derrota a {evento.defensor}."
                    )

                return random.choice([

                    f"☠️ {evento.defensor} cae debilitado.",

                    f"💥 {evento.defensor} no puede continuar.",

                    f"⚠️ {evento.defensor} queda fuera de combate.",

                ])

            if evento.critico:

                return random.choice([

                    f"💥 ¡Golpe crítico de {nombre}!",

                    f"💥 {nombre} conecta un ataque devastador.",

                    f"🔥 ¡{nombre} encuentra un punto débil!",

                ])

            if veces >= 4:

                return random.choice([

                    f"🔥 {nombre} mantiene la presión.",

                    f"⚔️ {nombre} domina completamente este duelo.",

                    f"⚡ {nombre} sigue atacando sin descanso.",

                ])

            return random.choice([

                f"⚔️ {nombre} usa {evento.movimiento}.",

                f"🔥 {nombre} ataca con {evento.movimiento}.",

                f"⚡ {nombre} lanza {evento.movimiento}.",

            ])

        if evento.tipo == "cambio":

            return random.choice([

                f"➡️ {evento.entra} entra al combate.",

                f"🔄 {evento.sale} regresa y aparece {evento.entra}.",

                f"⚡ Es el turno de {evento.entra}.",

            ])

        if evento.tipo == "victoria":

            return random.choice([

                f"🏆 ¡{evento.ganador} gana el combate!",

                f"🎉 Victoria para {evento.ganador}.",

                f"✨ {evento.ganador} se lleva la batalla.",

            ])

        return ""