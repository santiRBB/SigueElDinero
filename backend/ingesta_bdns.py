"""
Ingesta de concesiones de BDNS (Base de Datos Nacional de Subvenciones) por comunidad autonoma,
agregadas mes a mes (SigueElDinero, fase 2).

Fuente: API publica de BDNS (https://www.infosubvenciones.es/bdnstrans/api/concesiones/busqueda),
sin API key.

Uso:
    python ingesta_bdns.py --mes 2026-08
    python ingesta_bdns.py --mes 2026-08 --desde-raw   # reprocesa desde raw/2026-08.jsonl.gz, sin red
    python ingesta_bdns.py --mes 2026-08 --continuar   # retoma un raw parcial en vez de arrancar de 0

Salidas (en ./salida_bdns/):
    raw/{YYYY-MM}.jsonl.gz                 -> concesiones crudas de ese mes, tal cual las devuelve la API
    agregado_ccaa_{YYYY-MM}.jsonl          -> una fila por CCAA con el total agregado de ese mes
    agregado_ccaa_organismo_{YYYY-MM}.jsonl -> top 15 organismos por importe y CCAA (+ "OTROS")
    sin_ccaa_asignada_{YYYY-MM}.jsonl      -> concesiones ESTATAL, o LOCAL sin organismo reconocido

Notas de diseno:
    - Cada mes se sobreescribe por completo en cada corrida (no se acumula) -> idempotente ante
      reprocesos. La corrida diaria reprocesa el mes en curso y el anterior; el backfill historico
      se corre mes a mes a mano.
      Ver docs/superpowers/specs/2026-08-30-bdns-concesiones-ccaa-pipeline-design.md
    - resolver_ccaa nunca lanza: una fila que no matchea ninguna CCAA se manda a sin_asignar,
      no interrumpe la ingesta del mes.
"""

import argparse
import calendar
import contextlib
import gzip
import json
import logging
import os
import re
import tempfile
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingesta_bdns")

BUSQUEDA_URL = "https://www.infosubvenciones.es/bdnstrans/api/concesiones/busqueda"
PAGE_SIZE = 1000
PAUSA_ENTRE_PAGINAS = 0.3
REINTENTOS = 5
# Base de la espera exponencial entre reintentos de una misma pagina (independiente de
# PAUSA_ENTRE_PAGINAS, que es la pausa entre paginas exitosas): 3, 6, 12, 24s, tope 30s. Subido desde
# un maximo de ~1.2s despues de que el backfill historico se cayera dos veces en un dia (2026-09-01 y
# 2026-09-02) por rachas de "The read operation timed out" en BDNS que duraban mas que el backoff
# viejo -- una pausa tan corta reintentaba contra el mismo bache de lentitud del servidor en vez de
# darle tiempo a recuperarse.
BACKOFF_BASE_REINTENTO = 3.0
BACKOFF_TOPE_REINTENTO = 30.0
# Timeout HTTP: el read timeout viejo (30s) coincidia exacto con la duracion de los timeouts vistos
# en produccion, lo que sugiere paginas que tardaban justo un poco mas de 30s en responder bajo
# carga (no una conexion muerta) y que un timeout mas generoso hubiera dejado completar.
HTTPX_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)

OUTPUT_DIR = Path("./salida_bdns")
RAW_DIR = OUTPUT_DIR / "raw"

CCAA_LOOKUP_PATH = Path(__file__).parent / "ccaa_lookup.json"
with open(CCAA_LOOKUP_PATH, "r", encoding="utf-8") as f:
    CCAA_LOOKUP = json.load(f)

# pais_lookup.json excluye deliberadamente nombres de pais que colisionan con nombres de lugares o
# instituciones espanolas comunes: ESPANA, GRANADA y SANTA LUCIA se sacaron de ahi despues de
# observar falsos positivos reales contra datos de produccion (una subvencion domestica a "LA
# COORDINADORA DE ONGD ESPANA" resolviendo a Espana como pais receptor; "Universidad de Granada" a
# Grenada; "Santa Lucia de Tirajana", un municipio de Gran Canaria, a Santa Lucia) -- ver spec de
# diseno. No los vuelvas a agregar sin resolver antes esa ambiguedad.
PAIS_LOOKUP_PATH = Path(__file__).parent / "pais_lookup.json"
with open(PAIS_LOOKUP_PATH, "r", encoding="utf-8") as f:
    PAIS_LOOKUP = json.load(f)

_PAIS_LOOKUP_POR_LARGO = sorted(PAIS_LOOKUP.items(), key=lambda kv: len(kv[0]), reverse=True)

NIVEL3_AECID = "AGENCIA ESTATAL AGENCIA ESPAÑOLA DE COOPERACIÓN INTERNACIONAL PARA EL DESARROLLO"


def normalizar(texto):
    """Mayusculas, sin tildes, espacios colapsados -- para matchear nombres BDNS contra
    ccaa_lookup.json sin depender de que la fuente sea consistente con acentos/espacios."""
    if not texto:
        return ""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return " ".join(sin_tildes.upper().split())


