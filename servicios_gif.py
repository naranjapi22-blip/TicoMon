import io
import aiohttp

from PIL import Image
from PIL import ImageSequence
from collections import OrderedDict


R2_PUBLIC_URL = (
    "https://pub-23cb564f6c174627926c1ac0409563d4.r2.dev"
)

CANVAS_W = 274
CANVAS_H = 235

MAX_CACHE = 256

_http_session = None

_gif_cache = OrderedDict()
_render_cache = OrderedDict()


async def _get_session():

    global _http_session

    if (
        _http_session is None
        or _http_session.closed
    ):

        _http_session = aiohttp.ClientSession()

    return _http_session


def _cache_get(cache, key):

    if key not in cache:

        return None

    cache.move_to_end(key)

    return cache[key]


def _cache_set(cache, key, value):

    cache[key] = value

    cache.move_to_end(key)

    while len(cache) > MAX_CACHE:

        cache.popitem(last=False)
async def _descargar_original(
    dex_id: int,
    es_shiny: bool
):

    carpeta = (
        "shiny"
        if es_shiny
        else
        "regular"
    )

    url = (
        f"{R2_PUBLIC_URL}/"
        f"{carpeta}/"
        f"{dex_id}.gif"
    )

    cache_key = (
        dex_id,
        es_shiny
    )

    datos = _cache_get(
        _gif_cache,
        cache_key
    )

    if datos is not None:

        return datos

    session = await _get_session()

    async with session.get(url) as resp:

        if resp.status != 200:

            raise RuntimeError(
                f"No se pudo descargar {url}"
            )

        datos = await resp.read()

    _cache_set(
        _gif_cache,
        cache_key,
        datos
    )

    return datos


def _abrir_gif(
    gif_bytes
):

    return Image.open(
        io.BytesIO(gif_bytes)
    )
def _escalar_frames(
    gif,
    display_scale=1.0
):

    frames = []
    durations = []

    loop = gif.info.get(
        "loop",
        0
    )

    # -------------------------
    # BBOX GLOBAL
    # -------------------------

    min_x = 999999
    min_y = 999999
    max_x = 0
    max_y = 0

    temp_frames = []

    for frame in ImageSequence.Iterator(gif):

        frame = frame.convert("RGBA")

        temp_frames.append(frame)

        bbox = frame.getbbox()

        if bbox is None:
            continue

        min_x = min(min_x, bbox[0])
        min_y = min(min_y, bbox[1])
        max_x = max(max_x, bbox[2])
        max_y = max(max_y, bbox[3])

    if max_x <= min_x or max_y <= min_y:

        min_x = 0
        min_y = 0
        max_x = 1
        max_y = 1

    # -------------------------
    # RECORTAR SIEMPRE IGUAL
    # -------------------------

    for frame in temp_frames:

        sprite = frame.crop(
            (
                min_x,
                min_y,
                max_x,
                max_y
            )
        )

        nuevo_w = max(
            1,
            int(
                sprite.width *
                display_scale
            )
        )

        nuevo_h = max(
            1,
            int(
                sprite.height *
                display_scale
            )
        )

        try:

            resample = Image.Resampling.LANCZOS

        except AttributeError:

            resample = Image.LANCZOS

        sprite = sprite.resize(
            (
                nuevo_w,
                nuevo_h
            ),
            resample
        )

        canvas = Image.new(
            "RGBA",
            (
                CANVAS_W,
                CANVAS_H
            ),
            (
                0,
                0,
                0,
                0
            )
        )

        x = (
            CANVAS_W -
            sprite.width
        ) // 2

        y = (
            CANVAS_H -
            sprite.height
        ) // 2

        canvas.alpha_composite(
            sprite,
            (
                x,
                y
            )
        )

        frames.append(canvas)

        durations.append(
            frame.info.get(
                "duration",
                gif.info.get(
                    "duration",
                    100
                )
            )
        )

    return (
        frames,
        durations,
        loop
    )
def _crear_gif(
    frames,
    durations,
    loop
):

    salida = io.BytesIO()

    frames[0].save(
        salida,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=loop,
        disposal=2,
        optimize=False
    )

    salida.seek(0)

    return salida


async def obtener_gif(
    dex_id: int,
    es_shiny: bool = False,
    display_scale: float = 1.0
):

    cache_key = (
        dex_id,
        es_shiny,
        round(display_scale, 2)
    )

    datos = _cache_get(
        _render_cache,
        cache_key
    )

    if datos is not None:

        return io.BytesIO(datos)

    gif_bytes = await _descargar_original(
        dex_id,
        es_shiny
    )

    gif = _abrir_gif(
        gif_bytes
    )

    frames, durations, loop = _escalar_frames(
        gif,
        display_scale
    )

    buffer = _crear_gif(
        frames,
        durations,
        loop
    )

    datos = buffer.getvalue()

    _cache_set(
        _render_cache,
        cache_key,
        datos
    )

    return io.BytesIO(datos)
def limpiar_cache():

    _gif_cache.clear()

    _render_cache.clear()


async def cerrar_sesion():

    global _http_session

    if (
        _http_session is not None
        and not _http_session.closed
    ):

        await _http_session.close()

    _http_session = None