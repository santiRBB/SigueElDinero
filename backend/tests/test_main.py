# backend/tests/test_main.py
from fastapi.testclient import TestClient

import main


def test_resumen_passes_query_params_through(monkeypatch):
    called_with = {}

    def fake_resumen(anio=None, grupo=None):
        called_with["anio"] = anio
        called_with["grupo"] = grupo
        return [{"iso_alpha3": "COL", "nombre": "Colombia", "importe_total_eur": 100.0, "n_intervenciones": 2}]

    monkeypatch.setattr(main, "resumen_paises", fake_resumen)
    client = TestClient(main.app)

    resp = client.get("/api/paises/resumen", params={"anio": 2025, "grupo": "720"})

    assert resp.status_code == 200
    assert resp.json() == [{"iso_alpha3": "COL", "nombre": "Colombia", "importe_total_eur": 100.0, "n_intervenciones": 2}]
    assert called_with == {"anio": 2025, "grupo": "720"}


def test_resumen_without_query_params(monkeypatch):
    monkeypatch.setattr(main, "resumen_paises", lambda anio=None, grupo=None: [])
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


def test_pais_por_anio_returns_404_when_country_not_found(monkeypatch):
    monkeypatch.setattr(main, "pais_por_anio", lambda iso_alpha3, grupo=None: None)
    client = TestClient(main.app)

    resp = client.get("/api/paises/ZZZ/por-anio")

    assert resp.status_code == 404


def test_pais_por_anio_returns_data_when_found(monkeypatch):
    fake = [{"anio": 2024, "importe_eur": 100.0, "n_intervenciones": 2}]
    called_with = {}

    def fake_por_anio(iso_alpha3, grupo=None):
        called_with["iso_alpha3"] = iso_alpha3
        called_with["grupo"] = grupo
        return fake

    monkeypatch.setattr(main, "pais_por_anio", fake_por_anio)
    client = TestClient(main.app)

    resp = client.get("/api/paises/col/por-anio", params={"grupo": "720"})

    assert resp.status_code == 200
    assert resp.json() == fake
    assert called_with == {"iso_alpha3": "COL", "grupo": "720"}


def test_anios_endpoint(monkeypatch):
    monkeypatch.setattr(main, "anios_disponibles", lambda: [2023, 2024, 2025])
    client = TestClient(main.app)

    resp = client.get("/api/filtros/anios")

    assert resp.status_code == 200
    assert resp.json() == [2023, 2024, 2025]


def test_sectores_endpoint(monkeypatch):
    monkeypatch.setattr(main, "sectores_disponibles", lambda: [{"codigo_grupo": "720", "nombre": "Emergency Response"}])
    client = TestClient(main.app)

    resp = client.get("/api/filtros/sectores")

    assert resp.status_code == 200
    assert resp.json() == [{"codigo_grupo": "720", "nombre": "Emergency Response"}]


def test_resumen_por_anio_endpoint(monkeypatch):
    monkeypatch.setattr(main, "resumen_por_anio", lambda grupo=None: [{"anio": 2024, "importe_eur": 100.0, "n_intervenciones": 2}])
    client = TestClient(main.app)

    resp = client.get("/api/resumen/por-anio")

    assert resp.status_code == 200
    assert resp.json() == [{"anio": 2024, "importe_eur": 100.0, "n_intervenciones": 2}]


def test_resumen_por_grupo_endpoint(monkeypatch):
    monkeypatch.setattr(main, "resumen_por_grupo", lambda anio=None: [{"codigo_grupo": "720", "nombre": "Emergency Response", "importe_eur": 500.0, "n_intervenciones": 1}])
    client = TestClient(main.app)

    resp = client.get("/api/resumen/por-grupo", params={"anio": 2024})

    assert resp.status_code == 200
    assert resp.json() == [{"codigo_grupo": "720", "nombre": "Emergency Response", "importe_eur": 500.0, "n_intervenciones": 1}]


def test_buscar_proyectos_endpoint_passes_params(monkeypatch):
    called_with = {}

    def fake_buscar(q=None, anio=None, grupo=None, pais=None, pagina=1, por_pagina=30):
        called_with.update({"q": q, "anio": anio, "grupo": grupo, "pais": pais, "pagina": pagina, "por_pagina": por_pagina})
        return {"total": 0, "pagina": pagina, "por_pagina": por_pagina, "resultados": []}

    monkeypatch.setattr(main, "buscar_proyectos", fake_buscar)
    client = TestClient(main.app)

    resp = client.get("/api/proyectos/buscar", params={"q": "agua", "anio": 2024, "grupo": "720", "pais": "COL", "pagina": 2, "por_pagina": 10})

    assert resp.status_code == 200
    assert resp.json() == {"total": 0, "pagina": 2, "por_pagina": 10, "resultados": []}
    assert called_with == {"q": "agua", "anio": 2024, "grupo": "720", "pais": "COL", "pagina": 2, "por_pagina": 10}


def test_buscar_proyectos_endpoint_defaults(monkeypatch):
    called_with = {}

    def fake_buscar(q=None, anio=None, grupo=None, pais=None, pagina=1, por_pagina=30):
        called_with.update({"q": q, "pagina": pagina, "por_pagina": por_pagina})
        return {"total": 0, "pagina": pagina, "por_pagina": por_pagina, "resultados": []}

    monkeypatch.setattr(main, "buscar_proyectos", fake_buscar)
    client = TestClient(main.app)

    resp = client.get("/api/proyectos/buscar")

    assert resp.status_code == 200
    assert called_with == {"q": None, "pagina": 1, "por_pagina": 30}
