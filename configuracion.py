import sqlite3
from discord.ext import commands

def init_config_db():
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS canales_config (guild_id INTEGER PRIMARY KEY, canal_id INTEGER)')
    conn.commit()
    conn.close()

def set_canal(guild_id, canal_id):
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO canales_config (guild_id, canal_id) VALUES (?, ?)", (guild_id, canal_id))
    conn.commit()
    conn.close()

def obtener_canal(guild_id):
    conn = sqlite3.connect('fumo_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT canal_id FROM canales_config WHERE guild_id = ?", (guild_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def canal_restringido():
    async def predicate(ctx):
        # Excepción solo para tu ID de usuario (pon tu ID real aquí)
        if ctx.author.id == 113100351531417600:
            return True
            
        canal_permitido = obtener_canal(ctx.guild.id)
        if canal_permitido and ctx.channel.id != canal_permitido:
            return False
        return True
    return commands.check(predicate)