"""
Carga agregado_ccaa_*.jsonl (generados por ingesta_bdns.py) a Supabase/Postgres.

Requisitos y configuracion: igual que cargar_supabase.py (ver su docstring) --
un archivo .env con DATABASE_URL en esta misma carpeta.

Uso:
    python cargar_bdns.py

Carga TODOS los archivos agregado_ccaa_*.jsonl presentes en ./salida_bdns/ (uno por mes procesado
en la corrida actual de ingesta_bdns.py -- puede haber varios, p.ej. la corrida diaria procesa el
mes en curso y el anterior).
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
    archivos = sorted(SALIDA_DIR.glob("agregado_ccaa_[0-9]*.jsonl"))
    if not archivos:
        raise SystemExit(
            f"No hay archivos agregado_ccaa_[0-9]*.jsonl en {SALIDA_DIR}. Ejecuta antes ingesta_bdns.py"
        )

    filas = []
    for archivo in archivos:
        with open(archivo, "r", encoding="utf-8") as f:
            for linea in f:
                filas.append(json.loads(linea))

    archivos_organismo = sorted(SALIDA_DIR.glob("agregado_ccaa_organismo_*.jsonl"))
    filas_organismo = []
    for archivo in archivos_organismo:
        with open(archivo, "r", encoding="utf-8") as f:
            for linea in f:
                filas_organismo.append(json.loads(linea))

    print(f"Leidas {len(filas)} filas de {len(archivos)} archivo(s) (fact_gasto_ccaa)")
    print(f"Leidas {len(filas_organismo)} filas de {len(archivos_organismo)} archivo(s) (fact_gasto_ccaa_organismo)")

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute("select codigo_ine, ccaa_id from dim_ccaa")
        ccaa_id_por_codigo = dict(cur.fetchall())

        registros = []
        for fila in filas:
            ccaa_id = ccaa_id_por_codigo.get(fila["codigo_ine"])
            if ccaa_id is None:
                print(f"AVISO: codigo_ine desconocido {fila['codigo_ine']!r}, fila omitida")
                continue
            registros.append((
                ccaa_id, fila["anio"], fila["mes"],
                fila["importe_total_eur"], fila["n_concesiones"],
            ))

        meses = {(fila["anio"], fila["mes"]) for fila in filas}
        if meses:
            cur.execute(
                "delete from fact_gasto_ccaa where (anio, mes) in %s",
                (tuple(meses),),
            )

        psycopg2.extras.execute_values(
            cur,
            """
            insert into fact_gasto_ccaa (ccaa_id, anio, mes, importe_total_eur, n_concesiones)
            values %s
            on conflict (ccaa_id, anio, mes) do update set
                importe_total_eur = excluded.importe_total_eur,
                n_concesiones = excluded.n_concesiones,
                fecha_actualizacion = now()
            """,
            registros,
        )
        print(f"fact_gasto_ccaa: {len(registros)} filas insertadas/actualizadas")

        registros_organismo = []
        for fila in filas_organismo:
            ccaa_id = ccaa_id_por_codigo.get(fila["codigo_ine"])
            if ccaa_id is None:
                print(f"AVISO: codigo_ine desconocido {fila['codigo_ine']!r}, fila de organismo omitida")
                continue
            registros_organismo.append((
                ccaa_id, fila["anio"], fila["mes"], fila["organismo"],
                fila["importe_total_eur"], fila["n_concesiones"],
            ))

        meses_organismo = {(fila["anio"], fila["mes"]) for fila in filas_organismo}
        if meses_organismo:
            cur.execute(
                "delete from fact_gasto_ccaa_organismo where (anio, mes) in %s",
                (tuple(meses_organismo),),
            )

        psycopg2.extras.execute_values(
            cur,
            """
            insert into fact_gasto_ccaa_organismo (ccaa_id, anio, mes, organismo, importe_total_eur, n_concesiones)
            values %s
            on conflict (ccaa_id, anio, mes, organismo) do update set
                importe_total_eur = excluded.importe_total_eur,
                n_concesiones = excluded.n_concesiones
            """,
            registros_organismo,
        )
        print(f"fact_gasto_ccaa_organismo: {len(registros_organismo)} filas insertadas/actualizadas")

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
