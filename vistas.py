import discord
import random
import math
import logging
import database
import sqlite3
import datetime
import os
import gestor_spawn
import servicios
from logger_config import log

COOLDOWN_LANZAMIENTO = 10.0
COOLDOWN_GRACE = 0.25

INICIALES = [
    {"nombre": "Bulbasaur", "id": 1}, {"nombre": "Charmander", "id": 4}, {"nombre": "Squirtle", "id": 7},
    {"nombre": "Chikorita", "id": 152}, {"nombre": "Cyndaquil", "id": 155}, {"nombre": "Totodile", "id": 158},
    {"nombre": "Treecko", "id": 252}, {"nombre": "Torchic", "id": 255}, {"nombre": "Mudkip", "id": 258},
    {"nombre": "Turtwig", "id": 387}, {"nombre": "Chimchar", "id": 390}, {"nombre": "Piplup", "id": 393},
    {"nombre": "Snivy", "id": 495}, {"nombre": "Tepig", "id": 498}, {"nombre": "Oshawott", "id": 501},
    {"nombre": "Chespin", "id": 650}, {"nombre": "Fennekin", "id": 653}, {"nombre": "Froakie", "id": 656},
    {"nombre": "Rowlet", "id": 722}, {"nombre": "Litten", "id": 725}, {"nombre": "Popplio", "id": 728},
    {"nombre": "Grookey", "id": 810}, {"nombre": "Scorbunny", "id": 813}, {"nombre": "Sobble", "id": 816},
    {"nombre": "Sprigatito", "id": 906}, {"nombre": "Fuecoco", "id": 909}, {"nombre": "Quaxly", "id": 912}
]
# --- CLASE PARA EL MENÚ DE TIPOS ---
class TipoSelect(discord.ui.Select):
    def __init__(self, tenidos):
        tipos = ["all", "fire", "water", "grass", "electric", "ice", "fighting", 
                 "poison", "ground", "flying", "psychic", "bug", "rock", "ghost", 
                 "dragon", "steel", "dark", "fairy"]
        options = [discord.SelectOption(label=t.capitalize(), value=t) for t in tipos]
        super().__init__(placeholder="Filtrar por tipo...", options=options, custom_id="filtro_tipo")
        self.tenidos = tenidos

    async def callback(self, interaction: discord.Interaction):
            self.view.filtro_actual = self.values[0]
            self.view.pagina = 0
            
            # Obtenemos los IDs filtrados
            ids_filtrados = await servicios.filtrar_capturas_por_tipo(
                interaction.client.session, self.view.filtro_actual, self.tenidos
            )
            
            # CORRECCIÓN: Actualizamos siempre, incluso si la lista es vacía
            self.view.total_pokes = ids_filtrados
            
            # Si la lista está vacía, reiniciamos las páginas a una lista vacía
            if not ids_filtrados:
                self.view.paginas = []
            else:
                self.view.paginas = [ids_filtrados[i:i + 10] for i in range(0, len(ids_filtrados), 10)]
            
            await self.view.generar_vista_pokedex(interaction, interaction.client.session)

