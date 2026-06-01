import discord
import aiohttp
import random
import os
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image
import io

# Cargar configuración
load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.event
async def setup_hook():
    bot.session = aiohttp.ClientSession()

@bot.event
async def close():
    await bot.session.close()

async def obtener_pokemon(id_o_nombre):
    async with bot.session.get(f"https://pokeapi.co/api/v2/pokemon/{id_o_nombre}") as resp:
        data = await resp.json()
    async with bot.session.get(data['species']['url']) as resp_species:
        species = await resp_species.json()
    return data, species
# --- SERVICIOS BASE ---
async def obtener_pokemon(id_o_nombre):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://pokeapi.co/api/v2/pokemon/{id_o_nombre}") as resp:
            data = await resp.json()
        async with session.get(data['species']['url']) as resp_species:
            species = await resp_species.json()
    return data, species

# --- CONFIGURACIÓN DE REGIONES ---
REGIONES = {
    "1": (1, 151), "2": (152, 251), "3": (252, 386),
    "4": (387, 493), "5": (494, 649), "6": (650, 721),
    "7": (722, 809), "8": (810, 905), "9": (906, 1025)
}

# --- FUNCIONES DE IMAGEN ---
def generar_silueta(image):
    img_data = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            if img_data[x, y][3] > 0: # Si no es transparente
                img_data[x, y] = (0, 0, 0, 255) # Pintar de negro
    return image

async def generar_collage(ids_y_urls, tenidos):
    sprite_size = 96
    num_pokes = len(ids_y_urls)
    collage = Image.new('RGBA', (num_pokes * sprite_size, sprite_size), (0,0,0,0))
    async with aiohttp.ClientSession() as session:
        for i, (id_p, url) in enumerate(ids_y_urls):
            async with session.get(url) as resp:
                data = await resp.read()
                img = Image.open(io.BytesIO(data)).convert('RGBA')
                # Si no está en 'tenidos', aplicamos el filtro de silueta
                if id_p not in tenidos:
                    img = generar_silueta(img)
                collage.paste(img, (i * sprite_size, 0), img)
    buffer = io.BytesIO()
    collage.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

