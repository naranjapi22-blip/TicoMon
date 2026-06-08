import asyncpg
import os

class PokedexCache:
    def __init__(self):
        # Neon te da esta URL en su dashboard
        self.DATABASE_URL = os.getenv("DATABASE_URL")

    async def _get_pool(self):
        return await asyncpg.create_pool(self.DATABASE_URL)

    async def inicializar_bd(self):
        """Crea la tabla en tu base de datos de Neon."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
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
        await pool.close()

    async def guardar_pokemon(self, id_p, nombre, tipos, es_legendario, es_mitico):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO pokemon_data (id, nombre, tipos, es_legendario, es_mitico)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO UPDATE SET 
                nombre = $2, tipos = $3, es_legendario = $4, es_mitico = $5
            """, id_p, nombre.lower(), ",".join(tipos), es_legendario, es_mitico)
        await pool.close()

    async def obtener_id_pokedex_por_nombre(self, nombre):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT id FROM pokemon_data WHERE nombre = $1", nombre.lower())
            return result
        await pool.close()

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
        await pool.close()

db_cache = PokedexCache()