# --- CLASE PRINCIPAL DE POKEDEX ---
class PokedexView(discord.ui.View):
    # Asegúrate de que el __init__ acepte inicio y fin, incluso si no los usas para filtrar
    def __init__(self, region, tenidos, inicio=1, fin=1025, es_coleccion_personal=False, modo_shiny=False):
        super().__init__(timeout=60)
        self.region = region
        self.tenidos = sorted(list(tenidos))
        self.es_coleccion_personal = es_coleccion_personal
        self.modo_shiny = modo_shiny
        self.filtro_actual = "all"
        
        # Lógica para definir qué se muestra
        if self.es_coleccion_personal:
            self.total_pokes = self.tenidos
        else:
            self.total_pokes = list(range(inicio, fin + 1))
            
        self.paginas = [self.total_pokes[i:i + 10] for i in range(0, len(self.total_pokes), 10)]
        self.pagina = 0
        
        # AÑADIR EL MENÚ DE TIPOS AQUÍ
        self.add_item(TipoSelect(self.tenidos))

    async def generar_vista_pokedex(self, interaction_or_ctx, session):
            # 1. CASO: LISTA VACÍA
            if not self.total_pokes:
                embed = discord.Embed(
                    title=f"🎒 Colección | Tipo: {self.filtro_actual.capitalize()}",
                    description="¡No tienes Pokémon de ese tipo!"
                )
                
                if hasattr(interaction_or_ctx, 'response'):
                    # IMPORTANTE: attachments=[] borra cualquier imagen que hubiera antes
                    await interaction_or_ctx.response.edit_message(embed=embed, attachments=[], view=self)
                else:
                    await interaction_or_ctx.send(embed=embed, view=self)
                return

            # 2. CASO: LISTA CON DATOS
            ids_actuales = self.paginas[self.pagina]
            url_base = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
            data_pokes = [(i, f"{url_base}{i}.png") for i in ids_actuales]
            
            buffer = await servicios.generar_collage(session, data_pokes, self.tenidos)
            file = discord.File(buffer, filename="pokedex.png")
            
            embed = discord.Embed(
                title=f"🎒 Colección | Tipo: {self.filtro_actual.capitalize()}", 
                description=f"Página {self.pagina + 1}/{max(1, len(self.paginas))}"
            )
            embed.set_image(url="attachment://pokedex.png")
            
            # 3. EDICIÓN O ENVÍO
            if hasattr(interaction_or_ctx, 'response') and interaction_or_ctx.response.is_done():
                # Si ya se respondió antes (ej: al navegar páginas), usamos followup
                await interaction_or_ctx.followup.edit_message(message_id=interaction_or_ctx.message.id, embed=embed, attachments=[file], view=self)
            elif hasattr(interaction_or_ctx, 'response'):
                # Primera respuesta a la interacción (ej: al usar el menú desplegable)
                await interaction_or_ctx.response.edit_message(embed=embed, attachments=[file], view=self)
            else:
                # Comando inicial normal
                await interaction_or_ctx.send(embed=embed, file=file, view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina = (self.pagina - 1) % max(1, len(self.paginas))
        await self.generar_vista_pokedex(interaction, interaction.client.session)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina = (self.pagina + 1) % max(1, len(self.paginas))
        await self.generar_vista_pokedex(interaction, interaction.client.session)

class SpawnSelectionView(discord.ui.View):
    def __init__(self, data_pokes, autor_original):
        super().__init__(timeout=60) # Tienen 60 segundos para elegir
        self.data_pokes = data_pokes 
        self.autor_original = autor_original 
        self.message = None # <-- Añadimos esto para guardar el mensaje y poder editarlo al final

    # --- NUEVA FUNCIÓN PARA CUANDO SE ACABA EL TIEMPO ---
    async def on_timeout(self):
        # Desactivamos los 3 botones para que se pongan grises
        for child in self.children:
            child.disabled = True
            
        if self.message:
            try:
                # Agarramos el embed original y lo cambiamos a rojo
                embed_huida = self.message.embeds[0]
                embed_huida.title = "💨 ¡Los Pokémon salvajes huyeron!"
                embed_huida.description = "Tardaste demasiado en decidir y escaparon entre la hierba alta."
                embed_huida.color = discord.Color.red()
                
                # Actualizamos el mensaje en Discord
                await self.message.edit(embed=embed_huida, view=self)
            except discord.HTTPException:
                pass
        # 1. Liberar el canal para que otros puedan usar !spawn
        import gestor_spawn
        if self.message:
            gestor_spawn.canales_ocupados.discard(self.message.channel.id)
            
            # 2. Avisar que el tiempo pasó
            try:
                await self.message.edit(content="❌ El Pokémon huyó porque nadie lo atrapó a tiempo.", view=None)
            except:
                pass
    # --- EL GUARDA DE SEGURIDAD ---
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Si el que hace clic NO es el dueño del comando...
        if interaction.user != self.autor_original:
            # Mandamos el regaño privado (ephemeral=True hace que solo él lo vea)
            await interaction.response.send_message(
                "¡Hey! 🛑 Consigue tu propio Pokémon usando `!spawn`. Este encuentro no es tuyo.", 
                ephemeral=True
            )
            return False # Bloquea el clic
        
        return True # Si es el dueño, lo deja pasar con normalidad

    # --- MANEJO DE LA SELECCIÓN ---
    # --- MANEJO DE LA SELECCIÓN ---
    async def manejar_seleccion(self, interaction: discord.Interaction, indice: int):
        self.stop()
        for child in self.children:
            child.disabled = True
        
        # 'data' es el JSON del pokemon, 'species' es el JSON de la especie
        data, species = self.data_pokes[indice]
        
        es_shiny = (random.randint(1, 50) == 1)
        es_legendario = species.get('is_legendary', False)
        
        # --- AQUÍ OBTENEMOS EL CAPTURE_RATE ---
        # Si la API no lo tiene, por defecto ponemos 45 (estándar)
        capture_rate = species.get('capture_rate', 45)
        
        etiquetas = []
        if es_shiny: etiquetas.append("✨ SHINY")
        if es_legendario: etiquetas.append("👑 LEGENDARIO")
        
        titulo_revelado = f"¡Es un {data['name'].capitalize()} salvaje!"
        if etiquetas: 
            titulo_revelado = f"{' '.join(etiquetas)} {titulo_revelado}"
            
        color_embed = discord.Color.gold() if (es_shiny or es_legendario) else discord.Color.green()
        embed_revelado = discord.Embed(title=titulo_revelado, color=color_embed)
        
        if es_shiny:
            url_imagen = data['sprites']['other']['official-artwork']['front_shiny']
        else:
            url_imagen = data['sprites']['other']['official-artwork']['front_default']
        
        embed_revelado.set_image(url=url_imagen)
        embed_revelado.set_footer(text="Intentos fallidos: 0/20")
        
        # --- AQUÍ ESTÁ LA CORRECCIÓN ---
        # Pasamos el capture_rate que acabamos de extraer
        view_captura = BotonCaptura(
            pokemon_data=data, 
            es_legendario=es_legendario, 
            es_shiny=es_shiny, 
            capture_rate=capture_rate
        )
        
        await interaction.response.edit_message(embed=embed_revelado, attachments=[], view=view_captura)

    # --- BOTONES DE LA INTERFAZ ---
    @discord.ui.button(label="[1] Opción 1", style=discord.ButtonStyle.primary)
    async def btn_opcion_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.manejar_seleccion(interaction, 0)

    @discord.ui.button(label="[2] Opción 2", style=discord.ButtonStyle.primary)
    async def btn_opcion_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.manejar_seleccion(interaction, 1)

    @discord.ui.button(label="[3] Opción 3", style=discord.ButtonStyle.primary)
    async def btn_opcion_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.manejar_seleccion(interaction, 2)

# Configuración de logs solicitada
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger('bot_captura') # Opcional: Nombre para identificar el log

import discord
import math
import random
from logger_config import log

class BotonCaptura(discord.ui.View):
    def __init__(self, pokemon_data, es_legendario, es_shiny, capture_rate):
        super().__init__(timeout=300.0)
        self.nombre = pokemon_data['name']
        self.es_legendario = es_legendario
        self.es_shiny = es_shiny
        self.capture_rate = capture_rate # Valor R de la API
        self.intentos_fallidos = 0
        self.max_intentos = 20
        self.user_cooldowns = {}
        self.alguien_lo_atrapo = False

    def _segundos_restantes_cooldown(self, user_id, ahora):
        ultimo = self.user_cooldowns.get(user_id)
        if ultimo is None:
            return 0.0
        return COOLDOWN_LANZAMIENTO - (ahora - ultimo)

    async def on_timeout(self):
        gestor_spawn.canales_ocupados.discard(self.message.channel.id)
        try:
            await self.message.edit(content="💨 El encuentro expiró.", view=None)
        except:
            pass

    @discord.ui.button(label="¡Lanzar Pokéball!", style=discord.ButtonStyle.primary, emoji="🔴")
    async def boton_captura(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.alguien_lo_atrapo:
            return await interaction.response.send_message("💨 ¡Llegaste tarde! Alguien más fue más rápido.", ephemeral=True)

        try:
            user_id = interaction.user.id
            ahora = discord.utils.utcnow().timestamp()

            restante = self._segundos_restantes_cooldown(user_id, ahora)
            if restante > COOLDOWN_GRACE:
                segundos = max(1, math.ceil(restante))
                return await interaction.response.send_message(f"⏱️ Espera {segundos}s para volver a lanzar.", ephemeral=True)

            self.user_cooldowns[user_id] = ahora
            await interaction.response.defer(ephemeral=True)

            # --- MATEMÁTICA DE CAPTURA AJUSTADA ---
            azar = random.random()
            
            # Asignación de bolas
            if azar < 0.01: bonus_bola, nombre_bola = 255.0, "Master Ball"
            elif azar < 0.15: bonus_bola, nombre_bola = 2.0, "Ultra Ball"
            elif azar < 0.40: bonus_bola, nombre_bola = 1.5, "Great Ball"
            else: bonus_bola, nombre_bola = 1.0, "Pokéball"

            # --- CORRECCIÓN: LÓGICA DE MASTER BALL ---
            if nombre_bola == "Master Ball":
                prob_final = 1.0  # 100% de éxito garantizado
            else:
                # La fórmula de dificultad normal para las otras bolas
                FACTOR_DIFICULTAD = 0.7 
                FACTOR_DESGASTE = 0.008
                prob_base = ((self.capture_rate / 255) * bonus_bola) * FACTOR_DIFICULTAD
                prob_final = prob_base + (self.intentos_fallidos * FACTOR_DESGASTE)
                prob_final = min(prob_final, 0.95) # El tope sigue aplicando solo a las normales

            # --- INTENTO DE CAPTURA ---
            if random.random() < prob_final:
                self.alguien_lo_atrapo = True 
                
                try:
                    await database.guardar_captura(user_id, self.nombre, self.es_shiny, pokeball=nombre_bola)
                    gestor_spawn.canales_ocupados.discard(interaction.channel.id)

                    log.info(f"✅ [Captura] {interaction.user.name} atrapó a {self.nombre} con {nombre_bola}.")

                    await interaction.message.edit(
                        content=f"🎉 {interaction.user.mention} capturó a **{self.nombre.capitalize()}** usando una **{nombre_bola}**!", 
                        view=None
                    )
                    self.stop()
                except Exception as db_error:
                    self.alguien_lo_atrapo = False
                    log.error(f"Error de BD: {db_error}", exc_info=True)
                    await interaction.followup.send("⚠️ Error interno. ¡Inténtalo de nuevo!", ephemeral=True)

            else:
                self.intentos_fallidos += 1
                if self.intentos_fallidos >= self.max_intentos:
                    self.alguien_lo_atrapo = True
                    gestor_spawn.canales_ocupados.discard(interaction.channel.id)
                    await interaction.message.edit(content="💨 ¡El Pokémon escapó tras fallar demasiadas veces!", view=None)
                    self.stop()
                else:
                    embed = interaction.message.embeds[0]
                    embed.set_footer(text=f"Intentos: {self.intentos_fallidos}/{self.max_intentos}")
                    await interaction.message.edit(embed=embed)
                    await interaction.followup.send(f"❌ Lanzaste una {nombre_bola} pero fallaste. ¡El Pokémon está más cansado!", ephemeral=True)

        except Exception as e:
            log.error(f"🚨 Error crítico en captura: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message("⚠️ Error inesperado.", ephemeral=True)
            else:
                await interaction.followup.send("⚠️ Error inesperado.", ephemeral=True)
class InfoView(discord.ui.View):
    def __init__(self, user_id, data, versiones, mostrar_shiny): # Agregamos user_id
        super().__init__(timeout=60)
        self.user_id = user_id
        self.data = data
        self.versiones = versiones
        self.mostrar_shiny = mostrar_shiny
        
        # Desactivamos el botón si no tiene ambas versiones
        if 0 not in versiones or 1 not in versiones:
            for item in self.children:
                if item.custom_id == "boton_cambiar":
                    item.disabled = True


    def crear_embed(self):
            poke_id = self.data['id']
            if self.mostrar_shiny:
                url_grande = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/{poke_id}.png"
                url_sprite = self.data['sprites']['front_shiny']
            else:
                url_grande = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke_id}.png"
                url_sprite = self.data['sprites']['front_default']
                
            titulo = f"{self.data['name'].capitalize()} {'✨ Shiny' if self.mostrar_shiny else ''}"
            
            # 1. Obtenemos datos de DB
            fecha_primera, cantidad = database.obtener_info_captura(self.user_id, self.data['name'])
            
            # 2. Formateamos fecha de forma segura
            fecha_str = "N/A"
            if isinstance(fecha_primera, datetime.datetime):
                # Convierte el objeto fecha a formato YYYY-MM-DD
                fecha_str = fecha_primera.strftime('%Y-%m-%d')
            elif isinstance(fecha_primera, str) and fecha_primera != 'Desconocido':
                # Si por casualidad llega como texto, intentamos el split original
                fecha_str = fecha_primera.split()[0]
            
            # 3. Construimos el texto base
            info_text = f"✨ **Tipo:** {', '.join([t['type']['name'].capitalize() for t in self.data['types']])}\n"
            info_text += f"📅 **Primera captura:** {fecha_str}\n"
            info_text += f"🔢 **Total capturados:** {cantidad}\n"
            info_text += f"📏 **Altura:** {self.data['height']/10}m | ⚖️ **Peso:** {self.data['weight']/10}kg\n"
            
            # ... (el resto de tu código igual)
            
            # 4. Creamos el Embed
            embed = discord.Embed(title=titulo, color=discord.Color.dark_grey())
            embed.set_image(url=url_grande)
            embed.set_thumbnail(url=url_sprite)
            
            # 5. Añadimos el campo de Detalles Generales
            embed.add_field(name="📋 Detalles Generales", value=info_text, inline=False)
            
            # 6. Añadimos las estadísticas
            stats_text = ""
            for stat in self.data['stats']:
                stats_text += f"`{stat['stat']['name'].capitalize():<15}: {stat['base_stat']:<3}`\n"
            
            embed.add_field(name="📊 Estadísticas Base", value=stats_text, inline=False)
            
            return embed

    async def enviar_embed(self, ctx):
        await ctx.send(embed=self.crear_embed(), view=self)

    @discord.ui.button(label="Cambiar Versión", style=discord.ButtonStyle.secondary, custom_id="boton_cambiar")
    async def boton_cambiar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mostrar_shiny = not self.mostrar_shiny
        await interaction.response.edit_message(embed=self.crear_embed(), view=self)
class SeleccionInicialView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.index = 0

    def get_embed(self):
        poke = INICIALES[self.index]
        embed = discord.Embed(title=f"Elige a tu inicial: {poke['nombre']}", color=discord.Color.green())
        # Usamos la URL oficial de imágenes de Pokémon
        embed.set_image(url=f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke['id']}.png")
        embed.set_footer(text=f"Pokémon {self.index + 1} de {len(INICIALES)}")
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index - 1) % len(INICIALES)
        await interaction.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="¡Lo elijo a él!", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        poke = INICIALES[self.index]
        import database
        import datetime
        
        conn = database.get_connection()
        cursor = conn.cursor()

        if os.environ.get('DATABASE_URL'):
            # Lógica para PostgreSQL
            # 'ON CONFLICT DO NOTHING' equivale al 'INSERT OR IGNORE' de SQLite
            cursor.execute("""
                INSERT INTO iniciacion (user_id, recibio_inicial) 
                VALUES (%s, 1) 
                ON CONFLICT(user_id) DO NOTHING
            """, (str(self.user_id),))
        else:
            # Lógica para SQLite
            cursor.execute("INSERT OR IGNORE INTO iniciacion (user_id, recibio_inicial) VALUES (?, 1)", (self.user_id,))

        conn.commit()
        conn.close()
        
        # 2. Guardar inicial en capturas
        await database.guardar_captura(self.user_id, poke['nombre'], es_shiny=False, pokeball='Pokéball')
        
        # 3. INICIALIZAR ENERGÍA EN LA BASE DE DATOS (Persistente)
        # Usamos la función de base de datos directamente
        database.actualizar_energia_db(self.user_id, 12, datetime.datetime.now())
        
        await interaction.response.edit_message(
            content=f"🎉 ¡Felicidades! Has elegido a **{poke['nombre']}**. ¡Tu aventura comienza ahora!", 
            embed=None, 
            view=None
        )

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index + 1) % len(INICIALES)
        await interaction.response.edit_message(embed=self.get_embed())
async def liberar_canal(channel_id):
    import gestor_spawn
    gestor_spawn.canales_ocupados.discard(ctx.channel.id)