def resolver_ccaa(fila):
    """Codigo INE de dim_ccaa para una concesion, o None si no se puede asignar
    (ESTATAL, o LOCAL cuyo organismo no esta en ccaa_lookup.json)."""
    nivel1 = fila.get("nivel1")
    nivel2_norm = normalizar(fila.get("nivel2"))

    if nivel1 == "AUTONOMICA":
        return CCAA_LOOKUP["autonomica"].get(nivel2_norm)

    if nivel1 == "LOCAL":
        if nivel2_norm in CCAA_LOOKUP["local_exacto"]:
            return CCAA_LOOKUP["local_exacto"][nivel2_norm]
        for keyword, lugares in CCAA_LOOKUP["local_patron"].items():
            if keyword.upper() not in nivel2_norm:
                continue
            for lugar, codigo_ine in lugares.items():
                if lugar in nivel2_norm:
                    return codigo_ine
        return None

    return None


def resolver_pais_aecid(texto):
    """iso_alpha3 si `texto` (el campo "convocatoria" de una concesion BDNS) menciona
    exactamente un pais de PAIS_LOOKUP sin ambiguedad, o None si no menciona ninguno o menciona
    mas de uno.

    Dos salvaguardas contra falsos positivos, ambas necesarias:
    - Limite de palabra (\\b): "JORDANIA" no debe matchear dentro de "CISJORDANIA".
    - Preferencia por el nombre mas largo que matchea en cada posicion, marcando esos caracteres
      como ocupados: sin esto, un texto que solo menciona "GUINEA-BISAU" contaria como DOS paises
      (GUINEA y GUINEA-BISAU, porque "GUINEA" tambien matchea con limite de palabra ahi mismo:
      el guion es un caracter no alfanumerico) y se descartaria como ambiguo por error.

    Nunca adivina: cobertura baja es preferible a un pais incorrecto (ver spec)."""
    if not texto:
        return None
    texto_norm = normalizar(texto)
    ocupado = [False] * len(texto_norm)
    paises_encontrados = set()
    for nombre, iso_alpha3 in _PAIS_LOOKUP_POR_LARGO:
        patron = r"\b" + re.escape(nombre) + r"\b"
        for match in re.finditer(patron, texto_norm):
            inicio, fin = match.span()
            if any(ocupado[inicio:fin]):
                continue
            for i in range(inicio, fin):
                ocupado[i] = True
            paises_encontrados.add(iso_alpha3)
    if len(paises_encontrados) == 1:
        return paises_encontrados.pop()
    return None


def es_concesion_aecid(fila):
    """True si la fila es una concesion de BDNS otorgada directamente por AECID (nivel1=ESTADO,
    nivel3 con el nombre exacto de la agencia -- verificado estable en muestras de 2022 a 2026)."""
    return fila.get("nivel1") == "ESTADO" and normalizar(fila.get("nivel3")) == normalizar(NIVEL3_AECID)


def ultimo_dia_mes(anio, mes):
    return calendar.monthrange(anio, mes)[1]


def _get_con_reintentos(client, url, params):
    """Pide una pagina con reintentos: cubre tanto el fallo de red (client.get/raise_for_status)
    como el de parseo del cuerpo (resp.json()) con la misma logica de backoff. Una respuesta que
    llego pero vino corrupta (JSON invalido, codificacion invalida -- se vio en produccion bajo
    carga con varias corridas en paralelo) es tan transitoria como un timeout de red; antes se
    escapaba de este reintento y tiraba todo el mes en curso en vez de solo esa pagina. Devuelve el
    dict ya parseado, no la respuesta cruda."""
    for intento in range(1, REINTENTOS + 1):
        try:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if intento == REINTENTOS:
                raise
            espera = min(BACKOFF_BASE_REINTENTO * (2 ** (intento - 1)), BACKOFF_TOPE_REINTENTO)
            log.warning(
                "Fallo en pagina %s (intento %d/%d): %s -- reintentando en %.1fs",
                params.get("page"), intento, REINTENTOS, e, espera,
            )
            time.sleep(espera)


def _acumular_fila(fila, totales_ccaa, totales_organismo, sin_asignar, ids_vistos, concesiones_aecid=None):
    """Aplica resolver_ccaa a una fila y actualiza los cuatro acumuladores in-place. Reutilizada
    tanto por procesar_mes (paginando la API en vivo) como por reprocesar_desde_raw (releyendo un
    raw/*.jsonl.gz ya descargado, sin red) -- misma logica de agregacion sin importar de donde
    vinieron las filas.

    ids_vistos es un set de "id" de concesion ya contabilizados en este mes (incluye los que ya
    estaban en disco de una corrida anterior si se esta retomando con --continuar, ver
    _cargar_checkpoint). Defensa contra que la misma concesion aparezca en mas de una pagina: la API
    de BDNS no acepta ningun parametro de orden explicito, y se confirmo el 2026-09-03 que su
    totalElements/last no es fiable a partir de cierto volumen (la misma consulta de un solo dia
    devolvio 2.147.627 y 48.974 en llamadas distintas) -- sin un orden estable, un mes que tarda
    horas en paginarse contra un dataset que se sigue escribiendo en vivo puede ver la misma fila
    desplazarse de pagina. Devuelve True si la fila era un duplicado (se descarta sin tocar ningun
    acumulador ni concesiones_aecid), False en caso contrario. Una fila sin "id" nunca se considera
    duplicada (no deberia pasar en datos reales de la API, pero por si acaso no se descarta a ciegas).

    concesiones_aecid es un canal ADICIONAL, no una rama alternativa: una fila de AECID
    (es_concesion_aecid) sigue yendo tambien a sin_asignar como antes (nivel1=ESTADO nunca matchea
    ninguna CCAA), y ademas se agrega aqui si concesiones_aecid no es None."""
    fila_id = fila.get("id")
    if fila_id is not None:
        if fila_id in ids_vistos:
            return True
        ids_vistos.add(fila_id)

    if concesiones_aecid is not None and es_concesion_aecid(fila):
        concesiones_aecid.append(fila)

    codigo_ine = resolver_ccaa(fila)
    if codigo_ine is None:
        sin_asignar.append(fila)
        return False

    importe = fila.get("importe") or 0.0

    acumulado = totales_ccaa.setdefault(
        codigo_ine, {"importe_total_eur": 0.0, "n_concesiones": 0}
    )
    acumulado["importe_total_eur"] += importe
    acumulado["n_concesiones"] += 1

    organismo = (fila.get("nivel3") or "").strip() or "SIN ORGANISMO"
    org_dict = totales_organismo.setdefault(codigo_ine, {})
    acumulado_org = org_dict.setdefault(
        organismo, {"importe_total_eur": 0.0, "n_concesiones": 0}
    )
    acumulado_org["importe_total_eur"] += importe
    acumulado_org["n_concesiones"] += 1
    return False


