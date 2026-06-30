class DirectorCombate:

    def analizar(
        self,
        eventos,
        snapshots,
    ):

        timeline = []

        for evento in eventos:

            indice = max(0, evento.turno - 1)

            estado = snapshots[indice]

            pausa = self._pausa_evento(evento)

            timeline.append({

                "evento": evento,

                "estado": estado,

                "pausa": pausa,

            })

        return timeline

    def _pausa_evento(
        self,
        evento,
    ):

        if evento.tipo == "inicio":
            return 2.5

        if evento.tipo == "victoria":
            return 4.0

        if evento.tipo == "cambio":
            return 2.5

        if evento.tipo == "ataque":
            return 2.0

        if getattr(evento, "debilitado", False):
            return 3.0

        if getattr(evento, "critico", False):
            return 2.5

        return 1.8