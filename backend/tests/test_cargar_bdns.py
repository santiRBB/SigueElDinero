import inspect
import os
import re

# cargar_bdns.py levanta SystemExit al importarse si falta DATABASE_URL (no hay .env en el entorno
# de test) -- se define un valor cualquiera antes del import para poder ejercitar el modulo sin una
# conexion real a Postgres (este archivo no prueba nada que use psycopg2.connect).
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

import cargar_bdns  # noqa: E402


def _extraer_patron_glob(nombre_funcion, variable):
    """Extrae el patron pasado a SALIDA_DIR.glob(...) que se asigna a `variable` dentro de la
    funcion `nombre_funcion` de cargar_bdns.py, leyendo el codigo fuente real -- para que el test
    quede atado al patron efectivamente usado por el codigo de produccion, no a una copia manual
    que podria desincronizarse silenciosamente si el patron cambia."""
    fuente = inspect.getsource(getattr(cargar_bdns, nombre_funcion))
    match = re.search(
        re.escape(variable) + r'\s*=\s*sorted\(SALIDA_DIR\.glob\("([^"]+)"\)\)',
        fuente,
    )
    assert match, f"no se encontro '{variable} = sorted(SALIDA_DIR.glob(...))' en {nombre_funcion}"
    return match.group(1)


def test_cargar_incremental_glob_excluye_el_archivo_de_organismo(tmp_path):
    """Regresion del bug critico: el glob de archivos CCAA en cargar_incremental() no debe matchear
    tambien incremental_agregado_ccaa_organismo_{fecha}.jsonl -- ese archivo trae las mismas claves
    (codigo_ine, anio, mes, importe_total_eur, n_concesiones) que el archivo real de CCAA, asi que
    nada explota con un KeyError, pero cada (ccaa_id, anio, mes) terminaria contabilizado dos veces
    (una por la fila real de CCAA, otra por cada fila de organismo con ese mismo total)."""
    archivo_ccaa = tmp_path / "incremental_agregado_ccaa_2026-09-06.jsonl"
    archivo_ccaa.write_text(
        '{"codigo_ine": "09", "anio": 2026, "mes": 9, "importe_total_eur": 100.0, "n_concesiones": 1}\n',
        encoding="utf-8",
    )
    (tmp_path / "incremental_agregado_ccaa_organismo_2026-09-06.jsonl").write_text(
        '{"codigo_ine": "09", "anio": 2026, "mes": 9, "organismo": "X", '
        '"importe_total_eur": 100.0, "n_concesiones": 1}\n',
        encoding="utf-8",
    )

    patron = _extraer_patron_glob("cargar_incremental", "archivos")
    assert patron == "incremental_agregado_ccaa_[0-9]*.jsonl"

    archivos = sorted(tmp_path.glob(patron))

    assert archivos == [archivo_ccaa]


def test_cargar_incremental_glob_sigue_matcheando_varios_archivos_de_ccaa(tmp_path):
    """El patron corregido no debe volverse tan estricto que deje de matchear el caso normal de
    varios archivos delta (uno por dia) presentes a la vez en salida_bdns/."""
    archivo_1 = tmp_path / "incremental_agregado_ccaa_2026-09-05.jsonl"
    archivo_2 = tmp_path / "incremental_agregado_ccaa_2026-09-06.jsonl"
    archivo_1.write_text("", encoding="utf-8")
    archivo_2.write_text("", encoding="utf-8")

    patron = _extraer_patron_glob("cargar_incremental", "archivos")

    assert sorted(tmp_path.glob(patron)) == [archivo_1, archivo_2]


def test_cargar_glob_no_incremental_ya_excluia_el_archivo_de_organismo(tmp_path):
    """Mismo patron ya usado (correctamente) por cargar() -- confirma que cargar_incremental() ahora
    sigue la misma convencion, no una nueva."""
    (tmp_path / "agregado_ccaa_2026-08.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "agregado_ccaa_organismo_2026-08.jsonl").write_text("", encoding="utf-8")

    patron = _extraer_patron_glob("cargar", "archivos")

    assert patron == "agregado_ccaa_[0-9]*.jsonl"
    assert sorted(tmp_path.glob(patron)) == [tmp_path / "agregado_ccaa_2026-08.jsonl"]
