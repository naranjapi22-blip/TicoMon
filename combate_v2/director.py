class DirectorCombate:

    def analizar(
    self,
    eventos,
    snapshots,
    ):

        escenas = []

        escena_actual = []

        turno_actual = None

        for evento in eventos:

            if turno_actual is None:
                turno_actual = evento.turno

            if evento.turno != turno_actual:

                escenas.append(
                    self._crear_escena(
                        turno_actual,
                        escena_actual,
                        snapshots[turno_actual - 1]
                    )
                )
                escena_actual = []

                turno_actual = evento.turno

            escena_actual.append(evento)

        if escena_actual:

            escenas.append(
                self._crear_escena(
                    turno_actual,
                    escena_actual,
                    snapshots[turno_actual - 1]
                )
            )

        return escenas

    def _crear_escena(
        self,
        turno,
        eventos,
        estado,
    ):

        pausa = 1.5

        for e in eventos:

            if e.tipo == "victoria":
                pausa = 3.0

            elif e.tipo == "cambio":
                pausa = 2.6

            elif getattr(e, "debilitado", False):
                pausa = 2.5

            elif getattr(e, "critico", False):
                pausa = 2.0

        return {

            "turno": turno,

            "eventos": eventos,

            "estado": estado,

            "pausa": pausa,

        }