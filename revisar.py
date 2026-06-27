from pathlib import Path
from PIL import Image, ImageSequence

# ==========================================
# CONFIGURACIÓN
# ==========================================

ORIGEN = Path("gifs/regular")
DESTINO = Path("gifs_reajustados/regular")

DESTINO.mkdir(parents=True, exist_ok=True)

# Margen alrededor del Pokémon
MARGEN = 20

# ==========================================
# BUSCAR EL GIF MÁS GRANDE
# ==========================================

max_w = 0
max_h = 0

for archivo in ORIGEN.glob("*.gif"):
    try:
        with Image.open(archivo) as gif:
            max_w = max(max_w, gif.width)
            max_h = max(max_h, gif.height)
    except Exception as e:
        print(f"Error leyendo {archivo.name}: {e}")

canvas_w = max_w + MARGEN * 2
canvas_h = max_h + MARGEN * 2

print("=" * 50)
print("Canvas final:", canvas_w, "x", canvas_h)
print("=" * 50)

# ==========================================
# REGENERAR LOS GIFS
# ==========================================

procesados = 0

for archivo in ORIGEN.glob("*.gif"):
    try:
        with Image.open(archivo) as gif:

            frames = []
            durations = []

            for frame in ImageSequence.Iterator(gif):

                frame = frame.convert("RGBA")

                canvas = Image.new(
                    "RGBA",
                    (canvas_w, canvas_h),
                    (0, 0, 0, 0)
                )

                x = (canvas_w - frame.width) // 2
                y = (canvas_h - frame.height) // 2

                canvas.alpha_composite(frame, (x, y))

                frames.append(canvas)

                durations.append(
                    frame.info.get(
                        "duration",
                        gif.info.get("duration", 100)
                    )
                )

            frames[0].save(
                DESTINO / archivo.name,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=gif.info.get("loop", 0),
                disposal=2,
                optimize=False
            )

            procesados += 1

    except Exception as e:
        print(f"Error procesando {archivo.name}: {e}")

print()
print(f"✅ {procesados} GIFs reajustados correctamente.")
print(f"📁 Carpeta de salida: {DESTINO}")