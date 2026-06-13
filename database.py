import sqlite3
import asyncio
import os
import psycopg2
from logger_config import log
import logging
import random
import records
from datetime import datetime, timezone


# 1. Asegúrate de tener esto arriba en tu archivo
NATURALEZAS = [
    "Fuerte", "Dócil", "Seria", "Rara", "Agitada", "Huraña", "Firme", "Pícara", "Audaz",
    "Osada", "Floja", "Plácida", "Modesta", "Afable", "Mansa", "Alocada", "Serena",
    "Amable", "Cauta", "Grosera", "Tímida", "Activa", "Alegre", "Ingenua", "Quietud"
]


DATABASE_URL = os.environ.get('DATABASE_URL')
db_lock = asyncio.Lock()
POKEMON_CACHE = {}
def obtener_pokemon_cache(pokemon_id):

    return POKEMON_CACHE.get(
        pokemon_id
    )
# --- Lógica de IVs (puedes poner esto en utils.py e importarlo) ---
def generar_iv_final():
    if random.random() < 0.005:  # 0.5% probabilidad de 0
        return 0
    return sum(random.randint(1, 6) for _ in range(5)) + 1


def get_connection():
    try:
        if DATABASE_URL:
            # Se conecta a Neon (PostgreSQL)
            conn = psycopg2.connect(DATABASE_URL)
            log.debug("✅ Conexión a PostgreSQL establecida")
            return conn
        else:
            # Se conecta a SQLite (Local)
            conn = sqlite3.connect('fumo_data.db')
            log.debug("✅ Conexión a SQLite establecida")
            return conn
    except Exception as e:
        log.error(f"🚨 Error al conectar a la base de datos: {e}", exc_info=True)
        raise

