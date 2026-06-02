import discord
import sqlite3
import database
import servicios
import psycopg2
import os

# --- 1. MEMORIA DE SEGURIDAD (Evita la clonación) ---
usuarios_ocupados = set()

# --- 2. LÓGICA DE TRANSFERENCIA SEGURA ---
async def transferir_pokemon_seguro(user_de, user_para, nombre, es_shiny):
    """Busca un único Pokémon en el inventario y le cambia el dueño."""
    # Usamos el candado compartido para evitar condiciones de carrera
    async with database.db_lock:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Detectamos si estamos en Postgres para usar la sintaxis correcta
        is_postgres = os.environ.get('DATABASE_URL') is not None
        
        # 1. Buscamos el ID exacto
        if is_postgres:
            cursor.execute('''
                SELECT id FROM capturas 
                WHERE user_id = %s AND pokemon_nombre = %s AND es_shiny = %s 
                LIMIT 1
            ''', (str(user_de), nombre.lower(), 1 if es_shiny else 0))
        else:
            cursor.execute('''
                SELECT id FROM capturas 
                WHERE user_id = ? AND pokemon_nombre = ? AND es_shiny = ? 
                LIMIT 1
            ''', (user_de, nombre.lower(), 1 if es_shiny else 0))
        
        resultado = cursor.fetchone()
        
        exito = False
        if resultado:
            id_captura = resultado[0]
            # 2. Actualizamos al nuevo dueño
            if is_postgres:
                cursor.execute('UPDATE capturas SET user_id = %s WHERE id = %s', (str(user_para), id_captura))
            else:
                cursor.execute('UPDATE capturas SET user_id = ? WHERE id = ?', (user_para, id_captura))
            
            conn.commit()
            exito = True
            
        conn.close()
        return exito

# --- 3. MODAL (Pop-up para escribir la oferta) ---
class ModalOferta(discord.ui.Modal, title='Elige tu Pokémon para ofrecer'):
    oferta = discord.ui.TextInput(
        label='Nombre del Pokémon (Añade "shiny" si lo es)',
        placeholder='Ejemplo: charizard o charizard shiny',
        required=True
    )

    def __init__(self, view, jugador_id):
        super().__init__()
        self.vista_trade = view
        self.jugador_id = jugador_id

    async def on_submit(self, interaction: discord.Interaction):
        texto = self.oferta.value.lower().strip()
        quiere_shiny = False
        
        if texto.endswith(" shiny"):
            quiere_shiny = True
            nombre = texto[:-6].strip()
        else:
            nombre = texto

        # Validamos si el jugador realmente tiene el Pokémon usando tu DB actual
        versiones = database.obtener_versiones_pokemon(self.jugador_id, nombre)
        
        if not versiones:
            return await interaction.response.send_message(f"❌ No tienes a {nombre.capitalize()}.", ephemeral=True)
            
        if quiere_shiny and 1 not in versiones:
            return await interaction.response.send_message(f"❌ No tienes la versión ✨ Shiny de {nombre.capitalize()}.", ephemeral=True)
            
        if not quiere_shiny and 0 not in versiones:
            return await interaction.response.send_message(f"❌ Solo tienes la versión Shiny. Especifica '{nombre} shiny'.", ephemeral=True)

        # Actualizamos la mesa de intercambio
        await self.vista_trade.registrar_oferta(interaction, self.jugador_id, nombre, quiere_shiny)

