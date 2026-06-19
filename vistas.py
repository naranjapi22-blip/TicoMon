import asyncio
import gestor_spawn
import traceback
import discord
import random
import math
import logging
import database
import sqlite3
from datetime import datetime, timezone
import os
import gestor_spawn
import servicios
from logger_config import log
from pathlib import Path
from captura_imagen import (
    generar_imagen_captura
)
from mapeo_pokes import obtener_id_gif # Asegúrate de tener este import al inicio del archivo
import records  # Importa tu archivo de lógica de récords
COOLDOWN_LANZAMIENTO = 10.0
COOLDOWN_GRACE = 0.25





def liberar_canal_completo(channel_id):
    import gestor_spawn

    gestor_spawn.canales_ocupados.discard(
        channel_id
    )

    if hasattr(
        gestor_spawn,
        "vistas_activas"
    ):
        gestor_spawn.vistas_activas.pop(
            channel_id,
            None
        )

    task = gestor_spawn.tareas_limpieza.pop(
        channel_id,
        None
    )

    if task:
        task.cancel()

    log.info(
        f"🟢 Canal liberado: {channel_id}"
    )

    if task:
        task.cancel()

        log.info(
            f"🧹 Tarea de limpieza cancelada: {channel_id}"
        )

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
        # 1. DIFERIR LA INTERACCIÓN: Evita el error de "Unknown Interaction"
        await interaction.response.defer()

        self.view.filtro_actual = self.values[0]
        self.view.pagina = 0
        
        # 2. Lógica de filtrado
        ids_filtrados = await servicios.filtrar_capturas_por_tipo(
            interaction.client.session, self.view.filtro_actual, self.tenidos
        )
        
        self.view.total_pokes = ids_filtrados
        
        if not ids_filtrados:
            self.view.paginas = []
        else:
            self.view.paginas = [ids_filtrados[i:i + 10] for i in range(0, len(ids_filtrados), 10)]
        
        await self.view.generar_vista_pokedex(interaction, interaction.client.session)

# --- CLASE PRINCIPAL DE POKEDEX ---
class PokedexView(discord.ui.View):
    def __init__(self, region, tenidos, inicio=1, fin=1025, es_coleccion_personal=False, modo_shiny=False):
        super().__init__(timeout=60)
        self.region = region
        self.tenidos = sorted(list(tenidos))
        self.es_coleccion_personal = es_coleccion_personal
        self.modo_shiny = modo_shiny  # Guardamos el modo
        self.filtro_actual = "all"
        
        if self.es_coleccion_personal:
            self.total_pokes = self.tenidos
        else:
            self.total_pokes = list(range(inicio, fin + 1))
            
        self.paginas = [self.total_pokes[i:i + 10] for i in range(0, len(self.total_pokes), 10)]
        self.pagina = 0
        
        # self.add_item(TipoSelect(self.tenidos)) # Asegúrate de tener esta clase definida

