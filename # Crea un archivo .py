# Crea un archivo .env en la misma carpeta donde ejecutes este script
with open(".env", "w") as f:
    f.write("TOKEN=TU_TOKEN_AQUI_PEGADO")
    
print("Archivo .env creado con éxito.")