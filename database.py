import sqlite3
import asyncio
import os
import psycopg2
from logger_config import log
import logging
import random
import records
from datetime import datetime, timezone
from candy import add_candy_for_pokemon
pokemon_por_id = {}
id_por_nombre = {}
# =====================================================
# NOTA DE AUDITORÍA (Junio 2026)
#
# La migración SQLite -> PostgreSQL fue completada.
#
# Las funciones:
#   _equipo_existe()
#   _equipo_tiene_columna()
#   _migrar_equipo_nombre_a_captura_id()
#
# permanecen únicamente por compatibilidad histórica.
#
# Revisar su eliminación cuando ya no existan bases de
# datos antiguas que requieran migración.
# =====================================================
# 1. Asegúrate de tener esto arriba en tu archivo
NATURALEZAS = [
    "Fuerte", "Dócil", "Seria", "Rara", "Agitada", "Huraña", "Firme", "Pícara", "Audaz",
    "Osada", "Floja", "Plácida", "Modesta", "Afable", "Mansa", "Alocada", "Serena",
    "Amable", "Cauta", "Grosera", "Tímida", "Activa", "Alegre", "Ingenua", "Quietud"
]


DATABASE_URL = os.environ.get('DATABASE_URL')
db_lock = asyncio.Lock()
POKEMON_CACHE = {}
POKEMON_CACHE_NOMBRE = {}
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
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        log.error(f"🚨 Error al conectar a la base de datos: {e}", exc_info=True)
        raise
def init_db():
    try:
        log.info("📍 Inicializando base de datos...")
        conn = get_connection()
        cursor = conn.cursor()

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

        log.info("✅ Tabla 'capturas' creada/verificada")

        conn.commit()
        conn.close()

        init_equipo_db()

        log.info("✅ Base de datos inicializada correctamente")

    except Exception as e:
        log.error(
            f"🚨 Error al inicializar la base de datos: {e}",
            exc_info=True
        )
        raise


async def guardar_captura(
    user_id,
    pokemon_nombre,
    tamano_factor,
    es_shiny=False,
    pokeball='Pokéball'
):
    async with db_lock:

        conn = None
        resultado = None

        try:

            # 1. Cálculos iniciales
            naturaleza_seleccionada = random.choice(
                NATURALEZAS
            )

            iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe = [
                random.randint(0, 31)
                for _ in range(6)
            ]

            fecha_ahora = datetime.now(
                timezone.utc
            )

            # 2. Conexión
            conn = get_connection()
            cursor = conn.cursor()

            # 3. Inserción
            campos = (
                "user_id, pokemon_nombre, es_shiny, "
                "pokeball, fecha, iv_hp, iv_atk, iv_def, "
                "iv_spa, iv_spd, iv_spe, naturaleza, "
                "tamano_factor"
            )

            valores = (
                str(user_id),
                pokemon_nombre.lower(),
                1 if es_shiny else 0,
                pokeball,
                fecha_ahora,
                iv_hp,
                iv_atk,
                iv_def,
                iv_spa,
                iv_spd,
                iv_spe,
                naturaleza_seleccionada,
                tamano_factor
            )

            cursor.execute(
                f"""
                INSERT INTO capturas ({campos})
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                RETURNING id
                """,
                valores
            )

            res = cursor.fetchone()
            id_pokemon = res[0] if res else None

            # 4. Verificación de récords
            if id_pokemon:

                resultado = (
                    records.verificar_y_actualizar_record(
                        cursor,
                        pokemon_nombre.lower(),
                        id_pokemon,
                        str(user_id),
                        tamano_factor,
                        fecha_ahora
                    )
                )

                if resultado:

                    log.info(
                        f"🏆 Récord actualizado "
                        f"({resultado}) para "
                        f"{pokemon_nombre.capitalize()} "
                        f"(ID: {id_pokemon})"
                    )

            # 5. Confirmación
            conn.commit()

            add_candy_for_pokemon(
                user_id,
                pokemon_nombre,
                1
            )

            log.info(
                f"✅ Captura guardada: "
                f"{pokemon_nombre.capitalize()} "
                f"con ID: {id_pokemon}"
            )

            return id_pokemon, resultado

        except Exception as e:

            if conn:
                conn.rollback()

            log.error(
                f"🚨 Error al guardar o verificar récord: {e}",
                exc_info=True
            )

            raise

        finally:

            if conn:
                conn.close()
