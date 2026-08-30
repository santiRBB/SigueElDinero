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
import time
import unicodedata
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


def procesar_mes(anio, mes, client):
    """Pagina /concesiones/busqueda para un mes completo, agrega por CCAA y devuelve
    (totales_ccaa, sin_asignar, filas_raw) sin tocar disco -- quien llama decide que hacer
    con el resultado (ver escribir_salidas)."""
    fecha_desde = f"01/{mes:02d}/{anio}"
    fecha_hasta = f"{ultimo_dia_mes(anio, mes):02d}/{mes:02d}/{anio}"

    totales_ccaa = {}
    sin_asignar = []
    filas_raw = []

    page = 0
    while True:
        resp = _get_con_reintentos(client, BUSQUEDA_URL, {
            "page": page, "pageSize": PAGE_SIZE,
            "fechaDesde": fecha_desde, "fechaHasta": fecha_hasta,
        })
        data = resp.json()

        for fila in data["content"]:
            filas_raw.append(fila)
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

    return totales_ccaa, sin_asignar, filas_raw
