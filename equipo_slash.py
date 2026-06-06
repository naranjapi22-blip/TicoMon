import asyncio

import aiohttp
import discord
from discord import app_commands

import database
import servicios
from vistas_equipo import crear_embed_captura_stats

_tipos_cache: dict[str, str] = {}

equipo_group = app_commands.Group(name="equipo", description="Gestiona tu equipo de Pokémon")


async def _tipos_de(session, nombre: str) -> str:
    clave = nombre.lower()
    if clave in _tipos_cache:
        return _tipos_cache[clave]
    data, _ = await servicios.obtener_pokemon(session, nombre)
    if not data:
        _tipos_cache[clave] = "?"
        return "?"
    tipos = " / ".join(t["type"]["name"].capitalize() for t in data.get("types", []))
    _tipos_cache[clave] = tipos
    return tipos


async def _prefetch_tipos(session, capturas: list[dict]):
    unicos = {c["nombre"] for c in capturas}
    pendientes = [n for n in unicos if n.lower() not in _tipos_cache]
    if pendientes:
        await asyncio.gather(*[_tipos_de(session, n) for n in pendientes])


def _etiqueta_captura(cap: dict) -> str:
    tipos = _tipos_cache.get(cap["nombre"].lower(), "?")
    shiny = "✨ " if cap["es_shiny"] else ""
    return f"{shiny}{cap['nombre'].capitalize()} #{cap['id']} · {tipos} · {cap['iv_pct']}%"


def _filtrar_capturas(capturas: list[dict], query: str) -> list[dict]:
    q = query.strip().lower().lstrip("#")
    if not q:
        return capturas
    if q.isdigit():
        return [c for c in capturas if c["id"] == int(q)]
    return [
        c for c in capturas
        if q in c["nombre"].lower() or q in str(c["id"])
    ]


def _capturas_disponibles(user_id: int) -> list[dict]:
    ids_equipo = {c for c in database.obtener_equipo(user_id) if c is not None}
    return database.listar_capturas_usuario(user_id, excluir_ids=ids_equipo)


async def _session_del_bot(bot) -> aiohttp.ClientSession:
    if not hasattr(bot, "session") or bot.session.closed:
        bot.session = aiohttp.ClientSession()
    return bot.session


@equipo_group.command(name="agregar", description="Añade una captura de tu inventario al equipo")
@app_commands.describe(captura="Elige uno de tus Pokémon (nombre, ID o tipo)")
async def equipo_agregar(interaction: discord.Interaction, captura: str):
    await interaction.response.defer(ephemeral=True)

    try:
        captura_id = int(captura)
    except ValueError:
        return await interaction.followup.send("❌ Selecciona una captura válida del menú.", ephemeral=True)

    if database.contar_equipo(interaction.user.id) >= 9:
        return await interaction.followup.send("❌ Tu equipo está completo (9/9).", ephemeral=True)

    cap = database.obtener_captura(interaction.user.id, captura_id)
    if not cap:
        return await interaction.followup.send("❌ Esa captura no existe en tu inventario.", ephemeral=True)

    try:
        slot = database.agregar_a_equipo(interaction.user.id, captura_id)
    except database.EquipoError as e:
        return await interaction.followup.send(f"❌ {e}", ephemeral=True)

    session = await _session_del_bot(interaction.client)
    embed = await crear_embed_captura_stats(session, interaction.user.id, captura_id)
    embed.description = f"✅ Añadido al slot **{slot}**."
    await interaction.followup.send(embed=embed, ephemeral=True)


@equipo_agregar.autocomplete("captura")
async def equipo_agregar_autocomplete(interaction: discord.Interaction, current: str):
    capturas = _capturas_disponibles(interaction.user.id)
    capturas = _filtrar_capturas(capturas, current)[:25]

    if not capturas:
        return []

    session = await _session_del_bot(interaction.client)
    await _prefetch_tipos(session, capturas)

    return [
        app_commands.Choice(name=_etiqueta_captura(c)[:100], value=str(c["id"]))
        for c in capturas
    ]


async def setup(bot):
    bot.tree.add_command(equipo_group)
