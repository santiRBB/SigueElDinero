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
import tempfile
import time
import unicodedata
from collections import Counter
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingesta_bdns")

BUSQUEDA_URL = "https://www.infosubvenciones.es/bdnstrans/api/concesiones/busqueda"
PAGE_SIZE = 1000
PAUSA_ENTRE_PAGINAS = 0.3
REINTENTOS = 3

OUTPUT_DIR = Path("./salida_bdns")
RAW_DIR = OUTPUT_DIR / "raw"

CCAA_LOOKUP_PATH = Path(__file__).parent / "ccaa_lookup.json"
with open(CCAA_LOOKUP_PATH, "r", encoding="utf-8") as f:
    CCAA_LOOKUP = json.load(f)


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
            espera = PAUSA_ENTRE_PAGINAS * (2 ** intento)
            log.warning(
                "Fallo en pagina %s (intento %d/%d): %s -- reintentando en %.1fs",
                params.get("page"), intento, REINTENTOS, e, espera,
            )
            time.sleep(espera)


def _acumular_fila(fila, totales_ccaa, totales_organismo, sin_asignar):
    """Aplica resolver_ccaa a una fila y actualiza los tres acumuladores in-place. Reutilizada tanto
    por procesar_mes (paginando la API en vivo) como por reprocesar_desde_raw (releyendo un
    raw/*.jsonl.gz ya descargado, sin red) -- misma logica de agregacion sin importar de donde
    vinieron las filas."""
    codigo_ine = resolver_ccaa(fila)
    if codigo_ine is None:
        sin_asignar.append(fila)
        return

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


def procesar_mes(
    anio, mes, client, raw_writer,
    totales_ccaa=None, totales_organismo=None, sin_asignar=None, pagina_inicial=0,
):
    """Pagina /concesiones/busqueda desde pagina_inicial (0 por defecto, es decir el mes completo)
    hasta el final, agrega por CCAA y por organismo dentro de cada CCAA, y devuelve (totales_ccaa,
    totales_organismo, sin_asignar, num_paginas). Cada fila se escribe a medida que llega en
    raw_writer (cualquier objeto con .write(str) -> None, p.ej. un gzip.open(...) en modo texto) --
    no acumula las filas crudas en memoria. Quien llama controla el ciclo de vida del archivo
    (abrirlo, pasarlo aqui, cerrarlo); ver main(). num_paginas permite detectar en los logs una
    respuesta prematuramente truncada por la API.

    totales_ccaa/totales_organismo/sin_asignar aceptan acumuladores ya iniciados (en vez de vacios)
    para retomar un mes cortado a mitad de camino -- ver main() y el flag --continuar: como cada
    fila ya escrita en el raw de una corrida anterior sigue integra en disco (el gzip se cierra bien
    incluso si procesar_mes termina en excepcion, solo un kill del proceso lo dejaria a medias),
    alcanza con re-sumar esas filas y pedir desde pagina_inicial en adelante, en vez de reprocesar
    el mes entero de nuevo."""
    fecha_desde = f"01/{mes:02d}/{anio}"
    fecha_hasta = f"{ultimo_dia_mes(anio, mes):02d}/{mes:02d}/{anio}"

    totales_ccaa = {} if totales_ccaa is None else totales_ccaa
    totales_organismo = {} if totales_organismo is None else totales_organismo
    sin_asignar = [] if sin_asignar is None else sin_asignar

    page = pagina_inicial
    num_paginas = 0
    while True:
        data = _get_con_reintentos(client, BUSQUEDA_URL, {
            "page": page, "pageSize": PAGE_SIZE,
            "fechaDesde": fecha_desde, "fechaHasta": fecha_hasta,
        })
        num_paginas += 1

        for fila in data["content"]:
            raw_writer.write(json.dumps(fila, ensure_ascii=False) + "\n")
            _acumular_fila(fila, totales_ccaa, totales_organismo, sin_asignar)

        if data.get("last", True) or not data["content"]:
            break
        page += 1
        time.sleep(PAUSA_ENTRE_PAGINAS)

    return totales_ccaa, totales_organismo, sin_asignar, num_paginas


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