def init_db():
    try:
        log.info("📍 Inicializando base de datos...")
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Creamos la tabla (Usamos SERIAL para Postgres, AUTOINCREMENT para SQLite)
        if DATABASE_URL:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS capturas (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    pokemon_nombre TEXT,
                    es_shiny INTEGER DEFAULT 0,
                    pokeball TEXT DEFAULT 'Pokéball',
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            log.info("✅ Tabla 'capturas' creada/verificada en PostgreSQL")
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS capturas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    pokemon_nombre TEXT,
                    es_shiny INTEGER DEFAULT 0,
                    pokeball TEXT DEFAULT 'Pokéball',
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            log.info("✅ Tabla 'capturas' creada/verificada en SQLite")
        
        conn.commit()
        conn.close()
        init_equipo_db()
        log.info("✅ Base de datos inicializada correctamente")
        
    except Exception as e:
        log.error(f"🚨 Error al inicializar la base de datos: {e}", exc_info=True)
        raise



async def guardar_captura(user_id, pokemon_nombre, tamano_factor, es_shiny=False, pokeball='Pokéball'):
    async with db_lock:
        conn = None
        resultado = None  # Inicializamos la variable de récord
        try:
            # 1. Cálculos iniciales
            naturaleza_seleccionada = random.choice(NATURALEZAS)
            iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe = [random.randint(0, 31) for _ in range(6)]
            fecha_ahora = datetime.now(timezone.utc)
            
            # 2. Conexión
            conn = get_connection()
            cursor = conn.cursor()
            
            # 3. Inserción
            campos = "user_id, pokemon_nombre, es_shiny, pokeball, fecha, iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe, naturaleza, tamano_factor"
            valores = (
                str(user_id), 
                pokemon_nombre.lower(), 
                1 if es_shiny else 0, # es_shiny
                pokeball, 
                fecha_ahora,          # fecha
                iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe, 
                naturaleza_seleccionada, 
                tamano_factor         # <--- TIENE QUE SER EL ÚLTIMO
                )

            if DATABASE_URL:
                cursor.execute(f"INSERT INTO capturas ({campos}) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", valores)
                res = cursor.fetchone()
                id_pokemon = res[0] if res else None
            else:
                cursor.execute(f"INSERT INTO capturas ({campos}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", valores)
                id_pokemon = cursor.lastrowid
            
            # 5. VERIFICACIÓN DE RÉCORDS
            if id_pokemon:
                resultado = records.verificar_y_actualizar_record(cursor, pokemon_nombre.lower(), id_pokemon, str(user_id), tamano_factor, fecha_ahora)
                if resultado:
                    log.info(f"🏆 Récord actualizado ({resultado}) para {pokemon_nombre.capitalize()} (ID: {id_pokemon})")
            
            # 6. Confirmación
            conn.commit()
            log.info(f"✅ Captura guardada: {pokemon_nombre.capitalize()} con ID: {id_pokemon}")
            
            # ¡IMPORTANTE! Retornamos ambos valores
            return id_pokemon, resultado
            
        except Exception as e:
            if conn:
                conn.rollback()
            log.error(f"🚨 Error al guardar o verificar récord: {e}", exc_info=True)
            raise # Esto permite que el try/except en vistas.py capture el error
        finally:
            if conn:
                conn.close()
def ejecutar_consulta(query_pg, query_sql, params):
    """Auxiliar para ejecutar consultas con diferentes sintaxis"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query_pg if DATABASE_URL else query_sql, params)
        res = cursor.fetchall()
        log.debug(f"✅ Consulta ejecutada: {len(res)} resultados")
        return res
    except Exception as e:
        log.error(f"🚨 Error al ejecutar consulta: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()

def obtener_capturas(user_id, solo_shiny=False):
    try:
        log.debug(f"🔍 Obteniendo capturas para user {user_id} (Solo shiny: {solo_shiny})")
        if DATABASE_URL:
            q = "SELECT pokemon_nombre FROM capturas WHERE user_id = %s" + (" AND es_shiny = 1" if solo_shiny else "")
            res = ejecutar_consulta(q, q.replace("%s", "?"), (str(user_id),))
        else:
            q = "SELECT pokemon_nombre FROM capturas WHERE user_id = ?" + (" AND es_shiny = 1" if solo_shiny else "")
            res = ejecutar_consulta(q.replace("%s", "?"), q, (user_id,))
        
        capturas = [fila[0] for fila in res]
        log.info(f"✅ Se obtuvieron {len(capturas)} capturas para user {user_id}")
        return capturas
    except Exception as e:
        log.error(f"🚨 Error al obtener capturas: {e}", exc_info=True)
        return []

def obtener_versiones_pokemon(user_id, nombre_pokemon):
    try:
        log.debug(f"🔍 Obteniendo versiones de {nombre_pokemon} para user {user_id}")
        if DATABASE_URL:
            res = ejecutar_consulta("SELECT es_shiny FROM capturas WHERE user_id = %s AND pokemon_nombre = %s", 
                                   "SELECT es_shiny FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", 
                                   (str(user_id), nombre_pokemon.lower()))
        else:
            res = ejecutar_consulta("SELECT es_shiny FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", 
                                   "SELECT es_shiny FROM capturas WHERE user_id = ? AND pokemon_nombre = ?", 
                                   (user_id, nombre_pokemon.lower()))
        
        versiones = [fila[0] for fila in res]
        log.info(f"✅ Se obtuvieron {len(versiones)} versiones de {nombre_pokemon} para user {user_id}")
        return versiones
    except Exception as e:
        log.error(f"🚨 Error al obtener versiones de {nombre_pokemon}: {e}", exc_info=True)
        return []

def obtener_info_captura(user_id, nombre_pokemon):
    conn = None
    try:
        log.debug(f"🔍 Obteniendo info de captura: {nombre_pokemon} - User {user_id}")
        conn = get_connection()
        cursor = conn.cursor()
        
        # Agregamos la columna 'id' a la selección y usamos array_agg (Postgres) o group_concat (SQLite)
        # Si usas Postgres (DATABASE_URL), array_agg es lo ideal:
        if DATABASE_URL:
            query = """
                SELECT MIN(fecha), COUNT(*), ARRAY_AGG(id) 
                FROM capturas 
                WHERE user_id = %s AND pokemon_nombre = %s
            """
        else:
            # Si usas SQLite local, usamos group_concat:
            query = """
                SELECT MIN(fecha), COUNT(*), GROUP_CONCAT(id) 
                FROM capturas 
                WHERE user_id = ? AND pokemon_nombre = ?
            """
            
        cursor.execute(query, (str(user_id), nombre_pokemon.lower()))
        res = cursor.fetchone() # res será (fecha, cantidad, ids)
        
        # Procesamos los IDs para asegurar que siempre sea una lista
        fecha, cantidad, ids_raw = res if res else (None, 0, "")
        
        # Convertimos el string/array de IDs a una lista de números
        if ids_raw:
            if isinstance(ids_raw, str): # Caso SQLite
                lista_ids = [int(i) for i in ids_raw.split(',')]
            else: # Caso Postgres (ya es lista/array)
                lista_ids = ids_raw
        else:
            lista_ids = []

        log.info(f"✅ Info de captura obtenida: {nombre_pokemon} - Cantidad: {cantidad}")
        return fecha, cantidad, lista_ids

    except Exception as e:
        log.error(f"🚨 Error al obtener info de captura: {e}", exc_info=True)
        return None, 0, []
    finally:
        if conn:
            conn.close()

def init_energia_db():
    try:
        log.info("📍 Inicializando tabla de energía...")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS energia (
                user_id BIGINT PRIMARY KEY,
                intentos INTEGER DEFAULT 12,
                ultima_recarga TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        log.info("✅ Tabla 'energia' creada/verificada")
    except Exception as e:
        log.error(f"🚨 Error al inicializar tabla de energía: {e}", exc_info=True)
        raise

def obtener_energia_db(user_id):
    conn = None
    try:
        log.debug(f"🔍 Obteniendo energía para user {user_id}")
        conn = get_connection()
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("SELECT intentos, ultima_recarga FROM energia WHERE user_id = %s", (str(user_id),))
        else:
            cursor.execute("SELECT intentos, ultima_recarga FROM energia WHERE user_id = ?", (user_id,))
        
        res = cursor.fetchone()
        if res:
            log.info(f"✅ Energía obtenida: User {user_id} - Intentos: {res[0]}")
        else:
            log.warning(f"⚠️ No se encontró energía para user {user_id}")
        return res
    except Exception as e:
        log.error(f"🚨 Error al obtener energía: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()

async def actualizar_energia_db(bot, user_id, intentos, ultima_recarga):
    try:
        # SIEMPRE eliminamos la zona horaria antes de enviar a la BD
        if ultima_recarga.tzinfo is not None:
            ultima_recarga = ultima_recarga.replace(tzinfo=None)
        
        log.debug(f"💾 Actualizando energía: User {user_id} - Intentos: {intentos}")
        
        async with bot.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO energia (user_id, intentos, ultima_recarga) 
                VALUES ($1, $2, $3)
                ON CONFLICT(user_id) 
                DO UPDATE SET 
                    intentos = EXCLUDED.intentos, 
                    ultima_recarga = EXCLUDED.ultima_recarga
            """, str(user_id), intentos, ultima_recarga)
                                        
        log.info(f"✅ Energía actualizada: User {user_id}")
        
    except Exception as e:
        log.error(f"🚨 Error al actualizar energía: {e}", exc_info=True)
        raise

