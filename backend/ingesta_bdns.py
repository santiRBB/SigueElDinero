"""
Ingesta de concesiones de BDNS (Base de Datos Nacional de Subvenciones) por comunidad autonoma,
agregadas mes a mes (SigueElDinero, fase 2).

Fuente: API publica de BDNS (https://www.infosubvenciones.es/bdnstrans/api/concesiones/busqueda),
sin API key.

Uso:
    python ingesta_bdns.py --mes 2026-08

Salidas (en ./salida_bdns/):
    raw/{YYYY-MM}.jsonl.gz                 -> concesiones crudas de ese mes, tal cual las devuelve la API
    agregado_ccaa_{YYYY-MM}.jsonl          -> una fila por CCAA con el total agregado de ese mes
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
    for intento in range(1, REINTENTOS + 1):
        try:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp
        except Exception as e:
            if intento == REINTENTOS:
                raise
            espera = PAUSA_ENTRE_PAGINAS * (2 ** intento)
            log.warning(
                "Fallo en pagina %s (intento %d/%d): %s -- reintentando en %.1fs",
                params.get("page"), intento, REINTENTOS, e, espera,
            )
            time.sleep(espera)


def procesar_mes(anio, mes, client, raw_writer):
    """Pagina /concesiones/busqueda para un mes completo, agrega por CCAA y devuelve
    (totales_ccaa, sin_asignar, num_paginas). Cada fila se escribe a medida que llega en
    raw_writer (cualquier objeto con .write(str) -> None, p.ej. un gzip.open(...) en modo
    texto) -- no acumula las filas crudas en memoria. Quien llama controla el ciclo de vida
    del archivo (abrirlo, pasarlo aqui, cerrarlo); ver main(). num_paginas permite detectar
    en los logs una respuesta prematuramente truncada por la API."""
    fecha_desde = f"01/{mes:02d}/{anio}"
    fecha_hasta = f"{ultimo_dia_mes(anio, mes):02d}/{mes:02d}/{anio}"

    totales_ccaa = {}
    sin_asignar = []

    page = 0
    num_paginas = 0
    while True:
        resp = _get_con_reintentos(client, BUSQUEDA_URL, {
            "page": page, "pageSize": PAGE_SIZE,
            "fechaDesde": fecha_desde, "fechaHasta": fecha_hasta,
        })
        data = resp.json()
        num_paginas += 1

        for fila in data["content"]:
            raw_writer.write(json.dumps(fila, ensure_ascii=False) + "\n")
            codigo_ine = resolver_ccaa(fila)
            if codigo_ine is None:
                sin_asignar.append(fila)
                continue
            acumulado = totales_ccaa.setdefault(
                codigo_ine, {"importe_total_eur": 0.0, "n_concesiones": 0}
            )
            acumulado["importe_total_eur"] += fila.get("importe") or 0.0
            acumulado["n_concesiones"] += 1

        if data.get("last", True) or not data["content"]:
            break
        page += 1
        time.sleep(PAUSA_ENTRE_PAGINAS)

    return totales_ccaa, sin_asignar, num_paginas


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


def escribir_salidas(anio, mes, totales_ccaa, sin_asignar):
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
        OUTPUT_DIR / f"sin_ccaa_asignada_{sufijo}.jsonl",
        (json.dumps(fila, ensure_ascii=False) for fila in sin_asignar),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mes", required=True, help="YYYY-MM")
    args = parser.parse_args()
    anio, mes = (int(x) for x in args.mes.split("-"))

    log.info("Procesando concesiones BDNS de %04d-%02d...", anio, mes)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sufijo = f"{anio}-{mes:02d}"
    with httpx.Client(timeout=15) as client:
        with gzip.open(RAW_DIR / f"{sufijo}.jsonl.gz", "wt", encoding="utf-8") as raw_writer:
            totales_ccaa, sin_asignar, num_paginas = procesar_mes(anio, mes, client, raw_writer)
    escribir_salidas(anio, mes, totales_ccaa, sin_asignar)

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