# --- 4. LA MESA DE INTERCAMBIO (View) ---
class SalaIntercambio(discord.ui.View):
    def __init__(self, jugador1, jugador2):
        super().__init__(timeout=120) # 2 minutos para hacer el trato
        self.j1 = jugador1
        self.j2 = jugador2
        
        # Estado de las ofertas: {"nombre": str, "shiny": bool, "listo": bool}
        self.oferta_j1 = None
        self.oferta_j2 = None

    async def on_timeout(self):
        # Si se acaba el tiempo, liberamos a los jugadores
        usuarios_ocupados.discard(self.j1.id)
        usuarios_ocupados.discard(self.j2.id)
        
        for child in self.children:
            child.disabled = True
            
        if hasattr(self, 'message'):
            embed = self.message.embeds[0]
            embed.color = discord.Color.red()
            embed.title = "⌛ El tiempo de intercambio expiró."
            await self.message.edit(embed=embed, view=self)

    def generar_embed(self):
        embed = discord.Embed(title="🤝 Sala de Intercambio", color=discord.Color.blue())
        
        # Texto Oferta Jugador 1
        if self.oferta_j1:
            texto_j1 = f"**{self.oferta_j1['nombre'].capitalize()}** {'✨' if self.oferta_j1['shiny'] else ''}"
            if self.oferta_j1.get('listo'): texto_j1 += " ✅ (Listo)"
        else:
            texto_j1 = "Esperando oferta..."
            
        # Texto Oferta Jugador 2
        if self.oferta_j2:
            texto_j2 = f"**{self.oferta_j2['nombre'].capitalize()}** {'✨' if self.oferta_j2['shiny'] else ''}"
            if self.oferta_j2.get('listo'): texto_j2 += " ✅ (Listo)"
        else:
            texto_j2 = "Esperando oferta..."

        embed.add_field(name=f"📦 Oferta de {self.j1.display_name}", value=texto_j1, inline=True)
        embed.add_field(name="🔄", value="intercambia por", inline=True)
        embed.add_field(name=f"📦 Oferta de {self.j2.display_name}", value=texto_j2, inline=True)
        
        return embed

    async def registrar_oferta(self, interaction, jugador_id, nombre, shiny):
        if jugador_id == self.j1.id:
            self.oferta_j1 = {"nombre": nombre, "shiny": shiny, "listo": False}
        else:
            self.oferta_j2 = {"nombre": nombre, "shiny": shiny, "listo": False}
            
        await interaction.response.edit_message(embed=self.generar_embed(), view=self)

    @discord.ui.button(label="Hacer/Cambiar Oferta", style=discord.ButtonStyle.primary, custom_id="btn_oferta")
    async def btn_ofertar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.j1.id, self.j2.id]:
            return await interaction.response.send_message("❌ Esta mesa no es tuya.", ephemeral=True)
            
        # Desmarcamos el "listo" si deciden cambiar la oferta a la mitad
        if interaction.user.id == self.j1.id and self.oferta_j1: self.oferta_j1['listo'] = False
        if interaction.user.id == self.j2.id and self.oferta_j2: self.oferta_j2['listo'] = False
            
        await interaction.response.send_modal(ModalOferta(self, interaction.user.id))

    @discord.ui.button(label="Confirmar Trato ✅", style=discord.ButtonStyle.success, custom_id="btn_confirmar")
    async def btn_confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.j1.id, self.j2.id]:
            return await interaction.response.send_message("❌ Esta mesa no es tuya.", ephemeral=True)

        if interaction.user.id == self.j1.id:
            if not self.oferta_j1: return await interaction.response.send_message("Debes hacer una oferta primero.", ephemeral=True)
            self.oferta_j1['listo'] = True
            
        if interaction.user.id == self.j2.id:
            if not self.oferta_j2: return await interaction.response.send_message("Debes hacer una oferta primero.", ephemeral=True)
            self.oferta_j2['listo'] = True

        await interaction.response.edit_message(embed=self.generar_embed(), view=self)

        # --- FASE JIT: SI AMBOS ESTÁN LISTOS, EJECUTAMOS EL TRATO ---
        if self.oferta_j1 and self.oferta_j1.get('listo') and self.oferta_j2 and self.oferta_j2.get('listo'):
            for child in self.children: child.disabled = True # Desactivar botones
            
            # Validación Final (JIT) e Intercambio cruzado en DB
            exito_j1 = await transferir_pokemon_seguro(self.j1.id, self.j2.id, self.oferta_j1['nombre'], 1 if self.oferta_j1['shiny'] else 0)
            exito_j2 = await transferir_pokemon_seguro(self.j2.id, self.j1.id, self.oferta_j2['nombre'], 1 if self.oferta_j2['shiny'] else 0)

            usuarios_ocupados.discard(self.j1.id)
            usuarios_ocupados.discard(self.j2.id)

            if exito_j1 and exito_j2:
                embed_final = discord.Embed(title="🎉 ¡Intercambio Exitoso!", description=f"{self.j1.mention} y {self.j2.mention} han intercambiado Pokémon.", color=discord.Color.green())
                await interaction.message.edit(embed=embed_final, view=self)
            else:
                # Si falló, es porque alguien liberó al Pokémon en el último segundo (trampa)
                embed_fallo = discord.Embed(title="❌ Error Crítico", description="Uno de los Pokémon desapareció del inventario. El trato se ha cancelado por seguridad.", color=discord.Color.red())
                await interaction.message.edit(embed=embed_fallo, view=self)
            self.stop()

    @discord.ui.button(label="Cancelar ❌", style=discord.ButtonStyle.danger, custom_id="btn_cancelar")
    async def btn_cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.j1.id, self.j2.id]:
            return await interaction.response.send_message("❌ Esta mesa no es tuya.", ephemeral=True)
            
        usuarios_ocupados.discard(self.j1.id)
        usuarios_ocupados.discard(self.j2.id)
        
        for child in self.children: child.disabled = True
        embed = self.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "🚫 Intercambio cancelado"
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

# --- 5. COMANDO PRINCIPAL A ENLAZAR EN MAIN ---
def iniciar_modulo_intercambio(bot):
    @bot.command(name="trade")
    async def trade(ctx, usuario: discord.Member):
        """Inicia una sala de intercambio segura con otro jugador."""
        # Filtros de seguridad iniciales
        if usuario.bot:
            return await ctx.send("❌ No puedes intercambiar con un bot.")
        if usuario.id == ctx.author.id:
            return await ctx.send("❌ No puedes intercambiar contigo mismo.")
            
        # Comprobación de candados
        if ctx.author.id in usuarios_ocupados:
            return await ctx.send("❌ Ya estás en medio de un trato. Termínalo o espera a que expire.")
        if usuario.id in usuarios_ocupados:
            return await ctx.send(f"❌ {usuario.display_name} está ocupado en otro intercambio.")

        # Bloqueamos a los dos jugadores
        usuarios_ocupados.add(ctx.author.id)
        usuarios_ocupados.add(usuario.id)

        # Iniciamos la sala
        vista = SalaIntercambio(ctx.author, usuario)
        embed = vista.generar_embed()
        
        mensaje = await ctx.send(f"📢 {usuario.mention}, ¡{ctx.author.display_name} te ha invitado a intercambiar Pokémon!", embed=embed, view=vista)
        vista.message = mensaje