def ejecutar_consulta(query, params):
    """Auxiliar para ejecutar consultas"""
    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(query, params)

        res = cursor.fetchall()

        log.debug(
            f"✅ Consulta ejecutada: {len(res)} resultados"
        )

        return res

    except Exception as e:

        log.error(
            f"🚨 Error al ejecutar consulta: {e}",
            exc_info=True
        )

        raise

    finally:

        if conn:
            conn.close()

def obtener_capturas(user_id, solo_shiny=False):

    try:

        log.debug(
            f"🔍 Obteniendo capturas para user {user_id} "
            f"(Solo shiny: {solo_shiny})"
        )

        q = (
            "SELECT pokemon_nombre "
            "FROM capturas "
            "WHERE user_id = %s"
            + (
                " AND es_shiny = 1"
                if solo_shiny
                else ""
            )
        )

        res = ejecutar_consulta(
            q,
            (str(user_id),)
        )

        capturas = [fila[0] for fila in res]

        log.info(
            f"✅ Se obtuvieron {len(capturas)} "
            f"capturas para user {user_id}"
        )

        return capturas

    except Exception as e:

        log.error(
            f"🚨 Error al obtener capturas: {e}",
            exc_info=True
        )

        return []

def obtener_versiones_pokemon(
    user_id,
    nombre_pokemon
):

    try:

        log.debug(
            f"🔍 Obteniendo versiones de "
            f"{nombre_pokemon} "
            f"para user {user_id}"
        )

        res = ejecutar_consulta(
            """
            SELECT es_shiny
            FROM capturas
            WHERE user_id = %s
            AND pokemon_nombre = %s
            """,
            (
                str(user_id),
                nombre_pokemon.lower()
            )
        )

        versiones = [
            fila[0]
            for fila in res
        ]

        log.info(
            f"✅ Se obtuvieron "
            f"{len(versiones)} versiones "
            f"de {nombre_pokemon}"
        )

        return versiones

    except Exception as e:

        log.error(
            f"🚨 Error al obtener versiones "
            f"de {nombre_pokemon}: {e}",
            exc_info=True
        )

        return []