def escribir_salidas(anio, mes, totales_ccaa, totales_organismo, sin_asignar):
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
    sin_ccaa_asignada) de un mes a partir de su raw/{YYYY-MM}.jsonl.gz ya descargado, sin volver a
    pegarle a la API de BDNS. Pensado para poblar agregado_ccaa_organismo_{YYYY-MM}.jsonl en meses
    que ya se habian backfilleado antes de que ese desglose existiera -- y de paso, si
    ccaa_lookup.json crecio despues de esa corrida original, mejora tambien la asignacion a CCAA.

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
    try:
        with gzip.open(raw_path, "rt", encoding="utf-8") as f:
            for linea in f:
                fila = json.loads(linea)
                _acumular_fila(fila, totales_ccaa, totales_organismo, sin_asignar)
    except Exception as e:
        raise SystemExit(
            f"{raw_path} esta corrupto o incompleto ({e}) -- probablemente quedo asi por un corte "
            f"abrupto del proceso (kill, corte de luz) mientras se escribia, no por una excepcion "
            f"normal de Python. No se puede reprocesar sin red: hace falta volver a bajarlo con "
            f"`python ingesta_bdns.py --mes {sufijo}` (sin --desde-raw)."
        ) from e

    totales_organismo = recortar_top_organismos(totales_organismo)
    escribir_salidas(anio, mes, totales_ccaa, totales_organismo, sin_asignar)

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
    (totales_ccaa, totales_organismo, sin_asignar, pagina_inicial).

    Si no hay nada que retomar, si el raw existente tiene menos de una pagina completa, o si no se
    puede leer (p.ej. quedo a medias por un kill del proceso, no por una excepcion normal de
    Python), devuelve acumuladores vacios y pagina_inicial=0 -- en esos casos el caller trunca el
    raw y arranca de cero, exactamente igual que sin --continuar."""
    raw_path = RAW_DIR / f"{sufijo}.jsonl.gz"
    if not raw_path.exists():
        return {}, {}, [], 0

    totales_ccaa = {}
    totales_organismo = {}
    sin_asignar = []
    n_filas_previas = 0
    try:
        with gzip.open(raw_path, "rt", encoding="utf-8") as f:
            for linea in f:
                _acumular_fila(json.loads(linea), totales_ccaa, totales_organismo, sin_asignar)
                n_filas_previas += 1
    except Exception as e:
        log.warning("No se pudo leer el raw parcial de %s (%s) -- arrancando de cero.", sufijo, e)
        return {}, {}, [], 0

    pagina_inicial = n_filas_previas // PAGE_SIZE
    if pagina_inicial == 0:
        # Menos de una pagina completa en disco -- se descarta y se arranca de cero (el caller
        # trunca el raw), en vez de arriesgarse a contar dos veces esas filas cuando la pagina 0
        # se vuelva a pedir.
        return {}, {}, [], 0

    log.info(
        "Retomando %s desde un raw parcial (%d filas ya en disco, pagina %d)...",
        sufijo, n_filas_previas, pagina_inicial,
    )
    return totales_ccaa, totales_organismo, sin_asignar, pagina_inicial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mes", required=True, help="YYYY-MM")
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
    anio, mes = (int(x) for x in args.mes.split("-"))
    sufijo = f"{anio}-{mes:02d}"

    with _lock_mes(sufijo):
        if args.desde_raw:
            reprocesar_desde_raw(anio, mes)
            return

        log.info("Procesando concesiones BDNS de %04d-%02d...", anio, mes)
        RAW_DIR.mkdir(parents=True, exist_ok=True)

        totales_ccaa, totales_organismo, sin_asignar, pagina_inicial = (
            _cargar_checkpoint(sufijo) if args.continuar else ({}, {}, [], 0)
        )
        modo_apertura = "at" if pagina_inicial else "wt"
        marcador_completo = _ruta_marcador_completo(sufijo)
        if modo_apertura == "wt":
            # Arranque fresco (sin --continuar, o --continuar sin nada que retomar): invalidar
            # cualquier marcador de una corrida completa anterior antes de truncar el raw, para que un
            # fallo a mitad de este nuevo intento no deje un marcador "completo" apuntando a un raw
            # que ahora esta truncado.
            marcador_completo.unlink(missing_ok=True)

        with httpx.Client(timeout=30) as client:
            with gzip.open(RAW_DIR / f"{sufijo}.jsonl.gz", modo_apertura, encoding="utf-8") as raw_writer:
                totales_ccaa, totales_organismo, sin_asignar, num_paginas = procesar_mes(
                    anio, mes, client, raw_writer,
                    totales_ccaa=totales_ccaa, totales_organismo=totales_organismo,
                    sin_asignar=sin_asignar, pagina_inicial=pagina_inicial,
                )
        marcador_completo.touch()
        totales_organismo = recortar_top_organismos(totales_organismo)
        escribir_salidas(anio, mes, totales_ccaa, totales_organismo, sin_asignar)

        total_filas = sum(v["n_concesiones"] for v in totales_ccaa.values()) + len(sin_asignar)

        log.info(
            "Listo. Filas: %d | CCAA con datos: %d | Sin asignar: %d",
            total_filas, len(totales_ccaa), len(sin_asignar),
        )
        log.info("Paginas procesadas: %d", num_paginas)
        log.info("Total de filas procesadas este mes: %d", total_filas)
        log.info("Salida en: %s", OUTPUT_DIR.resolve())

        no_asignados_local = Counter(
            normalizar(fila.get("nivel2")) for fila in sin_asignar if fila.get("nivel1") == "LOCAL"
        )
        for nombre, n in no_asignados_local.most_common(20):
            log.info("Sin asignar (LOCAL): %s (%d)", nombre, n)


if __name__ == "__main__":
    main()
