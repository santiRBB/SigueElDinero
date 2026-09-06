import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

import json
from pathlib import Path

_CRS_GRUPOS_PATH = Path(__file__).parent / "crs_grupos.json"
with open(_CRS_GRUPOS_PATH, encoding="utf-8") as f:
    CRS_GRUPOS: dict[str, str] = json.load(f)


def _nombre_grupo(codigo_grupo: str | None) -> str | None:
    if codigo_grupo is None:
        return None
    return CRS_GRUPOS.get(codigo_grupo)


DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "Falta DATABASE_URL. Crea backend/.env con la cadena de conexion (ver cargar_supabase.py)."
        )
    return psycopg2.connect(DATABASE_URL)


def resumen_paises(anio: int | None = None, grupo: str | None = None) -> list[dict]:
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
    if grupo is not None:
        sql += " and substring(c.codigo_crs from 1 for 3) = %s"
        params.append(grupo)
    sql += " group by p.iso_alpha3, p.nombre order by importe_total_eur desc"

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def resumen_ccaa(anio: int | None = None) -> list[dict]:
    join_sql = "left join fact_gasto_ccaa f on f.ccaa_id = c.ccaa_id"
    params: list = []
    if anio is not None:
        join_sql += " and f.anio = %s"
        params.append(anio)

    sql = f"""
        select c.codigo_ine, c.nombre,
               coalesce(sum(f.importe_total_eur), 0) as importe_total_eur,
               coalesce(sum(f.n_concesiones), 0) as n_concesiones
        from dim_ccaa c
        {join_sql}
        group by c.codigo_ine, c.nombre
        order by importe_total_eur desc
    """

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def detalle_ccaa(codigo_ine: str, anio: int | None = None) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "select ccaa_id, codigo_ine, nombre from dim_ccaa where codigo_ine = %s",
                [codigo_ine],
            )
            ccaa = cur.fetchone()
            if ccaa is None:
                return None
            ccaa_id = ccaa["ccaa_id"]

            join_sql = "left join fact_gasto_ccaa f on f.ccaa_id = c.ccaa_id"
            total_params: list = []
            if anio is not None:
                join_sql += " and f.anio = %s"
                total_params.append(anio)
            total_params.append(codigo_ine)

            cur.execute(
                f"""
                select coalesce(sum(f.importe_total_eur), 0) as importe_total_eur,
                       coalesce(sum(f.n_concesiones), 0) as n_concesiones
                from dim_ccaa c
                {join_sql}
                where c.codigo_ine = %s
                group by c.codigo_ine
                """,
                total_params,
            )
            totales = cur.fetchone()

            org_sql = """
                select organismo,
                       sum(importe_total_eur) as importe_total_eur,
                       sum(n_concesiones) as n_concesiones
                from fact_gasto_ccaa_organismo
                where ccaa_id = %s
            """
            org_params: list = [ccaa_id]
            if anio is not None:
                org_sql += " and anio = %s"
                org_params.append(anio)
            org_sql += " group by organismo order by importe_total_eur desc"
            cur.execute(org_sql, org_params)
            organismos = cur.fetchall()

            return {
                "ccaa": {"codigo_ine": ccaa["codigo_ine"], "nombre": ccaa["nombre"]},
                "importe_total_eur": totales["importe_total_eur"],
                "n_concesiones": totales["n_concesiones"],
                "organismos": organismos,
            }
    finally:
        conn.close()


def ccaa_por_anio(codigo_ine: str) -> list[dict] | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("select 1 as exists from dim_ccaa where codigo_ine = %s", [codigo_ine])
            if cur.fetchone() is None:
                return None

            cur.execute(
                """
                select f.anio,
                       coalesce(sum(f.importe_total_eur), 0) as importe_eur,
                       coalesce(sum(f.n_concesiones), 0) as n_concesiones
                from fact_gasto_ccaa f
                join dim_ccaa c on c.ccaa_id = f.ccaa_id
                where c.codigo_ine = %s
                group by f.anio
                order by f.anio
                """,
                [codigo_ine],
            )
            return cur.fetchall()
    finally:
        conn.close()


