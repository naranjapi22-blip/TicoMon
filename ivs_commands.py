import discord
from discord.ext import commands
from database import get_connection

class IvsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ivs")
    async def ver_ivs(self, ctx, id_pokemon: int):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Consultamos el Pokémon
        cursor.execute("""
            SELECT pokemon_nombre, iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe 
            FROM capturas 
            WHERE id = %s
        """, (str(id_pokemon),)) # Convertido a string por si la base de datos lo pide así, es más seguro
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            await ctx.send("❌ No existe ningún Pokémon con ese ID.")
            return

        nombre, hp, atk, defs, spa, spd, spe = resultado
        ivs = [hp, atk, defs, spa, spd, spe]
        total = sum(ivs)
        porcentaje = round((total / 186) * 100, 2)
        
        # Color dinámico basado en la calidad
        if porcentaje >= 85: color = discord.Color.gold()     # Épico
        elif porcentaje >= 70: color = discord.Color.green()  # Excelente
        else: color = discord.Color.blue()                    # Normal

        embed = discord.Embed(title=f"🧬 IVs de {nombre.capitalize()} (ID: {id_pokemon})", color=color)
        embed.add_field(name="Estadísticas", value=f"""
HP: `{hp}/31` | ATK: `{atk}/31`
DEF: `{defs}/31` | SPA: `{spa}/31`
SPD: `{spd}/31` | SPE: `{spe}/31`
        """, inline=False)
        embed.add_field(name="Potencial Total", value=f"**{total}/186** ({porcentaje}%)", inline=True)
        
        await ctx.send(embed=embed)

# ESTO ERA LO QUE FALTABA
async def setup(bot):
    await bot.add_cog(IvsCommands(bot))