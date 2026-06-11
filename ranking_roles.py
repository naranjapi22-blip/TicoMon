import discord
from discord.ext import commands

import database


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

        # Quitar rol a cualquiera que lo tenga
        for miembro in guild.members:

            if rol in miembro.roles:
                await miembro.remove_roles(
                    rol,
                    reason="Actualización de ranking"
                )

        # Asignar al nuevo líder
        miembro = guild.get_member(user_id)

        if miembro:
            await miembro.add_roles(
                rol,
                reason="Líder actual del ranking"
            )

    @commands.command(name="actualizarrankings")
    @commands.has_permissions(administrator=True)
    async def actualizar_rankings(self, ctx):

        guild = ctx.guild

        roles = await self.asegurar_roles(guild)

        lider_pokedex = await self.obtener_lider_pokedex()
        lider_shiny = await self.obtener_lider_shiny()
        lider_legend = await self.obtener_lider_legendario()

        if lider_pokedex:
            await self.asignar_rol_exclusivo(
                guild,
                roles["🏆 Maestro Pokédex"],
                lider_pokedex
            )

        if lider_shiny:
            await self.asignar_rol_exclusivo(
                guild,
                roles["✨ Rey Shiny"],
                lider_shiny
            )

        if lider_legend:
            await self.asignar_rol_exclusivo(
                guild,
                roles["👑 Rey Legendario"],
                lider_legend
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


async def setup(bot):
    await bot.add_cog(RankingRoles(bot))