def obtener_info_captura(user_id, nombre_pokemon):
    conn = None
    try:
        log.debug(
            f"🔍 Obteniendo info de captura: "
            f"{nombre_pokemon} - User {user_id}"
        )

        conn = get_connection()
        cursor = conn.cursor()
        nombre = nombre_pokemon.lower()
        uid = _uid(user_id)

        cursor.execute(
            """
            SELECT MIN(fecha), COUNT(*)
            FROM capturas
            WHERE user_id = %s
            AND pokemon_nombre = %s
            """,
            (uid, nombre),
        )

        res = cursor.fetchone()
        fecha, cantidad = res if res else (None, 0)

        cursor.execute(
            """
            SELECT id, es_shiny
            FROM capturas
            WHERE user_id = %s
            AND pokemon_nombre = %s
            ORDER BY id
            """,
            (uid, nombre),
        )
        filas_capturas = cursor.fetchall()

        cursor.execute(
            """
            SELECT id_pokemon_grande, id_pokemon_pequeno
            FROM RECORDS_ESPECIE
            WHERE pokemon_nombre = %s
            """,
            (nombre,),
        )
        record_row = cursor.fetchone()
        ids_record = set()
        if record_row:
            if record_row[0] is not None:
                ids_record.add(int(record_row[0]))
            if record_row[1] is not None:
                ids_record.add(int(record_row[1]))

        capturas = [
            {
                "id": int(fila[0]),
                "es_shiny": bool(fila[1]),
                "tiene_record": int(fila[0]) in ids_record,
            }
            for fila in filas_capturas
        ]

        log.info(
            f"✅ Info de captura obtenida: "
            f"{nombre_pokemon} - Cantidad: {cantidad}"
        )

        return fecha, cantidad, capturas

    except Exception as e:
        log.error(
            f"🚨 Error al obtener info de captura: {e}",
            exc_info=True
        )
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
        cursor.execute(
            "SELECT intentos, ultima_recarga FROM energia WHERE user_id = %s",
            (str(user_id),)
        )
        
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
        
        cursor.execute(
            "SELECT DISTINCT pokemon_nombre FROM capturas WHERE user_id = %s",
            (str(user_id),)
)
            
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
    """
    LEGADO (Junio 2026)

    Utilizado para detectar estructuras antiguas de la tabla
    'equipo' durante la migración de pokemon_nombre -> captura_id.

    Actualmente solo es llamado por init_equipo_db().

    Si la migración histórica deja de ser necesaria esta función
    podrá eliminarse junto con _migrar_equipo_nombre_a_captura_id().
    """
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
    """
    MIGRACIÓN HISTÓRICA (Junio 2026)

    Convierte equipos antiguos que almacenaban:

        pokemon_nombre

    al formato actual:

        captura_id

    La tabla actual en producción ya utiliza captura_id.

    Mantener únicamente por compatibilidad con bases de datos
    antiguas que aún no hayan ejecutado esta migración.

    Candidata a eliminación futura.
    """

    log.info("📍 Migrando equipo: pokemon_nombre → captura_id...")
    cursor.execute(
        "SELECT user_id, slot, pokemon_nombre FROM equipo"
)
    filas = cursor.fetchall()

    cursor.execute("DROP TABLE equipo")
    _crear_tabla_equipo(cursor)

    for user_id, slot, nombre in filas:
        cap = obtener_mejor_captura(user_id, nombre)
        if not cap:
            continue
        captura_id = cap[0]
        cursor.execute(
            """
            INSERT INTO equipo (user_id, slot, captura_id)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (_uid(user_id), slot, captura_id),
        )
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
    """
    COMPATIBILIDAD DE DATOS (Junio 2026)

    La tabla capturas almacena user_id como TEXT.
    La tabla equipo almacena user_id como BIGINT.

    Esta función normaliza el valor para las consultas
    relacionadas con equipo.

    Debería eliminarse cuando ambas tablas utilicen el
    mismo tipo de dato para user_id.
    """
    return str(user_id) if DATABASE_URL else user_id


def obtener_captura(user_id, captura_id: int):
    """Retorna (id, nombre, shiny, naturaleza, ivs...) o None si no es del usuario."""
    conn = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, pokemon_nombre, es_shiny, naturaleza,
                iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe
            FROM capturas
            WHERE id = %s AND user_id = %s
            """,
            (captura_id, _uid(user_id)),
        )
        return cursor.fetchone()

    except Exception as e:

        log.error(
            f"🚨 Error obtener_captura: {e}",
            exc_info=True
        )

        return None

    finally:

        if conn:
            conn.close()


def obtener_capturas_por_ids(user_id, captura_ids: list) -> dict[int, tuple]:
    """Mapa captura_id -> fila de obtener_captura para un lote de IDs."""
    ids = [int(i) for i in captura_ids if str(i).isdigit()]
    if not ids:
        return {}

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        resultado = {}
        placeholders = ",".join(["%s"] * len(ids))

        cursor.execute(
            f"""
            SELECT id, pokemon_nombre, es_shiny, naturaleza,
                iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe
            FROM capturas
            WHERE user_id = %s
            AND id IN ({placeholders})
            """,
            [_uid(user_id), *ids],
        )
        for fila in cursor.fetchall():
            resultado[int(fila[0])] = fila
        return resultado
    except Exception as e:
        log.error(f"🚨 Error obtener_capturas_por_ids: {e}", exc_info=True)
        return {}
    finally:
        if conn:
            conn.close()


