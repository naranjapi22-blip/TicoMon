from animaciones.animacion_captura import CaptureAnimation


anim = CaptureAnimation(

    sprite_path="sprites/regular/3.png",

    pokemon_name="Pikachu",

    capturado=True

)

anim.render()

anim.save_gif("captura.gif")

print("==========================================")
print(" Capture Animation - Test 01")
print("==========================================")
print("Resultado : OK")
print("GIF : captura.gif")
print("==========================================")