class PokedexView(discord.ui.View):
    def __init__(self, region, tenidos, inicio=1, fin=1025, es_coleccion_personal=False, modo_shiny=False):
        super().__init__(timeout=60)
        self.region = region
        self.tenidos = sorted(list(tenidos))
        self.es_coleccion_personal = es_coleccion_personal
        self.modo_shiny = modo_shiny
        self.filtro_actual = "All" # Valor por defecto
        
        if self.es_coleccion_personal:
            self.total_pokes = self.tenidos
        else:
            self.total_pokes = list(range(inicio, fin + 1))
            
        self.paginas = [self.total_pokes[i:i + 10] for i in range(0, len(self.total_pokes), 10)]
        self.pagina = 0

    async def generar_vista_pokedex(self, interaction_or_ctx, session):
        # 1. CASO: LISTA VACÍA
        if not self.total_pokes:
            embed = discord.Embed(
                title=f"🎒 Colección | {'Shiny ' if self.modo_shiny else ''}Tipo: {self.filtro_actual.capitalize()}",
                description="¡No tienes Pokémon de ese tipo!"
            )
            
            if isinstance(interaction_or_ctx, discord.Interaction):
                if interaction_or_ctx.response.is_done():
                    await interaction_or_ctx.followup.edit_message(message_id=interaction_or_ctx.message.id, embed=embed, attachments=[], view=self)
                else:
                    await interaction_or_ctx.response.edit_message(embed=embed, attachments=[], view=self)
            else:
                await interaction_or_ctx.send(embed=embed, view=self)
            return

        # 2. CASO: LISTA CON DATOS
        ids_actuales = self.paginas[self.pagina]
        
        # Corrección: Definimos la ruta dependiendo del modo
        sub_path = "shiny/" if self.modo_shiny else ""
        url_base = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{sub_path}"
        
        data_pokes = [(i, f"{url_base}{i}.png") for i in ids_actuales]
        
        # Se pasa modo_shiny a la función para que el servicio sepa qué procesar
        buffer = await servicios.generar_collage(session, data_pokes, self.tenidos, es_shiny=self.modo_shiny)
        file = discord.File(buffer, filename="pokedex.png")
        
        embed = discord.Embed(
            title=f"🎒 Colección | {'Shiny ' if self.modo_shiny else ''}Tipo: {self.filtro_actual.capitalize()}", 
            description=f"Página {self.pagina + 1}/{max(1, len(self.paginas))}"
        )
        embed.set_image(url="attachment://pokedex.png")
        
        # 3. EDICIÓN ROBUSTA
        if isinstance(interaction_or_ctx, discord.Interaction):
            if interaction_or_ctx.response.is_done():
                await interaction_or_ctx.followup.edit_message(
                    message_id=interaction_or_ctx.message.id, 
                    embed=embed, 
                    attachments=[file], 
                    view=self
                )
            else:
                await interaction_or_ctx.response.edit_message(
                    embed=embed, 
                    attachments=[file], 
                    view=self
                )
        else:
            await interaction_or_ctx.send(embed=embed, file=file, view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina = (self.pagina - 1) % max(1, len(self.paginas))
        await self.generar_vista_pokedex(interaction, interaction.client.session)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina = (self.pagina + 1) % max(1, len(self.paginas))
        await self.generar_vista_pokedex(interaction, interaction.client.session)
def obtener_rareza(capture_rate):
    if capture_rate >= 225:
        return "muy_comun"
    elif capture_rate >= 150:
        return "comun"
    elif capture_rate >= 90:
        return "poco_comun"
    elif capture_rate >= 45:
        return "raro"
    elif capture_rate >= 20:
        return "epico"
    elif capture_rate >= 5:
        return "mitico"
    else:
        return "legendario"
class SpawnSelectionView(discord.ui.View):
    def __init__(self, data_pokes, autor_original):
        super().__init__(timeout=180) # Tienen 60 segundos para elegir
        self.data_pokes = data_pokes 
        self.autor_original = autor_original 
        self.message = None # <-- Añadimos esto para guardar el mensaje y poder editarlo al final

    async def on_timeout(self):
        # 1. Desactivamos los botones siempre
        for child in self.children:
            child.disabled = True
            
        
        # 2. Seguridad: Intentamos editar el mensaje solo si existe
        if hasattr(self, 'message') and self.message:
            try:
                # Actualizamos el embed original a modo "Huida"
                if self.message.embeds:
                    embed_huida = self.message.embeds[0]
                    embed_huida.title = "💨 ¡Los Pokémon salvajes huyeron!"
                    embed_huida.description = "Tardaste demasiado en decidir y escaparon."
                    embed_huida.color = discord.Color.red()
                    
                    # Editamos el mensaje con el embed modificado y los botones deshabilitados
                    await self.message.edit(embed=embed_huida, view=self)
            
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"Error al editar mensaje en on_timeout: {e}")
            
            # 3. Liberamos el canal usando el ID del mensaje vinculado
            gestor_spawn.canales_ocupados.discard(self.message.channel.id)
            # Limpiamos la referencia de la vista si implementaste el diccionario de control
            gestor_spawn.vistas_activas.pop(self.message.channel.id, None)

        else:
            # CASO DE EMERGENCIA: Si no hay mensaje, intentamos limpiar 
            print("on_timeout: No se pudo liberar el canal automáticamente (falta referencia self.message).")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:

        if interaction.user != self.autor_original:

            try:
                await interaction.response.send_message(
                    "¡Hey! 🛑 Consigue tu propio Pokémon usando `!spawn`. Este encuentro no es tuyo.",
                    ephemeral=True
                )
            except discord.InteractionResponded:
                try:
                    await interaction.followup.send(
                        "¡Hey! 🛑 Consigue tu propio Pokémon usando `!spawn`. Este encuentro no es tuyo.",
                        ephemeral=True
                    )
                except discord.NotFound:
                    pass

            return False

        return True

    # --- SE ELIMINÓ LA FUNCIÓN 'boton_captura' DE AQUÍ (Pertenece a la clase BotonCaptura) ---

    # --- MANEJO DE LA SELECCIÓN ---
    async def manejar_seleccion(
        self,
        interaction: discord.Interaction,
        indice: int
    ):

        # Validación defensiva
        if indice < 0 or indice >= len(self.data_pokes):

            try:
                await interaction.response.send_message(
                    "❌ Esta opción ya no está disponible.",
                    ephemeral=True
                )
            except discord.InteractionResponded:
                pass

            return

        # Evita doble clic
        self.stop()

        for child in self.children:
            child.disabled = True

        # Datos del Pokémon elegido
        data, species, es_shiny, rareza = self.data_pokes[indice]

        from mapeo_pokes import obtener_id_gif

        dex_id = data['id']
        id_final = obtener_id_gif(dex_id)

        R2_PUBLIC_URL = "https://pub-23cb564f6c174627926c1ac0409563d4.r2.dev"

        path_folder = "shiny" if es_shiny else "regular"

        url_gif = (
            f"{R2_PUBLIC_URL}/"
            f"{path_folder}/{id_final}.gif"
        )
        # Variables para captura
        es_legendario = species.get('is_legendary', False)
        capture_rate = species.get('capture_rate', 45)
        tamano_factor = round(random.uniform(0.50, 1.50), 2)

        etiquetas = []
        if es_shiny:
            etiquetas.append("✨ SHINY")
        if es_legendario:
            etiquetas.append("👑 LEGENDARIO")

        rareza = obtener_rareza(capture_rate)

        titulo_revelado = f"¡Es un {data['name'].capitalize()} salvaje!"
        if etiquetas:
            titulo_revelado = f"{' '.join(etiquetas)} {titulo_revelado}"

        color_embed = (
            discord.Color.gold()
            if (es_shiny or es_legendario)
            else discord.Color.green()
        )

        embed_revelado = discord.Embed(
            title=titulo_revelado,
            description=f"**Rareza:** {obtener_nombre_rareza(rareza)}",
            color=color_embed
        )

        embed_revelado.set_image(url=url_gif)
        embed_revelado.set_footer(text="Intentos fallidos: 0")

        view_captura = BotonCaptura(
            pokemon_data=data,
            rareza=rareza,
            es_shiny=es_shiny,
            capture_rate=capture_rate,
            tamano_factor=tamano_factor
        )

        # Editar el mensaje original
        await interaction.response.edit_message(
            embed=embed_revelado,
            attachments=[],
            view=view_captura
        )

    # --- BOTONES ---
    @discord.ui.button(label="[1] Opción 1", style=discord.ButtonStyle.primary)
    async def opcion1(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.manejar_seleccion(interaction, 0)

    @discord.ui.button(label="[2] Opción 2", style=discord.ButtonStyle.primary)
    async def opcion2(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.manejar_seleccion(interaction, 1)

    @discord.ui.button(label="[3] Opción 3", style=discord.ButtonStyle.primary)
    async def opcion3(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.manejar_seleccion(interaction, 2)


class BotonCaptura(discord.ui.View):
    def __init__(
        self,
        pokemon_data,
        rareza,
        es_shiny,
        capture_rate,
        tamano_factor
    ):
        super().__init__(timeout=300.0)

        self.lock_captura = asyncio.Lock()
        self.message = None

        self.pokemon_id = pokemon_data["id"]

        self.nombre = pokemon_data["name"]
        self.rareza = rareza
        self.es_shiny = es_shiny
        self.capture_rate = capture_rate
        self.tamano_factor = tamano_factor

        self.usuario_capturador = None
        self.tiempo_aparicion = datetime.now(timezone.utc)
        self.intentos_fallidos = 0
        self.user_cooldowns = {}
        self.alguien_lo_atrapo = False

    async def on_timeout(self):
        if self.alguien_lo_atrapo:
            return

        for child in self.children:
            child.disabled = True
        
        try:
            if self.message:
                await self.message.edit(content="💨 ¡El Pokémon se cansó de esperar y ha huido!", view=self)
        except:
            pass
        
        import gestor_spawn
        gestor_spawn.canales_ocupados.discard(self.message.channel.id if self.message else 0)
        self.stop()

    def _segundos_restantes_cooldown(self, user_id, ahora):
        ultimo = self.user_cooldowns.get(user_id)
        if ultimo is None:
            return 0.0
        return COOLDOWN_LANZAMIENTO - (ahora - ultimo)

    @discord.ui.button(
        label="¡Lanzar Pokéball!",
        style=discord.ButtonStyle.primary,
        emoji="🔴"
    )
    async def boton_captura(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        async with self.lock_captura:

            # 1. EL ESCUDO: Va de primerito
            if interaction.response.is_done():
                return

            # 2. Llegó tarde
            if self.alguien_lo_atrapo:

                try:

                    if interaction.user.id == self.usuario_capturador:

                        await interaction.response.send_message(
                            "✅ Ya capturaste este Pokémon.",
                            ephemeral=True
                        )

                    else:

                        await interaction.response.send_message(
                            "💨 ¡Llegaste tarde!",
                            ephemeral=True
                        )

                except discord.NotFound:
                    pass

                return
            # 3. Reservamos la interacción
            try:

                await interaction.response.defer(ephemeral=True)
            except (
                discord.NotFound,
                discord.errors.InteractionResponded
            ):
                return
                
            try:
                self.message = interaction.message # Aseguramos referencia
                user_id = interaction.user.id
                ahora = discord.utils.utcnow().timestamp()

                restante = self._segundos_restantes_cooldown(user_id, ahora)
                if restante > COOLDOWN_GRACE:
                    segundos = max(1, math.ceil(restante))
                    return await interaction.followup.send(f"⏱️ Espera {segundos}s para volver a lanzar.", ephemeral=True)

                self.user_cooldowns[user_id] = ahora
                

                # --- LÓGICA DE SEGURIDAD (Timer y Huída) ---
                tiempo_pasado = (datetime.now(timezone.utc) - self.tiempo_aparicion).total_seconds()
                
                if tiempo_pasado > 300:
                    self.alguien_lo_atrapo = True
                    self.usuario_capturador = interaction.user.id
                    liberar_canal_completo(interaction.channel.id)
                    await interaction.message.edit(content="💨 ¡El tiempo se ha agotado! El Pokémon ha huido.", view=None)
                    return self.stop()

                if self.intentos_fallidos > 30:
                    if random.random() < (self.intentos_fallidos * 0.003):
                        self.alguien_lo_atrapo = True
                        self.usuario_capturador = interaction.user.id
                        liberar_canal_completo(interaction.channel.id)
                        await interaction.message.edit(content="💨 ¡El Pokémon se ha asustado y ha huido!", view=None)
                        return self.stop()

                # --- MATEMÁTICA DE CAPTURA (INTEGRANDO TUS % BASE) ---
                azar = random.random()
                if azar < 0.002: bonus_bola, nombre_bola = 255.0, "Master Ball" # Rareza ajustada
                elif azar < 0.10: bonus_bola, nombre_bola = 1.4, "Ultra Ball"    # Nerfeada
                elif azar < 0.30: bonus_bola, nombre_bola = 1.20, "Great Ball"   # Nerfeada
                else: bonus_bola, nombre_bola = 1.0, "Pokéball"

                multiplicador_shiny = 1.0 

                if nombre_bola == "Master Ball":
                    prob_final = 1.0

                else:
                    
                    if self.rareza == "muy_comun":
                        base_pct = 0.10

                    elif self.rareza == "comun":
                        base_pct = 0.07

                    elif self.rareza == "poco_comun":
                        base_pct = 0.05

                    elif self.rareza == "raro":
                        base_pct = 0.03

                    elif self.rareza == "epico":
                        base_pct = 0.015

                    elif self.rareza == "mitico":
                        base_pct = 0.005

                    elif self.rareza == "legendario":
                        base_pct = 0.002

                    else:
                        log.warning(f"⚠️ Rareza desconocida: [{self.rareza}]")
                        base_pct = 0.04

                    # Bono de bola
                    prob_con_bola = (
                        base_pct *
                        ((self.capture_rate / 255.0) ** 0.5)
                    ) * bonus_bola

                    # Desgaste
                    if self.rareza == "legendario":
                        FACTOR_DESGASTE = 0.002

                    elif self.rareza == "mitico":
                        FACTOR_DESGASTE = 0.003

                    elif self.rareza == "epico":
                        FACTOR_DESGASTE = 0.005

                    elif self.rareza == "raro":
                        FACTOR_DESGASTE = 0.008

                    elif self.rareza == "poco_comun":
                        FACTOR_DESGASTE = 0.010

                    elif self.rareza == "comun":
                        FACTOR_DESGASTE = 0.015

                    else:
                        FACTOR_DESGASTE = 0.020

                    prob_final = prob_con_bola + (
                        self.intentos_fallidos * FACTOR_DESGASTE
                    )

                    TOPE_MAXIMO = 0.30 if (
                        self.es_shiny or
                        self.rareza == "legendario" or
                        self.rareza == "mitico"
                    ) else 0.45

                    prob_final = min(prob_final, TOPE_MAXIMO)

                porcentaje = f"{max(0, prob_final * 100):.2f}"

                # --- INTENTO DE CAPTURA ---
                if random.random() < prob_final:

                    try:

                        # RESERVAR EL POKÉMON ANTES DE GUARDAR
                        self.alguien_lo_atrapo = True
                        self.usuario_capturador = interaction.user.id

                        id_captura, resultado_record = (
                            await database.guardar_captura(
                                user_id=user_id,
                                pokemon_nombre=self.nombre,
                                tamano_factor=self.tamano_factor,
                                es_shiny=self.es_shiny,
                                pokeball=nombre_bola
                            )
                        )
                        print(
                            f"POKEMON ID: {self.pokemon_id}"
                        )
                        trainer = await database.obtener_trainer(
                            interaction.user.id
                        )
                        buffer_captura = await generar_imagen_captura(
                            trainer=trainer,
                            pokemon_id=self.pokemon_id,
                            es_shiny=self.es_shiny,
                            jugador=interaction.user.display_name,
                            pokemon=self.nombre
                        )
                        if trainer:

                            ruta_trainer = (
                                Path("sprites/trainers")
                                / f"{trainer}.png"
                            )

                            if ruta_trainer.exists():

                                await interaction.channel.send(
                                    file=discord.File(
                                        ruta_trainer,
                                        filename="trainer.png"
                                    )
                                )

                        liberar_canal_completo(
                            interaction.channel.id
                        )

                        mensaje = (
                            f"🎉 {interaction.user.mention} "
                            f"capturó a **{self.nombre.capitalize()}** "
                            f"(ID: {id_captura}) usando una "
                            f"**{nombre_bola}**! ({porcentaje}%)"
                        )

                        if resultado_record == "NUEVO_RECORD_GRANDE":

                            mensaje += (
                                "\n👑 **¡Nuevo Récord XXL!** "
                                "Has entrado en el Salón de la Fama."
                            )

                        elif resultado_record == "NUEVO_RECORD_PEQUENO":

                            mensaje += (
                                "\n🤏 **¡Nuevo Récord XXS!** "
                                "Has entrado en el Salón de la Fama."
                            )

                        await interaction.message.edit(
                            content=mensaje,
                            attachments=[
                                discord.File(
                                    buffer_captura,
                                    filename="captura.png"
                                )
                            ],
                            view=None
                        )

                        self.stop()

                    except Exception as db_error:

                        # SI FALLA LA BD LIBERAMOS LA RESERVA
                        self.alguien_lo_atrapo = False
                        self.usuario_capturador = None

                        log.error(
                            f"Error BD: {db_error}",
                            exc_info=True
                        )

                        await interaction.followup.send(
                            "⚠️ Error interno de base de datos.",
                            ephemeral=True
                        )
                else:

                    # Liberar reserva
                    self.alguien_lo_atrapo = False
                    self.usuario_capturador = None

                    self.intentos_fallidos += 1

                    embed = interaction.message.embeds[0]
                    embed.set_footer(
                        text=f"Intentos fallidos: {self.intentos_fallidos}"
                    )

                    await interaction.message.edit(embed=embed)

                    await interaction.followup.send(
                        f"❌ Fallaste la {nombre_bola} con un ({porcentaje}%). ¡El Pokémon está más cansado!",
                        ephemeral=True
                    )

            except Exception as e:

                liberar_canal_completo(interaction.channel.id)
                gestor_spawn.canales_ocupados.discard(interaction.channel.id)

                self.alguien_lo_atrapo = False
                self.usuario_capturador = None
                log.error(
                    f"🚨 Error crítico en captura: {e}",
                    exc_info=True
                )

                print("========== TRACEBACK COMPLETO ==========")
                traceback.print_exc()
                print("========================================")

                try:
                    await interaction.followup.send(
                        "⚠️ El encuentro ha finalizado debido a un error.",
                        ephemeral=True
                    )
                except discord.NotFound:
                    pass

                self.stop()
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
            url_grande = (
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/"
                f"sprites/pokemon/other/official-artwork/shiny/{poke_id}.png"
            )

            url_sprite = (
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/"
                f"sprites/pokemon/shiny/{poke_id}.png"
            )

        else:

            url_grande = (
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/"
                f"sprites/pokemon/other/official-artwork/{poke_id}.png"
            )

            url_sprite = (
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/"
                f"sprites/pokemon/{poke_id}.png"
            )
                    
        titulo = f"{self.data['nombre'].capitalize()} {'✨ Shiny' if self.mostrar_shiny else ''}"
        
        # 1. Obtenemos datos de DB (ahora recibimos los tres valores)
        fecha_primera, cantidad, lista_ids = database.obtener_info_captura(
            self.user_id,
            self.data['nombre']
        )
        
        # 2. Formateamos fecha de forma segura
        fecha_str = "N/A"
        try:
            if isinstance(fecha_primera, datetime):
                fecha_str = fecha_primera.strftime('%Y-%m-%d')
            elif isinstance(fecha_primera, str):
                # Limpieza extra: si es un string, intentamos obtener solo la fecha
                # y filtramos valores inválidos
                if fecha_primera.lower() not in ['desconocido', 'n/a', 'none']:
                    fecha_str = fecha_primera.split()[0]
        except Exception as e:
            # Si algo falla (ej. el formato de fecha es rarísimo), 
            # mantendremos "N/A" en lugar de crashear el bot
            print(f"⚠️ Error formateando fecha: {e}")
            fecha_str = "N/A"
        # 3. Formateamos los IDs de captura (mostrando los últimos 8 para no saturar)
        if lista_ids:
            if len(lista_ids) > 8:
                ids_formateados = ", ".join([f"#{id_cap}" for id_cap in lista_ids[-8:]]) + "..."
            else:
                ids_formateados = ", ".join([f"#{id_cap}" for id_cap in lista_ids])
        else:
            ids_formateados = "Ninguno"
        
        # 4. Construimos el texto base
        tipos = ", ".join(
            t.capitalize()
            for t in self.data["tipos"].split(",")
        )

        info_text = f"✨ **Tipo:** {tipos}\n"
        info_text += f"📅 **Primera captura:** {fecha_str}\n"
        info_text += f"🔢 **Total capturados:** {cantidad}\n"
        info_text += f"🆔 **IDs de captura:** {ids_formateados}\n"
        info_text += f"📏 **Altura:** {self.data['height']/10}m | ⚖️ **Peso:** {self.data['weight']/10}kg\n"
        
        # 5. Creamos el Embed
        embed = discord.Embed(title=titulo, color=discord.Color.dark_grey())
        embed.set_image(url=url_grande)
        embed.set_thumbnail(url=url_sprite)
        
        # 6. Añadimos campo de Detalles Generales
        embed.add_field(name="📋 Detalles Generales", value=info_text, inline=False)
        
        # 7. Añadimos las estadísticas
        stats_text = (
            f"`HP             : {self.data['hp']}`\n"
            f"`Attack         : {self.data['attack']}`\n"
            f"`Defense        : {self.data['defense']}`\n"
            f"`Sp. Attack     : {self.data['special_attack']}`\n"
            f"`Sp. Defense    : {self.data['special_defense']}`\n"
            f"`Speed          : {self.data['speed']}`"
        )
                
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
        await database.guardar_captura(
            self.user_id,
            poke['nombre'],
            tamano_factor=1.0,
            es_shiny=False,
            pokeball='Pokéball'
        )
        
        # 3. INICIALIZAR ENERGÍA EN LA BASE DE DATOS (Persistente)
        # Usamos la función de base de datos directamente
        await database.actualizar_energia_db(
            interaction.client,
            self.user_id,
            12,
            datetime.now(timezone.utc)
        )
        
        await interaction.response.edit_message(
            content=f"🎉 ¡Felicidades! Has elegido a **{poke['nombre']}**. ¡Tu aventura comienza ahora!", 
            embed=None, 
            view=None
        )

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index + 1) % len(INICIALES)
        await interaction.response.edit_message(embed=self.get_embed())
def obtener_nombre_rareza(rareza):
    nombres = {
        "muy_comun": "Muy Común 🟢",
        "comun": "Común ⚪",
        "poco_comun": "Poco Común 🔵",
        "raro": "Raro 🟣",
        "epico": "Épico 🔴",
        "mitico": "Mítico 🟡",
        "legendario": "Legendario 👑"
    }
    return nombres.get(rareza, rareza)