def _acumular_fila_incremental(fila, totales_ccaa, totales_organismo, sin_asignar, ids_vistos, concesiones_aecid=None):
    """Igual que _acumular_fila, pero indexa totales_ccaa/totales_organismo por (codigo_ine, anio,
    mes) en vez de por codigo_ine solo -- necesario porque procesar_incremental no esta acotado a un
    unico mes: pagina el feed global de BDNS sin filtro de fecha, asi que una misma corrida puede
    traer filas de meses distintos (esa es justamente la ventaja: una concesion dada de alta hoy con
    fechaConcesion de hace 3 meses se agrega correctamente a ese mes viejo, no al mes en curso)."""
    fila_id = fila.get("id")
    if fila_id is not None:
        if fila_id in ids_vistos:
            return True
        ids_vistos.add(fila_id)

    if concesiones_aecid is not None and es_concesion_aecid(fila):
        concesiones_aecid.append(fila)

    codigo_ine = resolver_ccaa(fila)
    if codigo_ine is None:
        sin_asignar.append(fila)
        return False

    fecha_concesion = fila.get("fechaConcesion") or ""
    anio, mes = int(fecha_concesion[:4]), int(fecha_concesion[5:7])
    clave = (codigo_ine, anio, mes)

    importe = fila.get("importe") or 0.0
    acumulado = totales_ccaa.setdefault(clave, {"importe_total_eur": 0.0, "n_concesiones": 0})
    acumulado["importe_total_eur"] += importe
    acumulado["n_concesiones"] += 1

    organismo = (fila.get("nivel3") or "").strip() or "SIN ORGANISMO"
    org_dict = totales_organismo.setdefault(clave, {})
    acumulado_org = org_dict.setdefault(organismo, {"importe_total_eur": 0.0, "n_concesiones": 0})
    acumulado_org["importe_total_eur"] += importe
    acumulado_org["n_concesiones"] += 1
    return False


MAX_PAGINAS_INCREMENTAL = 500
# A diferencia de MAX_PAGINAS_POR_MES (pensado para un mes completo, potencialmente millones de
# filas), una corrida incremental solo deberia necesitar del orden de decenas a un centenar de
# paginas por dia (ver docs/superpowers/specs/2026-09-06-bdns-ingesta-incremental-design.md: entre
# la pagina 0 y la 100 del feed sin filtrar ya se paso de "ayer" a "anteayer" en fechaAlta). Si una
# corrida incremental supera esto sin llegar al watermark, lo mas probable es un watermark corrompido
# o sembrado mal -- investigar, no subir el numero a ciegas.


def procesar_incremental(client, raw_writer, ultimo_id_procesado):
    """Pagina /concesiones/busqueda SIN fechaDesde/fechaHasta -- el feed global de BDNS, verificado
    empiricamente (2026-09-06) estable en orden descendente por id (que se correlaciona con
    fechaAlta: en la practica, orden de insercion). Corta apenas encuentra una fila con
    id <= ultimo_id_procesado -- todo lo que sigue en esa pagina y en las siguientes ya fue contado
    en una corrida anterior, no hace falta seguir pidiendo.

    A diferencia de procesar_mes, los acumuladores quedan indexados por (codigo_ine, anio, mes) en
    vez de por un unico mes fijo -- ver _acumular_fila_incremental.

    Devuelve (totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, max_id_visto,
    num_paginas). max_id_visto es el id mas alto encontrado en la corrida (el primero de la pagina 0,
    por construccion del orden descendente) -- es lo que escribir_salidas_incremental graba para que
    cargar_bdns.py sepa hasta donde avanzar el watermark en la proxima corrida. Es None si no habia
    ninguna fila nueva (la corrida no encontro nada por encima de ultimo_id_procesado)."""
    totales_ccaa = {}
    totales_organismo = {}
    sin_asignar = []
    concesiones_aecid = []
    ids_vistos = set()
    max_id_visto = None

    page = 0
    num_paginas = 0
    terminado = False
    while True:
        data = _get_con_reintentos(client, BUSQUEDA_URL, {"page": page, "pageSize": PAGE_SIZE})
        num_paginas += 1

        if not data["content"]:
            break

        for fila in data["content"]:
            fila_id = fila.get("id")
            if fila_id is not None and fila_id <= ultimo_id_procesado:
                terminado = True
                break
            if max_id_visto is None:
                max_id_visto = fila_id
            raw_writer.write(json.dumps(fila, ensure_ascii=False) + "\n")
            _acumular_fila_incremental(fila, totales_ccaa, totales_organismo, sin_asignar, ids_vistos, concesiones_aecid)

        if terminado:
            break
        if num_paginas >= MAX_PAGINAS_INCREMENTAL:
            raise SystemExit(
                f"Se superaron las {MAX_PAGINAS_INCREMENTAL} paginas ({MAX_PAGINAS_INCREMENTAL * PAGE_SIZE} "
                f"filas) sin llegar al watermark (id={ultimo_id_procesado}). Muy por encima de lo "
                f"esperado para una corrida diaria -- investigar el watermark antes de reintentar."
            )
        page += 1
        time.sleep(PAUSA_ENTRE_PAGINAS)

    return totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, max_id_visto, num_paginas