def detalle_pais(iso_alpha3: str, anio: int | None = None, grupo: str | None = None) -> dict | None:
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
                select substring(c.codigo_crs from 1 for 3) as codigo_grupo,
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
            if grupo is not None:
                cat_sql += " and substring(c.codigo_crs from 1 for 3) = %s"
                cat_params.append(grupo)
            cat_sql += " group by codigo_grupo order by importe_eur desc"
            cur.execute(cat_sql, cat_params)
            categorias = cur.fetchall()
            for cat in categorias:
                cat["nombre"] = _nombre_grupo(cat["codigo_grupo"])

            proy_sql = """
                select f.aid, f.titulo, o.nombre as organismo_ejecutor,
                       c.codigo_crs as sector_crs_code, c.nombre as sector_crs_nombre,
                       f.importe_pais_eur, f.porcentaje_pais, f.porcentaje_fuente,
                       f.start_date, f.end_date, f.url_fuente, f.url_bdns, f.bdns_tipo_convocatoria
                from fact_gasto f
                join dim_pais p on p.pais_id = f.pais_id
                left join dim_organismo o on o.organismo_id = f.organismo_id
                left join dim_categoria c on c.categoria_id = f.categoria_id
                where p.iso_alpha3 = %s
            """
            proy_params: list = [iso_alpha3]
            if anio is not None:
                proy_sql += " and extract(year from f.start_date) = %s"
                proy_params.append(anio)
            if grupo is not None:
                proy_sql += " and substring(c.codigo_crs from 1 for 3) = %s"
                proy_params.append(grupo)
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
                select anio from (
                    select distinct extract(year from start_date)::int as anio
                    from fact_gasto
                    where start_date is not null
                    union
                    select distinct anio
                    from fact_gasto_ccaa
                ) t
                order by anio
                """
            )
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def sectores_disponibles() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                select distinct substring(codigo_crs from 1 for 3) as codigo_grupo
                from dim_categoria
                where codigo_crs is not null
                order by codigo_grupo
                """
            )
            codigos = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
    return [
        {"codigo_grupo": codigo, "nombre": _nombre_grupo(codigo)}
        for codigo in codigos
        if _nombre_grupo(codigo) is not None
    ]


_NO_PUBLICADO_EN_IATI = """
    not exists (
        select 1 from fact_gasto f
        where split_part(f.url_bdns, '/convocatorias/', 2) = b.numero_convocatoria
    )
"""