def obtener_inventario_usuario(user_id) -> list[dict]:
    """Inventario completo con dex id y tipos desde pokemon_data."""
    conn = None
    iv_pct = "((c.iv_hp + c.iv_atk + c.iv_def + c.iv_spa + c.iv_spd + c.iv_spe) * 100 / 186)"
    try:
        conn = get_connection()
        cursor = conn.cursor()
        uid = str(user_id) if DATABASE_URL else user_id
        if DATABASE_URL:
            cursor.execute(
                f"""
                SELECT
                    c.id,
                    c.pokemon_nombre,
                    c.es_shiny,
                    {iv_pct},
                    p.id,
                    p.tipos
                FROM capturas c
                LEFT JOIN pokemon_data p ON c.pokemon_nombre = p.nombre
                WHERE c.user_id = %s
                """,
                (uid,),
            )
        else:
            cursor.execute(
                f"""
                SELECT
                    c.id,
                    c.pokemon_nombre,
                    c.es_shiny,
                    {iv_pct},
                    p.id,
                    p.tipos
                FROM capturas c
                LEFT JOIN pokemon_data p ON c.pokemon_nombre = p.nombre
                WHERE c.user_id = ?
                """,
                (uid,),
            )
        return [
            {
                "id": fila[0],
                "nombre": fila[1],
                "es_shiny": bool(fila[2]),
                "iv_pct": float(fila[3] or 0),
                "dex_id": fila[4],
                "tipos": fila[5] or "",
            }
            for fila in cursor.fetchall()
        ]
    except Exception as e:
        log.error(f"🚨 Error obtener_inventario_usuario: {e}", exc_info=True)
        return []
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
        cursor.execute(
            f"""
            SELECT id, pokemon_nombre, es_shiny, {iv_pct}
            FROM capturas
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (_uid(user_id),),
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
        cursor.execute(
            """
            SELECT slot, captura_id
            FROM equipo
            WHERE user_id = %s
            ORDER BY slot
            """,
            (_uid(user_id),),
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
        cursor.execute(
            "DELETE FROM equipo WHERE user_id = %s AND slot = %s",
            (_uid(user_id), slot),
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
        cursor.execute(
            """
            INSERT INTO equipo (user_id, slot, captura_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, slot)
            DO UPDATE SET captura_id = EXCLUDED.captura_id
            """,
            (_uid(user_id), slot, captura_id),
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
        cursor.execute(
            f"""
            SELECT id, iv_hp, iv_atk, iv_def,
                iv_spa, iv_spd, iv_spe,
                es_shiny
            FROM capturas
            WHERE user_id = %s
            AND pokemon_nombre = %s
            ORDER BY {iv_sum} DESC
            """,
            (_uid(user_id), nombre.lower()),
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
        cursor.execute(
            "SELECT es_legendario, es_mitico FROM pokemon_data WHERE id = %s",
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

        cursor.execute(
            """
            UPDATE pokemon_data
            SET capture_rate = %s
            WHERE id = %s
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

    if not nombre:
        return None

    return POKEMON_CACHE_NOMBRE.get(
        nombre.lower()
    )
def obtener_id_pokemon(nombre):
    pokemon = obtener_pokemon_local_nombre(
        nombre
    )

    if not pokemon:
        return None

    return pokemon["id"]
pokemon_por_id = {}
id_por_nombre = {}

def cargar_cache_pokemon():

    global POKEMON_CACHE
    global POKEMON_CACHE_NOMBRE
    global pokemon_por_id
    global id_por_nombre

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
                es_mitico,
                hp,
                attack,
                defense,
                special_attack,
                special_defense,
                speed,
                height,
                weight
            FROM pokemon_data
        """)

        filas = cursor.fetchall()

        POKEMON_CACHE.clear()
        POKEMON_CACHE_NOMBRE.clear()

        pokemon_por_id.clear()
        id_por_nombre.clear()

        for fila in filas:

            pokemon = {
                "id": fila[0],
                "nombre": fila[1],
                "tipos": fila[2],
                "capture_rate": fila[3],
                "es_legendario": fila[4],
                "es_mitico": fila[5],
                "hp": fila[6],
                "attack": fila[7],
                "defense": fila[8],
                "special_attack": fila[9],
                "special_defense": fila[10],
                "speed": fila[11],
                "height": fila[12],
                "weight": fila[13]
            }

            # Caché completa
            POKEMON_CACHE[fila[0]] = pokemon

            POKEMON_CACHE_NOMBRE[
                fila[1].lower()
            ] = pokemon

            # Caché rápida nombre <-> id
            pokemon_por_id[fila[0]] = fila[1]

            id_por_nombre[
                fila[1].lower()
            ] = fila[0]

        log.info(
            f"✅ Cache Pokémon cargada: "
            f"{len(POKEMON_CACHE)} registros"
        )

    finally:

        cursor.close()
        conn.close()
def obtener_ids_sin_stats():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT id
            FROM pokemon_data
            WHERE hp IS NULL
        """)

        return [fila[0] for fila in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()
def actualizar_stats_pokemon(
    pokemon_id,
    hp,
    attack,
    defense,
    special_attack,
    special_defense,
    speed,
    height,
    weight
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE pokemon_data
            SET
                hp = %s,
                attack = %s,
                defense = %s,
                special_attack = %s,
                special_defense = %s,
                speed = %s,
                height = %s,
                weight = %s
            WHERE id = %s
            """,
            (
                hp,
                attack,
                defense,
                special_attack,
                special_defense,
                speed,
                height,
                weight,
                pokemon_id
            )
        )

        conn.commit()

    finally:

        cursor.close()
        conn.close()
def obtener_duplicados(user_id, limite=15, tipo=None):

    conn = get_connection()
    cursor = conn.cursor()

    if tipo:

        cursor.execute("""
            SELECT
                c.pokemon_nombre,
                COUNT(*) as cantidad
            FROM capturas c
            JOIN pokemon_data p
                ON LOWER(c.pokemon_nombre) = LOWER(p.nombre)
            WHERE c.user_id = %s
              AND p.tipos ILIKE %s
            GROUP BY c.pokemon_nombre
            HAVING COUNT(*) > 1
            ORDER BY cantidad DESC
            LIMIT %s
        """, (
            str(user_id),
            f"%{tipo.lower()}%",
            limite
        ))

    else:

        cursor.execute("""
            SELECT
                pokemon_nombre,
                COUNT(*) as cantidad
            FROM capturas
            WHERE user_id = %s
            GROUP BY pokemon_nombre
            HAVING COUNT(*) > 1
            ORDER BY cantidad DESC
            LIMIT %s
        """, (
            str(user_id),
            limite
        ))

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    return resultado

def obtener_nombre_local(id_pokemon):

    return pokemon_por_id.get(
        id_pokemon,
        "???"
    )


async def guardar_trainer(
    user_id,
    trainer
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO trainers_usuario
            (
                user_id,
                trainer_sprite
            )
            VALUES
            (
                %s,
                %s
            )
            ON CONFLICT (user_id)
            DO UPDATE SET
            trainer_sprite = EXCLUDED.trainer_sprite
            """,
            (
                str(user_id),
                trainer
            )
        )

        conn.commit()

    finally:

        cursor.close()
        conn.close()
async def obtener_trainer(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT trainer_sprite
            FROM trainers_usuario
            WHERE user_id = %s
            """,
            (str(user_id),)
        )

        fila = cursor.fetchone()

        if fila:

            return fila[0]

        return None

    finally:

        cursor.close()
        conn.close()