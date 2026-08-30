"""
Backfill historico de concesiones BDNS: corre ingesta_bdns.py mes a mes, desde 2022-01 (inicio real
de datos en BDNS) hasta el mes indicado (por defecto, el mes actual UTC).

Uso:
    python backfill_bdns.py                          # 2022-01 hasta el mes actual
    python backfill_bdns.py --hasta 2026-08           # 2022-01 hasta agosto 2026
    python backfill_bdns.py --desde 2023-01 --hasta 2023-12
    python backfill_bdns.py --forzar                  # reprocesa incluso los meses ya completados
    python backfill_bdns.py --rellenar-organismo      # ver seccion aparte mas abajo

Cada mes es independiente e idempotente (ingesta_bdns.py sobrescribe por completo su propio mes),
asi que si el backfill se corta a medias basta con volver a correr este script: los meses que ya
tienen agregado_ccaa_{YYYY-MM}.jsonl se saltan salvo --forzar.

Un mes que falla (timeout de red, error HTTP tras agotar los reintentos internos de ingesta_bdns.py,
etc.) se reintenta completo hasta REINTENTOS_MES veces, con una pausa entre intentos -- un fallo
transitorio en la pagina 500 de 900 no te obliga a estar reiniciando el backfill a mano. Solo si un
mes se sigue cayendo tras agotar esos reintentos se detiene todo el backfill (en vez de seguir con
datos parciales silenciosos); volver a correr el script retoma justo desde ese mes.

--rellenar-organismo:
    agregado_ccaa_organismo_{YYYY-MM}.jsonl se agrego despues de que ya existiera este backfill, asi
    que los meses backfilleados antes de esa fecha no tienen ese archivo. --rellenar-organismo NO
    vuelve a pegarle a la API: para cada mes en el rango que ya tiene raw/{YYYY-MM}.jsonl.gz local
    pero todavia no tiene agregado_ccaa_organismo_{YYYY-MM}.jsonl, lo reprocesa desde ese raw ya
    descargado (`ingesta_bdns.py --mes X --desde-raw`). Usa el mismo --desde/--hasta que el modo
    normal; --forzar no aplica a este modo (si algun dia hace falta forzar un reproceso puntual, se
    borra a mano el agregado_ccaa_organismo_{YYYY-MM}.jsonl de ese mes y se vuelve a correr).
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
OUTPUT_DIR = BACKEND_DIR / "salida_bdns"

REINTENTOS_MES = 3
PAUSA_ENTRE_REINTENTOS_MES = 30


def parse_mes(valor):
    anio, mes = valor.split("-")
    return int(anio), int(mes)


def generar_meses(desde, hasta):
    anio, mes = desde
    while (anio, mes) <= hasta:
        yield anio, mes
        mes += 1
        if mes > 12:
            mes = 1
            anio += 1


def ejecutar_mes(sufijo):
    """Corre ingesta_bdns.py para un mes, reintentando el mes completo ante un fallo. Devuelve True
    si termino con exito, False si se agotaron los reintentos."""
    for intento in range(1, REINTENTOS_MES + 1):
        resultado = subprocess.run(
            [sys.executable, "ingesta_bdns.py", "--mes", sufijo],
            cwd=BACKEND_DIR,
        )
        if resultado.returncode == 0:
            return True
        if intento < REINTENTOS_MES:
            print(
                f"[{sufijo}] fallo (intento {intento}/{REINTENTOS_MES}, codigo {resultado.returncode}), "
                f"reintentando en {PAUSA_ENTRE_REINTENTOS_MES}s..."
            )
            time.sleep(PAUSA_ENTRE_REINTENTOS_MES)

    print(f"[{sufijo}] fallo tras {REINTENTOS_MES} intentos.")
    return False


def ejecutar_backfill(desde, hasta, forzar):
    for anio, mes in generar_meses(desde, hasta):
        sufijo = f"{anio}-{mes:02d}"
        agregado = OUTPUT_DIR / f"agregado_ccaa_{sufijo}.jsonl"
        if agregado.exists() and not forzar:
            print(f"[{sufijo}] ya procesado, salteando (usa --forzar para reprocesar)")
            continue

        print(f"[{sufijo}] procesando...")
        if not ejecutar_mes(sufijo):
            print(f"Backfill detenido. Volve a correr este script para retomar desde {sufijo}.")
            sys.exit(1)

    print("Backfill completo.")


def ejecutar_relleno_organismo(desde, hasta):
    """Para cada mes en el rango que ya tiene raw/{mes}.jsonl.gz local pero todavia no tiene
    agregado_ccaa_organismo_{mes}.jsonl, lo reprocesa desde ese raw (sin red) via
    `ingesta_bdns.py --mes X --desde-raw`. Ver docstring del modulo."""
    for anio, mes in generar_meses(desde, hasta):
        sufijo = f"{anio}-{mes:02d}"
        raw_path = OUTPUT_DIR / "raw" / f"{sufijo}.jsonl.gz"
        organismo_path = OUTPUT_DIR / f"agregado_ccaa_organismo_{sufijo}.jsonl"

        if not raw_path.exists():
            print(f"[{sufijo}] sin raw local, salteando (correr el backfill normal primero)")
            continue
        if organismo_path.exists():
            print(f"[{sufijo}] ya tiene organismo, salteando")
            continue

        print(f"[{sufijo}] reprocesando organismo desde raw local...")
        resultado = subprocess.run(
            [sys.executable, "ingesta_bdns.py", "--mes", sufijo, "--desde-raw"],
            cwd=BACKEND_DIR,
        )
        if resultado.returncode != 0:
            print(f"[{sufijo}] fallo (codigo {resultado.returncode}). Relleno detenido.")
            print(f"Volve a correr este script para retomar desde {sufijo}.")
            sys.exit(1)

    print("Relleno de organismo completo.")


def main():
    mes_actual_utc = datetime.now(timezone.utc).strftime("%Y-%m")

    parser = argparse.ArgumentParser()
    parser.add_argument("--desde", default="2022-01", help="YYYY-MM (por defecto 2022-01)")
    parser.add_argument("--hasta", default=mes_actual_utc, help="YYYY-MM (por defecto el mes actual)")
    parser.add_argument("--forzar", action="store_true", help="reprocesa meses ya completados")
    parser.add_argument(
        "--rellenar-organismo", action="store_true",
        help="solo rellena agregado_ccaa_organismo faltante desde raw local, sin red (ver docstring)",
    )
    args = parser.parse_args()

    if args.rellenar_organismo:
        ejecutar_relleno_organismo(parse_mes(args.desde), parse_mes(args.hasta))
        return

    ejecutar_backfill(parse_mes(args.desde), parse_mes(args.hasta), args.forzar)


if __name__ == "__main__":
    main()
