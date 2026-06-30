import random


class NarradorCombate:

    def __init__(self):

        self.ataques = {}
        self.ko = {}

    def narrar_evento(self, evento):

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

            texto = random.choice([

                f"⚔️ {nombre} usa {evento.movimiento}.",

                f"🔥 {nombre} ataca con {evento.movimiento}.",

                f"⚡ {nombre} lanza {evento.movimiento}.",

            ])

            if evento.dano > 0:

                texto += (
                    f"\n💥 {evento.defensor} recibe "
                    f"{evento.dano} de daño."
                )

            if evento.critico:

                texto += "\n💢 ¡Golpe crítico!"

            if getattr(evento, "efectividad", 1) > 1:

                texto += "\n🔥 ¡Es muy eficaz!"

            elif getattr(evento, "efectividad", 1) < 1:

                texto += "\n🛡️ No es muy eficaz."

            if evento.debilitado:

                self.ko[nombre] = (
                    self.ko.get(nombre, 0) + 1
                )

                texto += (
                    f"\n☠️ {evento.defensor} cae debilitado."
                )

            elif veces >= 4:

                texto += random.choice([

                    "\n⚔️ Mantiene la presión.",

                    "\n🔥 Domina completamente el combate.",

                    "\n⚡ No da respiro al rival.",

                ])

            return texto

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