import discord


class SelectorIncursion(discord.ui.View):

    def __init__(self, raid):
        super().__init__(timeout=300)

        self.raid = raid

    @discord.ui.button(
        label="Pikachu",
        style=discord.ButtonStyle.blurple
    )
    async def pikachu(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Elegiste Pikachu",
            ephemeral=True
        )

    @discord.ui.button(
        label="Charizard",
        style=discord.ButtonStyle.blurple
    )
    async def charizard(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.raid.seleccionar_pokemon(
            interaction.user.id,
            6
        )

        print(
            f"Selecciones: {self.raid.selecciones}"
        )

        await interaction.response.send_message(
            "Elegiste Charizard",
            ephemeral=True
        )

    @discord.ui.button(
        label="Dragonite",
        style=discord.ButtonStyle.blurple
    )
    async def dragonite(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Elegiste Dragonite",
            ephemeral=True
        )