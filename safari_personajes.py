import random

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

FRASES_GUIA = {
    "inicio": {
        "papel": [
            "Las huellas son recientes. Mantengan los ojos abiertos.",
            "Hay varios senderos que no aparecen en los mapas.",
            "Algo se mueve más adelante. Lo averiguaremos pronto.",
            "Revisen sus brújulas; aquí el norte a veces hace cosas raras.",
            "El viento está cambiando, presten atención a las corrientes.",
            "Pisada fresca. Estamos pisando los talones a nuestra presa.",
            "Muévanse en silencio, no queremos espantar a lo que sea que nos vigila.",
            "El terreno está removido, algo ha pasado por aquí hace poco.",
            "Mantengan la formación, el camino se vuelve complicado a partir de ahora."
        ],
        "gin": [
            "He leído sobre esta zona. Tiene una fauna muy interesante.",
            "Los Pokémon de aquí tienen comportamientos particulares.",
            "Será una buena oportunidad para aprender algo nuevo.",
            "Según mis datos, este ecosistema es sumamente complejo.",
            "Observen la vegetación; hay signos claros de adaptaciones únicas.",
            "El comportamiento de los Pokémon aquí es un fenómeno digno de estudio.",
            "Es fascinante notar cómo la humedad afecta la densidad de la población local.",
            "La biodiversidad de este sector es, cuanto menos, excepcional.",
            "Anoten esto en sus cuadernos; estas condiciones son raras de observar."
        ],
        "yogy": [
            "¡Hoy encontraremos algo increíble!",
            "¿Listos para salir de la ruta segura?",
            "Las mejores historias empiezan con una mala idea.",
            "¡Hoy es el día en que hacemos historia!",
            "Si no hay un poco de riesgo, ¿qué chiste tiene?",
            "¡A darle! Quiero ver qué es lo que tanto miedo les da.",
            "¡Sientan esa energía! Algo grande nos espera ahí fuera.",
            "¿Quién necesita un mapa cuando tienes instinto aventurero?",
            "¡Ni se les ocurra mirar atrás, lo mejor está adelante!"
        ],
        "jorroco": [
            "¿Estamos seguros de que esto es una buena idea?",
            "No me gusta ese ruido...",
            "Todavía estamos a tiempo de volver.",
            "¿Escucharon eso? Juraría que algo acaba de gruñir detrás de nosotros.",
            "Me arrepiento de no haber desayunado algo más ligero hoy.",
            "Si ven que empiezo a correr, no me sigan, solo sálvense ustedes.",
            "¿Por qué siempre elegimos los lugares más aterradores?",
            "Siento que nos están observando, ¿ustedes no sienten lo mismo?",
            "Solo espero que lo que sea que vivía aquí esté durmiendo."
        ]
    },

    "viaje": {
        "papel": [
            "El terreno cambia. Manténganse atentos.",
            "Hay marcas recientes en el camino.",
            "Algo ha pasado por esta zona.",
            "Las señales son cada vez más claras.",
            "Este sendero nos está llevando a algún lugar interesante.",
            "El camino se estrecha, caminen con cuidado.",
            "Observen bien a los lados, no dejen pasar ningún detalle.",
            "Si seguimos este rastro, llegaremos directo al punto de interés."
        ],

        "gin": [
            "Este ecosistema parece diferente al anterior.",
            "Las condiciones ambientales están cambiando.",
            "Curioso... no esperaba esta variedad de especies.",
            "La biodiversidad aquí es notable.",
            "Hay patrones interesantes en esta zona.",
            "Analizando el sustrato, diría que estamos cerca de un hábitat único.",
            "El comportamiento de los Pokémon cambió bruscamente, ¿lo notaron?",
            "Las lecturas del escáner están arrojando resultados inusuales."
        ],

        "yogy": [
            "¡Esto apenas está empezando!",
            "¡Sigamos avanzando!",
            "¡Todavía no hemos visto nada!",
            "¡Tengo el presentimiento de que viene algo grande!",
            "¡La aventura está mejorando!",
            "¡Vamos, que el camino se pone cada vez mejor!",
            "¡No se detengan ahora, lo emocionante está más adelante!",
            "¡Qué subidón de adrenalina, esto es exactamente lo que buscaba!"
        ],

        "jorroco": [
            "¿Seguro que vamos por el camino correcto?",
            "Este lugar me da mala espina.",
            "No me gusta el silencio...",
            "¿Soy el único que siente que nos observan?",
            "No sé ustedes, pero yo estoy alerta.",
            "Ese ruido que escuché hace un segundo no me dio buena espina.",
            "¿Podemos ir un poco más despacio? Me estoy quedando atrás.",
            "Cada vez estamos más lejos, ¿y si nos perdemos?"
        ]
    },

    "guarida": {
        "papel": [
            "Estas marcas son enormes...",
            "Nunca había visto rastros tan claros.",
            "Estamos entrando en territorio de algo grande.",
            "El aire aquí abajo es denso y cargado de energía.",
            "Silencio. Ese patrón de raspaduras no es natural.",
            "Cuidado con dónde ponen los pies, este terreno es inestable.",
            "Prepárense, el rastro termina aquí mismo.",
            "Estamos justo en el centro de su dominio, mantengan la calma.",
            "Este lugar parece haber sido excavado a toda prisa."
        ],

        "gin": [
            "Los registros mencionaban algo parecido.",
            "Esto explicaría muchos avistamientos recientes.",
            "Fascinante... realmente fascinante.",
            "La estructura de este habitáculo sugiere una inteligencia sorprendente.",
            "Interesante... los residuos coinciden con una dieta muy específica.",
            "La morfología de estos rastros desafía lo que sabemos de la especie.",
            "Es increíble ver cómo han aprovechado el entorno para protegerse.",
            "Este nivel de sofisticación en la guarida es un descubrimiento científico sin precedentes.",
            "Según el análisis térmico, la criatura debe ser de gran envergadura."
        ],

        "yogy": [
            "¡Por fin se puso interesante!",
            "Yo digo que sigamos adelante.",
            "Si hemos llegado hasta aquí, no pienso dar media vuelta.",
            "¡Miren el tamaño de esas marcas! ¡Esto se va a poner salvaje!",
            "¡Aquí es donde se forjan las leyendas, amigos!",
            "¡No me digan que se van a acobardar justo ahora!",
            "¡Esto es lo que vine a buscar! ¡Vamos directo al centro!",
            "¡Si algo sale de ahí, espero que sea igual de grande que sus huellas!",
            "¡Ni un paso atrás! ¡La mejor parte está empezando ahora!"
        ],

        "jorroco": [
            "¡Les dije que no entráramos aquí!",
            "Esto ya no me gusta nada.",
            "¿Alguien más quiere regresar a la camioneta?",
            "Esto huele mal... literalmente. Deberíamos irnos, ¿verdad?",
            "No quiero ser el primero en entrar, prefiero asegurar la retaguardia.",
            "Creo que prefiero la comodidad de mi casa a este agujero oscuro.",
            "¿Escucharon ese eco? Definitivamente no deberíamos estar aquí.",
            "Por favor, manténganse cerca... este lugar es demasiado lúgubre.",
            "Si aparece algo ahí dentro, juro que salgo corriendo sin avisar."
        ]
    },

    "legendario": {
        "papel": [
            "Esperen... eso no debería estar aquí.",
            "Si mis notas son correctas, estamos ante algo excepcional.",
            "Este podría ser el hallazgo de nuestras vidas.",
            "Cúbranse y observen. No queremos sobresaltarlo.",
            "Mi instinto no me engañaba, aquí hay algo único.",
            "Es impresionante... incluso más imponente que en los relatos.",
            "Mantengan la distancia, una criatura así no se deja ver dos veces.",
            "No hagan movimientos bruscos, es un espécimen magnífico.",
            "El mapa decía que esto era una leyenda, pero aquí está frente a nosotros."
        ],

        "gin": [
            "Las probabilidades de observar algo así son extremadamente bajas.",
            "Increíble. Nunca pensé verlo con mis propios ojos.",
            "Los libros no le hacen justicia.",
            "La evidencia científica no podía preparar nuestra mente para esto.",
            "La oportunidad de observar esto es un privilegio para cualquier académico.",
            "Esto reescribirá los manuales de campo sobre la zona.",
            "La energía que emana es diferente a cualquier cosa que haya registrado.",
            "No puedo creer que esté presenciando un fenómeno de este calibre.",
            "Tengo que registrar cada detalle de su fisiología, es un momento histórico."
        ],

        "yogy": [
            "¡Sabía que algo grande aparecería!",
            "Esto es exactamente por lo que vine.",
            "¡Vamos, esta es nuestra oportunidad!",
            "¡Qué maravilla! ¡Díganme que alguien le tomó una foto a esto!",
            "¡Atrévete a acercarte un poco más, no te arrepentirás!",
            "¡Esto es adrenalina pura! ¡Me encanta!",
            "¡Miren eso! ¡Esto supera cualquier sueño que haya tenido!",
            "¡No pestañeen, nos estamos perdiendo lo mejor!",
            "¡Increíble! ¡Este es el tipo de aventura que contaré toda mi vida!"
        ],

        "jorroco": [
            "¿Eso es normal?",
            "Por favor díganme que eso es amistoso.",
            "No estoy preparado para esto.",
            "¡Cuidado! ¡Está respirando! ¿Verdad que está respirando?",
            "Mis manos no dejan de temblar, no puedo ni sacar la cámara.",
            "Si parpadeo, ¿creen que dejará de mirarme así?",
            "¿Alguien más siente que nos está evaluando?",
            "Díganme que ya terminamos, tengo los nervios destrozados.",
            "No quiero ser grosero, pero... ¿podemos irnos antes de que decida acercarse?"
        ]
    },

    "final": {
        "papel": [
            "Buena expedición. Hemos descubierto bastante hoy.",
            "Anotaré todo lo que vimos.",
            "Cada safari nos enseña algo nuevo.",
            "Registrado. La expedición de hoy ha sido un éxito rotundo.",
            "Tomen aire, hemos cubierto una zona inexplorada.",
            "Un día de campo impecable. Nada que no podamos manejar.",
            "Recogiendo el equipo, el trabajo por hoy ha concluido.",
            "Marquen este punto en el mapa, será útil para futuras visitas.",
            "Buen trabajo equipo, hemos mantenido el rumbo en todo momento."
        ],

        "gin": [
            "Hemos reunido información valiosa.",
            "Fue una expedición muy productiva.",
            "Siempre hay algo nuevo que estudiar.",
            "La cantidad de datos recolectados es, cuanto menos, abrumadora.",
            "Mi bitácora estará llena de observaciones fascinantes esta noche.",
            "Espero que esto sirva para comprender mejor este hábitat.",
            "Los resultados de hoy merecen un análisis exhaustivo en el laboratorio.",
            "He obtenido conclusiones muy interesantes sobre las rutas migratorias.",
            "Una jornada excelente desde el punto de vista académico."
        ],

        "yogy": [
            "Valió completamente la pena.",
            "Yo volvería ahora mismo.",
            "La próxima expedición será todavía mejor.",
            "¡Eso fue épico! ¿Cuándo salimos a la siguiente?",
            "Me voy a casa con una sonrisa de oreja a oreja.",
            "¡Día de diez! Ni un solo minuto desperdiciado.",
            "¡Qué subidón! Esto es vivir al máximo.",
            "¡Ya estoy pensando en qué lugar inexplorado conquistaremos después!",
            "¡Abran paso, que hoy nos hemos ganado una buena cena!"
        ],

        "jorroco": [
            "Sobrevivimos. Eso cuenta como éxito.",
            "Me alegra que haya terminado.",
            "Necesito sentarme un rato después de esto.",
            "Prometo no volver a quejarme del ruido de la ciudad nunca más.",
            "Todavía me tiemblan las piernas, pero al menos estamos de una pieza.",
            "Ha sido el susto de mi vida, por favor, vámonos ya.",
            "¿Ya podemos decir que estamos a salvo?",
            "Mi corazón todavía va a mil por hora, qué experiencia tan intensa.",
            "Voy a necesitar una semana de descanso después de este safari."
        ]
    }

}
FRASES_RUTA = {

    "papel": {
        "izquierda": [
            "Las huellas continúan hacia la izquierda.",
            "Veo señales recientes por ese sendero.",
            "La vegetación está aplastada hacia la izquierda, sigamos por ahí.",
            "Hay un rastro claro que se desvía a la izquierda."
        ],
        "derecha": [
            "Hay marcas interesantes hacia la derecha.",
            "Algo pasó por ese camino.",
            "El terreno hacia la derecha parece menos transitado, es buena señal.",
            "Las pistas se inclinan hacia la derecha, no los pierdan de vista."
        ]
    },

    "gin": {
        "izquierda": [
            "Los datos favorecen la ruta izquierda.",
            "La actividad parece concentrarse hacia la izquierda.",
            "Basándome en las condiciones del suelo, la izquierda es la ruta lógica.",
            "La densidad de especies es mayor siguiendo hacia la izquierda."    
        ],
        "derecha": [
            "Mis observaciones apuntan a la derecha.",
            "La ruta derecha parece más prometedora.",
            "He detectado un patrón de movimiento interesante hacia la derecha.",
            "Los registros sugieren que el espécimen prefiere el sector derecho."
        ]
    },

    "yogy": {
        "izquierda": [
            "¡Izquierda! Tiene pinta de aventura.",
            "¡Yo iría por la izquierda sin pensarlo!",
            "¡La izquierda se ve genial, vamos a ver qué hay!",
            "¡A la izquierda, que ahí es donde está la diversión!"
        ],
        "derecha": [
            "¡La derecha se ve mucho más emocionante!",
            "¡Si buscan acción, vayamos por la derecha!",
            "¡Por la derecha, que ahí huele a descubrimiento épico!",
            "¡Vamos por la derecha! No tengo tiempo para aburrirme."
        ]
    },

    "jorroco": {
        "izquierda": [
            "No sé... pero preferiría la izquierda.",
            "La izquierda parece menos peligrosa.",
            "¿Podemos intentar por la izquierda? Parece más tranquilo.",
            "Si tenemos que elegir, prefiero el camino de la izquierda."
        ],
        "derecha": [
            "Tengo el presentimiento de que la derecha es mejor.",
            "No me pregunten por qué, pero diría derecha.",
            "Me da menos escalofríos ir hacia la derecha, vamos por ahí.",
            "Espero que no se arrepientan, pero yo elijo la derecha."
        ]
    }
}
def obtener_guia_aleatorio():

    guia_id = random.choice(
        list(GUIAS_SAFARI.keys())
    )

    return guia_id, GUIAS_SAFARI[guia_id]


def obtener_frase(
    guia_id,
    contexto
):

    frases = FRASES_GUIA.get(
        contexto,
        {}
    ).get(
        guia_id,
        []
    )

    if not frases:
        return ""

    return random.choice(frases)
PRECISION_GUIAS = {
    "papel": 0.45,
    "gin": 0.65,
    "yogy": 0.50,
    "jorroco": 0.40
}


def obtener_recomendacion_ruta(
    guia_id,
    lado
):

    frases = FRASES_RUTA.get(
        guia_id,
        {}
    ).get(
        lado,
        []
    )

    if not frases:
        return ""

    return random.choice(frases)


def obtener_lado_recomendado(
    guia_id,
    lado_correcto
):

    precision = PRECISION_GUIAS.get(
        guia_id,
        0.50
    )

    acierta = (
        random.random()
        <= precision
    )

    if acierta:
        return lado_correcto

    return (
        "derecha"
        if lado_correcto == "izquierda"
        else "izquierda"
    )