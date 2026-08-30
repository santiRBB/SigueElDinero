import io
import json

import pytest

import ingesta_bdns


class FakeResponsePagina:
    def __init__(self, content, last):
        self._content = content
        self._last = last

    def raise_for_status(self):
        pass

    def json(self):
        return {"content": self._content, "last": self._last}


class FakeClientPaginado:
    def __init__(self, paginas):
        self.paginas = paginas
        self.llamadas = []

    def get(self, url, params=None):
        self.llamadas.append((url, dict(params)))
        return self.paginas[params["page"]]


def test_normalizar_strips_accents_and_collapses_spaces():
    assert ingesta_bdns.normalizar("  Cataluña   ") == "CATALUNA"
    assert ingesta_bdns.normalizar("Región de Murcia") == "REGION DE MURCIA"
    assert ingesta_bdns.normalizar(None) == ""


def test_resolver_ccaa_autonomica_directo():
    fila = {"nivel1": "AUTONOMICA", "nivel2": "Cataluña"}
    assert ingesta_bdns.resolver_ccaa(fila) == "09"


def test_resolver_ccaa_autonomica_ciudad_autonoma():
    fila = {"nivel1": "AUTONOMICA", "nivel2": "CIUDAD AUTÓNOMA DE CEUTA"}
    assert ingesta_bdns.resolver_ccaa(fila) == "18"


def test_resolver_ccaa_local_diputacion_conocida():
    fila = {"nivel1": "LOCAL", "nivel2": "DIPUTACIÓN PROV. DE AVILA"}
    assert ingesta_bdns.resolver_ccaa(fila) == "07"


def test_resolver_ccaa_local_cabildo_conocido():
    fila = {"nivel1": "LOCAL", "nivel2": "CABILDO DE GRAN CANARIA"}
    assert ingesta_bdns.resolver_ccaa(fila) == "05"


def test_resolver_ccaa_local_ayuntamiento_no_reconocido():
    fila = {"nivel1": "LOCAL", "nivel2": "AYUNTAMIENTO DE NAVALUENGA"}
    assert ingesta_bdns.resolver_ccaa(fila) is None


def test_resolver_ccaa_estatal_devuelve_none():
    fila = {"nivel1": "ESTATAL", "nivel2": None}
    assert ingesta_bdns.resolver_ccaa(fila) is None


def test_procesar_mes_pagina_y_agrega_por_ccaa(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    paginas = [
        FakeResponsePagina(content=[
            {"nivel1": "AUTONOMICA", "nivel2": "Cataluña", "importe": 100.0},
            {"nivel1": "AUTONOMICA", "nivel2": "Cataluña", "importe": 50.0},
        ], last=False),
        FakeResponsePagina(content=[
            {"nivel1": "LOCAL", "nivel2": "CABILDO DE TENERIFE", "importe": 30.0},
            {"nivel1": "ESTATAL", "nivel2": None, "importe": 999.0},
        ], last=True),
    ]
    client = FakeClientPaginado(paginas)
    raw_writer = io.StringIO()

    totales, sin_asignar, num_paginas = ingesta_bdns.procesar_mes(2026, 8, client, raw_writer)

    assert totales == {
        "09": {"importe_total_eur": 150.0, "n_concesiones": 2},
        "05": {"importe_total_eur": 30.0, "n_concesiones": 1},
    }
    assert len(sin_asignar) == 1
    assert sin_asignar[0]["nivel1"] == "ESTATAL"
    assert num_paginas == 2
    filas_escritas = [json.loads(linea) for linea in raw_writer.getvalue().splitlines()]
    assert len(filas_escritas) == 4
    assert client.llamadas[0][1]["fechaDesde"] == "01/08/2026"
    assert client.llamadas[0][1]["fechaHasta"] == "31/08/2026"
    assert client.llamadas[1][1]["page"] == 1


def test_procesar_mes_reintenta_ante_fallo_de_red(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    intentos = {"n": 0}

    class FlakyClient:
        def get(self, url, params=None):
            intentos["n"] += 1
            if intentos["n"] < 3:
                raise RuntimeError("network down")
            return FakeResponsePagina(content=[], last=True)

    raw_writer = io.StringIO()
    totales, sin_asignar, num_paginas = ingesta_bdns.procesar_mes(2026, 8, FlakyClient(), raw_writer)

    assert intentos["n"] == 3
    assert totales == {}
    assert raw_writer.getvalue() == ""
    assert num_paginas == 1


def test_procesar_mes_lanza_tras_agotar_reintentos(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)

    class SiempreFalla:
        def get(self, url, params=None):
            raise RuntimeError("network down")

    with pytest.raises(RuntimeError):
        ingesta_bdns.procesar_mes(2026, 8, SiempreFalla(), io.StringIO())


def test_escribir_salidas_crea_los_archivos_agregados(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "OUTPUT_DIR", tmp_path)

    totales_ccaa = {"09": {"importe_total_eur": 150.0, "n_concesiones": 2}}
    sin_asignar = [{"nivel1": "ESTATAL", "nivel2": None, "importe": 999.0}]

    ingesta_bdns.escribir_salidas(2026, 8, totales_ccaa, sin_asignar)

    agregado_path = tmp_path / "agregado_ccaa_2026-08.jsonl"
    with open(agregado_path, encoding="utf-8") as f:
        fila = json.loads(f.readline())
    assert fila == {
        "codigo_ine": "09", "anio": 2026, "mes": 8,
        "importe_total_eur": 150.0, "n_concesiones": 2,
    }

    sin_asignar_path = tmp_path / "sin_ccaa_asignada_2026-08.jsonl"
    with open(sin_asignar_path, encoding="utf-8") as f:
        assert len(f.readlines()) == 1
