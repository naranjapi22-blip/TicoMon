from pathlib import Path
from PIL import Image, ImageSequence

# ==========================================
# CONFIGURACIÓN
# ==========================================

ORIGEN = Path("gifs/regular")
DESTINO = Path("gifs_reajustados_bbox/regular")

DESTINO.mkdir(parents=True, exist_ok=True)

MARGEN = 20

# ==========================================
# BUSCAR EL SPRITE MÁS GRANDE (NO EL CANVAS)
# ==========================================

max_sprite_w = 0
max_sprite_h = 0

for archivo in ORIGEN.glob("*.gif"):

    try:

        with Image.open(archivo) as gif:

            for frame in ImageSequence.Iterator(gif):

                frame = frame.convert("RGBA")

                bbox = frame.getbbox()

                if bbox is None:
                    continue

                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]

                max_sprite_w = max(max_sprite_w, w)
                max_sprite_h = max(max_sprite_h, h)

    except Exception as e:

        print(f"Error leyendo {archivo.name}: {e}")

canvas_w = max_sprite_w + MARGEN * 2
canvas_h = max_sprite_h + MARGEN * 2

print("=" * 50)
print("Canvas final:", canvas_w, "x", canvas_h)
print("=" * 50)

# ==========================================
# REGENERAR GIFS
# ==========================================

procesados = 0

for archivo in ORIGEN.glob("*.gif"):

    try:

        with Image.open(archivo) as gif:

            frames = []
            durations = []

            for frame in ImageSequence.Iterator(gif):

                frame = frame.convert("RGBA")

                bbox = frame.getbbox()

                if bbox is None:

                    sprite = Image.new("RGBA", (1, 1), (0, 0, 0, 0))

                else:

                    sprite = frame.crop(bbox)

                canvas = Image.new(
                    "RGBA",
                    (canvas_w, canvas_h),
                    (0, 0, 0, 0)
                )

                x = (canvas_w - sprite.width) // 2
                y = (canvas_h - sprite.height) // 2

                canvas.alpha_composite(sprite, (x, y))

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
print(f"✅ {procesados} GIFs procesados.")
print(f"📁 Salida: {DESTINO}")