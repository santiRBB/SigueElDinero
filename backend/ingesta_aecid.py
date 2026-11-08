"""
Ingesta de actividades de la AECID desde IATI D-Portal (SigueElDinero).

Fuente: D-Portal Q API (https://www.d-portal.org/q) via la libreria `diterator`.
No requiere API key.

Uso:
    pip install diterator --break-system-packages   # o en un venv normal
    python ingesta_aecid.py

Salidas:
    raw/{aid}.xml           -> XML crudo de cada actividad (para trazabilidad/reproceso)
    fact_gasto.jsonl        -> una linea JSON por (actividad x pais), listo para cargar en Postgres
    actividades_sin_pais.jsonl -> actividades sin recipient-country (para revisar aparte, p.ej. contribuciones a organismos multilaterales)

Notas de diseno:
    - reporting_ref = XM-DAC-50-21 es el codigo IATI de la AECID. Para anadir mas
      organismos espanoles publicando en IATI, basta con anadir su codigo a REPORTING_REFS.
    - El importe por pais se calcula como importe_total * percentage / 100, usando el
      `percentage` declarado por el propio publicador en <recipient-country>. Si una
      actividad no declara porcentaje pero si varios paises, IATI/D-Portal asumirian
      reparto igualitario; aqui lo marcamos explicitamente en el campo `percentage_source`
      para no fingir precision que la fuente no dio.
    - day_start/day_end de la tabla `act` son offsets de dia; para las fechas ISO reales
      usamos las de la propia actividad (activity_dates) via diterator, que ya las expone
      en formato ISO 8601.
"""

import json
import logging
import os
import re
import time
from pathlib import Path

import diterator.iterator
import httpx
import requests
from diterator import Iterator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingesta_aecid")

# Codigos IATI (reporting org) a ingerir. Anadir aqui otros organismos espanoles
# publicados en IATI segun se vayan identificando.
REPORTING_REFS = [
    "XM-DAC-50-21",  # AECID
]

OUTPUT_DIR = Path("./salida_aecid")
RAW_DIR = OUTPUT_DIR / "raw"
FACT_GASTO_PATH = OUTPUT_DIR / "fact_gasto.jsonl"
SIN_PAIS_PATH = OUTPUT_DIR / "actividades_sin_pais.jsonl"

# Tabla de referencia de codigos de sector OECD-DAC CRS (5 digitos), oficial de IATI:
# https://github.com/IATI/IATI-Codelists-NonEmbedded/blob/master/xml/Sector.xml
# Muchos publicadores (AECID incluida) no incluyen el <narrative> del nombre del
# sector en su XML, solo el codigo. En vez de dejar el nombre vacio, lo resolvemos
# contra esta tabla local -- es un codigo estandar y estable, no cambia por publicador.
CRS_SECTORES_PATH = Path(__file__).parent / "crs_sectores.json"
with open(CRS_SECTORES_PATH, "r", encoding="utf-8") as f:
    CRS_SECTORES = json.load(f)


DPORTAL_TIMEOUT = (10, 120)  # (conexion, lectura) en segundos


class _SesionConTimeout:
    """Sustituto minimo del modulo `requests` dentro de diterator: solo expone `.get`."""

    def __init__(self, session, timeout):
        self._session = session
        self._timeout = timeout

    def get(self, url, **kwargs):
        kwargs.setdefault("timeout", self._timeout)
        return self._session.get(url, **kwargs)