def obtener_lista_capturas(user_id):
    conn = None
    try:
        log.debug(f"🔍 Obteniendo lista de capturas únicas para user {user_id}")
        conn = get_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:
            cursor.execute("SELECT DISTINCT pokemon_nombre FROM capturas WHERE user_id = %s", (str(user_id),))
        else:
            cursor.execute("SELECT DISTINCT pokemon_nombre FROM capturas WHERE user_id = ?", (user_id,))
            
        res = [row[0] for row in cursor.fetchall()]
        log.info(f"✅ Lista de capturas obtenida: User {user_id} - {len(res)} pokémon únicos")
        return res
    except Exception as e:
        log.error(f"🚨 Error al obtener lista de capturas: {e}", exc_info=True)
        return []
    finally:
        if conn:
            conn.close()


class EquipoError(Exception):
    """Error de validación al modificar el equipo del jugador."""


def _equipo_existe(cursor) -> bool:
    if DATABASE_URL:
        cursor.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'equipo'"
        )
    else:
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='equipo'"
        )
    return cursor.fetchone() is not None


def _equipo_tiene_columna(cursor, columna: str) -> bool:
    if DATABASE_URL:
        cursor.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'equipo' AND column_name = %s
            """,
            (columna,),
        )
    else:
        cursor.execute("PRAGMA table_info(equipo)")
        return any(row[1] == columna for row in cursor.fetchall())
    return cursor.fetchone() is not None


def _crear_tabla_equipo(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipo (
            user_id BIGINT NOT NULL,
            slot INTEGER NOT NULL CHECK (slot BETWEEN 1 AND 9),
            captura_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, slot),
            UNIQUE (user_id, captura_id)
        )
    ''')


def _migrar_equipo_nombre_a_captura_id(cursor, conn):
    log.info("📍 Migrando equipo: pokemon_nombre → captura_id...")
    if DATABASE_URL:
        cursor.execute("SELECT user_id, slot, pokemon_nombre FROM equipo")
    else:
        cursor.execute("SELECT user_id, slot, pokemon_nombre FROM equipo")
    filas = cursor.fetchall()

    cursor.execute("DROP TABLE equipo")
    _crear_tabla_equipo(cursor)

    for user_id, slot, nombre in filas:
        cap = obtener_mejor_captura(user_id, nombre)
        if not cap:
            continue
        captura_id = cap[0]
        if DATABASE_URL:
            cursor.execute(
                """
                INSERT INTO equipo (user_id, slot, captura_id)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (_uid(user_id), slot, captura_id),
            )
        else:
            try:
                cursor.execute(
                    "INSERT INTO equipo (user_id, slot, captura_id) VALUES (?, ?, ?)",
                    (user_id, slot, captura_id),
                )
            except sqlite3.IntegrityError:
                pass
    conn.commit()
    log.info("✅ Migración de equipo completada")


