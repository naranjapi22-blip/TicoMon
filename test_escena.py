from PIL import Image, ImageSequence

# ======================================
# Configuración
# ======================================

BACKGROUND = "battle_bg.png"

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 360

MAX_POKEMON_SIZE = 120

FRAME_DURATION = 120

POKEMON = [

    # Equipo del jugador (espalda)

    ("gifs/back/6.gif",   40, 180),    # Charizard
    ("gifs/back/25.gif", 180, 230),    # Pikachu
    ("gifs/back/448.gif",320, 200),    # Lucario

    # Rival (frente)

    ("gifs/regular/3.gif", 470, 40),   # Venusaur
]

# ======================================
# Fondo
# ======================================

background = Image.open(BACKGROUND).convert("RGBA")
background = background.resize(
    (CANVAS_WIDTH, CANVAS_HEIGHT),
    Image.Resampling.LANCZOS
)

# ======================================
# Cargar GIF
# ======================================

sprites = []

for ruta, x, y in POKEMON:

    gif = Image.open(ruta)

    frames = []

    for i, frame in enumerate(ImageSequence.Iterator(gif)):

        # Solo usar la mitad de los frames
        if i % 2:
            continue

        frame = frame.convert("RGBA")

        escala = min(
            MAX_POKEMON_SIZE / frame.width,
            MAX_POKEMON_SIZE / frame.height,
            1
        )

        w = int(frame.width * escala)
        h = int(frame.height * escala)

        frame = frame.resize(
            (w, h),
            Image.Resampling.LANCZOS
        )

        frames.append(frame)

    sprites.append({
        "frames": frames,
        "x": x,
        "y": y
    })

# ======================================
# Total de frames
# ======================================

total_frames = max(
    len(s["frames"])
    for s in sprites
)

# ======================================
# Render
# ======================================

resultado = []

for i in range(total_frames):

    escena = background.copy()

    for sprite in sprites:

        frame = sprite["frames"][
            i % len(sprite["frames"])
        ]

        escena.paste(
            frame,
            (sprite["x"], sprite["y"]),
            frame
        )

    resultado.append(
        escena.convert(
            "P",
            palette=Image.Palette.ADAPTIVE
        )
    )

# ======================================
# Guardar
# ======================================

resultado[0].save(
    "escena.gif",
    save_all=True,
    append_images=resultado[1:],
    duration=FRAME_DURATION,
    loop=0,
    optimize=True,
    disposal=2
)

print("Escena creada.")