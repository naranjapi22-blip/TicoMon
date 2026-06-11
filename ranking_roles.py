import discord
from discord.ext import commands
import database
from database import guardar_canal_rankings
from database import obtener_canal_rankings
async def actualizar_roles_competitivos(cog, guild):
    canal_id = obtener_canal_rankings(guild.id)

    print(f"[RANKINGS] Canal configurado: {canal_id}")
    canal = None

    if canal_id:
        canal = guild.get_channel(canal_id)

    print(f"[RANKINGS] Canal encontrado: {canal}")
    roles = await cog.asegurar_roles(guild)

    lider_pokedex = await cog.obtener_lider_pokedex()
    lider_shiny = await cog.obtener_lider_shiny()
    lider_legend = await cog.obtener_lider_legendario()

    if lider_pokedex:
        await cog.asignar_rol_exclusivo(
            guild,
            roles["🏆 Maestro Pokédex"],
            lider_pokedex
        )

    if lider_shiny:
        await cog.asignar_rol_exclusivo(
            guild,
            roles["✨ Rey Shiny"],
            lider_shiny
        )

    if lider_legend:
        await cog.asignar_rol_exclusivo(
            guild,
            roles["👑 Rey Legendario"],
            lider_legend
        )

class RankingRoles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def asegurar_roles(self, guild):

        nombres_roles = [
            "🏆 Maestro Pokédex",
            "✨ Rey Shiny",
            "👑 Rey Legendario"
        ]

        roles = {}

        for nombre in nombres_roles:

            rol = discord.utils.get(
                guild.roles,
                name=nombre
            )

            if rol is None:
                rol = await guild.create_role(
                    name=nombre,
                    mentionable=True,
                    reason="Roles competitivos de TicoMon"
                )

            roles[nombre] = rol

        return roles

    async def obtener_lider_pokedex(self):

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT
                    user_id,
                    COUNT(DISTINCT pokemon_nombre) AS especies
                FROM capturas
                GROUP BY user_id
                ORDER BY especies DESC
                LIMIT 1
            """)

            fila = cursor.fetchone()

            return int(fila[0]) if fila else None

        finally:
            conn.close()

    async def obtener_lider_shiny(self):

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT
                    user_id,
                    COUNT(*) AS shinies
                FROM capturas
                WHERE es_shiny = 1
                GROUP BY user_id
                ORDER BY shinies DESC
                LIMIT 1
            """)

            fila = cursor.fetchone()

            return int(fila[0]) if fila else None

        finally:
            conn.close()

    async def obtener_lider_legendario(self):

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT
                    c.user_id,
                    COUNT(*) AS legendarios
                FROM capturas c
                JOIN pokemon_data p
                    ON LOWER(c.pokemon_nombre) = LOWER(p.nombre)
                WHERE p.es_legendario = TRUE
                   OR p.es_mitico = TRUE
                GROUP BY c.user_id
                ORDER BY legendarios DESC
                LIMIT 1
            """)

            fila = cursor.fetchone()

            return int(fila[0]) if fila else None

        finally:
            conn.close()

    async def asignar_rol_exclusivo(
        self,
        guild,
        rol,
        user_id
    ):

        # Verificar si el líder actual ya tiene el rol
        lider_actual = None


        if rol.members:
            lider_actual = rol.members[0]


        for m in guild.members:
            if rol in m.roles:
                print(f"   - {m} ({m.id})")



        canal = None
        canal_id = obtener_canal_rankings(guild.id)

        if canal_id:
            canal = guild.get_channel(canal_id)
        print(
            f"[ANUNCIOS] Canal encontrado: {canal}"
        )
        

        if lider_actual and lider_actual.id == user_id:

            print(
                f"[DEBUG] Sin cambios en {rol.name}"
            )

            return

        # Quitar el rol al líder anterior
        for miembro in guild.members:

            if rol in miembro.roles:
                await miembro.remove_roles(
                    rol,
                    reason="Actualización de ranking"
                )

        miembro = guild.get_member(user_id)

        if miembro is None:
            try:
                miembro = await guild.fetch_member(user_id)
            except Exception as e:
                print(f"No se pudo obtener miembro {user_id}: {e}")
                return

        try:
            await miembro.add_roles(
                rol,
                reason="Líder actual del ranking"
            )

            if canal:

                await canal.send(
                    f"🏆 Cambio de líder detectado en {rol.name}\n"
                    f"Nuevo líder: {miembro.mention}"
                )

            print(
                f"✅ {rol.name} asignado a {miembro}"
            )

        except Exception as e:
            print(
                f"❌ Error asignando {rol.name}: {e}"
            )

    @commands.command(name="actualizarrankings")
    @commands.has_permissions(administrator=True)
    async def actualizar_rankings(self, ctx):

        await actualizar_roles_competitivos(
            self,
            ctx.guild
        )

        embed = discord.Embed(
            title="🏆 Rankings actualizados",
            description=(
                "Los títulos competitivos fueron "
                "recalculados correctamente."
            ),
            color=discord.Color.gold()
        )

        await ctx.send(embed=embed)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(name="setrankings")
    async def setrankings(self, ctx):

        guardar_canal_rankings(
            ctx.guild.id,
            ctx.channel.id
        )

        embed = discord.Embed(
            title="✅ Canal de rankings configurado",
            description=(
                "Los anuncios automáticos de cambios "
                "de líder se enviarán en este canal."
            ),
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)
    @setrankings.error
    async def setrankings_error(self, ctx, error):

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "❌ Necesitas permisos de administrador."
            )
async def setup(bot):
    await bot.add_cog(RankingRoles(bot))