def init_equipo_db():
    try:
        log.info("📍 Inicializando tabla de equipo...")
        conn = get_connection()
        cursor = conn.cursor()

        if not _equipo_existe(cursor):
            _crear_tabla_equipo(cursor)
        elif _equipo_tiene_columna(cursor, "pokemon_nombre") and not _equipo_tiene_columna(cursor, "captura_id"):
            _migrar_equipo_nombre_a_captura_id(cursor, conn)
        elif not _equipo_tiene_columna(cursor, "captura_id"):
            _crear_tabla_equipo(cursor)

        conn.commit()
        conn.close()
        log.info("✅ Tabla 'equipo' creada/verificada")
    except Exception as e:
        log.error(f"🚨 Error al inicializar tabla de equipo: {e}", exc_info=True)
        raise


def _uid(user_id):
    return str(user_id) if DATABASE_URL else user_id


def obtener_captura(user_id, captura_id: int):
    """Retorna (id, pokemon_nombre, es_shiny, ivs...) o None si no es del usuario."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute(
                """
                SELECT id, pokemon_nombre, es_shiny,
                       iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe
                FROM capturas
                WHERE id = %s AND user_id = %s
                """,
                (captura_id, _uid(user_id)),
            )
        else:
            cursor.execute(
                """
                SELECT id, pokemon_nombre, es_shiny,
                       iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe
                FROM capturas
                WHERE id = ? AND user_id = ?
                """,
                (captura_id, user_id),
            )
        return cursor.fetchone()
    except Exception as e:
        log.error(f"🚨 Error obtener_captura: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()


def listar_capturas_usuario(user_id, excluir_ids: set | None = None) -> list[dict]:
    """Todas las capturas del usuario, opcionalmente excluyendo IDs ya en equipo."""
    excluir_ids = excluir_ids or set()
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        iv_pct = "((iv_hp + iv_atk + iv_def + iv_spa + iv_spd + iv_spe) * 100 / 186)"
        if DATABASE_URL:
            cursor.execute(
                f"""
                SELECT id, pokemon_nombre, es_shiny, {iv_pct}
                FROM capturas
                WHERE user_id = %s
                ORDER BY id DESC
                """,
                (_uid(user_id),),
            )
        else:
            cursor.execute(
                f"""
                SELECT id, pokemon_nombre, es_shiny, {iv_pct}
                FROM capturas
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user_id,),
            )
        resultado = []
        for captura_id, nombre, es_shiny, iv_pct_val in cursor.fetchall():
            if captura_id in excluir_ids:
                continue
            resultado.append({
                "id": captura_id,
                "nombre": nombre,
                "es_shiny": bool(es_shiny),
                "iv_pct": int(iv_pct_val or 0),
            })
        return resultado
    except Exception as e:
        log.error(f"🚨 Error listar_capturas_usuario: {e}", exc_info=True)
        return []
    finally:
        if conn:
            conn.close()


