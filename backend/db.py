import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "Falta DATABASE_URL. Crea backend/.env con la cadena de conexion (ver cargar_supabase.py)."
        )
    return psycopg2.connect(DATABASE_URL)


def resumen_paises(anio: int | None = None, sector: str | None = None) -> list[dict]:
    sql = """
        select p.iso_alpha3, p.nombre,
               coalesce(sum(f.importe_pais_eur), 0) as importe_total_eur,
               count(distinct f.aid) as n_intervenciones
        from fact_gasto f
        join dim_pais p on p.pais_id = f.pais_id
        left join dim_categoria c on c.categoria_id = f.categoria_id
        where p.iso_alpha3 is not null
    """
    params: list = []
    if anio is not None:
        sql += " and extract(year from f.start_date) = %s"
        params.append(anio)
    if sector is not None:
        sql += " and c.codigo_crs = %s"
        params.append(sector)
    sql += " group by p.iso_alpha3, p.nombre order by importe_total_eur desc"

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def detalle_pais(iso_alpha3: str, anio: int | None = None) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "select iso_alpha3, nombre, region from dim_pais where iso_alpha3 = %s",
                [iso_alpha3],
            )
            pais = cur.fetchone()
            if pais is None:
                return None

            cat_sql = """
                select c.codigo_crs, c.nombre,
                       coalesce(sum(f.importe_pais_eur), 0) as importe_eur,
                       count(distinct f.aid) as n_intervenciones
                from fact_gasto f
                join dim_pais p on p.pais_id = f.pais_id
                left join dim_categoria c on c.categoria_id = f.categoria_id
                where p.iso_alpha3 = %s
            """
            cat_params: list = [iso_alpha3]
            if anio is not None:
                cat_sql += " and extract(year from f.start_date) = %s"
                cat_params.append(anio)
            cat_sql += " group by c.codigo_crs, c.nombre order by importe_eur desc"
            cur.execute(cat_sql, cat_params)
            categorias = cur.fetchall()

            proy_sql = """
                select f.aid, f.titulo, o.nombre as organismo_ejecutor,
                       f.importe_pais_eur, f.porcentaje_pais, f.porcentaje_fuente,
                       f.start_date, f.end_date
                from fact_gasto f
                join dim_pais p on p.pais_id = f.pais_id
                left join dim_organismo o on o.organismo_id = f.organismo_id
                where p.iso_alpha3 = %s
            """
            proy_params: list = [iso_alpha3]
            if anio is not None:
                proy_sql += " and extract(year from f.start_date) = %s"
                proy_params.append(anio)
            proy_sql += " order by f.importe_pais_eur desc"
            cur.execute(proy_sql, proy_params)
            proyectos = cur.fetchall()

            return {"pais": pais, "categorias": categorias, "proyectos": proyectos}
    finally:
        conn.close()


def anios_disponibles() -> list[int]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                select distinct extract(year from start_date)::int as anio
                from fact_gasto
                where start_date is not null
                order by anio
                """
            )
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def sectores_disponibles() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("select codigo_crs, nombre from dim_categoria order by nombre")
            return cur.fetchall()
    finally:
        conn.close()