MAX_PAGINAS_POR_MES = 20000
# Tope de seguridad (20000 paginas x PAGE_SIZE = 20.000.000 de filas). No es un numero fino: el
# 2026-09-03 se vio que /concesiones/busqueda?fechaDesde=01/12/2025&fechaHasta=31/12/2025 devolvio
# 910.382, luego 6.077.077, y una consulta de un solo dia devolvio 2.147.627 y 48.974 en llamadas
# distintas -- pero tambien se vio que el 6.077.077 se repitio casi exacto (6.077.068) horas despues
# desde la propia web, y que la lectura mas baja (910.382 y el "107 paginas" posterior) pudo tener
# algun filtro extra aplicado sin querer (paso de verdad con un filtro de "Partidos politicos" que se
# colo en una de esas capturas). Osea: no hay certeza de si diciembre 2025 es un mes genuinamente
# enorme (varios millones de filas reales) o si el conteo de la API sigue siendo poco fiable -- ver
# docs/superpowers/... o memoria del 2026-09-03 para el detalle. Este tope ya no intenta detectar "el
# conteo esta roto" (eso dejo de poder afirmarse con confianza); solo evita que un bug real de otro
# tipo (p.ej. el filtro de fechas fallando del todo, que devuelve el historico completo de BDNS,
# ~29.5M filas a esta fecha) pagine durante dias sin que nadie se entere. Si un mes real llega a este
# tope, es mas probable que sea genuinamente ese tipo de bug que un mes normal -- investigar, no
# simplemente subir el numero.


def procesar_mes(
    anio, mes, client, raw_writer,
    totales_ccaa=None, totales_organismo=None, sin_asignar=None, concesiones_aecid=None,
    ids_vistos=None, pagina_inicial=0,
):
    """Pagina /concesiones/busqueda desde pagina_inicial (0 por defecto, es decir el mes completo)
    hasta el final, agrega por CCAA y por organismo dentro de cada CCAA, recolecta aparte las
    concesiones otorgadas directamente por AECID (ver es_concesion_aecid), y devuelve (totales_ccaa,
    totales_organismo, sin_asignar, concesiones_aecid, num_paginas). Cada fila se escribe a medida
    que llega en raw_writer (cualquier objeto con .write(str) -> None, p.ej. un gzip.open(...) en
    modo texto) -- no acumula las filas crudas en memoria. Quien llama controla el ciclo de vida del
    archivo (abrirlo, pasarlo aqui, cerrarlo); ver main(). num_paginas permite detectar en los logs
    una respuesta prematuramente truncada por la API.

    El corte de paginacion es unicamente `not data["content"]` (pagina vacia) -- el campo "last" que
    devuelve la API se ignora deliberadamente desde el 2026-09-03: esta calculado a partir del mismo
    totalElements que se confirmo poco fiable a este volumen (ver MAX_PAGINAS_POR_MES arriba), asi
    que confiar en "last" puede cortar la paginacion antes de tiempo (con "last": true en una pagina
    que en realidad no es la ultima) tanto como no cortarla nunca. Una pagina vacia siempre significa
    "no hay mas filas que matcheen", venga o no acompanada de un "last" correcto.

    Los cinco acumuladores (incluido ids_vistos, ver _acumular_fila) aceptan valores ya iniciados (en
    vez de vacios) para retomar un mes cortado a mitad de camino -- ver main() y el flag --continuar:
    como cada fila ya escrita en el raw de una corrida anterior sigue integra en disco (el gzip se
    cierra bien incluso si procesar_mes termina en excepcion, solo un kill del proceso lo dejaria a
    medias), alcanza con re-sumar esas filas y pedir desde pagina_inicial en adelante, en vez de
    reprocesar el mes entero de nuevo."""
    fecha_desde = f"01/{mes:02d}/{anio}"
    fecha_hasta = f"{ultimo_dia_mes(anio, mes):02d}/{mes:02d}/{anio}"

    totales_ccaa = {} if totales_ccaa is None else totales_ccaa
    totales_organismo = {} if totales_organismo is None else totales_organismo
    sin_asignar = [] if sin_asignar is None else sin_asignar
    concesiones_aecid = [] if concesiones_aecid is None else concesiones_aecid
    ids_vistos = set() if ids_vistos is None else ids_vistos

    page = pagina_inicial
    num_paginas = 0
    n_duplicados = 0
    while True:
        data = _get_con_reintentos(client, BUSQUEDA_URL, {
            "page": page, "pageSize": PAGE_SIZE,
            "fechaDesde": fecha_desde, "fechaHasta": fecha_hasta,
        })
        num_paginas += 1

        for fila in data["content"]:
            raw_writer.write(json.dumps(fila, ensure_ascii=False) + "\n")
            if _acumular_fila(fila, totales_ccaa, totales_organismo, sin_asignar, ids_vistos, concesiones_aecid):
                n_duplicados += 1

        if not data["content"]:
            break
        if num_paginas >= MAX_PAGINAS_POR_MES:
            raise SystemExit(
                f"Se superaron las {MAX_PAGINAS_POR_MES} paginas ({MAX_PAGINAS_POR_MES * PAGE_SIZE} "
                f"filas) procesando {anio:04d}-{mes:02d} sin que la API devolviera una pagina vacia. "
                f"Muy por encima de cualquier mes real visto hasta ahora -- ver MAX_PAGINAS_POR_MES. "
                f"Investigar antes de reintentar (y antes de subir el limite)."
            )
        page += 1
        time.sleep(PAUSA_ENTRE_PAGINAS)

    if n_duplicados:
        log.warning(
            "Se descartaron %d filas duplicadas (mismo id ya visto) procesando %04d-%02d.",
            n_duplicados, anio, mes,
        )

    return totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, num_paginas


