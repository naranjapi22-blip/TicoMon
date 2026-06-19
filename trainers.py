from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from io import BytesIO
import discord
import database
CARPETA_TRAINERS = Path(
    "sprites/trainers"
)

TRAINERS = sorted(
    archivo.stem
    for archivo in CARPETA_TRAINERS.glob("*.png")
)


async def generar_imagen_trainers(
    pagina=0
):

    POR_PAGINA = 10

    inicio = pagina * POR_PAGINA
    fin = inicio + POR_PAGINA

    trainers = TRAINERS[inicio:fin]

    columnas = 5
    filas = 2

    ancho_celda = 220
    alto_celda = 260

    ancho = columnas * ancho_celda
    alto = filas * alto_celda + 80

    imagen = Image.new(
        "RGBA",
        (ancho, alto),
        (30, 30, 30)
    )

    draw = ImageDraw.Draw(imagen)

    try:

        fuente_titulo = ImageFont.truetype(
            "fonts/DejaVuSans-Bold.ttf",
            36
        )

        fuente_nombre = ImageFont.truetype(
            "fonts/DejaVuSans-Bold.ttf",
            24
        )

    except Exception as e:

        print(f"Error cargando fuente: {e}")

        fuente_titulo = ImageFont.load_default()
        fuente_nombre = ImageFont.load_default()

    total_paginas = (
        len(TRAINERS) + POR_PAGINA - 1
    ) // POR_PAGINA

    draw.text(
        (20, 20),
        f"Entrenadores ({pagina + 1}/{total_paginas})",
        fill="white",
        font=fuente_titulo
    )

    y_offset = 80

    for indice, trainer in enumerate(trainers):

        columna = indice % columnas
        fila = indice // columnas

        x = columna * ancho_celda
        y = fila * alto_celda + y_offset

        ruta = (
            CARPETA_TRAINERS
            / f"{trainer}.png"
        )

        try:

            sprite = Image.open(
                ruta
            ).convert("RGBA")

            sprite.thumbnail(
                (120, 120)
            )

            sprite_x = (
                x +
                (ancho_celda - sprite.width) // 2
            )

            sprite_y = y + 10

            imagen.paste(
                sprite,
                (sprite_x, sprite_y),
                sprite
            )

        except Exception as e:

            print(
                f"Error cargando {trainer}: {e}"
            )

        numero_real = (
            inicio + indice + 1
        )

        nombre = (
            trainer
            .replace("-", " ")
            .replace("_", " ")
            .title()
        )

        texto = (
            f"{numero_real}. {nombre}"
        )

        bbox = draw.textbbox(
            (0, 0),
            texto,
            font=fuente_nombre
        )

        texto_ancho = (
            bbox[2] - bbox[0]
        )

        draw.text(
            (
                x +
                (ancho_celda - texto_ancho) // 2,
                y + 140
            ),
            texto,
            fill="white",
            font=fuente_nombre
        )

    buffer = BytesIO()

    imagen.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer
class VistaTrainers(discord.ui.View):

    def __init__(
        self,
        autor_id,
        pagina=0
    ):
        super().__init__(
            timeout=180
        )

        self.autor_id = autor_id
        self.pagina = pagina

    async def actualizar(
        self,
        interaction
    ):

        buffer = await generar_imagen_trainers(
            self.pagina
        )

        archivo = discord.File(
            buffer,
            filename="trainers.png"
        )

        await interaction.response.edit_message(
            attachments=[archivo],
            view=self
        )

    @discord.ui.button(
        emoji="⬅️",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def anterior(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.autor_id:

            return await interaction.response.send_message(
                "❌ Este menú no es tuyo.",
                ephemeral=True
            )

        if self.pagina > 0:

            self.pagina -= 1

        await self.actualizar(
            interaction
        )

    @discord.ui.button(
        label="Seleccionar",
        emoji="🎯",
        style=discord.ButtonStyle.success,
        row=0
    )
    async def seleccionar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.autor_id:

            return await interaction.response.send_message(
                "❌ Este menú no es tuyo.",
                ephemeral=True
            )

        await interaction.response.send_modal(
            ModalSeleccionTrainer(
                self.pagina
            )
        )

    @discord.ui.button(
        emoji="➡️",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def siguiente(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.autor_id:

            return await interaction.response.send_message(
                "❌ Este menú no es tuyo.",
                ephemeral=True
            )

        max_paginas = (
            len(TRAINERS) - 1
        ) // 10

        if self.pagina < max_paginas:

            self.pagina += 1

        await self.actualizar(
            interaction
        )
class ModalSeleccionTrainer(
    discord.ui.Modal,
    title="Seleccionar entrenador"
):

    numero = discord.ui.TextInput(
        label="Número del entrenador",
        placeholder="Ejemplo: 7"
    )

    def __init__(
        self,
        pagina
    ):
        super().__init__()

        self.pagina = pagina

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:

            numero = int(
                self.numero.value
            )

        except ValueError:

            return await interaction.response.send_message(
                "❌ Número inválido.",
                ephemeral=True
            )

        indice = numero - 1

        if (
            indice < 0
            or indice >= len(TRAINERS)
        ):
            return await interaction.response.send_message(
                "❌ Número inválido.",
                ephemeral=True
            )

        trainer = TRAINERS[indice]

        await database.guardar_trainer(
            interaction.user.id,
            trainer
        )

        await interaction.message.edit(
            content=f"✅ Trainer seleccionado: {trainer.replace('-', ' ').title()}",
            attachments=[],
            view=None
        )

        if interaction.message:

            try:
                await interaction.message.delete()

            except:
                pass