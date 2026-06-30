import asyncio
import logging
import random
import servicios
import database
log = logging.getLogger(__name__)
from database import guardar_captura
import discord
from vistas_safari import VistaSituacionSafari
from safari_personajes import (
    obtener_guia_aleatorio,
    obtener_frase,
    obtener_recomendacion_ruta,
    obtener_lado_recomendado
)
from utils_imagenes import crear_imagen_encuentro
from regiones import obtener_siguiente_region, obtener_rango_region
from rarezas import (
    pokemon_por_rareza,
    generar_ids_safari_region
)
DESCRIPCION_EVENTO = {
    "yacimiento":
        "💎 Se ha descubierto un yacimiento mineral. Pokémon de tipo Roca comienzan a emerger de las grietas.",

    "guarida":
        "🐉 Los rastros conducen a una enorme guarida. Algo poderoso parece habitar aquí...",

    "ruinas":
        "🏛️ Han dado con unas ruinas antiguas. Una extraña energía metálica resuena entre las estructuras.",

    "bosque":
        "🌲 El camino se interna en un bosque frondoso. Pokémon de tipo Planta observan desde la espesura.",

    "lago":
        "🌊 Un lago cristalino aparece ante ustedes. Pokémon de Agua emergen desde la profundidad.",

    "migracion":
        "🐾 Se escucha un estruendo colectivo. Una migración Pokémon atraviesa la zona.",

    "duelo":
        "🥊 Dos siluetas chocan con fuerza. Un intenso duelo Pokémon ocurre frente a la expedición.",

    "ventisca":
        "❄️ Una corriente helada congela el aire. Una ventisca dificulta el avance.",

    "distorsion":
        "🌀 La realidad parece ondularse. Una distorsión psíquica altera el entorno.",

    "noche":
        "🌙 La luz desaparece antes de tiempo. Pokémon de tipo Siniestro acechan desde las sombras.",

    "cementerio":
        "👻 Un aire fúnebre invade el lugar. Presencias espectrales recorren las tumbas cercanas.",

    "arcoiris":
        "✨ Un brillo multicolor ilumina el cielo. Una energía feérica envuelve la zona.",

    "espejismo":
        "🏜️ La visión se distorsiona. Un extraño espejismo aparece en el horizonte.",

    "pantano":
        "☣️ El terreno se vuelve viscoso e inestable. Un pantano tóxico se extiende frente a ustedes.",

    "tormenta":
        "⚡ Rayos caen a la distancia. Una tormenta eléctrica sacude la región.",

    "rafaga":
        "🌪️ Un viento huracanado golpea la expedición. Los cielos pertenecen a los Pokémon Voladores.",

    "volcan":
        "🔥 El suelo comienza a vibrar y calentarse. Un volcán activo despierta en las cercanías."
}
SITUACIONES_SAFARI = [

    {
        "id": "huellas",
        "texto": "🐾 Se observan huellas recientes.",

        "opcion_a": "🔍 Investigar",
        "modificador_a": {
            "guarida": 5,
            "ruinas": 3
        },

        "opcion_b": "📸 Documentar",
        "modificador_b": {
            "ruinas": 5,
            "yacimiento": 3
        },

        "opcion_c": "🚙 Continuar",
        "modificador_c": {
            "migracion": 2
        }
    },

    {
        "id": "bayas",
        "texto": "🍓 Un arbusto lleno de bayas.",

        "opcion_a": "🧺 Recoger",
        "modificador_a": {
            "bosque": 5,
            "migracion": 3
        },

        "opcion_b": "🍽️ Dejar comida cerca",
        "modificador_b": {
            "migracion": 5,
            "arcoiris": 3
        },

        "opcion_c": "🚙 Continuar",
        "modificador_c": {
            "rafaga": 2
        }
    },

    {
        "id": "arbustos",
        "texto": "🌿 Crujidos extraños en el follaje.",

        "opcion_a": "💥 Lanzar piedra",
        "modificador_a": {
            "duelo": 5,
            "pantano": 3
        },

        "opcion_b": "🤫 Acercarse con sigilo",
        "modificador_b": {
            "noche": 5,
            "distorsion": 3
        },

        "opcion_c": "🚙 Continuar",
        "modificador_c": {
            "migracion": 2
        }
    },

    {
        "id": "rio",
        "texto": "🌊 Un río atraviesa la ruta.",

        "opcion_a": "🎣 Pescar",
        "modificador_a": {
            "lago": 5,
            "migracion": 3
        },

        "opcion_b": "🛶 Cruzar",
        "modificador_b": {
            "rafaga": 5,
            "lago": 3
        },

        "opcion_c": "🚙 Buscar otro paso",
        "modificador_c": {
            "migracion": 2
        }
    },

    {
        "id": "cueva",
        "texto": "🕳️ La cueva emite un aire gélido.",

        "opcion_a": "🔦 Entrar",
        "modificador_a": {
            "ventisca": 5,
            "guarida": 3
        },

        "opcion_b": "🪨 Examinar entrada",
        "modificador_b": {
            "yacimiento": 5,
            "ruinas": 3
        },

        "opcion_c": "🚙 Continuar",
        "modificador_c": {
            "espejismo": 2
        }
    },

    {
        "id": "niebla",
        "texto": "🌫️ Una densa niebla cubre todo.",

        "opcion_a": "💡 Usar bengalas",
        "modificador_a": {
            "distorsion": 5,
            "noche": 3
        },

        "opcion_b": "🧭 Seguir rastros",
        "modificador_b": {
            "cementerio": 5,
            "espejismo": 3
        },

        "opcion_c": "🚙 Esperar y continuar",
        "modificador_c": {
            "migracion": 2
        }
    },

    {
        "id": "rugido",
        "texto": "🔊 Un rugido sacude el área.",

        "opcion_a": "⚔️ Preparar combate",
        "modificador_a": {
            "duelo": 5,
            "guarida": 3
        },

        "opcion_b": "🏃 Buscar refugio",
        "modificador_b": {
            "cementerio": 5,
            "noche": 3
        },

        "opcion_c": "🚙 Alejarse",
        "modificador_c": {
            "migracion": 2
        }
    },

    {
        "id": "campamento",
        "texto": "⛺ Restos de un campamento.",

        "opcion_a": "🍵 Descansar",
        "modificador_a": {
            "arcoiris": 5,
            "migracion": 3
        },

        "opcion_b": "🎒 Registrar suministros",
        "modificador_b": {
            "ruinas": 5,
            "yacimiento": 3
        },

        "opcion_c": "🚙 Continuar",
        "modificador_c": {
            "migracion": 2
        }
    }
]


