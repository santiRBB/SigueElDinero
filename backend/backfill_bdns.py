"""
Backfill historico de concesiones BDNS: corre ingesta_bdns.py mes a mes, desde 2022-01 (inicio real
de datos en BDNS) hasta el mes indicado (por defecto, el mes actual UTC).

Uso:
    python backfill_bdns.py                          # 2022-01 hasta el mes actual
    python backfill_bdns.py --hasta 2026-08           # 2022-01 hasta agosto 2026
    python backfill_bdns.py --desde 2023-01 --hasta 2023-12
    python backfill_bdns.py --forzar                  # reprocesa incluso los meses ya completados

Cada mes es independiente e idempotente (ingesta_bdns.py sobrescribe por completo su propio mes),
asi que si el backfill se corta a medias basta con volver a correr este script: los meses que ya
tienen agregado_ccaa_{YYYY-MM}.jsonl se saltan salvo --forzar.

Se detiene en el primer mes que falla (en vez de seguir con datos parciales silenciosos) -- volver
a correr el script retoma justo desde ese mes.
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
OUTPUT_DIR = BACKEND_DIR / "salida_bdns"


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


def main():
    mes_actual_utc = datetime.now(timezone.utc).strftime("%Y-%m")

    parser = argparse.ArgumentParser()
    parser.add_argument("--desde", default="2022-01", help="YYYY-MM (por defecto 2022-01)")
    parser.add_argument("--hasta", default=mes_actual_utc, help="YYYY-MM (por defecto el mes actual)")
    parser.add_argument("--forzar", action="store_true", help="reprocesa meses ya completados")
    args = parser.parse_args()

    desde = parse_mes(args.desde)
    hasta = parse_mes(args.hasta)

    for anio, mes in generar_meses(desde, hasta):
        sufijo = f"{anio}-{mes:02d}"
        agregado = OUTPUT_DIR / f"agregado_ccaa_{sufijo}.jsonl"
        if agregado.exists() and not args.forzar:
            print(f"[{sufijo}] ya procesado, salteando (usa --forzar para reprocesar)")
            continue

        print(f"[{sufijo}] procesando...")
        resultado = subprocess.run(
            [sys.executable, "ingesta_bdns.py", "--mes", sufijo],
            cwd=BACKEND_DIR,
        )
        if resultado.returncode != 0:
            print(f"[{sufijo}] fallo (codigo {resultado.returncode}). Backfill detenido.")
            print(f"Volve a correr este script para retomar desde {sufijo}.")
            sys.exit(1)

    print("Backfill completo.")


if __name__ == "__main__":
    main()
