import asyncio
import asyncpg
import random

# Reemplaza con tu URL de Neon
DATABASE_URL = "postgresql://neondb_owner:npg_nEgy43dlkmUq@ep-withered-brook-aq3njbjm-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

async def asignar_tamano_a_existentes():
    conn = await asyncpg.connect(DATABASE_URL)
    
    # 1. Seleccionamos todos los registros que aún no tienen tamaño
    # (O todos, si prefieres sobreescribirlos todos)
    capturas = await conn.fetch("SELECT id FROM CAPTURAS")
    
    print(f"🔄 Asignando tamaños a {len(capturas)} Pokémon existentes...")

    async with conn.transaction():
        for cap in capturas:
            # Generamos el factor aleatorio igual que en la función de guardado
            nuevo_tamano = round(random.uniform(0.50, 1.50), 2)
            
            # Actualizamos cada registro
            await conn.execute("UPDATE CAPTURAS SET tamano_factor = $1 WHERE id = $2", 
                               nuevo_tamano, cap['id'])
    
    print("✅ ¡Listo! Todos tus Pokémon antiguos ya tienen un tamaño definido.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(asignar_tamano_a_existentes())