def instalar_reintentos_dportal(total=5, backoff_factor=2, timeout=DPORTAL_TIMEOUT):
    """Hace que diterator reintente las paginas de d-portal ante 5xx o fallos de red.

    diterator pide cada pagina con `requests.get` a pelo (sin reintentos ni timeout)
    y ademas avanza el `offset` ANTES de comprobar el status, asi que capturar la
    excepcion fuera y seguir iterando se saltaria 100 actividades en silencio. Por
    eso el reintento tiene que ocurrir dentro de la propia peticion: sustituimos el
    `requests` que usa diterator.iterator por una Session con urllib3 Retry.

    Con backoff_factor=2 y total=5 las esperas son ~2, 4, 8, 16 s (~30 s en total).
    Si el error persiste se devuelve la ultima respuesta y diterator lanza el
    HTTPError de siempre, de modo que el job sigue fallando de forma visible.
    """
    retry = Retry(
        total=total,
        backoff_factor=backoff_factor,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    diterator.iterator.requests = _SesionConTimeout(session, timeout)


def get_amount_eur(activity):
    """Importe total de la actividad en EUR.

    Preferimos la suma de transacciones tipo 'Disbursement' (3) y si no hay,
    'Commitment' (2), ya que son los tipos mas representativos del gasto real
    o comprometido. Convertimos a EUR solo si la transaccion viene en EUR;
    si viene en otra moneda, la dejamos en su moneda original marcada como tal
    en vez de inventar un tipo de cambio.
    """
    disbursements = [t for t in activity.transactions if t.type == "3"]
    commitments = [t for t in activity.transactions if t.type == "2"]
    chosen = disbursements or commitments

    total_eur = 0.0
    total_otras_monedas = {}
    tx_type_used = "disbursement" if disbursements else ("commitment" if commitments else None)

    for t in chosen:
        currency = t.currency or activity.default_currency
        if currency == "EUR":
            total_eur += t.value
        else:
            total_otras_monedas[currency] = total_otras_monedas.get(currency, 0.0) + t.value

    return total_eur, total_otras_monedas, tx_type_used


def build_source_url(aid, reporting_ref):
    """Construye el enlace directo a la ficha publica de la actividad en datos.aecid.es.

    El slug de la URL es el propio codigo IATI sin el prefijo del organismo y en
    minusculas, p.ej.:
        aid            = "XM-DAC-50-21-Z01-24-H1-00100"
        reporting_ref  = "XM-DAC-50-21"
        slug           = "z01-24-h1-00100"
        url            = "https://datos.aecid.es/w/z01-24-h1-00100"

    Si el aid no empieza por el reporting_ref esperado (organismo distinto de
    AECID, o formato inesperado), devolvemos None en vez de construir una URL
    que probablemente sea incorrecta.
    """
    prefijo = reporting_ref + "-"
    if not aid.startswith(prefijo):
        return None
    slug = aid[len(prefijo):].lower()
    return f"https://datos.aecid.es/w/{slug}"


BDNS_LINK_RE = re.compile(
    r"https://www\.pap\.hacienda\.gob\.es/bdnstrans/([A-Z]{2})/[a-z]{2}/convocatorias/(\d+)"
)
BDNS_API_URL = "https://www.pap.hacienda.gob.es/bdnstrans/api/convocatorias"


def get_bdns_info(url_fuente, client=httpx):
    """(url_bdns, tipo_convocatoria) a partir de la ficha AECID de una actividad.

    `client` es cualquier objeto con un metodo `.get(url, **kwargs)` compatible con
    httpx -- por defecto el propio modulo httpx, o una instancia de httpx.Client
    (pasada desde main()) para reutilizar la conexion TCP/TLS entre actividades.

    Devuelve (None, None) si no hay ficha, si la ficha no enlaza a BDNS, o si cualquier
    peticion de red falla -- nunca lanza, para no interrumpir la ingesta por una actividad.
    """
    if not url_fuente:
        return None, None
    try:
        pagina = client.get(url_fuente, timeout=10, follow_redirects=True)
        pagina.raise_for_status()
        match = BDNS_LINK_RE.search(pagina.text)
        if not match:
            return None, None
        vpd, num_conv = match.group(1), match.group(2)
        url_bdns = match.group(0)
        api_resp = client.get(BDNS_API_URL, params={"vpd": vpd, "numConv": num_conv}, timeout=10)
        api_resp.raise_for_status()
        tipo_convocatoria = api_resp.json().get("tipoConvocatoria")
        return url_bdns, tipo_convocatoria
    except Exception as e:
        log.warning("No se pudo obtener info BDNS de %s: %s", url_fuente, e)
        return None, None


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    instalar_reintentos_dportal()

    n_actividades = 0
    n_filas_pais = 0
    n_sin_pais = 0

    with open(FACT_GASTO_PATH, "w", encoding="utf-8") as f_fact, \
         open(SIN_PAIS_PATH, "w", encoding="utf-8") as f_sin_pais, \
         httpx.Client() as bdns_client:

        for reporting_ref in REPORTING_REFS:
            log.info("Consultando actividades de reporting_ref=%s", reporting_ref)

            activities = Iterator({"reporting_ref": reporting_ref})

            for activity in activities:
                n_actividades += 1
                aid = activity.identifier

                # Guardar el XML crudo de la actividad para trazabilidad y reproceso futuro
                raw_path = RAW_DIR / f"{aid.replace('/', '_')}.xml"
                if not raw_path.exists():
                    try:
                        raw_path.write_text(
                            activity.get_node(".").toxml(), encoding="utf-8"
                        )
                    except Exception as e:
                        log.warning("No se pudo volcar XML crudo de %s: %s", aid, e)

                total_eur, otras_monedas, tx_type_used = get_amount_eur(activity)

                url_fuente = build_source_url(aid, reporting_ref)
                url_bdns, bdns_tipo_convocatoria = get_bdns_info(url_fuente, bdns_client)
                if url_fuente:
                    time.sleep(0.2)

                paises = activity.recipient_countries
                sectores = activity.sectors_by_vocabulary.get("1", [])  # 1 = OECD DAC CRS
                sector_principal = sectores[0].code if sectores else None
                sector_nombre = None
                sector_nombre_fuente = None
                if sectores:
                    narrativa = str(sectores[0].narrative) if sectores[0].narrative else ""
                    if narrativa.strip():
                        sector_nombre = narrativa.strip()
                        sector_nombre_fuente = "publicador"
                    else:
                        sector_nombre = CRS_SECTORES.get(sector_principal)
                        sector_nombre_fuente = "codelist_crs" if sector_nombre else None

                organismo_ejecutor = None
                for org in activity.participating_orgs:
                    if org.role == "4":  # 4 = Implementing organisation
                        organismo_ejecutor = str(org.name)
                        break

                base_record = {
                    "aid": aid,
                    "titulo": str(activity.title),
                    "descripcion": str(activity.description) if activity.description else None,
                    "reporting_org": str(activity.reporting_org.name),
                    "reporting_ref": reporting_ref,
                    "organismo_ejecutor": organismo_ejecutor,
                    "activity_status": activity.activity_status,
                    "start_date": activity.start_date_actual or activity.start_date_planned,
                    "end_date": activity.end_date_actual or activity.end_date_planned,
                    "sector_crs_code": sector_principal,
                    "sector_crs_nombre": sector_nombre,
                    "sector_crs_nombre_fuente": sector_nombre_fuente,  # "publicador" | "codelist_crs" | None
                    "importe_total_eur": round(total_eur, 2),
                    "importe_otras_monedas": otras_monedas or None,
                    "tipo_transaccion_usado": tx_type_used,  # disbursement | commitment | None
                    "url_fuente": url_fuente,
                    "url_bdns": url_bdns,
                    "bdns_tipo_convocatoria": bdns_tipo_convocatoria,
                }

                if not paises:
                    n_sin_pais += 1
                    f_sin_pais.write(json.dumps(base_record, ensure_ascii=False) + "\n")
                    continue

                # Si solo hay un pais y no trae percentage explicito, asumimos 100%
                # y lo marcamos como "declared" igualmente (no hay ambiguedad con 1 solo pais).
                for pais in paises:
                    pct_raw = pais.percentage
                    if pct_raw is not None:
                        pct = float(pct_raw)
                        pct_source = "declared"
                    elif len(paises) == 1:
                        pct = 100.0
                        pct_source = "declared"
                    else:
                        # Varios paises sin porcentaje explicito: repartimos a partes
                        # iguales pero lo dejamos marcado como asumido, no declarado.
                        pct = 100.0 / len(paises)
                        pct_source = "assumed_equal_split"

                    fila = dict(base_record)
                    fila.update({
                        "pais_codigo_iso2": pais.code,
                        "porcentaje_pais": pct,
                        "porcentaje_fuente": pct_source,
                        "importe_pais_eur": round(total_eur * pct / 100.0, 2),
                    })
                    f_fact.write(json.dumps(fila, ensure_ascii=False) + "\n")
                    n_filas_pais += 1

                if n_actividades % 50 == 0:
                    log.info("Procesadas %d actividades (%d filas pais)...", n_actividades, n_filas_pais)

    log.info(
        "Listo. Actividades: %d | Filas fact_gasto (actividad x pais): %d | Sin pais: %d",
        n_actividades, n_filas_pais, n_sin_pais,
    )
    log.info("Salida en: %s", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()