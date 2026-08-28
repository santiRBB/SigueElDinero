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
        "start_date": "2024-01-01", "end_date": None,
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
        "nombre": "Emergency Response",
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
        {"codigo_grupo": "140", "nombre": "Water Supply & Sanitation"},
        {"codigo_grupo": "720", "nombre": "Emergency Response"},
    ]
