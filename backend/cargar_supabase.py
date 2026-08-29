"""
Carga fact_gasto.jsonl (generado por ingesta_aecid.py) a Supabase/Postgres.

Requisitos:
    pip install psycopg2-binary pycountry python-dotenv --break-system-packages

Configuracion:
    Crea un archivo .env en esta misma carpeta con:
        DATABASE_URL=postgresql://postgres:TU_PASSWORD@db.TU_PROYECTO.supabase.co:5432/postgres

    Esa cadena la encuentras en Supabase -> Project Settings -> Database ->
    Connection string -> URI. Usa el modo "Session" (puerto 5432), no el
    "Transaction pooler" (puerto 6543), porque aqui hacemos varias sentencias
    dentro de la misma transaccion.

    NUNCA subas el .env a git. Anadelo a .gitignore si no lo esta ya.

Uso:
    1. Ejecuta antes schema.sql contra tu base (SQL editor de Supabase, o:
       psql "$DATABASE_URL" -f schema.sql)
    2. python cargar_supabase.py
"""

import json
import os
from pathlib import Path

import psycopg2
import psycopg2.extras
import pycountry
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit(
        "Falta DATABASE_URL. Crea un archivo .env con la cadena de conexion "
        "de Supabase (ver docstring de este script)."
    )

FACT_GASTO_PATH = Path("./salida_aecid/fact_gasto.jsonl")


def resolver_pais(iso2):
    """Devuelve (iso_alpha3, nombre) para un codigo ISO2, o (None, iso2) si no se reconoce."""
    pais = pycountry.countries.get(alpha_2=iso2)
    if pais:
        return pais.alpha_3, pais.name
    # Algunos codigos IATI no son ISO estandar (ej. codigos de region tipo Z01).
    # En ese caso devolvemos el propio codigo como fallback para no perder la fila.
    return None, iso2


def cargar():
    if not FACT_GASTO_PATH.exists():
        raise SystemExit(f"No encuentro {FACT_GASTO_PATH}. Ejecuta antes ingesta_aecid.py")

    filas = []
    with open(FACT_GASTO_PATH, "r", encoding="utf-8") as f:
        for linea in f:
            filas.append(json.loads(linea))

    print(f"Leidas {len(filas)} filas de {FACT_GASTO_PATH}")

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # --- 1. Upsert dim_pais ---
        paises_vistos = {}
        for fila in filas:
            iso2 = fila["pais_codigo_iso2"]
            if iso2 not in paises_vistos:
                iso3, nombre = resolver_pais(iso2)
                paises_vistos[iso2] = (iso3, nombre)

        pais_id_por_iso2 = {}
        for iso2, (iso3, nombre) in paises_vistos.items():
            cur.execute(
                """
                insert into dim_pais (iso_alpha2, iso_alpha3, nombre)
                values (%s, %s, %s)
                on conflict (iso_alpha2) do update set nombre = excluded.nombre
                returning pais_id
                """,
                (iso2, iso3, nombre),
            )
            pais_id_por_iso2[iso2] = cur.fetchone()[0]
        print(f"dim_pais: {len(pais_id_por_iso2)} paises procesados")

        # --- 2. Upsert dim_categoria (sector CRS) ---
        categorias_vistas = {}
        for fila in filas:
            code = fila.get("sector_crs_code")
            if code and code not in categorias_vistas:
                categorias_vistas[code] = (
                    fila.get("sector_crs_nombre"),
                    fila.get("sector_crs_nombre_fuente"),
                )

        categoria_id_por_codigo = {}
        for code, (nombre, nombre_fuente) in categorias_vistas.items():
            cur.execute(
                """
                insert into dim_categoria (codigo_crs, nombre, nombre_fuente)
                values (%s, %s, %s)
                on conflict (codigo_crs) do update set
                    nombre = excluded.nombre,
                    nombre_fuente = excluded.nombre_fuente
                returning categoria_id
                """,
                (code, nombre, nombre_fuente),
            )
            categoria_id_por_codigo[code] = cur.fetchone()[0]
        print(f"dim_categoria: {len(categoria_id_por_codigo)} sectores procesados")

        # --- 3. Upsert dim_organismo (ejecutor) ---
        organismos_vistos = set()
        for fila in filas:
            org = fila.get("organismo_ejecutor")
            if org:
                organismos_vistos.add(org)

        organismo_id_por_nombre = {}
        for org in organismos_vistos:
            cur.execute(
                """
                insert into dim_organismo (nombre, tipo)
                values (%s, 'ejecutor')
                on conflict (nombre) do update set nombre = excluded.nombre
                returning organismo_id
                """,
                (org,),
            )
            organismo_id_por_nombre[org] = cur.fetchone()[0]
        print(f"dim_organismo: {len(organismo_id_por_nombre)} organismos procesados")

        # --- 4. Upsert fact_gasto ---
        registros = []
        for fila in filas:
            registros.append((
                fila["aid"],
                pais_id_por_iso2.get(fila["pais_codigo_iso2"]),
                categoria_id_por_codigo.get(fila.get("sector_crs_code")),
                organismo_id_por_nombre.get(fila.get("organismo_ejecutor")),
                fila.get("titulo"),
                fila.get("descripcion"),
                fila.get("reporting_org"),
                "IATI",
                fila.get("reporting_ref"),
                fila.get("activity_status"),
                fila.get("start_date"),
                fila.get("end_date"),
                fila.get("importe_total_eur"),
                fila.get("porcentaje_pais"),
                fila.get("porcentaje_fuente"),
                fila.get("importe_pais_eur"),
                fila.get("tipo_transaccion_usado"),
                fila.get("url_fuente"),
                fila.get("url_bdns"),
                fila.get("bdns_tipo_convocatoria"),
            ))

        psycopg2.extras.execute_values(
            cur,
            """
            insert into fact_gasto (
                aid, pais_id, categoria_id, organismo_id, titulo, descripcion,
                reporting_org, fuente, reporting_ref, activity_status,
                start_date, end_date, importe_total_eur, porcentaje_pais,
                porcentaje_fuente, importe_pais_eur, tipo_transaccion, url_fuente,
                url_bdns, bdns_tipo_convocatoria
            ) values %s
            on conflict (aid, pais_id) do update set
                titulo = excluded.titulo,
                descripcion = excluded.descripcion,
                importe_total_eur = excluded.importe_total_eur,
                porcentaje_pais = excluded.porcentaje_pais,
                porcentaje_fuente = excluded.porcentaje_fuente,
                importe_pais_eur = excluded.importe_pais_eur,
                tipo_transaccion = excluded.tipo_transaccion,
                url_fuente = excluded.url_fuente,
                url_bdns = excluded.url_bdns,
                bdns_tipo_convocatoria = excluded.bdns_tipo_convocatoria,
                fecha_ingesta = now()
            """,
            registros,
        )
        print(f"fact_gasto: {len(registros)} filas insertadas/actualizadas")

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