"""
Carga agregado_aecid_*.jsonl (generados por ingesta_bdns.py) a Supabase/Postgres, en la tabla
fact_gasto_aecid_bdns.

Requisitos y configuracion: igual que cargar_supabase.py (ver su docstring) -- un archivo .env con
DATABASE_URL en esta misma carpeta.

Uso:
    python cargar_aecid_bdns.py

Carga TODOS los archivos agregado_aecid_*.jsonl presentes en ./salida_bdns/ -- puede haber varios,
p.ej. la corrida diaria procesa el mes en curso y el anterior.
"""

import json
import os
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit(
        "Falta DATABASE_URL. Crea un archivo .env con la cadena de conexion "
        "de Supabase (ver docstring de cargar_supabase.py)."
    )

SALIDA_DIR = Path("./salida_bdns")


def cargar():
    archivos = sorted(SALIDA_DIR.glob("agregado_aecid_*.jsonl"))
    if not archivos:
        raise SystemExit(
            f"No hay archivos agregado_aecid_*.jsonl en {SALIDA_DIR}. Ejecuta antes ingesta_bdns.py"
        )

    filas = []
    for archivo in archivos:
        with open(archivo, "r", encoding="utf-8") as f:
            for linea in f:
                filas.append(json.loads(linea))

    print(f"Leidas {len(filas)} filas de {len(archivos)} archivo(s) (fact_gasto_aecid_bdns)")

    registros = [
        (
            fila["concesion_id"], fila["numero_convocatoria"], fila["iso_alpha3"],
            fila["beneficiario"], fila["titulo"], fila["importe_eur"], fila["fecha_concesion"],
        )
        for fila in filas
    ]

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        psycopg2.extras.execute_values(
            cur,
            """
            insert into fact_gasto_aecid_bdns
                (concesion_id, numero_convocatoria, iso_alpha3, beneficiario, titulo, importe_eur, fecha_concesion)
            values %s
            on conflict (concesion_id) do update set
                numero_convocatoria = excluded.numero_convocatoria,
                iso_alpha3 = excluded.iso_alpha3,
                beneficiario = excluded.beneficiario,
                titulo = excluded.titulo,
                importe_eur = excluded.importe_eur,
                fecha_concesion = excluded.fecha_concesion
            """,
            registros,
        )
        print(f"fact_gasto_aecid_bdns: {len(registros)} filas insertadas/actualizadas")
        conn.commit()
        print("Carga completada correctamente.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    cargar()
