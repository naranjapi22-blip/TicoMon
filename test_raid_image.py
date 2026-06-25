from animaciones.animations.raid import RaidAnimation
from PIL import Image

# =====================================
# BACKGROUND (el que subiste)
# =====================================

background = Image.open("assets/backgrounds/raid_background.png")

alpha_sprite = Image.open("assets/pokemon/alpha/boss.png")

player_sprites = [
    Image.open("assets/pokemon/players/p1.png"),
    Image.open("assets/pokemon/players/p2.png"),
    Image.open("assets/pokemon/players/p3.png"),
]

# =====================================
# RAID
# =====================================

raid = RaidAnimation(
    background=background,
    alpha_sprite=alpha_sprite,
    player_sprites=player_sprites,
)

# IMPORTANTE: nuevo sistema
raid.build()

# =====================================
# EXPORT IMAGE FINAL
# =====================================

image = raid.export_image()

# =====================================
# GUARDAR RESULTADO
# =====================================

image.save("raid_output.png")

print("✅ Imagen generada: raid_output.png")
print("=== SYSTEM DEBUG ===")
print("Renderer:", raid.renderer.width, raid.renderer.height)
print("Scene actors:", len(raid.scene.actors))
print("Background size:", raid.background.size)
print("Players:", len(raid.player_sprites))
focus = raid.layout.get_focus_point()
print("FOCUS POINT:", focus)