def obtener_equipo(user_id) -> list:
    """Retorna 9 slots (índice 0 = slot 1). Vacío = None; lleno = captura_id."""
    slots = [None] * 9
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute(
                "SELECT slot, captura_id FROM equipo WHERE user_id = %s ORDER BY slot",
                (_uid(user_id),),
            )
        else:
            cursor.execute(
                "SELECT slot, captura_id FROM equipo WHERE user_id = ? ORDER BY slot",
                (user_id,),
            )
        for slot, captura_id in cursor.fetchall():
            if 1 <= slot <= 9:
                slots[slot - 1] = captura_id
        return slots
    except Exception as e:
        log.error(f"🚨 Error al obtener equipo: {e}", exc_info=True)
        return slots
    finally:
        if conn:
            conn.close()


def obtener_equipo_detalle(user_id) -> list:
    """9 slots con datos de captura o None."""
    slots = [None] * 9
    ids = obtener_equipo(user_id)
    for i, captura_id in enumerate(ids):
        if captura_id is None:
            continue
        cap = obtener_captura(user_id, captura_id)
        if not cap:
            continue
        slots[i] = {
            "id": cap[0],
            "nombre": cap[1],
            "es_shiny": bool(cap[2]),
        }
    return slots


def contar_equipo(user_id) -> int:
    return sum(1 for c in obtener_equipo(user_id) if c is not None)


def obtener_equipo_selector(user_id) -> dict:
    """Datos para el selector de !batalla: valores (IDs), etiquetas y mapa id→nombre."""
    detalle = [s for s in obtener_equipo_detalle(user_id) if s]
    valores = [str(s["id"]) for s in detalle]
    etiquetas = {}
    nombres = {}
    for s in detalle:
        sid = str(s["id"])
        shiny = "✨ " if s["es_shiny"] else ""
        etiquetas[sid] = f"{shiny}{s['nombre'].capitalize()} [#{s['id']}]"
        nombres[sid] = s["nombre"]
    return {"valores": valores, "etiquetas": etiquetas, "nombres": nombres}


def obtener_equipo_nombres(user_id) -> list[str]:
    """Nombres de especie del equipo guardado (para compatibilidad con combate)."""
    return [s["nombre"] for s in obtener_equipo_detalle(user_id) if s]


def nombres_desde_captura_ids(user_id, ids_seleccionados: list[str]) -> list[str]:
    # ¡Si el selector ya nos envió nombres en texto (ej: "pikachu"), los dejamos pasar tal cual!
    if ids_seleccionados and not str(ids_seleccionados[0]).isdigit():
        return ids_seleccionados
        
    # Si por alguna extraña razón llegan números, usamos el diccionario como respaldo
    detalle = obtener_equipo_detalle(user_id)
    mapa_nombres = {str(s["id"]): s["nombre"] for s in detalle if s}
    
    nombres = []
    for valor in ids_seleccionados:
        nombres.append(mapa_nombres.get(str(valor), str(valor)))
        
    return nombres

def _captura_en_equipo(user_id, captura_id: int) -> bool:
    return captura_id in [c for c in obtener_equipo(user_id) if c is not None]


def _primer_slot_libre(slots: list) -> int | None:
    for i, captura_id in enumerate(slots):
        if captura_id is None:
            return i + 1
    return None


def agregar_a_equipo(user_id, captura_id: int) -> int:
    """Añade al primer slot libre. Retorna el slot usado."""
    cap = obtener_captura(user_id, captura_id)
    if not cap:
        raise EquipoError("No tienes esa captura en tu inventario.")
    if _captura_en_equipo(user_id, captura_id):
        raise EquipoError("Esa captura ya está en tu equipo.")
    slots = obtener_equipo(user_id)
    slot = _primer_slot_libre(slots)
    if slot is None:
        raise EquipoError("Tu equipo está completo (9/9).")
    _insertar_slot(user_id, slot, captura_id)
    return slot


