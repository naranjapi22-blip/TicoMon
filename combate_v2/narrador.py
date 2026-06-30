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

        # ===========================
        # NUEVO
        # ===========================

        if evento.tipo == "movimiento":

            nombre = evento.atacante

            self.ataques[nombre] = (
                self.ataques.get(nombre, 0) + 1
            )

            return random.choice([

                f"⚔️ {nombre} usa {evento.movimiento}.",

                f"🔥 {nombre} ataca con {evento.movimiento}.",

                f"⚡ {nombre} lanza {evento.movimiento}.",

            ])

        # ===========================
        # NUEVO
        # ===========================

        if evento.tipo == "dano":

            texto = (
                f"💥 {evento.defensor} recibe "
                f"{evento.dano} de daño."
            )

            if evento.critico:

                texto += "\n💢 ¡Golpe crítico!"

            if evento.efectivo > 1:

                texto += "\n🔥 ¡Es muy eficaz!"

            elif evento.efectivo < 1:

                texto += "\n🛡️ No es muy eficaz."

            return texto


        if evento.tipo == "ko":

            return random.choice([

                f"☠️ {evento.pokemon} cae debilitado.",

                f"💥 {evento.pokemon} ya no puede continuar.",

                f"⚠️ {evento.pokemon} queda fuera de combate.",

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