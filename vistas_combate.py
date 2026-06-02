import discord
import asyncio
import imagencomb  # Tu archivo de generación de imágenes
import combate_servicios
import servicios # Importamos servicios para obtener el ID si falta
from combate import CombateSim

class VistaCombate(discord.ui.View):
    def __init__(self, p1, p2, equipo1_nombres, equipo2_nombres, session):
        super().__init__(timeout=300)
        self.p1 = p1
        self.p2 = p2
        self.equipo1_nombres = equipo1_nombres
        self.equipo2_nombres = equipo2_nombres
        self.session = session
        self.combate = None 

    async def preparar_combate(self):
        equipo1 = await combate_servicios.preparar_equipos_completos(self.equipo1_nombres)
        equipo2 = await combate_servicios.preparar_equipos_completos(self.equipo2_nombres)
        self.combate = CombateSim(equipo1, equipo2)

    @discord.ui.button(label="¡Iniciar Combate Automático!", style=discord.ButtonStyle.danger)
    async def iniciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.response.edit_message(content="⚔️ **¡El combate ha comenzado!**", view=self)
        msg = await interaction.original_response()
        
        while not self.combate.es_fin_del_juego():
            resumen_ronda = self.combate.ejecutar_ronda()
            
            e1 = self.combate.equipos["Jugador 1"]
            e2 = self.combate.equipos["Jugador 2"]
            p1_actual = e1['pokes'][e1['activo']]
            p2_actual = e2['pokes'][e2['activo']]
            
            # --- CORRECCIÓN DEL KEYERROR ---
            # Si 'id' no existe, lo obtenemos usando el nombre (asumiendo que tienes una función para eso)
            # Si no tienes servicios.obtener_id_por_nombre, puedes usar esta lógica rápida:
            # Dentro de tu bucle:
            id1 = p1_actual.get('id') or await servicios.obtener_id_por_nombre(self.session, p1_actual['nombre'])
            id2 = p2_actual.get('id') or await servicios.obtener_id_por_nombre(self.session, p2_actual['nombre'])
            
            # 1. Generar la imagen de combate
            buffer = await imagencomb.generar_escena_combate(self.session, id1, id2)
            file = discord.File(buffer, filename="combate.png")
            
            # 2. Crear el Embed
            embed = discord.Embed(title="⚔️ Combate Pokémon 3vs3", color=discord.Color.blue())
            embed.set_image(url="attachment://combate.png")
            
            embed.add_field(name=f"👤 {self.p1.display_name}", value=f"**{p1_actual['nombre']}**\nHP: {max(0, e1['hp'][e1['activo']])}", inline=True)
            embed.add_field(name="🆚", value="VS", inline=True)
            embed.add_field(name=f"👤 {self.p2.display_name}", value=f"**{p2_actual['nombre']}**\nHP: {max(0, e2['hp'][e2['activo']])}", inline=True)
            embed.add_field(name="📜 Resumen de la ronda", value=resumen_ronda, inline=False)
            
            # 3. Editar mensaje
            await msg.edit(embed=embed, attachments=[file])
            
            ganador = self.combate.es_fin_del_juego()
            if ganador:
                await interaction.followup.send(f"🏆 **¡El combate ha finalizado!**\nEl ganador es: **{self.p1.display_name if ganador == 'Jugador 1' else self.p2.display_name}**")
                break
            
            await asyncio.sleep(4)

    async def on_timeout(self):
        self.stop()

class SelectorPaginado(discord.ui.View):
    def __init__(self, user, lista_completa):
        super().__init__()
        self.user = user
        self.lista_completa = lista_completa
        self.pagina_actual = 0
        self.seleccionados = []
        self.paginas = [lista_completa[i:i + 25] for i in range(0, len(lista_completa), 25)]
        self.actualizar_select()

    def actualizar_select(self):
        self.clear_items()
        if len(self.paginas) > 1:
            btn_atras = discord.ui.Button(label="◀️", style=discord.ButtonStyle.secondary)
            btn_atras.callback = self.ir_atras
            self.add_item(btn_atras)
            btn_adelante = discord.ui.Button(label="▶️", style=discord.ButtonStyle.secondary)
            btn_adelante.callback = self.ir_adelante
            self.add_item(btn_adelante)

        opciones = []
        offset = self.pagina_actual * 25
        for i, nombre in enumerate(self.paginas[self.pagina_actual]):
            valor_unico = f"{nombre}_{offset + i}"
            opciones.append(discord.SelectOption(label=nombre, value=valor_unico))

        self.select = discord.ui.Select(placeholder=f"Página {self.pagina_actual + 1} (Elige hasta 3)",
                                        min_values=1, max_values=3, options=opciones)
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def ir_atras(self, interaction):
        self.pagina_actual = max(0, self.pagina_actual - 1)
        self.actualizar_select()
        await interaction.response.edit_message(view=self)

    async def ir_adelante(self, interaction):
        self.pagina_actual = min(len(self.paginas) - 1, self.pagina_actual + 1)
        self.actualizar_select()
        await interaction.response.edit_message(view=self)

    async def select_callback(self, interaction):
        if interaction.user != self.user: return await interaction.response.send_message("No es tu turno.", ephemeral=True)
        for valor in self.select.values:
            nombre_limpio = valor.split('_')[0]
            if nombre_limpio not in self.seleccionados:
                self.seleccionados.append(nombre_limpio)
        await interaction.response.send_message(f"✅ Añadidos: {len(self.seleccionados)}/3", ephemeral=True)
        if len(self.seleccionados) >= 3:
            self.stop()