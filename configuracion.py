import os
import sqlite3
import psycopg2
from discord.ext import commands

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect('fumo_data.db')

def init_config_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Usamos BIGINT para IDs de Discord
    cursor.execute('CREATE TABLE IF NOT EXISTS canales_config (guild_id BIGINT PRIMARY KEY, canal_id BIGINT)')
    conn.commit()
    conn.close()

def set_canal(guild_id, canal_id):
    conn = get_connection()
    cursor = conn.cursor()
    if DATABASE_URL:
        # Sintaxis PostgreSQL: INSERT ... ON CONFLICT
        query = """
            INSERT INTO canales_config (guild_id, canal_id) VALUES (%s, %s)
            ON CONFLICT(guild_id) DO UPDATE SET canal_id = EXCLUDED.canal_id
        """
        cursor.execute(query, (guild_id, canal_id))
    else:
        # Sintaxis SQLite
        cursor.execute("REPLACE INTO canales_config (guild_id, canal_id) VALUES (?, ?)", (guild_id, canal_id))
    conn.commit()
    conn.close()

def obtener_canal(guild_id):
    conn = get_connection()
    cursor = conn.cursor()
    if DATABASE_URL:
        cursor.execute("SELECT canal_id FROM canales_config WHERE guild_id = %s", (guild_id,))
    else:
        cursor.execute("SELECT canal_id FROM canales_config WHERE guild_id = ?", (guild_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def canal_restringido():
    async def predicate(ctx):
        # Asegúrate de usar el ID de usuario correcto aquí
        if ctx.author.id == 113100351531417600:
            return True
        canal_permitido = obtener_canal(ctx.guild.id)
        if canal_permitido and ctx.channel.id != canal_permitido:
            return False
        return True
    return commands.check(predicate)