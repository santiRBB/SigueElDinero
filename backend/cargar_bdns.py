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

import argparse
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


def cargar_incremental():
    """Contraparte de cargar() para el modo delta: en vez de reemplazar el mes completo, SUMA los
    deltas leidos de incremental_agregado_ccaa_*.jsonl / incremental_agregado_ccaa_organismo_*.jsonl
    a lo que ya exista, y avanza bdns_ingesta_estado.ultimo_id_procesado -- todo en una unica
    transaccion. Si cualquier paso falla, rollback completo (ni los totales ni el watermark quedan
    modificados) para que la proxima corrida vuelva a pedir exactamente el mismo rango sin haber
    perdido ni duplicado nada (ver docs/superpowers/specs/2026-09-06-bdns-ingesta-incremental-design.md).

    No aplica recortar_top_organismos ni ningun tope de "top 15" -- ver la nota en
    escribir_salidas_incremental (ingesta_bdns.py) sobre por que eso solo tiene sentido con
    visibilidad del mes completo, que es lo que aporta la reconciliacion semanal. Esa reconciliacion
    solo reprocesa 2 meses (actual y anterior): el desglose por organismo de meses mas viejos, a los
    que este modo incremental si puede sumarles filas, puede crecer sin tope con el tiempo sin volver
    a recortarse a top-15+OTROS. Aceptado por ahora; arreglarlo bien implicaria mover el recorte a la
    capa de lectura/consulta."""
    archivos = sorted(SALIDA_DIR.glob("incremental_agregado_ccaa_[0-9]*.jsonl"))
    if not archivos:
        raise SystemExit(
            f"No hay archivos incremental_agregado_ccaa_[0-9]*.jsonl en {SALIDA_DIR}. "
            f"Ejecuta antes ingesta_bdns.py --incremental"
        )
    archivos_max_id = sorted(SALIDA_DIR.glob("incremental_max_id_*.txt"))
    if not archivos_max_id:
        raise SystemExit(f"No hay archivo incremental_max_id_*.txt en {SALIDA_DIR}.")
    nuevo_watermark = int(archivos_max_id[-1].read_text(encoding="utf-8").strip())

    filas = []
    for archivo in archivos:
        with open(archivo, "r", encoding="utf-8") as f:
            for linea in f:
                filas.append(json.loads(linea))

    archivos_organismo = sorted(SALIDA_DIR.glob("incremental_agregado_ccaa_organismo_*.jsonl"))
    filas_organismo = []
    for archivo in archivos_organismo:
        with open(archivo, "r", encoding="utf-8") as f:
            for linea in f:
                filas_organismo.append(json.loads(linea))

    print(f"Leidas {len(filas)} filas delta de {len(archivos)} archivo(s) (fact_gasto_ccaa, modo incremental)")
    print(f"Leidas {len(filas_organismo)} filas delta de {len(archivos_organismo)} archivo(s) (fact_gasto_ccaa_organismo, modo incremental)")
    print(f"Nuevo watermark a confirmar: {nuevo_watermark}")

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute("select ultimo_id_procesado from bdns_ingesta_estado where id = 1 for update")
        fila_estado = cur.fetchone()
        if fila_estado is None:
            raise SystemExit(
                "No existe fila en bdns_ingesta_estado -- hace falta sembrarla a mano una unica vez "
                "(ver docs/superpowers/specs/2026-09-06-bdns-ingesta-incremental-design.md, seccion "
                "Migracion/bootstrap) antes de correr el modo incremental."
            )
        watermark_actual = fila_estado[0]
        if nuevo_watermark < watermark_actual:
            raise SystemExit(
                f"El nuevo watermark ({nuevo_watermark}) es menor al ya confirmado "
                f"({watermark_actual}) -- no se aplica, para no retroceder el estado."
            )

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

        if registros:
            psycopg2.extras.execute_values(
                cur,
                """
                insert into fact_gasto_ccaa (ccaa_id, anio, mes, importe_total_eur, n_concesiones)
                values %s
                on conflict (ccaa_id, anio, mes) do update set
                    importe_total_eur = fact_gasto_ccaa.importe_total_eur + excluded.importe_total_eur,
                    n_concesiones = fact_gasto_ccaa.n_concesiones + excluded.n_concesiones,
                    fecha_actualizacion = now()
                """,
                registros,
            )
        print(f"fact_gasto_ccaa: {len(registros)} filas sumadas (modo incremental)")

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

        if registros_organismo:
            psycopg2.extras.execute_values(
                cur,
                """
                insert into fact_gasto_ccaa_organismo (ccaa_id, anio, mes, organismo, importe_total_eur, n_concesiones)
                values %s
                on conflict (ccaa_id, anio, mes, organismo) do update set
                    importe_total_eur = fact_gasto_ccaa_organismo.importe_total_eur + excluded.importe_total_eur,
                    n_concesiones = fact_gasto_ccaa_organismo.n_concesiones + excluded.n_concesiones
                """,
                registros_organismo,
            )
        print(f"fact_gasto_ccaa_organismo: {len(registros_organismo)} filas sumadas (modo incremental)")

        cur.execute(
            "update bdns_ingesta_estado set ultimo_id_procesado = %s, fecha_actualizacion = now() where id = 1",
            (nuevo_watermark,),
        )

        conn.commit()
        print(f"Carga incremental completada. Watermark actualizado a {nuevo_watermark}.")

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--incremental", action="store_true",
        help="modo delta: suma en vez de reemplazar, y avanza bdns_ingesta_estado (ver "
             "docs/superpowers/specs/2026-09-06-bdns-ingesta-incremental-design.md)",
    )
    args = parser.parse_args()
    if args.incremental:
        cargar_incremental()
    else:
        cargar()


if __name__ == "__main__":
    main()