def resumen_aecid_bdns() -> dict:
    """Concesiones de AECID vistas en BDNS que todavia no aparecen publicadas en IATI
    (fact_gasto), agrupadas por pais cuando ese pais ya tiene actividad IATI propia (fila en
    dim_pais) -- todo lo demas (sin pais identificado, o pais identificado pero aun sin fila en
    dim_pais) cae en sin_pais, ya que no hay ninguna ficha /paises/XXX navegable para el.

    El dedup es EXACTO, no una heuristica: se extrae el sufijo numerico de fact_gasto.url_bdns
    (todo lo que sigue a "/convocatorias/") y se compara por igualdad contra numero_convocatoria --
    verificado en vivo contra la API de BDNS que ese sufijo es literalmente ese campo (ver spec).
    Se usa split_part + igualdad en vez de LIKE con concatenacion: evita que un numero_convocatoria
    con caracteres '%'/'_' (nunca deberia pasar, pero no esta validado en la ingesta) se interprete
    como comodin, y permite que Postgres resuelva el anti-join con un hash en vez de un escaneo por
    fila.

    Nota: el dedup es a nivel de convocatoria, no de concesion individual -- si IATI publica una
    sola actividad para una convocatoria con varias concesiones BDNS, se suprimen todas las
    concesiones de esa convocatoria, no solo la publicada. Es el comportamiento conservador
    correcto: nunca se corre el riesgo de contar doble, a costa de ocultar alguna concesion de esa
    convocatoria que todavia no tenga su propia actividad IATI."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"""
                select b.iso_alpha3, p.nombre as pais_nombre, b.importe_eur, b.n_concesiones
                from (
                    select b.iso_alpha3,
                           sum(b.importe_eur) as importe_eur,
                           count(*) as n_concesiones
                    from fact_gasto_aecid_bdns b
                    where {_NO_PUBLICADO_EN_IATI}
                    group by b.iso_alpha3
                ) b
                join dim_pais p on p.iso_alpha3 = b.iso_alpha3
                order by b.importe_eur desc
            """)
            por_pais = cur.fetchall()

            cur.execute(f"""
                select coalesce(sum(b.importe_eur), 0) as importe_eur,
                       coalesce(count(*), 0) as n_concesiones
                from fact_gasto_aecid_bdns b
                where {_NO_PUBLICADO_EN_IATI}
                and (
                    b.iso_alpha3 is null
                    or not exists (select 1 from dim_pais p where p.iso_alpha3 = b.iso_alpha3)
                )
            """)
            sin_pais = cur.fetchone()
    finally:
        conn.close()
    return {"por_pais": por_pais, "sin_pais": sin_pais}


def concesiones_aecid_bdns(iso_alpha3: str | None = None, pagina: int = 1, por_pagina: int = 30) -> dict:
    """Concesiones individuales de AECID vistas en BDNS y aun no publicadas en IATI (mismo
    criterio de dedup que resumen_aecid_bdns), para poder enlazar cada una a su convocatoria en
    BDNS. iso_alpha3='SIN_PAIS' filtra a las concesiones sin pais identificado; None trae todas."""
    por_pagina = min(por_pagina, 100)
    base_sql = f"""
        from fact_gasto_aecid_bdns b
        left join dim_pais p on p.iso_alpha3 = b.iso_alpha3
        where {_NO_PUBLICADO_EN_IATI}
    """
    params: list = []
    if iso_alpha3 == "SIN_PAIS":
        base_sql += " and b.iso_alpha3 is null"
    elif iso_alpha3 is not None:
        base_sql += " and b.iso_alpha3 = %s"
        params.append(iso_alpha3)

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"select count(*) as total {base_sql}", params)
            total = cur.fetchone()["total"]

            sql = f"""
                select b.concesion_id, b.beneficiario, b.titulo, b.importe_eur,
                       b.fecha_concesion, b.iso_alpha3, p.nombre as pais_nombre,
                       b.numero_convocatoria
                {base_sql}
                order by b.importe_eur desc
                limit %s offset %s
            """
            offset = max(pagina - 1, 0) * por_pagina
            cur.execute(sql, params + [por_pagina, offset])
            resultados = cur.fetchall()
    finally:
        conn.close()

    for row in resultados:
        numero_convocatoria = row.pop("numero_convocatoria")
        row["url_bdns"] = f"https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias/{numero_convocatoria}"

    return {"total": total, "pagina": pagina, "por_pagina": por_pagina, "resultados": resultados}


def resumen_por_anio(grupo: str | None = None) -> list[dict]:
    sql = """
        select extract(year from f.start_date)::int as anio,
               coalesce(sum(f.importe_pais_eur), 0) as importe_eur,
               count(distinct f.aid) as n_intervenciones
        from fact_gasto f
        left join dim_categoria c on c.categoria_id = f.categoria_id
        where f.start_date is not null
    """
    params: list = []
    if grupo is not None:
        sql += " and substring(c.codigo_crs from 1 for 3) = %s"
        params.append(grupo)
    sql += " group by anio order by anio"

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def resumen_por_grupo(anio: int | None = None) -> list[dict]:
    sql = """
        select substring(c.codigo_crs from 1 for 3) as codigo_grupo,
               coalesce(sum(f.importe_pais_eur), 0) as importe_eur,
               count(distinct f.aid) as n_intervenciones
        from fact_gasto f
        left join dim_categoria c on c.categoria_id = f.categoria_id
    """
    params: list = []
    if anio is not None:
        sql += " where extract(year from f.start_date) = %s"
        params.append(anio)
    sql += " group by codigo_grupo order by importe_eur desc"

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    finally:
        conn.close()
    for row in rows:
        row["nombre"] = _nombre_grupo(row["codigo_grupo"])
    return rows


def pais_por_anio(iso_alpha3: str, grupo: str | None = None) -> list[dict] | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("select 1 as exists from dim_pais where iso_alpha3 = %s", [iso_alpha3])
            if cur.fetchone() is None:
                return None

            sql = """
                select extract(year from f.start_date)::int as anio,
                       coalesce(sum(f.importe_pais_eur), 0) as importe_eur,
                       count(distinct f.aid) as n_intervenciones
                from fact_gasto f
                join dim_pais p on p.pais_id = f.pais_id
                left join dim_categoria c on c.categoria_id = f.categoria_id
                where p.iso_alpha3 = %s and f.start_date is not null
            """
            params: list = [iso_alpha3]
            if grupo is not None:
                sql += " and substring(c.codigo_crs from 1 for 3) = %s"
                params.append(grupo)
            sql += " group by anio order by anio"
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


ORDENES_BUSQUEDA = {
    "importe_desc": "f.importe_pais_eur desc",
    "importe_asc": "f.importe_pais_eur asc",
    "fecha_desc": "f.start_date desc nulls last",
    "fecha_asc": "f.start_date asc nulls last",
}
ORDEN_BUSQUEDA_DEFECTO = "importe_desc"


def buscar_proyectos(
    q: str | None = None,
    anio: int | None = None,
    grupo: str | None = None,
    pais: str | None = None,
    pagina: int = 1,
    por_pagina: int = 30,
    orden: str | None = None,
) -> dict:
    base_sql = """
        from fact_gasto f
        join dim_pais p on p.pais_id = f.pais_id
        left join dim_categoria c on c.categoria_id = f.categoria_id
        left join dim_organismo o on o.organismo_id = f.organismo_id
        where 1 = 1
    """
    params: list = []
    if q:
        base_sql += " and (f.titulo ilike %s or o.nombre ilike %s or p.nombre ilike %s)"
        needle = f"%{q}%"
        params.extend([needle, needle, needle])
    if anio is not None:
        base_sql += " and extract(year from f.start_date) = %s"
        params.append(anio)
    if grupo is not None:
        base_sql += " and substring(c.codigo_crs from 1 for 3) = %s"
        params.append(grupo)
    if pais is not None:
        base_sql += " and p.iso_alpha3 = %s"
        params.append(pais)

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"select count(*) as total {base_sql}", params)
            total = cur.fetchone()["total"]

            sql = f"""
                select f.aid, f.titulo, o.nombre as organismo_ejecutor,
                       p.iso_alpha3 as pais_iso3, p.nombre as pais_nombre,
                       substring(c.codigo_crs from 1 for 3) as codigo_grupo,
                       c.codigo_crs as sector_crs_code, c.nombre as sector_crs_nombre,
                       f.importe_pais_eur, f.porcentaje_pais, f.porcentaje_fuente,
                       f.start_date, f.end_date, f.url_fuente, f.url_bdns, f.bdns_tipo_convocatoria
                {base_sql}
                order by {ORDENES_BUSQUEDA.get(orden, ORDENES_BUSQUEDA[ORDEN_BUSQUEDA_DEFECTO])}
                limit %s offset %s
            """
            offset = max(pagina - 1, 0) * por_pagina
            cur.execute(sql, params + [por_pagina, offset])
            resultados = cur.fetchall()
    finally:
        conn.close()

    for row in resultados:
        row["grupo_nombre"] = _nombre_grupo(row["codigo_grupo"])

    return {"total": total, "pagina": pagina, "por_pagina": por_pagina, "resultados": resultados}
