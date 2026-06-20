"""Mapeo de naturalezas en español (DB) a identificadores Showdown (inglés)."""

from ivs_commands import NATURALEZAS

_ES_A_POKE_ENV = {
    "atq": "atk",
    "def": "def",
    "esp_atq": "spa",
    "esp_def": "spd",
    "vel": "spe",
}


def naturaleza_a_showdown(naturaleza_es: str | None, gen_natures: dict) -> str:
    """Convierte naturaleza almacenada en español al id de poke-env."""
    nat = NATURALEZAS.get((naturaleza_es or "Fuerte").capitalize(), NATURALEZAS["Fuerte"])
    objetivo = {_ES_A_POKE_ENV[k]: v for k, v in nat.items()}

    for nombre, mults in gen_natures.items():
        if all(abs(mults[stat] - objetivo[stat]) < 0.001 for stat in objetivo):
            return nombre
    return "hardy"
