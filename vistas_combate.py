import discord
import asyncio
import random
import imagencomb  # Tu motor de imágenes local
import servicios   # Para obtener IDs si es necesario
from combate import CombateSim
import combate_servicios

class VistaCombate(discord.ui.View):
    def __init__(self, p1, p2, equipo1_nombres, equipo2_nombres, session):
        super().__init__(timeout=300)
        self.p1 = p1
        self.p2 = p2
        self.equipo1_nombres = equipo1_nombres
        self.equipo2_nombres = equipo2_nombres
        self.session = session
        self.combate = None 

    def generar_barra_hp(self, hp_actual, hp_max):
        """Genera una barra de vida visual de 10 bloques basada en el máximo real del Pokémon."""
        llenos = int((max(0, hp_actual) / hp_max) * 10)
        vacios = 10 - llenos
        return f"[{'█' * llenos}{'░' * vacios}] {max(0, hp_actual)}/{hp_max}"

    async def preparar_combate(self):
        equipo1 = await combate_servicios.preparar_equipos_completos(self.equipo1_nombres)
        equipo2 = await combate_servicios.preparar_equipos_completos(self.equipo2_nombres)
        self.combate = CombateSim(equipo1, equipo2)

    @discord.ui.button(label="¡Iniciar Combate Épico!", style=discord.ButtonStyle.danger)
    async def iniciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.response.edit_message(content="⚔️ **¡El combate ha comenzado!**", view=self)
        msg = await interaction.original_response()
        
        while not self.combate.es_fin_del_juego():
            # 1. Ejecutar ronda y obtener datos
            resumen_ronda = self.combate.ejecutar_ronda()
            e1 = self.combate.equipos["Jugador 1"]
            e2 = self.combate.equipos["Jugador 2"]
            p1_actual = e1['pokes'][e1['activo']]
            p2_actual = e2['pokes'][e2['activo']]
            
            # Obtener HP actuales y máximos de la instancia del combate
            hp1 = e1['hp'][e1['activo']]
            hp_max1 = e1['hp_max'][e1['activo']]
            hp2 = e2['hp'][e2['activo']]
            hp_max2 = e2['hp_max'][e2['activo']]
            
            # 2. Determinar quién ataca para el efecto visual
            turno_atacante = 1 if resumen_ronda.startswith(p1_actual['nombre']) else 2
            
            # 3. Obtener IDs para imagencomb
            id1 = p1_actual.get('id') or await servicios.obtener_id_por_nombre(self.session, p1_actual['nombre'])
            id2 = p2_actual.get('id') or await servicios.obtener_id_por_nombre(self.session, p2_actual['nombre'])
            
            # 4. Generar la imagen con vida dinámica
            buffer = await imagencomb.generar_escena_combate(
                self.session, id1, id2, hp1=hp1, hp2=hp2, hp_max=max(hp_max1, hp_max2), turno_jugador=turno_atacante
            )
            file = discord.File(buffer, filename="combate.png")
            
            # 5. Crear Embed
            embed = discord.Embed(title="⚔️ Duelo Épico", color=discord.Color.red())
            embed.set_image(url="attachment://combate.png")
            
            embed.add_field(
                name=f"👤 {self.p1.display_name}", 
                value=f"**{p1_actual['nombre']}**\n{self.generar_barra_hp(hp1, hp_max1)}", 
                inline=True
            )
            embed.add_field(name="VS", value="🆚", inline=True)
            embed.add_field(
                name=f"👤 {self.p2.display_name}", 
                value=f"**{p2_actual['nombre']}**\n{self.generar_barra_hp(hp2, hp_max2)}", 
                inline=True
            )
            embed.add_field(name="📜 Resumen de la ronda", value=resumen_ronda, inline=False)
            
            await msg.edit(embed=embed, attachments=[file])
            
            # 6. Comprobar fin
            ganador = self.combate.es_fin_del_juego()
            if ganador:
                await interaction.followup.send(f"🏆 **¡El combate ha finalizado!**\nEl ganador es: **{self.p1.display_name if ganador == 'Jugador 1' else self.p2.display_name}**")
                break
            
            await asyncio.sleep(6)

    def on_timeout(self):
        self.stop()

# --- SELECTOR PAGINADO ---
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

        opciones = [discord.SelectOption(label=p, value=p) for p in self.paginas[self.pagina_actual]]
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
            if valor not in self.seleccionados:
                self.seleccionados.append(valor)
        await interaction.response.send_message(f"✅ Añadidos: {len(self.seleccionados)}/3", ephemeral=True)
        if len(self.seleccionados) >= 3:
            self.stop()