def reemplazar_en_equipo(user_id, slot: int, captura_id: int):
    if not 1 <= slot <= 9:
        raise EquipoError("El slot debe estar entre 1 y 9.")
    cap = obtener_captura(user_id, captura_id)
    if not cap:
        raise EquipoError("No tienes esa captura en tu inventario.")
    equipo = obtener_equipo(user_id)
    for i, actual_id in enumerate(equipo):
        if actual_id == captura_id and (i + 1) != slot:
            raise EquipoError("Esa captura ya está en otro slot del equipo.")
    _insertar_slot(user_id, slot, captura_id)


def quitar_de_equipo(user_id, slot: int):
    if not 1 <= slot <= 9:
        raise EquipoError("El slot debe estar entre 1 y 9.")
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute(
                "DELETE FROM equipo WHERE user_id = %s AND slot = %s",
                (_uid(user_id), slot),
            )
        else:
            cursor.execute(
                "DELETE FROM equipo WHERE user_id = ? AND slot = ?",
                (user_id, slot),
            )
        conn.commit()
    finally:
        if conn:
            conn.close()


def _insertar_slot(user_id, slot: int, captura_id: int):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute(
                """
                INSERT INTO equipo (user_id, slot, captura_id) VALUES (%s, %s, %s)
                ON CONFLICT (user_id, slot) DO UPDATE SET captura_id = EXCLUDED.captura_id
                """,
                (_uid(user_id), slot, captura_id),
            )
        else:
            cursor.execute("DELETE FROM equipo WHERE user_id = ? AND slot = ?", (user_id, slot))
            cursor.execute(
                "INSERT INTO equipo (user_id, slot, captura_id) VALUES (?, ?, ?)",
                (user_id, slot, captura_id),
            )
        conn.commit()
    finally:
        if conn:
            conn.close()


