import pytest

import db


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, list(params) if params is not None else []))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.closed = False

    def cursor(self, cursor_factory=None):
        return self._cursor

    def close(self):
        self.closed = True


def test_resumen_paises_without_filters(monkeypatch):
    rows = [{"iso_alpha3": "COL", "nombre": "Colombia", "importe_total_eur": 100.0, "n_intervenciones": 2}]
    cursor = FakeCursor(rows)
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    result = db.resumen_paises()

    assert result == rows
    assert conn.closed is True
    sql, params = cursor.executed[0]
    assert params == []
    assert "extract(year from f.start_date)" not in sql
    assert "substring(c.codigo_crs" not in sql


def test_resumen_paises_applies_anio_and_grupo_filters(monkeypatch):
    cursor = FakeCursor(rows=[])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    db.resumen_paises(anio=2025, grupo="720")

    sql, params = cursor.executed[0]
    assert params == [2025, "720"]
    assert "extract(year from f.start_date) = %s" in sql
    assert "substring(c.codigo_crs from 1 for 3) = %s" in sql


def test_detalle_pais_returns_none_when_country_not_found(monkeypatch):
    cursor = FakeCursor(rows=[])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    result = db.detalle_pais("ZZZ")

    assert result is None
    assert conn.closed is True


def test_detalle_pais_returns_pais_categorias_and_proyectos(monkeypatch):
    pais_row = {"iso_alpha3": "COL", "nombre": "Colombia", "region": "LatAm"}
    categorias_rows = [{"codigo_grupo": "720", "importe_eur": 500.0, "n_intervenciones": 1}]
    proyectos_rows = [{
        "aid": "AID-1", "titulo": "Proyecto X", "organismo_ejecutor": "ONG Y",
        "importe_pais_eur": 500.0, "porcentaje_pais": 100.0, "porcentaje_fuente": "declared",
        "start_date": "2024-01-01", "end_date": None, "url_fuente": "https://datos.aecid.es/w/ejemplo",
    }]

    class MultiQueryCursor(FakeCursor):
        def __init__(self):
            super().__init__(rows=[])
            self._responses = [[pais_row], categorias_rows, proyectos_rows]
            self._call = 0

        def execute(self, sql, params=None):
            super().execute(sql, params)

        def fetchone(self):
            return self._responses[self._call][0] if self._responses[self._call] else None

        def fetchall(self):
            rows = self._responses[self._call]
            self._call += 1
            return rows

    cursor = MultiQueryCursor()
    original_fetchone = cursor.fetchone

    def fetchone_then_advance():
        result = original_fetchone()
        cursor._call += 1
        return result

    cursor.fetchone = fetchone_then_advance
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    result = db.detalle_pais("COL", anio=2024)

    assert result["pais"] == pais_row
    assert result["categorias"] == [{
        "codigo_grupo": "720", "importe_eur": 500.0, "n_intervenciones": 1,
        "nombre": "Respuesta de emergencia",
    }]
    assert result["proyectos"] == proyectos_rows
    assert len(cursor.executed) == 3
    for _, params in cursor.executed[1:]:
        assert params[0] == "COL"
        assert 2024 in params


def test_anios_disponibles(monkeypatch):
    cursor = FakeCursor(rows=[(2023,), (2024,), (2025,)])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    assert db.anios_disponibles() == [2023, 2024, 2025]


def test_sectores_disponibles(monkeypatch):
    cursor = FakeCursor(rows=[("140",), ("720",)])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    result = db.sectores_disponibles()

    assert result == [
        {"codigo_grupo": "140", "nombre": "Abastecimiento de agua y saneamiento"},
        {"codigo_grupo": "720", "nombre": "Respuesta de emergencia"},
    ]


def test_resumen_por_anio_without_filter(monkeypatch):
    rows = [{"anio": 2024, "importe_eur": 100.0, "n_intervenciones": 2}, {"anio": 2025, "importe_eur": 200.0, "n_intervenciones": 3}]
    cursor = FakeCursor(rows)
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    result = db.resumen_por_anio()

    assert result == rows
    sql, params = cursor.executed[0]
    assert params == []
    assert "substring(c.codigo_crs" not in sql


def test_resumen_por_anio_applies_grupo_filter(monkeypatch):
    cursor = FakeCursor(rows=[])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    db.resumen_por_anio(grupo="720")

    sql, params = cursor.executed[0]
    assert params == ["720"]
    assert "substring(c.codigo_crs from 1 for 3) = %s" in sql


def test_resumen_por_grupo_annotates_nombre(monkeypatch):
    rows = [{"codigo_grupo": "720", "importe_eur": 500.0, "n_intervenciones": 1}]
    cursor = FakeCursor(rows)
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    result = db.resumen_por_grupo(anio=2024)

    assert result == [{"codigo_grupo": "720", "importe_eur": 500.0, "n_intervenciones": 1, "nombre": "Respuesta de emergencia"}]
    sql, params = cursor.executed[0]
    assert params == [2024]
    assert "extract(year from f.start_date) = %s" in sql


def test_pais_por_anio_returns_none_when_country_not_found(monkeypatch):
    cursor = FakeCursor(rows=[])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    assert db.pais_por_anio("ZZZ") is None
    assert conn.closed is True