TOP_ORGANISMOS_POR_MES = 15


def recortar_top_organismos(totales_organismo, n=TOP_ORGANISMOS_POR_MES):
    """Por CCAA, se queda con los n organismos de mayor importe y agrupa el resto en "OTROS" --
    dentro de esa misma CCAA, nunca fuera de ella (el total de fact_gasto_ccaa/totales_ccaa no se
    toca). Si "OTROS" ya es uno de los organismos reales de mayor importe, el sobrante se suma a esa
    fila en vez de pisarla."""
    resultado = {}
    for codigo_ine, organismos in totales_organismo.items():
        ordenados = sorted(organismos.items(), key=lambda kv: kv[1]["importe_total_eur"], reverse=True)
        top = dict(ordenados[:n])
        resto = ordenados[n:]
        if resto:
            existente = top.get("OTROS", {"importe_total_eur": 0.0, "n_concesiones": 0})
            top["OTROS"] = {
                "importe_total_eur": existente["importe_total_eur"] + sum(v["importe_total_eur"] for _, v in resto),
                "n_concesiones": existente["n_concesiones"] + sum(v["n_concesiones"] for _, v in resto),
            }
        resultado[codigo_ine] = top
    return resultado


def _escribir_atomico(ruta, lineas):
    """Escribe `lineas` (un iterable de str, sin salto de linea) en `ruta` de forma atomica: primero
    a un archivo temporal en el mismo directorio, y solo al terminar sin errores lo renombra al
    nombre final con os.replace (atomico en POSIX y en Windows desde Python 3.3).

    Evita que un backfill_bdns.py que revisa "existe agregado_ccaa_{mes}.jsonl?" para saltear un mes
    ya procesado confunda un archivo truncado a medio escribir (proceso matado, corte de luz) con un
    mes completo: bajo este esquema, el archivo con el nombre final solo aparece una vez que esta
    integro.
    """
    tmp_fd, tmp_path = tempfile.mkstemp(dir=ruta.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            for linea in lineas:
                f.write(linea + "\n")
        os.replace(tmp_path, ruta)
    except Exception:
        os.unlink(tmp_path)
        raise


def escribir_salidas(anio, mes, totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid=None):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sufijo = f"{anio}-{mes:02d}"

    _escribir_atomico(
        OUTPUT_DIR / f"agregado_ccaa_{sufijo}.jsonl",
        (
            json.dumps({
                "codigo_ine": codigo_ine, "anio": anio, "mes": mes,
                "importe_total_eur": round(totales["importe_total_eur"], 2),
                "n_concesiones": totales["n_concesiones"],
            }, ensure_ascii=False)
            for codigo_ine, totales in totales_ccaa.items()
        ),
    )

    _escribir_atomico(
        OUTPUT_DIR / f"agregado_ccaa_organismo_{sufijo}.jsonl",
        (
            json.dumps({
                "codigo_ine": codigo_ine, "anio": anio, "mes": mes,
                "organismo": organismo,
                "importe_total_eur": round(totales["importe_total_eur"], 2),
                "n_concesiones": totales["n_concesiones"],
            }, ensure_ascii=False)
            for codigo_ine, organismos in totales_organismo.items()
            for organismo, totales in organismos.items()
        ),
    )

    _escribir_atomico(
        OUTPUT_DIR / f"sin_ccaa_asignada_{sufijo}.jsonl",
        (json.dumps(fila, ensure_ascii=False) for fila in sin_asignar),
    )

    _escribir_atomico(
        OUTPUT_DIR / f"agregado_aecid_{sufijo}.jsonl",
        (
            json.dumps({
                "concesion_id": fila.get("id"),
                "numero_convocatoria": str(fila.get("numeroConvocatoria")),
                "iso_alpha3": resolver_pais_aecid(fila.get("convocatoria")),
                "beneficiario": fila.get("beneficiario"),
                "titulo": fila.get("convocatoria"),
                "importe_eur": round(fila.get("importe") or 0.0, 2),
                "fecha_concesion": fila.get("fechaConcesion"),
            }, ensure_ascii=False)
            for fila in (concesiones_aecid or [])
        ),
    )


def escribir_salidas_incremental(fecha, totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, max_id_visto):
    """Analoga a escribir_salidas, pero para una corrida de procesar_incremental: totales_ccaa y
    totales_organismo vienen indexados por (codigo_ine, anio, mes) en vez de por un unico mes, y no
    se aplica recortar_top_organismos -- una porcion diaria pequeña de organismos no es
    representativa del mes completo, y capearla a top-15 produciria un "OTROS" incorrecto que se
    sumaria mal en cargar_bdns.py. La reconciliacion semanal (que si ve el mes completo) es quien
    vuelve a normalizar fact_gasto_ccaa_organismo a top-15+OTROS.

    El nombre del archivo AECID (agregado_aecid_incremental-{fecha}.jsonl) esta elegido a proposito
    para matchear el glob "agregado_aecid_*.jsonl" que ya usa cargar_aecid_bdns.py sin necesitar
    ningun cambio en ese script."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    _escribir_atomico(
        OUTPUT_DIR / f"incremental_agregado_ccaa_{fecha}.jsonl",
        (
            json.dumps({
                "codigo_ine": codigo_ine, "anio": anio, "mes": mes,
                "importe_total_eur": round(totales["importe_total_eur"], 2),
                "n_concesiones": totales["n_concesiones"],
            }, ensure_ascii=False)
            for (codigo_ine, anio, mes), totales in totales_ccaa.items()
        ),
    )

    _escribir_atomico(
        OUTPUT_DIR / f"incremental_agregado_ccaa_organismo_{fecha}.jsonl",
        (
            json.dumps({
                "codigo_ine": codigo_ine, "anio": anio, "mes": mes,
                "organismo": organismo,
                "importe_total_eur": round(totales["importe_total_eur"], 2),
                "n_concesiones": totales["n_concesiones"],
            }, ensure_ascii=False)
            for (codigo_ine, anio, mes), organismos in totales_organismo.items()
            for organismo, totales in organismos.items()
        ),
    )

    _escribir_atomico(
        OUTPUT_DIR / f"sin_ccaa_asignada_incremental_{fecha}.jsonl",
        (json.dumps(fila, ensure_ascii=False) for fila in sin_asignar),
    )

    _escribir_atomico(
        OUTPUT_DIR / f"agregado_aecid_incremental-{fecha}.jsonl",
        (
            json.dumps({
                "concesion_id": fila.get("id"),
                "numero_convocatoria": str(fila.get("numeroConvocatoria")),
                "iso_alpha3": resolver_pais_aecid(fila.get("convocatoria")),
                "beneficiario": fila.get("beneficiario"),
                "titulo": fila.get("convocatoria"),
                "importe_eur": round(fila.get("importe") or 0.0, 2),
                "fecha_concesion": fila.get("fechaConcesion"),
            }, ensure_ascii=False)
            for fila in (concesiones_aecid or [])
        ),
    )

    (OUTPUT_DIR / f"incremental_max_id_{fecha}.txt").write_text(str(max_id_visto), encoding="utf-8")


def _ruta_marcador_completo(sufijo):
    """Archivo vacio que solo existe cuando procesar_mes termino de paginar un mes entero con
    exito (ver main()). Su ausencia es la unica forma confiable de distinguir un
    raw/{sufijo}.jsonl.gz genuinamente completo de uno que quedo a medias por una corrida
    interrumpida (timeout agotado, proceso cortado) -- ambos casos son gzips perfectamente
    legibles, la diferencia no se nota mirando el archivo en si."""
    return RAW_DIR / f"{sufijo}.completo"


def _ruta_lock(sufijo):
    return RAW_DIR / f"{sufijo}.lock"


@contextlib.contextmanager
def _lock_mes(sufijo):
    """Evita que dos corridas (--continuar, --desde-raw, o ambas, de este script o via
    backfill_bdns.py) toquen el raw de un mismo mes al mismo tiempo: dos procesos leyendo/escribiendo
    el mismo raw/{sufijo}.jsonl.gz en paralelo corrompen la lectura del gzip a medio escribir y
    hacen perder todo el progreso ya bajado de ese mes. Si el lock ya existe asumimos que hay otra
    corrida activa y abortamos de una; si en realidad quedo huerfano por un kill duro del proceso
    anterior, hay que borrarlo a mano antes de reintentar."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = _ruta_lock(sufijo)
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit(
            f"Ya hay otra corrida en curso para {sufijo} (existe {lock_path}). Si estas seguro de "
            f"que no es asi -- quedo huerfano por un proceso cortado a la fuerza -- borralo a mano "
            f"y volve a correr."
        )
    with os.fdopen(fd, "w") as f:
        f.write(str(os.getpid()))
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def reprocesar_desde_raw(anio, mes):
    """Reconstruye las salidas agregadas (agregado_ccaa, agregado_ccaa_organismo,
    sin_ccaa_asignada, agregado_aecid) de un mes a partir de su raw/{YYYY-MM}.jsonl.gz ya
    descargado, sin volver a pegarle a la API de BDNS. Pensado para poblar
    agregado_ccaa_organismo_{YYYY-MM}.jsonl en meses que ya se habian backfilleado antes de que ese
    desglose existiera (o, ahora, agregado_aecid_{YYYY-MM}.jsonl en meses backfilleados antes de que
    esta fuente existiera) -- y de paso, si ccaa_lookup.json o pais_lookup.json crecieron despues de
    esa corrida original, mejora tambien la asignacion.

    Lanza SystemExit si no existe el raw de ese mes, o si existe pero no tiene su marcador de mes
    completo (ver _ruta_marcador_completo) -- reprocesar un raw parcial produciria un agregado
    incompleto sin ningun aviso, exactamente el bug real que este chequeo existe para evitar."""
    sufijo = f"{anio}-{mes:02d}"
    raw_path = RAW_DIR / f"{sufijo}.jsonl.gz"
    if not raw_path.exists():
        raise SystemExit(
            f"No existe {raw_path} -- hace falta el raw original para reprocesar sin red "
            f"(correr primero `python ingesta_bdns.py --mes {sufijo}` contra la API)."
        )
    if not _ruta_marcador_completo(sufijo).exists():
        raise SystemExit(
            f"{raw_path} existe pero no tiene marcador de mes completo -- probablemente quedo "
            f"parcial por una corrida interrumpida. Reprocesarlo asi produciria un agregado "
            f"incompleto sin avisar. Termina de bajarlo primero con "
            f"`python ingesta_bdns.py --mes {sufijo} --continuar` (retoma desde donde quedo) "
            f"o sin --continuar para arrancar de cero."
        )

    log.info("Reprocesando %s desde raw local (sin red)...", sufijo)
    totales_ccaa = {}
    totales_organismo = {}
    sin_asignar = []
    concesiones_aecid = []
    ids_vistos = set()
    try:
        with gzip.open(raw_path, "rt", encoding="utf-8") as f:
            for linea in f:
                fila = json.loads(linea)
                _acumular_fila(fila, totales_ccaa, totales_organismo, sin_asignar, ids_vistos, concesiones_aecid)
    except Exception as e:
        raise SystemExit(
            f"{raw_path} esta corrupto o incompleto ({e}) -- probablemente quedo asi por un corte "
            f"abrupto del proceso (kill, corte de luz) mientras se escribia, no por una excepcion "
            f"normal de Python. No se puede reprocesar sin red: hace falta volver a bajarlo con "
            f"`python ingesta_bdns.py --mes {sufijo}` (sin --desde-raw)."
        ) from e

    totales_organismo = recortar_top_organismos(totales_organismo)
    escribir_salidas(anio, mes, totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid)

    total_filas = sum(v["n_concesiones"] for v in totales_ccaa.values()) + len(sin_asignar)
    log.info(
        "Listo (desde raw). Filas: %d | CCAA con datos: %d | Sin asignar: %d",
        total_filas, len(totales_ccaa), len(sin_asignar),
    )
    log.info("Salida en: %s", OUTPUT_DIR.resolve())


def _cargar_checkpoint(sufijo):
    """Si existe un raw/{sufijo}.jsonl.gz de un intento anterior de este mes, lo relee para
    reconstruir los acumuladores y calcula desde que pagina seguir (filas ya en disco entre
    PAGE_SIZE -- todas las paginas ya escritas estan completas, nunca a medias: procesar_mes solo
    escribe las filas de una pagina despues de haberla pedido entera con exito). Devuelve
    (totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, pagina_inicial).

    Si no hay nada que retomar, si el raw existente tiene menos de una pagina completa, o si no se
    puede leer (p.ej. quedo a medias por un kill del proceso, no por una excepcion normal de
    Python), devuelve acumuladores vacios y pagina_inicial=0 -- en esos casos el caller trunca el
    raw y arranca de cero, exactamente igual que sin --continuar. El ids_vistos devuelto (ver
    _acumular_fila) ya incluye los id de todas las filas releidas, para que procesar_mes siga
    detectando duplicados contra el historial completo del mes, no solo contra lo que se pida a
    partir de pagina_inicial."""
    raw_path = RAW_DIR / f"{sufijo}.jsonl.gz"
    if not raw_path.exists():
        return {}, {}, [], [], set(), 0

    totales_ccaa = {}
    totales_organismo = {}
    sin_asignar = []
    concesiones_aecid = []
    ids_vistos = set()
    n_filas_previas = 0
    try:
        with gzip.open(raw_path, "rt", encoding="utf-8") as f:
            for linea in f:
                _acumular_fila(json.loads(linea), totales_ccaa, totales_organismo, sin_asignar, ids_vistos, concesiones_aecid)
                n_filas_previas += 1
    except Exception as e:
        log.warning("No se pudo leer el raw parcial de %s (%s) -- arrancando de cero.", sufijo, e)
        return {}, {}, [], [], set(), 0

    pagina_inicial = n_filas_previas // PAGE_SIZE
    if pagina_inicial == 0:
        # Menos de una pagina completa en disco -- se descarta y se arranca de cero (el caller
        # trunca el raw), en vez de arriesgarse a contar dos veces esas filas cuando la pagina 0
        # se vuelva a pedir.
        return {}, {}, [], [], set(), 0

    log.info(
        "Retomando %s desde un raw parcial (%d filas ya en disco, pagina %d)...",
        sufijo, n_filas_previas, pagina_inicial,
    )
    return totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, ids_vistos, pagina_inicial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mes", help="YYYY-MM (requerido salvo con --incremental)")
    parser.add_argument(
        "--incremental", action="store_true",
        help="pagina el feed global de BDNS desde --desde-id en vez de un mes fijo (ver "
             "docs/superpowers/specs/2026-09-06-bdns-ingesta-incremental-design.md)",
    )
    parser.add_argument(
        "--desde-id", type=int,
        help="ultimo id ya procesado (requerido con --incremental; es solo una pista de corte, la "
             "fuente de verdad del watermark vive en bdns_ingesta_estado y la actualiza cargar_bdns.py)",
    )
    parser.add_argument(
        "--desde-raw", action="store_true",
        help="reprocesa desde el raw/*.jsonl.gz ya descargado, sin red (requiere que ya exista)",
    )
    parser.add_argument(
        "--continuar", action="store_true",
        help="si ya existe un raw/*.jsonl.gz parcial de un intento anterior de este mes (p.ej. "
             "cortado por un fallo), retoma desde ahi en vez de empezar de cero. Si no existe, "
             "arranca igual que sin este flag.",
    )
    args = parser.parse_args()

    if args.incremental:
        if args.desde_id is None:
            parser.error("--incremental requiere --desde-id")
        with _lock_mes("incremental"):
            log.info("Procesando incremental BDNS desde id > %d...", args.desde_id)
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            with httpx.Client(timeout=HTTPX_TIMEOUT) as client:
                with gzip.open(RAW_DIR / f"incremental_{fecha}.jsonl.gz", "wt", encoding="utf-8") as raw_writer:
                    totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, max_id_visto, num_paginas = procesar_incremental(
                        client, raw_writer, args.desde_id,
                    )
            max_id_final = max_id_visto if max_id_visto is not None else args.desde_id
            escribir_salidas_incremental(fecha, totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, max_id_final)

            total_filas = sum(v["n_concesiones"] for v in totales_ccaa.values()) + len(sin_asignar)
            log.info(
                "Incremental listo. Filas nuevas: %d | Paginas: %d | Nuevo watermark: %d",
                total_filas, num_paginas, max_id_final,
            )
            log.info("Concesiones de AECID detectadas: %d", len(concesiones_aecid))
        return

    if not args.mes:
        parser.error("--mes es requerido salvo con --incremental")

    anio, mes = (int(x) for x in args.mes.split("-"))
    sufijo = f"{anio}-{mes:02d}"

    with _lock_mes(sufijo):
        if args.desde_raw:
            reprocesar_desde_raw(anio, mes)
            return

        log.info("Procesando concesiones BDNS de %04d-%02d...", anio, mes)
        RAW_DIR.mkdir(parents=True, exist_ok=True)

        totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, ids_vistos, pagina_inicial = (
            _cargar_checkpoint(sufijo) if args.continuar else ({}, {}, [], [], set(), 0)
        )
        modo_apertura = "at" if pagina_inicial else "wt"
        marcador_completo = _ruta_marcador_completo(sufijo)
        if modo_apertura == "wt":
            marcador_completo.unlink(missing_ok=True)

        with httpx.Client(timeout=HTTPX_TIMEOUT) as client:
            with gzip.open(RAW_DIR / f"{sufijo}.jsonl.gz", modo_apertura, encoding="utf-8") as raw_writer:
                totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, num_paginas = procesar_mes(
                    anio, mes, client, raw_writer,
                    totales_ccaa=totales_ccaa, totales_organismo=totales_organismo,
                    sin_asignar=sin_asignar, concesiones_aecid=concesiones_aecid,
                    ids_vistos=ids_vistos, pagina_inicial=pagina_inicial,
                )
        marcador_completo.touch()
        totales_organismo = recortar_top_organismos(totales_organismo)
        escribir_salidas(anio, mes, totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid)

        total_filas = sum(v["n_concesiones"] for v in totales_ccaa.values()) + len(sin_asignar)

        log.info(
            "Listo. Filas: %d | CCAA con datos: %d | Sin asignar: %d",
            total_filas, len(totales_ccaa), len(sin_asignar),
        )
        log.info("Paginas procesadas: %d", num_paginas)
        log.info("Total de filas procesadas este mes: %d", total_filas)
        log.info("Concesiones de AECID detectadas este mes: %d", len(concesiones_aecid))
        log.info("Salida en: %s", OUTPUT_DIR.resolve())

        no_asignados_local = Counter(
            normalizar(fila.get("nivel2")) for fila in sin_asignar if fila.get("nivel1") == "LOCAL"
        )
        for nombre, n in no_asignados_local.most_common(20):
            log.info("Sin asignar (LOCAL): %s (%d)", nombre, n)


if __name__ == "__main__":
    main()