GUIAS_SAFARI = {
    "papel": {
        "nombre": "Papel",
        "emoji": "🧭",
        "rol": "explorador"
    },
    "gin": {
        "nombre": "Gin",
        "emoji": "📚",
        "rol": "experto"
    },
    "yogy": {
        "nombre": "Yogy",
        "emoji": "😎",
        "rol": "aventurero"
    },
    "jorroco": {
        "nombre": "Jorroco",
        "emoji": "😅",
        "rol": "nervioso"
    }
}

EVENTOS_COMUNES = [
    "migracion",
    "volcan",
    "lago",
    "bosque",
    "tormenta",
    "ventisca",
    "duelo",
    "pantano",
    "espejismo",
    "rafaga",
    "distorsion",
    "yacimiento",
    "cementerio",
    "noche",
    "ruinas",
    "arcoiris"
]
CONFIG_SAFARIS = {

    1: {
        "encuentros": 5,
        "eventos": 3,
        "balls": 9
    },

    2: {
        "encuentros": 7,
        "eventos": 4,
        "balls": 12
    },

    3: {
        "encuentros": 9,
        "eventos": 5,
        "balls": 15
    },

    4: {
        "encuentros": 11,
        "eventos": 5,
        "balls": 18
    },

    5: {
        "encuentros": 13,
        "eventos": 6,
        "balls": 21
    }

}
class SafariManager:

    def __init__(self):
        self.pokemons_vistos = set()
        self.activo = False
        self.evento_actual = None
        self.guild_id = None
        self.canal_id = None
        self.modo_test = False
        self.participantes = {}
        self.canal = None
        self.session = None
        self.guia_id = None
        self.guia_actual = None
        self.creador_vistas = None
        self.modificador_evento = {}
        self.frases_viaje_usadas = 0
        self.encuentro_actual = {
            "pokemon_id": None,
            "nombre": None,
            "es_shiny": False,
            "tamano_factor": 1.0,
            "apuestas": {}
        }

        self.nivel_safari = 1
        self.config = CONFIG_SAFARIS[1]

        self.encuentro_numero = 0
        self.max_encuentros = self.config["encuentros"]
        self.balls_iniciales = self.config["balls"]

        self.tarea_principal = None

    async def iniciar_safari(
        self,
        guild_id,
        canal_id,
        canal,
        session,
        creador_vistas,
        nivel_safari
    ):
        self.guild_id = guild_id
        self.canal_id = canal_id
        self.canal = canal
        self.session = session
        self.creador_vistas = creador_vistas

        # Configuración del Safari
        self.nivel_safari = nivel_safari

        self.config = CONFIG_SAFARIS.get(
            nivel_safari,
            CONFIG_SAFARIS[1]
        )

        self.max_encuentros = self.config["encuentros"]
        self.balls_iniciales = self.config["balls"]
        cantidad_eventos = self.config["eventos"]

        self.activo = True
        self.participantes.clear()
        self.pokemons_vistos.clear()
        self.frases_viaje_usadas = 0

        self.guia_id, self.guia_actual = (
            obtener_guia_aleatorio()
        )

        self.encuentros_evento = set(
            random.sample(
                range(
                    1,
                    self.max_encuentros + 1
                ),
                cantidad_eventos
            )
        )

        self.mapa_eventos = {
            encuentro: {
                "evento": None,
                "activo": None,
                "evento_generado": False
            }
            for encuentro in sorted(
                self.encuentros_evento
            )
        }

        print(f"SAFARI NIVEL: {self.nivel_safari}")
        print(f"CONFIG: {self.config}")
        print(f"EVENTOS SAFARI: {self.encuentros_evento}")
        print(f"MAPA EVENTOS: {self.mapa_eventos}")

        self.region_actual = obtener_siguiente_region()

        self.encuentro_actual = {
            "pokemon_id": None,
            "nombre": None,
            "es_shiny": False,
            "tamano_factor": 1.0,
            "apuestas": {}
        }

        self.encuentro_numero = 0

        log.info(
            f"🚙 Safari nivel {self.nivel_safari} iniciado en guild {guild_id}"
        )

    async def finalizar_safari(self):

        if self.canal:

            frase = obtener_frase(
                self.guia_id,
                "final"
            )

            await self.canal.send(
                f"🏁 **Safari finalizado**\n\n"
                f"{self.guia_actual['emoji']} "
                f"**Guía {self.guia_actual['nombre']}**\n"
                f"💬 {frase}"
            )

        self.activo = False

        self.guild_id = None
        self.canal_id = None


        ranking = sorted(
            self.participantes.items(),
            key=lambda x: x[1]["capturas"],
            reverse=True
        )

        texto = "🏆 Resultados del Safari\n\n"

        for posicion, (user_id, datos) in enumerate(ranking, start=1):

            texto += (
                f"{posicion}. <@{user_id}> - "
                f"{datos['capturas']} captura(s)\n"
            )

        if self.canal:
            await self.canal.send(texto)
        self.session = None
        self.creador_vistas = None
        
        self.participantes.clear()

        self.encuentro_actual = {
            "pokemon_id": None,
            "nombre": None,
            "es_shiny": False,
            "tamano_factor": 1.0,
            "apuestas": {}
        }

        self.encuentro_numero = 0

    async def ejecutar_encuentro(self):
        EVENTOS_TIPO = {
            "migracion": "normal",
            "volcan": "fire",
            "lago": "water",
            "bosque": "grass",
            "tormenta": "electric",
            "ventisca": "ice",
            "duelo": "fighting",
            "pantano": "poison",
            "espejismo": "ground",
            "rafaga": "flying",
            "distorsion": "psychic",
            "yacimiento": "rock",
            "cementerio": "ghost",
            "noche": "dark",
            "ruinas": "steel",
            "arcoiris": "fairy",
            "guarida": "dragon"
        }
        print(
            f"ENCUENTRO ACTUAL: "
            f"{self.encuentro_numero}"
        )

        print(
            f"EVENTOS PROGRAMADOS: "
            f"{self.encuentros_evento}"
        )
        # ==========================
        # FRASE DE VIAJE
        # ==========================

        if (
            self.encuentro_numero > 1
            and self.frases_viaje_usadas < 2
            and random.random() <= 0.35
        ):

            frase = obtener_frase(
                self.guia_id,
                "viaje"
            )

            if frase:

                self.frases_viaje_usadas += 1

                await self.canal.send(
                    f"{self.guia_actual['emoji']} "
                    f"**{self.guia_actual['nombre']}**\n\n"
                    f"💬 {frase}"
                )
        evento = None
        legendario_evento = False
        if (
            self.encuentro_numero
            in self.mapa_eventos
        ):

            info = self.mapa_eventos[
                self.encuentro_numero
            ]

            await self.resolver_situacion_safari()
        if self.encuentro_numero in self.encuentros_evento:

            print(
                f"EVENTO ENCUENTRO "
                f"{self.encuentro_numero}"
            )

            if self.encuentro_numero in self.encuentros_evento:

                info_evento = self.mapa_eventos[
                    self.encuentro_numero
                ]

                if info_evento["activo"] is False:

                    evento = None

                else:

                    if not info_evento.get("evento_generado"):

                        info_evento["evento"] = (
                            self.generar_evento_safari()
                        )

                        info_evento["evento_generado"] = True

                        print(
                            f"EVENTO GENERADO: "
                            f"{info_evento['evento']}"
                        )

                        evento = info_evento["evento"]

                        print(
                            f"EVENTO FINAL: "
                            f"{evento}"
                        )

                        if evento in DESCRIPCION_EVENTO:

                            await self.canal.send(
                                DESCRIPCION_EVENTO[evento]
                            )
                    self.modificador_evento = {}

                legendario_evento = (
                    random.random() <= 0.02
                )

            legendario_evento = (
                random.random() <= 0.02
            )

            print(
                f"EVENTO SAFARI: {evento}"
            )

            print(
                f"EVENTOS PROGRAMADOS: "
                f"{self.encuentros_evento}"
            )

        pokemons = []

        rango = obtener_rango_region(
            self.region_actual
        )

        if evento == "guarida":

            ids_safari = generar_pokemons_por_tipo_global(
                "dragon",
                self.pokemons_vistos,
                incluir_legendarios=legendario_evento
            )

        elif evento in EVENTOS_TIPO:

            ids_safari = generar_pokemons_por_tipo(
                EVENTOS_TIPO[evento],
                rango["inicio"],
                rango["fin"],
                self.pokemons_vistos,
                incluir_legendarios=legendario_evento
            )

        else:

            ids_safari = generar_ids_safari_region(
                rango["inicio"],
                rango["fin"],
                self.pokemons_vistos,
                self.encuentro_numero
            )
        print(
            f"TIPO EVENTO: {evento} | "
            f"IDS: {ids_safari}"
        )
        for pokemon_id in ids_safari:
            self.pokemons_vistos.add(
                pokemon_id
            )
        print("IDS SAFARI:", ids_safari)
        print(
            f"REGION: {self.region_actual} | "
            f"RANGO: {rango['inicio']}-{rango['fin']}"
        )
        encuentro_shiny = (
            random.random() <= 0.0025
        )
        for slot, pokemon_id_tmp in enumerate(
            ids_safari,
            start=1
        ):

            pokemon_local = database.obtener_pokemon_local(
                pokemon_id_tmp
            )

            if not pokemon_local:
                continue
            pokemons.append({
                "slot": slot,
                "pokemon_id": pokemon_id_tmp,
                "nombre": pokemon_local["nombre"].lower(),
                "capture_rate": pokemon_local["capture_rate"],
                "es_shiny": encuentro_shiny,
                "tamano_factor": round(
                    random.uniform(0.50, 1.50),
                    2
                )
            })

        self.crear_encuentro(
            pokemons
        )

        if legendario_evento:

            await self.canal.send(
                "✨ **¡Se siente una presencia extraordinaria en la zona!**"
            )
        from vistas_safari import VistaSeleccionPokemon
        view = VistaSeleccionPokemon(
            self.guild_id,
            self.encuentro_actual["pokemons"]
        )

        pokemon_texto = "\n".join(
            [
                f"{p['slot']}️⃣ {'✨ SHINY ✨ ' if p['es_shiny'] else ''}{p['nombre'].capitalize()}"
                for p in self.encuentro_actual["pokemons"]
            ]
        )
        embed = discord.Embed(
            title=f"🚙 Encuentro {self.encuentro_numero}/{self.max_encuentros}",
            description=(
                f"🐾 Pokémon disponibles:\n\n"
                f"{pokemon_texto}\n\n"
                f"⏳ Tienen 30 segundos para elegir."
            )
        )
        buffer = await crear_imagen_encuentro(
            self.encuentro_actual["pokemons"],
            self.session,
        )
        print("POKEMONS:", pokemons)
        print("BUFFER:", buffer)
        if buffer:
            print("IMAGEN GENERADA")
        else:
            print("NO SE GENERÓ IMAGEN")
        file = None

        if buffer:
            file = discord.File(
                buffer,
                filename="encuentro.png"
            )
        embed.set_image(url="attachment://encuentro.png")

        mensaje = await self.canal.send(
            embed=embed,
            file=file,
            view=view
        )
        view.message = mensaje

        await asyncio.sleep(30)

        apuestas = self.encuentro_actual["apuestas"]

        if not apuestas:

            await self.canal.send(
                "💨 Nadie intentó capturar al Pokémon."
            )

        else:

            await self.canal.send(
                f"🎯 Participaron {len(apuestas)} entrenador(es)."
            )

        await self.resolver_apuestas()
    async def resolver_apuestas(self):

        apuestas = self.encuentro_actual["apuestas"]

        for pokemon in self.encuentro_actual["pokemons"]:

            print(
                f"RESOLVIENDO SLOT {pokemon['slot']} "
                f"{pokemon['nombre']}"
            )

            slot = pokemon["slot"]

            apuestas_slot = {
                user_id: datos
                for user_id, datos in apuestas.items()
                if datos["slot"] == slot
            }

            print(
                f"APUESTAS SLOT {slot}: "
                f"{apuestas_slot}"
            )

            if not apuestas_slot:
                continue

            intentos = []

            for user_id, datos_apuesta in apuestas_slot.items():

                intentos.extend(
                    [user_id] * datos_apuesta["balls"]
                )

            random.shuffle(intentos)

            pokemon_capturado = False

            for user_id in intentos:

                capture_rate = pokemon["capture_rate"]

                probabilidad = (
                    0.05 +
                    (capture_rate / 255) * 0.35
                )

                probabilidad = min(
                    probabilidad,
                    0.95
                )

                capturado = (
                    random.random() <= probabilidad
                )

                print(
                    f"ROLL={capturado} "
                    f"prob={probabilidad:.2%}"
                )

                if not capturado:
                    continue

                print(
                    f"CAPTURADO -> {pokemon['nombre']} "
                    f"por {user_id}"
                )

                nombre = pokemon["nombre"].capitalize()
                es_shiny = pokemon["es_shiny"]
                tamano_factor = pokemon["tamano_factor"]

                if not self.modo_test:

                    try:

                        await guardar_captura(
                            user_id,
                            nombre,
                            tamano_factor,
                            es_shiny
                        )

                    except Exception as e:

                        log.error(
                            f"Error guardando captura Safari: {e}",
                            exc_info=True
                        )

                        continue

                self.participantes[user_id]["capturas"] += 1

                if self.canal and not self.modo_test:
                    await self.canal.send(
                        f"🎉 <@{user_id}> capturó a {nombre}."
                    )

                pokemon_capturado = True

                break

            if not pokemon_capturado:

                nombre = pokemon["nombre"].capitalize()

                if self.canal and not self.modo_test:
                    await self.canal.send(
                        f"💨 {nombre} escapó del Safari."
                    )
    async def simular_encuentro(self):

        self.encuentro_actual["apuestas"] = {}

        for user_id, datos in self.participantes.items():

            if datos["balls"] <= 0:
                continue

            balls = min(
                random.randint(1, 3),
                datos["balls"]
            )

            slot = random.randint(1, 3)

            datos["balls"] -= balls

            self.encuentro_actual["apuestas"][user_id] = {
                "balls": balls,
                "slot": slot
            }

        await self.resolver_apuestas()
    async def ejecutar_safari(self):

        self.encuentro_numero = 1

        while self.encuentro_numero <= self.max_encuentros:

            await self.ejecutar_encuentro()

            self.encuentro_numero += 1

        await self.finalizar_safari()

        await self.finalizar_safari()
    def agregar_participante(
        self,
        user_id
    ):

        if not self.activo:
            return False

        if user_id in self.participantes:
            return False

        self.participantes[user_id] = {
            "balls": self.balls_iniciales,
            "capturas": 0
        }

        log.info(
            f"🚙 Participante agregado: {user_id}"
        )

        return True

    def es_participante(
        self,
        user_id
    ):
        return user_id in self.participantes

    def obtener_participante(
        self,
        user_id
    ):
        return self.participantes.get(user_id)

    def cantidad_participantes(
        self
    ):
        return len(self.participantes)

    def crear_encuentro(
        self,
        pokemons
    ):

        self.encuentro_actual = {
            "pokemons": pokemons,
            "apuestas": {},
            "selecciones": {}
        }

        log.info(
            f"🐾 Encuentro creado con {len(pokemons)} Pokémon(s)"
        )

    def registrar_apuesta(
        self,
        user_id,
        cantidad,
        slot=1
        ):

        if user_id not in self.participantes:
            return False, "No participas en este Safari."

        if user_id in self.encuentro_actual["apuestas"]:
            return False, "Ya elegiste en este encuentro."

        datos = self.participantes[user_id]

        if datos["balls"] < cantidad:
            return False, "No tienes suficientes Safari Balls."

        datos["balls"] -= cantidad

        balls_restantes = datos["balls"]

        self.encuentro_actual["apuestas"][user_id] = {
            "balls": cantidad,
            "slot": slot
        }

        log.info(
            f"🎯 Apuesta: user={user_id} slot={slot} balls={cantidad}"
        )
        log.info(
            f"🎯 Usuario {user_id} apostó {cantidad} balls"
        )

        log.info(
            f"🎯 Apuestas actuales: {self.encuentro_actual['apuestas']}"
        )
        pokemon = next(
            p
            for p in self.encuentro_actual["pokemons"]
            if p["slot"] == slot
        )

        nombre_pokemon = (
            f"✨ SHINY ✨ {pokemon['nombre'].capitalize()}"
            if pokemon["es_shiny"]
            else pokemon["nombre"].capitalize()
        )
        return (
            True,
            f"🎾 Lanzarás {cantidad} Safari Balls a {nombre_pokemon}.\n\n"
            f"🎒 Safari Balls restantes: {balls_restantes}"
        )
    async def resolver_situacion_safari(self):

        situacion = random.choice(
            SITUACIONES_SAFARI
        )

        view = VistaSituacionSafari(
            situacion
        )

        embed = discord.Embed(
            title="🤔 Decisión de la Expedición",
            description=situacion["texto"],
            color=discord.Color.orange()
        )

        mensaje = await self.canal.send(
            embed=embed,
            view=view
        )

        await asyncio.sleep(20)

        try:
            await mensaje.edit(view=None)
        except:
            pass

        resultado = view.resolver_resultado()

        self.modificador_evento = (
            view.modificador_ganador
        )

        if resultado == "A":

            opcion_ganadora = (
                situacion["opcion_a"]
            )

        elif resultado == "B":

            opcion_ganadora = (
                situacion["opcion_b"]
            )

        else:

            opcion_ganadora = (
                situacion["opcion_c"]
            )

        await self.canal.send(
            "🗳️ **Decisión tomada**\n\n"
            f"{situacion['opcion_a']}: **{view.votos_a}** votos\n"
            f"{situacion['opcion_b']}: **{view.votos_b}** votos\n"
            f"{situacion['opcion_c']}: **{view.votos_c}** votos\n\n"
            f"➡️ {opcion_ganadora}"
        )
        
    def generar_evento_safari(self):
        print(
            f"MODIFICADOR ACTUAL: "
            f"{self.modificador_evento}"
        )
        pesos = {
            evento: 1
            for evento in EVENTOS_COMUNES
        }

        for evento, bonus in (
            self.modificador_evento.items()
        ):

            if evento in pesos:

                pesos[evento] += bonus

        print(
            f"MODIFICADORES: {self.modificador_evento}"
        )

        print(
            f"PESOS EVENTOS: {pesos}"
        )

        return random.choices(
            list(pesos.keys()),
            weights=list(pesos.values()),
            k=1
        )[0]
    def obtener_balls(self, user_id):

        if user_id not in self.participantes:
            return 0

        return self.participantes[user_id]["balls"]
