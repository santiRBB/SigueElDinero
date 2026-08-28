# backend/tests/test_main.py
from fastapi.testclient import TestClient

import main


def test_resumen_passes_query_params_through(monkeypatch):
    called_with = {}

    def fake_resumen(anio=None, sector=None):
        called_with["anio"] = anio
        called_with["sector"] = sector
        return [{"iso_alpha3": "COL", "nombre": "Colombia", "importe_total_eur": 100.0, "n_intervenciones": 2}]

    monkeypatch.setattr(main, "resumen_paises", fake_resumen)
    client = TestClient(main.app)

    resp = client.get("/api/paises/resumen", params={"anio": 2025, "sector": "72050"})

    assert resp.status_code == 200
    assert resp.json() == [{"iso_alpha3": "COL", "nombre": "Colombia", "importe_total_eur": 100.0, "n_intervenciones": 2}]
    assert called_with == {"anio": 2025, "sector": "72050"}


def test_resumen_without_query_params(monkeypatch):
    monkeypatch.setattr(main, "resumen_paises", lambda anio=None, sector=None: [])
    client = TestClient(main.app)

    resp = client.get("/api/paises/resumen")

    assert resp.status_code == 200
    assert resp.json() == []


def test_detalle_returns_404_when_country_not_found(monkeypatch):
    monkeypatch.setattr(main, "detalle_pais", lambda iso_alpha3, anio=None: None)
    client = TestClient(main.app)

    resp = client.get("/api/paises/ZZZ/detalle")

    assert resp.status_code == 404


def test_detalle_returns_data_when_found(monkeypatch):
    fake = {"pais": {"iso_alpha3": "COL", "nombre": "Colombia", "region": None}, "categorias": [], "proyectos": []}
    called_with = {}

    def fake_detalle(iso_alpha3, anio=None):
        called_with["iso_alpha3"] = iso_alpha3
        called_with["anio"] = anio
        return fake

    monkeypatch.setattr(main, "detalle_pais", fake_detalle)
    client = TestClient(main.app)

    resp = client.get("/api/paises/col/detalle", params={"anio": 2024})

    assert resp.status_code == 200
    assert resp.json() == fake
    assert called_with == {"iso_alpha3": "COL", "anio": 2024}


def test_anios_endpoint(monkeypatch):
    monkeypatch.setattr(main, "anios_disponibles", lambda: [2023, 2024, 2025])
    client = TestClient(main.app)

    resp = client.get("/api/filtros/anios")

    assert resp.status_code == 200
    assert resp.json() == [2023, 2024, 2025]


def test_sectores_endpoint(monkeypatch):
    monkeypatch.setattr(main, "sectores_disponibles", lambda: [{"codigo_crs": "72050", "nombre": "Ayuda humanitaria"}])
    client = TestClient(main.app)

    resp = client.get("/api/filtros/sectores")

    assert resp.status_code == 200
    assert resp.json() == [{"codigo_crs": "72050", "nombre": "Ayuda humanitaria"}]