# --- COMANDO POKEDEX ---
class PokedexView(discord.ui.View):
    def __init__(self, region, inicio, fin, tenidos):
        super().__init__(timeout=60)
        self.region = region
        self.inicio = inicio
        self.fin = fin
        self.tenidos = tenidos
        # Dividimos el rango total en páginas de 10
        self.total_pokes = list(range(inicio, fin + 1))
        self.paginas = [self.total_pokes[i:i + 10] for i in range(0, len(self.total_pokes), 10)]
        self.pagina = 0

    async def generar_vista_pokedex(self, interaction_or_ctx):
        # Obtenemos los IDs de la página actual
        ids_actuales = self.paginas[self.pagina]
        # Creamos las tuplas (id, url)
        data_pokes = [(i, f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{i}.png") for i in ids_actuales]
        
        buffer = await generar_collage(data_pokes, self.tenidos)
        file = discord.File(buffer, filename="pokedex.png")
        
        embed = discord.Embed(title=f"🎒 Pokedex Región {self.region}", description=f"Página {self.pagina + 1}/{len(self.paginas)}")
        embed.set_image(url="attachment://pokedex.png")
        
        if hasattr(interaction_or_ctx, 'response'):
            await interaction_or_ctx.response.edit_message(embed=embed, attachments=[file], view=self)
        else:
            await interaction_or_ctx.send(embed=embed, file=file, view=self)

    @discord.ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.primary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina = (self.pagina - 1) % len(self.paginas)
        await self.generar_vista_pokedex(interaction)

    @discord.ui.button(label="Siguiente ➡️", style=discord.ButtonStyle.primary)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina = (self.pagina + 1) % len(self.paginas)
        await self.generar_vista_pokedex(interaction)

@bot.command()
async def pokedex(ctx, region: str):
    if region not in REGIONES:
        await ctx.send("Región no válida. Usa del 1 al 9.")
        return
    
    inicio, fin = REGIONES[region]
    # Aquí consultarás tu base de datos después
    tenidos = [1, 4, 7, 25, 150] 
    
    view = PokedexView(region, inicio, fin, tenidos)
    await view.generar_vista_pokedex(ctx)
async def testinfo(ctx, nombre_o_id: str):
    try:
        data, species = await obtener_pokemon(nombre_o_id.lower())
        stats_dict = {s['stat']['name']: s['base_stat'] for s in data['stats']}
        
        embed = discord.Embed(title=f"Lv. 50 {data['name'].capitalize()}", color=discord.Color.blue())
        embed.set_thumbnail(url=data['sprites']['front_default'])
        
        peso_kg = data['weight'] / 10
        detalles = f"**Tipo:** {', '.join([t['type']['name'].capitalize() for t in data['types']])}\n**Peso:** {peso_kg}kg"
        embed.add_field(name="Detalles", value=detalles, inline=False)
        
        stats_texto = (
            f"❤️ HP: {stats_dict.get('hp')}\n"
            f"⚔️ Attack: {stats_dict.get('attack')}\n"
            f"🛡️ Defense: {stats_dict.get('defense')}\n"
            f"🔥 Sp. Atk: {stats_dict.get('special-attack')}\n"
            f"💧 Sp. Def: {stats_dict.get('special-defense')}\n"
            f"⚡ Speed: {stats_dict.get('speed')}"
        )
        embed.add_field(name="Estadísticas Base", value=stats_texto, inline=False)
        embed.set_image(url=data['sprites']['other']['official-artwork']['front_default'])
        embed.set_footer(text=f"ID: {data['id']} | Pokémon consultado")
        await ctx.send(embed=embed)
    except:
        await ctx.send("No pude encontrar ese Pokémon.")

class BotonCaptura(discord.ui.View):
    def __init__(self, pokemon_nombre, es_legendario, es_shiny):
        super().__init__(timeout=300.0)
        self.nombre = pokemon_nombre
        self.es_legendario = es_legendario
        self.es_shiny = es_shiny
        self.intentos = 0
        self.es_especial = self.es_legendario or self.es_shiny
        self.max_intentos = 10 if self.es_especial else 5
        self.user_cooldowns = {}

    @discord.ui.button(label="¡Lanzar Pokéball!", style=discord.ButtonStyle.primary, emoji="🔴")
    async def boton_captura(self, interaction: discord.Interaction, button: discord.ui.Button):
        ahora = discord.utils.utcnow().timestamp()
        user_id = interaction.user.id
        cooldown = 10

        if user_id in self.user_cooldowns and (ahora - self.user_cooldowns[user_id] < cooldown):
            tiempo_restante = int(cooldown - (ahora - self.user_cooldowns[user_id]))
            await interaction.response.send_message(f"⏱️ Espera {tiempo_restante}s.", ephemeral=True)
            return

        self.user_cooldowns[user_id] = ahora
        await interaction.response.defer(ephemeral=True)

        prob_base = 0.04 if self.es_especial else 0.30
        azar = random.random()
        
        if self.es_especial:
            if azar < 0.01:
                prob_final, mensaje_bola = 1.0, "una MASTER BALL (¡Captura Garantizada!)"
            elif azar < 0.26: 
                prob_final, mensaje_bola = prob_base + 0.15, "una Ultra Ball"
            elif azar < 0.96: 
                prob_final, mensaje_bola = prob_base + 0.10, "una Great Ball"
            else:
                prob_final, mensaje_bola = prob_base, "una Pokéball"
        else:
            if azar < 0.005:
                prob_final, mensaje_bola = 1.0, "una MASTER BALL (¡Captura Garantizada!)"
            elif azar < 0.10:
                prob_final, mensaje_bola = prob_base + 0.15, "una Ultra Ball"
            elif azar < 0.30:
                prob_final, mensaje_bola = prob_base + 0.10, "una Great Ball"
            else:
                prob_final, mensaje_bola = prob_base, "una Pokéball"

        if random.random() < prob_final:
            await interaction.message.edit(content=f"🎉 {interaction.user.mention} lanzó {mensaje_bola} y capturó a {'SHINY ' if self.es_shiny else ''}{self.nombre.capitalize()}!", view=None)
            self.stop()
        else:
            self.intentos += 1
            if self.intentos >= self.max_intentos:
                await interaction.message.edit(content="💨 ¡El Pokémon escapó!", view=None)
                self.stop()
            else:
                embed = interaction.message.embeds[0]
                embed.set_footer(text=f"Intentos fallidos: {self.intentos}/{self.max_intentos}")
                await interaction.message.edit(embed=embed)
                await interaction.followup.send(f"❌ Lanzaste {mensaje_bola} pero fallaste. ¡Sigue intentándolo!", ephemeral=True)

@bot.command()
async def spawn(ctx, forzar_shiny: bool = False):
    try:
        with open('lista_spawn.txt', 'r') as f:
            lista = f.read().splitlines()
        data, species = await obtener_pokemon(random.choice(lista))
        es_shiny = forzar_shiny or random.randint(1, 50) == 1
        embed = discord.Embed(
            title=f"{'✨' if es_shiny else ''} ¡Un {data['name'].capitalize()} salvaje apareció!",
            color=discord.Color.gold() if es_shiny else discord.Color.green()
        )
        embed.set_image(url=data['sprites']['front_shiny'] if es_shiny else data['sprites']['front_default'])
        es_legendario = species.get('is_legendary', False)
        max_i = 10 if (es_legendario or es_shiny) else 5
        embed.set_footer(text=f"Intentos fallidos: 0/{max_i}")
        view = BotonCaptura(data['name'], es_legendario, es_shiny)
        await ctx.send(embed=embed, view=view)
    except:
        await ctx.send("Error al generar el Pokémon.")

bot.run(TOKEN)