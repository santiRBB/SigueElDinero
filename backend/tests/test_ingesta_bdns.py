import gzip
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


def test_resolver_ccaa_local_ayuntamiento_via_exacto():
    fila = {"nivel1": "LOCAL", "nivel2": "Córdoba"}
    assert ingesta_bdns.resolver_ccaa(fila) == "01"


def test_resolver_ccaa_local_ayuntamiento_via_exacto_con_coma():
    fila = {"nivel1": "LOCAL", "nivel2": "Vall d'Uixo, La"}
    assert ingesta_bdns.resolver_ccaa(fila) == "10"


def test_resolver_ccaa_estatal_devuelve_none():
    fila = {"nivel1": "ESTATAL", "nivel2": None}
    assert ingesta_bdns.resolver_ccaa(fila) is None


def test_procesar_mes_pagina_y_agrega_por_ccaa(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    paginas = [
        FakeResponsePagina(content=[
            {"nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Departamento A", "importe": 100.0},
            {"nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Departamento B", "importe": 50.0},
        ], last=False),
        FakeResponsePagina(content=[
            {"nivel1": "LOCAL", "nivel2": "CABILDO DE TENERIFE", "nivel3": "Cabildo de Tenerife", "importe": 30.0},
            {"nivel1": "ESTATAL", "nivel2": None, "importe": 999.0},
        ], last=True),
    ]
    client = FakeClientPaginado(paginas)
    raw_writer = io.StringIO()

    totales, totales_organismo, sin_asignar, num_paginas = ingesta_bdns.procesar_mes(2026, 8, client, raw_writer)

    assert totales == {
        "09": {"importe_total_eur": 150.0, "n_concesiones": 2},
        "05": {"importe_total_eur": 30.0, "n_concesiones": 1},
    }
    assert totales_organismo == {
        "09": {
            "Departamento A": {"importe_total_eur": 100.0, "n_concesiones": 1},
            "Departamento B": {"importe_total_eur": 50.0, "n_concesiones": 1},
        },
        "05": {
            "Cabildo de Tenerife": {"importe_total_eur": 30.0, "n_concesiones": 1},
        },
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
    totales, totales_organismo, sin_asignar, num_paginas = ingesta_bdns.procesar_mes(2026, 8, FlakyClient(), raw_writer)

    assert intentos["n"] == 3
    assert totales == {}
    assert totales_organismo == {}
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
    totales_organismo = {"09": {"Departamento A": {"importe_total_eur": 100.0, "n_concesiones": 1}}}
    sin_asignar = [{"nivel1": "ESTATAL", "nivel2": None, "importe": 999.0}]

    ingesta_bdns.escribir_salidas(2026, 8, totales_ccaa, totales_organismo, sin_asignar)

    agregado_path = tmp_path / "agregado_ccaa_2026-08.jsonl"
    with open(agregado_path, encoding="utf-8") as f:
        fila = json.loads(f.readline())
    assert fila == {
        "codigo_ine": "09", "anio": 2026, "mes": 8,
        "importe_total_eur": 150.0, "n_concesiones": 2,
    }

    organismo_path = tmp_path / "agregado_ccaa_organismo_2026-08.jsonl"
    with open(organismo_path, encoding="utf-8") as f:
        fila_org = json.loads(f.readline())
    assert fila_org == {
        "codigo_ine": "09", "anio": 2026, "mes": 8,
        "organismo": "Departamento A", "importe_total_eur": 100.0, "n_concesiones": 1,
    }

    sin_asignar_path = tmp_path / "sin_ccaa_asignada_2026-08.jsonl"
    with open(sin_asignar_path, encoding="utf-8") as f:
        assert len(f.readlines()) == 1


def test_escribir_salidas_no_deja_archivo_final_si_falla_a_mitad(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "OUTPUT_DIR", tmp_path)

    def lineas_que_fallan():
        yield '{"ok": true}'
        raise RuntimeError("se corto la escritura")

    with pytest.raises(RuntimeError):
        ingesta_bdns._escribir_atomico(tmp_path / "salida.jsonl", lineas_que_fallan())

    assert not (tmp_path / "salida.jsonl").exists()
    assert list(tmp_path.glob("*.tmp")) == []


def test_escribir_salidas_reemplaza_un_archivo_previo_completo(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "OUTPUT_DIR", tmp_path)

    ingesta_bdns.escribir_salidas(2026, 8, {"09": {"importe_total_eur": 100.0, "n_concesiones": 1}}, {}, [])
    ingesta_bdns.escribir_salidas(2026, 8, {"01": {"importe_total_eur": 200.0, "n_concesiones": 2}}, {}, [])

    agregado_path = tmp_path / "agregado_ccaa_2026-08.jsonl"
    with open(agregado_path, encoding="utf-8") as f:
        filas = [json.loads(linea) for linea in f]
    assert filas == [{
        "codigo_ine": "01", "anio": 2026, "mes": 8,
        "importe_total_eur": 200.0, "n_concesiones": 2,
    }]


def test_recortar_top_organismos_agrupa_el_resto_en_otros():
    totales_organismo = {
        "09": {f"Organismo {i}": {"importe_total_eur": float(20 - i), "n_concesiones": 1} for i in range(20)},
    }

    recortado = ingesta_bdns.recortar_top_organismos(totales_organismo, n=15)

    assert len(recortado["09"]) == 16  # 15 + OTROS
    assert "OTROS" in recortado["09"]
    assert recortado["09"]["OTROS"]["n_concesiones"] == 5
    assert recortado["09"]["OTROS"]["importe_total_eur"] == pytest.approx(5.0 + 4.0 + 3.0 + 2.0 + 1.0)


def test_recortar_top_organismos_sin_recorte_si_hay_15_o_menos():
    totales_organismo = {
        "09": {"Organismo A": {"importe_total_eur": 100.0, "n_concesiones": 1}},
    }

    recortado = ingesta_bdns.recortar_top_organismos(totales_organismo, n=15)

    assert recortado == totales_organismo
    assert "OTROS" not in recortado["09"]


def test_recortar_top_organismos_suma_a_un_otros_existente():
    organismos = {f"Organismo {i}": {"importe_total_eur": float(20 - i), "n_concesiones": 1} for i in range(15)}
    organismos["OTROS"] = {"importe_total_eur": 500.0, "n_concesiones": 3}
    organismos["Organismo chico"] = {"importe_total_eur": 0.5, "n_concesiones": 1}
    totales_organismo = {"09": organismos}

    recortado = ingesta_bdns.recortar_top_organismos(totales_organismo, n=15)

    # "OTROS" (500.0) entra en el top 15 por importe; Organismo 14 (6.0) y "Organismo chico" (0.5)
    # son los que sobran y se suman al "OTROS" existente en vez de pisarlo.
    assert recortado["09"]["OTROS"]["importe_total_eur"] == pytest.approx(500.0 + 6.0 + 0.5)
    assert recortado["09"]["OTROS"]["n_concesiones"] == 3 + 1 + 1
    assert len(recortado["09"]) == 15


def test_recortar_top_organismos_exactamente_n_no_agrega_otros():
    totales_organismo = {
        "09": {f"Organismo {i}": {"importe_total_eur": float(15 - i), "n_concesiones": 1} for i in range(15)},
    }

    recortado = ingesta_bdns.recortar_top_organismos(totales_organismo, n=15)

    assert len(recortado["09"]) == 15
    assert "OTROS" not in recortado["09"]
    assert recortado == totales_organismo


def test_recortar_top_organismos_n_mas_uno_agrega_un_solo_organismo_a_otros():
    totales_organismo = {
        "09": {f"Organismo {i}": {"importe_total_eur": float(16 - i), "n_concesiones": 1} for i in range(16)},
    }

    recortado = ingesta_bdns.recortar_top_organismos(totales_organismo, n=15)

    assert len(recortado["09"]) == 16  # 15 top + OTROS
    assert recortado["09"]["OTROS"] == {"importe_total_eur": 1.0, "n_concesiones": 1}


def test_reprocesar_desde_raw_lanza_si_no_existe_el_raw(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(ingesta_bdns, "RAW_DIR", tmp_path / "raw")

    with pytest.raises(SystemExit):
        ingesta_bdns.reprocesar_desde_raw(2026, 8)


def test_reprocesar_desde_raw_reconstruye_agregados_desde_el_raw_local(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "OUTPUT_DIR", tmp_path)
    raw_dir = tmp_path / "raw"
    monkeypatch.setattr(ingesta_bdns, "RAW_DIR", raw_dir)
    raw_dir.mkdir()

    filas_raw = [
        {"nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Departamento A", "importe": 100.0},
        {"nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Departamento B", "importe": 50.0},
        {"nivel1": "ESTATAL", "nivel2": None, "importe": 999.0},
    ]
    with gzip.open(raw_dir / "2026-08.jsonl.gz", "wt", encoding="utf-8") as f:
        for fila in filas_raw:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")

    ingesta_bdns.reprocesar_desde_raw(2026, 8)

    agregado_path = tmp_path / "agregado_ccaa_2026-08.jsonl"
    with open(agregado_path, encoding="utf-8") as f:
        fila = json.loads(f.readline())
    assert fila == {
        "codigo_ine": "09", "anio": 2026, "mes": 8,
        "importe_total_eur": 150.0, "n_concesiones": 2,
    }

    organismo_path = tmp_path / "agregado_ccaa_organismo_2026-08.jsonl"
    with open(organismo_path, encoding="utf-8") as f:
        filas_org = [json.loads(linea) for linea in f]
    assert {(f["organismo"], f["importe_total_eur"]) for f in filas_org} == {
        ("Departamento A", 100.0), ("Departamento B", 50.0),
    }

    sin_asignar_path = tmp_path / "sin_ccaa_asignada_2026-08.jsonl"
    with open(sin_asignar_path, encoding="utf-8") as f:
        assert len(f.readlines()) == 1
