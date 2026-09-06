"""
Imprime por stdout el ultimo_id_procesado actual de bdns_ingesta_estado -- lo usa el workflow para
pasarselo como --desde-id a `ingesta_bdns.py --incremental`.

Requisitos: igual que cargar_bdns.py -- un archivo .env con DATABASE_URL en esta misma carpeta.

Uso:
    python leer_watermark.py
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit(
        "Falta DATABASE_URL. Crea un archivo .env con la cadena de conexion de Supabase "
        "(ver docstring de cargar_supabase.py)."
    )


def leer_watermark():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        cur = conn.cursor()
        cur.execute("select ultimo_id_procesado from bdns_ingesta_estado where id = 1")
        fila = cur.fetchone()
        if fila is None:
            raise SystemExit(
                "No existe fila en bdns_ingesta_estado -- hace falta sembrarla a mano una unica vez "
                "(ver docs/superpowers/specs/2026-09-06-bdns-ingesta-incremental-design.md, seccion "
                "Migracion/bootstrap) antes de correr el modo incremental."
            )
        return fila[0]
    finally:
        conn.close()


if __name__ == "__main__":
    print(leer_watermark())