def test_pais_por_anio_returns_yearly_totals(monkeypatch):
    anios_rows = [{"anio": 2024, "importe_eur": 100.0, "n_intervenciones": 2}]

    class MultiQueryCursor(FakeCursor):
        def __init__(self):
            super().__init__(rows=[])
            self._responses = [[{"exists": 1}], anios_rows]
            self._call = 0

        def fetchone(self):
            row = self._responses[self._call][0] if self._responses[self._call] else None
            self._call += 1
            return row

        def fetchall(self):
            rows = self._responses[self._call]
            self._call += 1
            return rows

    cursor = MultiQueryCursor()
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    result = db.pais_por_anio("COL", grupo="720")

    assert result == anios_rows
    assert len(cursor.executed) == 2
    _, params = cursor.executed[1]
    assert params == ["COL", "720"]


def test_buscar_proyectos_returns_total_and_resultados(monkeypatch):
    proyectos_rows = [{
        "aid": "AID-1", "titulo": "Proyecto X", "organismo_ejecutor": "ONG Y",
        "pais_iso3": "COL", "pais_nombre": "Colombia", "codigo_grupo": "720",
        "importe_pais_eur": 500.0, "porcentaje_pais": 100.0, "porcentaje_fuente": "declared",
        "start_date": "2024-01-01", "end_date": None, "url_fuente": None,
    }]

    class MultiQueryCursor(FakeCursor):
        def __init__(self):
            super().__init__(rows=[])
            self._responses = [[{"total": 1}], proyectos_rows]
            self._call = 0

        def fetchone(self):
            row = self._responses[self._call][0] if self._responses[self._call] else None
            self._call += 1
            return row

        def fetchall(self):
            rows = self._responses[self._call]
            self._call += 1
            return rows

    cursor = MultiQueryCursor()
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    result = db.buscar_proyectos(q="agua", anio=2024, grupo="720", pais="COL", pagina=2, por_pagina=10)

    assert result["total"] == 1
    assert result["pagina"] == 2
    assert result["por_pagina"] == 10
    assert result["resultados"] == [{
        "aid": "AID-1", "titulo": "Proyecto X", "organismo_ejecutor": "ONG Y",
        "pais_iso3": "COL", "pais_nombre": "Colombia", "codigo_grupo": "720",
        "importe_pais_eur": 500.0, "porcentaje_pais": 100.0, "porcentaje_fuente": "declared",
        "start_date": "2024-01-01", "end_date": None, "url_fuente": None,
        "grupo_nombre": "Respuesta de emergencia",
    }]
    count_sql, count_params = cursor.executed[0]
    assert "ilike" in count_sql
    assert count_params == ["%agua%", "%agua%", "%agua%", 2024, "720", "COL"]
    results_sql, results_params = cursor.executed[1]
    assert "limit %s offset %s" in results_sql
    assert results_params[-2:] == [10, 10]


def test_buscar_proyectos_without_query_text(monkeypatch):
    cursor = FakeCursor(rows=[])
    conn = FakeConnection(cursor)
    cursor._responses = [[{"total": 0}], []]
    cursor._call = 0

    def fetchone():
        row = cursor._responses[cursor._call][0] if cursor._responses[cursor._call] else None
        cursor._call += 1
        return row

    def fetchall():
        rows = cursor._responses[cursor._call]
        cursor._call += 1
        return rows

    cursor.fetchone = fetchone
    cursor.fetchall = fetchall
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    db.buscar_proyectos()

    count_sql, count_params = cursor.executed[0]
    assert "ilike" not in count_sql
    assert count_params == []


class _EmptyResultCursor(FakeCursor):
    """Answers the count query with 0, then the results query with []."""

    def __init__(self):
        super().__init__(rows=[])
        self._responses = [[{"total": 0}], []]
        self._call = 0

    def fetchone(self):
        row = self._responses[self._call][0] if self._responses[self._call] else None
        self._call += 1
        return row

    def fetchall(self):
        rows = self._responses[self._call]
        self._call += 1
        return rows


def test_buscar_proyectos_orders_by_importe_desc_by_default(monkeypatch):
    cursor = _EmptyResultCursor()
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    db.buscar_proyectos()

    results_sql, _ = cursor.executed[1]
    assert "order by f.importe_pais_eur desc" in results_sql


@pytest.mark.parametrize(
    "orden,esperado",
    [
        ("importe_asc", "order by f.importe_pais_eur asc"),
        ("fecha_desc", "order by f.start_date desc nulls last"),
        ("fecha_asc", "order by f.start_date asc nulls last"),
    ],
)
def test_buscar_proyectos_applies_whitelisted_orden(monkeypatch, orden, esperado):
    cursor = _EmptyResultCursor()
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    db.buscar_proyectos(orden=orden)

    results_sql, _ = cursor.executed[1]
    assert esperado in results_sql


def test_buscar_proyectos_falls_back_to_default_orden_for_unknown_value(monkeypatch):
    cursor = _EmptyResultCursor()
    conn = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: conn)

    db.buscar_proyectos(orden="'; drop table fact_gasto; --")

    results_sql, _ = cursor.executed[1]
    assert "order by f.importe_pais_eur desc" in results_sql