# ==========================
# Registro global
# ==========================

safaris_activos = {}


def obtener_safari(guild_id):

    return safaris_activos.get(
        guild_id
    )


def crear_safari(
    guild_id,
    canal_id
):

    safari = SafariManager()

    safaris_activos[guild_id] = safari

    return safari


def eliminar_safari(
    guild_id
):

    safaris_activos.pop(
        guild_id,
        None
    )
def generar_pokemons_por_tipo(
    tipo,
    inicio,
    fin,
    excluidos=None,
    incluir_legendarios=False
):

    if excluidos is None:
        excluidos = set()

    conn = database.get_connection()
    cursor = conn.cursor()

    if incluir_legendarios:

        cursor.execute(
            """
            SELECT id
            FROM pokemon_data
            WHERE tipos ILIKE %s
            AND id BETWEEN %s AND %s
            """,
            (
                f"%{tipo}%",
                inicio,
                fin
            )
        )

    else:

        cursor.execute(
            """
            SELECT id
            FROM pokemon_data
            WHERE tipos ILIKE %s
            AND id BETWEEN %s AND %s
            AND es_legendario = false
            AND es_mitico = false
            """,
            (
                f"%{tipo}%",
                inicio,
                fin
            )
        )

    ids = [
        fila[0]
        for fila in cursor.fetchall()
        if fila[0] not in excluidos
    ]

    conn.close()

    return random.sample(
        ids,
        min(3, len(ids))
    )
def generar_pokemons_por_tipo_global(
    tipo,
    excluidos=None,
    incluir_legendarios=False
):

    if excluidos is None:
        excluidos = set()

    conn = database.get_connection()
    cursor = conn.cursor()

    if incluir_legendarios:

        cursor.execute(
            """
            SELECT id
            FROM pokemon_data
            WHERE tipos ILIKE %s
            """,
            (
                f"%{tipo}%",
            )
        )

    else:

        cursor.execute(
            """
            SELECT id
            FROM pokemon_data
            WHERE tipos ILIKE %s
            AND es_legendario = false
            AND es_mitico = false
            """,
            (
                f"%{tipo}%",
            )
        )

    ids = [
        fila[0]
        for fila in cursor.fetchall()
        if fila[0] not in excluidos
    ]

    conn.close()

    return random.sample(
        ids,
        min(3, len(ids))
    )
ACCIONES_EXPEDICION = [
    ("cebo", "🍓 Tirar Cebo"),
    ("huellas", "🔍 Seguir Huellas"),
    ("ruido", "🔥 Hacer Ruido"),
    ("continuar", "🚙 Continuar")
]

