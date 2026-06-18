import discord
import sqlite3
import database
import servicios
import psycopg2
import os

# --- 1. MEMORIA DE SEGURIDAD (Evita la clonación) ---
usuarios_ocupados = set()

# --- 2. LÓGICA DE TRANSFERENCIA SEGURA ---
async def intercambio_atomico(
    user1,
    user2,
    pokemon_id_1,
    pokemon_id_2
):
    """
    Intercambio seguro y atómico.
    O se completan ambos movimientos o no se hace ninguno.
    """

    async with database.db_lock:

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            # Protección extra
            if user1 == user2:
                conn.rollback()
                return False

            # Protección extra
            if pokemon_id_1 == pokemon_id_2:
                conn.rollback()
                return False

            # Bloquear Pokémon del jugador 1
            cursor.execute(
                """
                SELECT id
                FROM capturas
                WHERE id = %s
                AND user_id = %s
                FOR UPDATE
                """,
                (
                    pokemon_id_1,
                    str(user1)
                )
            )

            poke1 = cursor.fetchone()

            # Bloquear Pokémon del jugador 2
            cursor.execute(
                """
                SELECT id
                FROM capturas
                WHERE id = %s
                AND user_id = %s
                FOR UPDATE
                """,
                (
                    pokemon_id_2,
                    str(user2)
                )
            )

            poke2 = cursor.fetchone()

            if not poke1 or not poke2:
                conn.rollback()
                return False

            id_poke1 = poke1[0]
            id_poke2 = poke2[0]

            # Transferencia cruzada
            cursor.execute(
                """
                UPDATE capturas
                SET user_id = %s
                WHERE id = %s
                """,
                (
                    str(user2),
                    id_poke1
                )
            )

            cursor.execute(
                """
                UPDATE capturas
                SET user_id = %s
                WHERE id = %s
                """,
                (
                    str(user1),
                    id_poke2
                )
            )
            cursor.execute(
                """
                INSERT INTO historial_trades (
                    usuario_1,
                    usuario_2,
                    pokemon_1,
                    pokemon_2
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    str(user1),
                    str(user2),
                    pokemon_id_1,
                    pokemon_id_2
                )
            )
            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"[TRADE ERROR] {e}")
            return False

        finally:
            cursor.close()
            conn.close()

# --- 3. MODAL (Pop-up para escribir la oferta) ---
class ModalOferta(discord.ui.Modal, title='Elige tu Pokémon para ofrecer'):
    oferta = discord.ui.TextInput(
        label='ID del Pokémon',
        placeholder='Ejemplo: 1542',
        required=True
    )

    def __init__(self, view, jugador_id):
        super().__init__()
        self.vista_trade = view
        self.jugador_id = jugador_id

    async def on_submit(self, interaction: discord.Interaction):

        try:
            pokemon_id = int(self.oferta.value.strip())
        except ValueError:
            return await interaction.response.send_message(
                "❌ Debes ingresar un ID válido.",
                ephemeral=True
            )

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    pokemon_nombre,
                    es_shiny,
                    iv_hp,
                    iv_atk,
                    iv_def,
                    iv_spa,
                    iv_spd,
                    iv_spe,
                    naturaleza,
                    tamano_factor
                FROM capturas
                WHERE id = %s
                AND user_id = %s
                """,
                (
                    pokemon_id,
                    str(self.jugador_id)
                )
            )

            pokemon = cursor.fetchone()

            if not pokemon:
                return await interaction.response.send_message(
                    "❌ Ese Pokémon no te pertenece o no existe.",
                    ephemeral=True
                )

            (
                _,
                nombre,
                shiny,
                iv_hp,
                iv_atk,
                iv_def,
                iv_spa,
                iv_spd,
                iv_spe,
                naturaleza,
                tamano_factor
            ) = pokemon

            iv_total = (
                iv_hp +
                iv_atk +
                iv_def +
                iv_spa +
                iv_spd +
                iv_spe
            )

            iv_pct = round((iv_total / 186) * 100, 1)

            if (
                self.vista_trade.oferta_j1
                and self.vista_trade.oferta_j1["id"] == pokemon_id
            ):
                return await interaction.response.send_message(
                    "❌ Ese Pokémon ya está en la mesa de intercambio.",
                    ephemeral=True
                )

            if (
                self.vista_trade.oferta_j2
                and self.vista_trade.oferta_j2["id"] == pokemon_id
            ):
                return await interaction.response.send_message(
                    "❌ Ese Pokémon ya está en la mesa de intercambio.",
                    ephemeral=True
                )

            await self.vista_trade.registrar_oferta(
                interaction,
                self.jugador_id,
                pokemon_id,
                nombre,
                bool(shiny),
                iv_pct,
                naturaleza,
                float(tamano_factor)
            )

        finally:
            cursor.close()
            conn.close()