def listar_capturas_por_especie(user_id, nombre: str) -> list:
    """
    Todas las capturas de una especie, ordenadas por IV total descendente.
    Cada fila: (id, iv_hp..iv_spe, es_shiny).
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        iv_sum = "(iv_hp + iv_atk + iv_def + iv_spa + iv_spd + iv_spe)"
        if DATABASE_URL:
            cursor.execute(
                f"""
                SELECT id, iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe, es_shiny
                FROM capturas
                WHERE user_id = %s AND pokemon_nombre = %s
                ORDER BY {iv_sum} DESC
                """,
                (_uid(user_id), nombre.lower()),
            )
        else:
            cursor.execute(
                f"""
                SELECT id, iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe, es_shiny
                FROM capturas
                WHERE user_id = ? AND pokemon_nombre = ?
                ORDER BY {iv_sum} DESC
                """,
                (user_id, nombre.lower()),
            )
        return cursor.fetchall()
    except Exception as e:
        log.error(f"🚨 Error listar_capturas_por_especie: {e}", exc_info=True)
        return []
    finally:
        if conn:
            conn.close()


def obtener_mejor_captura(user_id, nombre: str):
    """Retorna la mejor captura por IV total o None."""
    capturas = listar_capturas_por_especie(user_id, nombre)
    return capturas[0] if capturas else None


def obtener_tipo_especial(pokemon_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if DATABASE_URL:
            cursor.execute(
                "SELECT es_legendario, es_mitico FROM pokemon_data WHERE id = %s",
                (pokemon_id,)
            )
        else:
            cursor.execute(
                "SELECT es_legendario, es_mitico FROM pokemon_data WHERE id = ?",
                (pokemon_id,)
            )

        resultado = cursor.fetchone()

        if resultado:
            es_legendario, es_mitico = resultado
            return bool(es_legendario), bool(es_mitico)

        return False, False

    except Exception as e:
        log.error(f"Error obteniendo datos especiales del Pokémon {pokemon_id}: {e}")
        return False, False

    finally:
        cursor.close()
def actualizar_capture_rate(pokemon_id, capture_rate):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        log.info(f"Actualizando Pokémon {pokemon_id} con rate {capture_rate}")

        if DATABASE_URL:
            cursor.execute(
                """
                UPDATE pokemon_data
                SET capture_rate = %s
                WHERE id = %s
                """,
                (capture_rate, pokemon_id)
            )
        else:
            cursor.execute(
                """
                UPDATE pokemon_data
                SET capture_rate = ?
                WHERE id = ?
                """,
                (capture_rate, pokemon_id)
            )

        log.info(f"Pokémon {pokemon_id} -> Filas afectadas: {cursor.rowcount}")

        conn.commit()

    except Exception as e:
        log.error(f"Error actualizando capture_rate de {pokemon_id}: {e}")

    finally:
        cursor.close()
        conn.close()
def obtener_ids_sin_capture_rate():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM pokemon_data
            WHERE capture_rate IS NULL
            """
        )

        return [fila[0] for fila in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()
def obtener_datos_rareza():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, capture_rate, es_legendario, es_mitico
            FROM pokemon_data
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()
def guardar_canal_rankings(guild_id, canal_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO configuracion_servidor
        (guild_id, canal_rankings)
        VALUES (%s, %s)
        ON CONFLICT (guild_id)
        DO UPDATE SET
        canal_rankings = EXCLUDED.canal_rankings
    """, (guild_id, canal_id))

    conn.commit()
    cur.close()
    conn.close()
def obtener_canal_rankings(guild_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT canal_rankings
        FROM configuracion_servidor
        WHERE guild_id = %s
    """, (guild_id,))

    resultado = cur.fetchone()

    cur.close()
    conn.close()

    if resultado:
        return resultado[0]

    return None
def obtener_pokemon_local(pokemon_id):

    pokemon = POKEMON_CACHE.get(
        pokemon_id
    )

    if pokemon:

        return pokemon

    conn = get_connection()
    cursor = conn.cursor()

    try:

        if DATABASE_URL:

            cursor.execute(
                """
                SELECT
                    id,
                    nombre,
                    tipos,
                    capture_rate,
                    es_legendario,
                    es_mitico
                FROM pokemon_data
                WHERE id = %s
                """,
                (pokemon_id,)
            )

        else:

            cursor.execute(
                """
                SELECT
                    id,
                    nombre,
                    tipos,
                    capture_rate,
                    es_legendario,
                    es_mitico
                FROM pokemon_data
                WHERE id = ?
                """,
                (pokemon_id,)
            )

        fila = cursor.fetchone()

        if not fila:
            return None

        pokemon = {
            "id": fila[0],
            "nombre": fila[1],
            "tipos": fila[2],
            "capture_rate": fila[3],
            "es_legendario": fila[4],
            "es_mitico": fila[5]
        }
        return pokemon

    finally:
        cursor.close()
        conn.close()
def obtener_pokemon_local_nombre(nombre):
    conn = get_connection()
    cursor = conn.cursor()

    try:

        if DATABASE_URL:
            cursor.execute(
                """
                SELECT
                    id,
                    nombre,
                    tipos,
                    capture_rate,
                    es_legendario,
                    es_mitico
                FROM pokemon_data
                WHERE LOWER(nombre) = LOWER(%s)
                """,
                (nombre,)
            )
        else:
            cursor.execute(
                """
                SELECT
                    id,
                    nombre,
                    tipos,
                    capture_rate,
                    es_legendario,
                    es_mitico
                FROM pokemon_data
                WHERE LOWER(nombre) = LOWER(?)
                """,
                (nombre,)
            )

        fila = cursor.fetchone()

        if not fila:
            return None

        return {
            "id": fila[0],
            "nombre": fila[1],
            "tipos": fila[2],
            "capture_rate": fila[3],
            "es_legendario": fila[4],
            "es_mitico": fila[5]
        }

    finally:
        cursor.close()
        conn.close()
def obtener_id_pokemon(nombre):
    pokemon = obtener_pokemon_local_nombre(
        nombre
    )

    if not pokemon:
        return None

    return pokemon["id"]
def cargar_cache_pokemon():

    global POKEMON_CACHE

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                nombre,
                tipos,
                capture_rate,
                es_legendario,
                es_mitico
            FROM pokemon_data
        """)

        filas = cursor.fetchall()

        POKEMON_CACHE.clear()

        for fila in filas:

            POKEMON_CACHE[fila[0]] = {
                "id": fila[0],
                "nombre": fila[1],
                "tipos": fila[2],
                "capture_rate": fila[3],
                "es_legendario": fila[4],
                "es_mitico": fila[5]
            }

        log.info(
            f"✅ Cache Pokémon cargada: "
            f"{len(POKEMON_CACHE)} registros"
        )

    finally:

        cursor.close()
        conn.close()
