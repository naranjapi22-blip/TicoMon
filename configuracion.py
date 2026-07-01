from discord.ext import commands

async def init_config_db(bot):
    async with bot.db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS canales_config (
                guild_id BIGINT PRIMARY KEY,
                canal_id BIGINT
            )
        """)

async def set_canal(bot, guild_id, canal_id):
    async with bot.db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO canales_config (guild_id, canal_id)
            VALUES ($1, $2)
            ON CONFLICT (guild_id)
            DO UPDATE SET canal_id = EXCLUDED.canal_id
            """,
            guild_id,
            canal_id
        )

async def obtener_canal(bot, guild_id):
    async with bot.db_pool.acquire() as conn:

        row = await conn.fetchrow(
            """
            SELECT canal_id
            FROM canales_config
            WHERE guild_id = $1
            """,
            guild_id
        )

    return row["canal_id"] if row else None

def canal_restringido():

    async def predicate(ctx):

        if ctx.author.id == 113100351531417600:
            return True

        canal_permitido = await obtener_canal(
            ctx.bot,
            ctx.guild.id
        )

        if canal_permitido and ctx.channel.id != canal_permitido:
            return False

        return True

    return commands.check(predicate)