class SelectorPokemonTrade(discord.ui.View):

    def __init__(self, vista_trade, jugador_id):
        super().__init__(timeout=180)

        self.vista_trade = vista_trade
        self.jugador_id = jugador_id

        conn = database.get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
            SELECT
                c.id,
                c.pokemon_nombre,
                c.es_shiny,
                c.iv_hp,
                c.iv_atk,
                c.iv_def,
                c.iv_spa,
                c.iv_spd,
                c.iv_spe,
                c.naturaleza,
                c.tamano_factor,
                CASE
                    WHEN e.captura_id IS NOT NULL THEN TRUE
                    ELSE FALSE
                END AS en_equipo
            FROM capturas c
            LEFT JOIN equipo e
                ON e.captura_id = c.id
            WHERE c.user_id = %s
                """,
                (str(jugador_id),)
            )

            self.pokemones = cursor.fetchall()

        finally:
            cursor.close()
            conn.close()

        opciones = []

        for pokemon in self.pokemones:

            pokemon_id = pokemon[0]
            nombre = pokemon[1]
            shiny = pokemon[2]
            en_equipo = pokemon[11]

            iv_total = (
                pokemon[3] +
                pokemon[4] +
                pokemon[5] +
                pokemon[6] +
                pokemon[7] +
                pokemon[8]
            )

            iv_pct = round((iv_total / 186) * 100, 1)

            naturaleza = pokemon[9]

            iconos = ""

            if shiny:
                iconos += "✨"

            if en_equipo:
                iconos += "⭐"

            opciones.append(
                discord.SelectOption(
                    label=f"{iconos} {nombre.capitalize()} #{pokemon_id}"[:100],
                    description=f"📊 {iv_pct}% • {naturaleza}"[:100],
                    value=str(pokemon_id)
                )
            )
        self.select = discord.ui.Select(
            placeholder="📦 Selecciona un Pokémon",
            min_values=1,
            max_values=1,
            options=opciones
        )

        self.select.callback = self.seleccionar

        self.add_item(self.select)
        btn_buscar = discord.ui.Button(
            label="🔍 Buscar",
            style=discord.ButtonStyle.primary
        )

        btn_buscar.callback = self.buscar

        self.add_item(btn_buscar)
    async def seleccionar(self, interaction: discord.Interaction):

        pokemon_id = int(self.select.values[0])

        pokemon = next(
            p for p in self.pokemones
            if p[0] == pokemon_id
        )

        (
            pokemon_id,
            nombre,
            shiny,
            iv_hp,
            iv_atk,
            iv_def,
            iv_spa,
            iv_spd,
            iv_spe,
            naturaleza,
            tamano_factor
        ) = pokemon

        iv_total = (
            iv_hp +
            iv_atk +
            iv_def +
            iv_spa +
            iv_spd +
            iv_spe
        )

        iv_pct = round((iv_total / 186) * 100, 1)

        await self.vista_trade.registrar_oferta(
            interaction,
            self.jugador_id,
            pokemon_id,
            nombre,
            bool(shiny),
            iv_pct,
            naturaleza,
            float(tamano_factor)
        )

        self.stop()

        try:
            await interaction.edit_original_response(
                content="✅ Oferta realizada.",
                view=None
            )
        except:
            pass

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
        # Liberar jugadores
        usuarios_ocupados.discard(self.j1.id)
        usuarios_ocupados.discard(self.j2.id)

        # Limpiar ofertas
        self.oferta_j1 = None
        self.oferta_j2 = None

        # Desactivar botones
        for child in self.children:
            child.disabled = True

        if hasattr(self, "message"):
            embed = self.message.embeds[0]
            embed.color = discord.Color.red()
            embed.title = "⌛ El tiempo de intercambio expiró."

            await self.message.edit(
                embed=embed,
                view=self
            )

        self.stop()

    def generar_embed(self):
        embed = discord.Embed(title="🤝 Sala de Intercambio", color=discord.Color.blue())
        
        # Texto Oferta Jugador 1
        if self.oferta_j1:
            texto_j1 = (
                f"ID: `{self.oferta_j1['id']}`\n"
                f"**{self.oferta_j1['nombre'].capitalize()}** "
                f"{'✨' if self.oferta_j1['shiny'] else ''}\n"
                f"IVs: **{self.oferta_j1['iv_pct']}%**\n"
                f"Naturaleza: **{self.oferta_j1['naturaleza']}**\n"
                f"Tamaño: **{self.oferta_j1['tamano']}x**"
            )
            if self.oferta_j1.get('listo'): texto_j1 += " ✅ (Listo)"
        else:
            texto_j1 = "Esperando oferta..."
            
        # Texto Oferta Jugador 2
        if self.oferta_j2:
            texto_j2 = (
                f"ID: `{self.oferta_j2['id']}`\n"
                f"**{self.oferta_j2['nombre'].capitalize()}** "
                f"{'✨' if self.oferta_j2['shiny'] else ''}\n"
                f"IVs: **{self.oferta_j2['iv_pct']}%**\n"
                f"Naturaleza: **{self.oferta_j2['naturaleza']}**\n"
                f"Tamaño: **{self.oferta_j2['tamano']}x**"
            )

            if self.oferta_j2.get('listo'):
                texto_j2 += " ✅ (Listo)"
        else:
            texto_j2 = "Esperando oferta..."

        embed.add_field(name=f"📦 Oferta de {self.j1.display_name}", value=texto_j1, inline=True)
        embed.add_field(name="🔄", value="intercambia por", inline=True)
        embed.add_field(name=f"📦 Oferta de {self.j2.display_name}", value=texto_j2, inline=True)
        
        return embed

    async def registrar_oferta(
        self,
        interaction,
        jugador_id,
        pokemon_id,
        nombre,
        shiny,
        iv_pct,
        naturaleza,
        tamano_factor
    ):

        # No permitir usar el mismo Pokémon que está ofreciendo el otro jugador
        if (
            jugador_id == self.j1.id
            and self.oferta_j2
            and self.oferta_j2["id"] == pokemon_id
        ):
            return await interaction.response.send_message(
                "❌ Ese Pokémon ya está siendo ofrecido en el otro lado del intercambio.",
                ephemeral=True
            )

        if (
            jugador_id == self.j2.id
            and self.oferta_j1
            and self.oferta_j1["id"] == pokemon_id
        ):
            return await interaction.response.send_message(
                "❌ Ese Pokémon ya está siendo ofrecido en el otro lado del intercambio.",
                ephemeral=True
            )

        # No permitir seleccionar nuevamente el mismo Pokémon propio
        if (
            jugador_id == self.j1.id
            and self.oferta_j1
            and self.oferta_j1["id"] == pokemon_id
        ):
            return await interaction.response.send_message(
                "❌ Ya estás ofreciendo ese mismo Pokémon.",
                ephemeral=True
            )

        if (
            jugador_id == self.j2.id
            and self.oferta_j2
            and self.oferta_j2["id"] == pokemon_id
        ):
            return await interaction.response.send_message(
                "❌ Ya estás ofreciendo ese mismo Pokémon.",
                ephemeral=True
            )

        if jugador_id == self.j1.id:

            self.oferta_j1 = {
                "id": pokemon_id,
                "nombre": nombre,
                "shiny": shiny,
                "iv_pct": iv_pct,
                "naturaleza": naturaleza,
                "tamano": tamano_factor,
                "listo": False
            }

            if self.oferta_j2:
                self.oferta_j2["listo"] = False

        else:

            self.oferta_j2 = {
                "id": pokemon_id,
                "nombre": nombre,
                "shiny": shiny,
                "iv_pct": iv_pct,
                "naturaleza": naturaleza,
                "tamano": tamano_factor,
                "listo": False
            }

            if self.oferta_j1:
                self.oferta_j1["listo"] = False

        await interaction.response.defer()

        await self.message.edit(
            embed=self.generar_embed(),
            view=self
        )
    @discord.ui.button(label="Hacer/Cambiar Oferta", style=discord.ButtonStyle.primary, custom_id="btn_oferta")
    async def btn_ofertar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.j1.id, self.j2.id]:
            return await interaction.response.send_message("❌ Esta mesa no es tuya.", ephemeral=True)
            
        # Desmarcamos el "listo" si deciden cambiar la oferta a la mitad
        if self.oferta_j1:
            self.oferta_j1["listo"] = False

        if self.oferta_j2:
            self.oferta_j2["listo"] = False
            
       # await interaction.response.send_modal(ModalOferta(self, interaction.user.id))
        await interaction.response.send_message(
            "📦 Selecciona un Pokémon",
            view=SelectorPokemonTrade(
                self,
                interaction.user.id
            ),
            ephemeral=True
        )
    @discord.ui.button(
        label="Confirmar Trato ✅",
        style=discord.ButtonStyle.success,
        custom_id="btn_confirmar"
    )
    async def btn_confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id not in [self.j1.id, self.j2.id]:
            return await interaction.response.send_message(
                "❌ Esta mesa no es tuya.",
                ephemeral=True
            )

        # -------------------------
        # VALIDACIÓN JUGADOR 1
        # -------------------------
        if interaction.user.id == self.j1.id:

            if not self.oferta_j1:
                return await interaction.response.send_message(
                    "Debes hacer una oferta primero.",
                    ephemeral=True
                )

            conn = database.get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    SELECT id
                    FROM capturas
                    WHERE id = %s
                    AND user_id = %s
                    """,
                    (
                        self.oferta_j1["id"],
                        str(self.j1.id)
                    )
                )

                if not cursor.fetchone():
                    return await interaction.response.send_message(
                        "❌ Ya no posees ese Pokémon.",
                        ephemeral=True
                    )

            finally:
                cursor.close()
                conn.close()

            self.oferta_j1["listo"] = True

        # -------------------------
        # VALIDACIÓN JUGADOR 2
        # -------------------------
        elif interaction.user.id == self.j2.id:

            if not self.oferta_j2:
                return await interaction.response.send_message(
                    "Debes hacer una oferta primero.",
                    ephemeral=True
                )

            conn = database.get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    SELECT id
                    FROM capturas
                    WHERE id = %s
                    AND user_id = %s
                    """,
                    (
                        self.oferta_j2["id"],
                        str(self.j2.id)
                    )
                )

                if not cursor.fetchone():
                    return await interaction.response.send_message(
                        "❌ Ya no posees ese Pokémon.",
                        ephemeral=True
                    )

            finally:
                cursor.close()
                conn.close()

            self.oferta_j2["listo"] = True

        await interaction.response.edit_message(
            embed=self.generar_embed(),
            view=self
        )

        # -------------------------
        # EJECUTAR INTERCAMBIO
        # -------------------------
        if (
            self.oferta_j1
            and self.oferta_j1.get("listo")
            and self.oferta_j2
            and self.oferta_j2.get("listo")
        ):

            for child in self.children:
                child.disabled = True

            exito = await intercambio_atomico(
                self.j1.id,
                self.j2.id,
                self.oferta_j1["id"],
                self.oferta_j2["id"]
            )

            usuarios_ocupados.discard(self.j1.id)
            usuarios_ocupados.discard(self.j2.id)

            if exito:

                embed_final = discord.Embed(
                    title="🎉 ¡Intercambio Exitoso!",
                    description=(
                        f"**{self.j1.display_name}** entregó:\n"
                        f"• {self.oferta_j1['nombre'].capitalize()} "
                        f"(ID: {self.oferta_j1['id']})\n\n"
                        f"**{self.j2.display_name}** entregó:\n"
                        f"• {self.oferta_j2['nombre'].capitalize()} "
                        f"(ID: {self.oferta_j2['id']})"
                    ),
                    color=discord.Color.green()
                )

            else:

                embed_final = discord.Embed(
                    title="❌ Intercambio Cancelado",
                    description=(
                        "Uno de los Pokémon ya no estaba disponible "
                        "o ocurrió un error durante el intercambio."
                    ),
                    color=discord.Color.red()
                )

            await interaction.message.edit(
                embed=embed_final,
                view=self
            )

            # Limpiar memoria
            self.oferta_j1 = None
            self.oferta_j2 = None

            self.stop()
    @discord.ui.button(label="Cancelar ❌", style=discord.ButtonStyle.danger, custom_id="btn_cancelar")
    async def btn_cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.j1.id, self.j2.id]:
            return await interaction.response.send_message("❌ Esta mesa no es tuya.", ephemeral=True)
                
        usuarios_ocupados.discard(self.j1.id)
        usuarios_ocupados.discard(self.j2.id)

            # Limpiar memoria
        self.oferta_j1 = None
        self.oferta_j2 = None

        for child in self.children:
                child.disabled = True

        embed = self.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "🚫 Intercambio cancelado"

        await interaction.response.edit_message(
            embed=embed,
             view=self
        )

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