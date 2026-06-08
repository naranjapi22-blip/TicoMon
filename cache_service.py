import asyncpg
import os
import logging

class PokedexCache:
    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.pool = None
        self.logger = logging.getLogger("PokedexCache")

    async def _get_pool(self):
        """Devuelve el pool existente o crea uno nuevo si no existe."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.DATABASE_URL, min_size=1, max_size=10)
        return self.pool

    async def inicializar_bd(self):
        """Crea la tabla y los índices necesarios."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS pokemon_data (
                            id INTEGER PRIMARY KEY,
                            nombre TEXT NOT NULL UNIQUE,
                            tipos TEXT NOT NULL,
                            es_legendario BOOLEAN DEFAULT FALSE,
                            es_mitico BOOLEAN DEFAULT FALSE
                        )
                    """)
                    await conn.execute("CREATE INDEX IF NOT EXISTS idx_tipos ON pokemon_data(tipos)")
                    await conn.execute("CREATE INDEX IF NOT EXISTS idx_nombre ON pokemon_data(nombre)")
            print("✅ Estructura de tabla verificada en Neon.")
        except Exception as e:
            print(f"❌ Error crítico al inicializar BD: {e}")

    async def guardar_pokemon(self, id_p, nombre, tipos, es_legendario, es_mitico):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO pokemon_data (id, nombre, tipos, es_legendario, es_mitico)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO UPDATE SET 
                nombre = $2, tipos = $3, es_legendario = $4, es_mitico = $5
            """, id_p, nombre.lower(), ",".join(tipos), es_legendario, es_mitico)

    async def obtener_id_pokedex_por_nombre(self, nombre):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval("SELECT id FROM pokemon_data WHERE nombre = $1", nombre.lower())

    async def obtener_ids_por_filtro(self, filtro_tipo=None, legendarios=False):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            query = "SELECT id FROM pokemon_data WHERE 1=1"
            args = []
            if legendarios:
                query += " AND (es_legendario IS TRUE OR es_mitico IS TRUE)"
            if filtro_tipo:
                query += " AND tipos LIKE $1"
                args.append(f"%{filtro_tipo.lower()}%")
            
            rows = await conn.fetch(query, *args)
            return {row['id'] for row in rows}

    async def cerrar_pool(self):
        """Se llama cuando el bot se apaga."""
        if self.pool:
            await self.pool.close()

db_cache = PokedexCache()
async def obtener_ids_por_nombres(self, nombres_lista):
    """Obtiene todos los IDs en una sola consulta masiva."""
    if not nombres_lista:
        return {}
        
    pool = await self._get_pool()
    nombres_limpios = [n.lower() for n in nombres_capturados] # Opcional si ya están limpios
    
    async with pool.acquire() as conn:
        # Consulta masiva: es infinitamente más rápida que hacer un for
        rows = await conn.fetch("SELECT nombre, id FROM pokemon_data WHERE nombre = ANY($1)", nombres_lista)
        return {row['nombre']: row['id'] for row in rows}