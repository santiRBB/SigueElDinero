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


class FakeResponseJsonRota:
    """Simula una respuesta HTTP que llega bien (2xx) pero cuyo cuerpo no se puede parsear como
    JSON -- para probar que _get_con_reintentos tambien reintenta ante esto, no solo ante fallos
    de red (caso real visto en produccion: UnicodeDecodeError al parsear resp.json())."""

    def __init__(self, data=None, fallar=False):
        self._data = data
        self._fallar = fallar

    def raise_for_status(self):
        pass

    def json(self):
        if self._fallar:
            raise UnicodeDecodeError("utf-8", b"\xf3", 0, 1, "invalid continuation byte")
        return self._data


def test_get_con_reintentos_reintenta_ante_json_corrupto(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    respuestas = iter([
        FakeResponseJsonRota(fallar=True),
        FakeResponseJsonRota(fallar=True),
        FakeResponseJsonRota(data={"content": [], "last": True}),
    ])

    class ClientePaginaRota:
        def get(self, url, params=None):
            return next(respuestas)

    data = ingesta_bdns._get_con_reintentos(ClientePaginaRota(), ingesta_bdns.BUSQUEDA_URL, {"page": 0})

    assert data == {"content": [], "last": True}


def test_get_con_reintentos_lanza_tras_agotar_reintentos_por_json_corrupto(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)

    class ClienteSiempreJsonRoto:
        def get(self, url, params=None):
            return FakeResponseJsonRota(fallar=True)

    with pytest.raises(UnicodeDecodeError):
        ingesta_bdns._get_con_reintentos(ClienteSiempreJsonRoto(), ingesta_bdns.BUSQUEDA_URL, {"page": 0})


def test_procesar_mes_pagina_y_agrega_por_ccaa(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    paginas = [
        FakeResponsePagina(content=[
            {"id": 1, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Departamento A", "importe": 100.0},
            {"id": 2, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Departamento B", "importe": 50.0},
        ], last=False),
        FakeResponsePagina(content=[
            {"id": 3, "nivel1": "LOCAL", "nivel2": "CABILDO DE TENERIFE", "nivel3": "Cabildo de Tenerife", "importe": 30.0},
            {"id": 4, "nivel1": "ESTATAL", "nivel2": None, "importe": 999.0},
        ], last=True),
        FakeResponsePagina(content=[], last=True),
    ]
    client = FakeClientPaginado(paginas)
    raw_writer = io.StringIO()

    totales, totales_organismo, sin_asignar, concesiones_aecid, num_paginas = ingesta_bdns.procesar_mes(2026, 8, client, raw_writer)

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
    # Tres pedidos: dos con contenido y uno mas vacio -- el corte es "content" vacio, no "last"
    # (ver docstring de procesar_mes: "last" se ignora deliberadamente desde el 2026-09-03).
    assert num_paginas == 3
    assert concesiones_aecid == []
    filas_escritas = [json.loads(linea) for linea in raw_writer.getvalue().splitlines()]
    assert len(filas_escritas) == 4
    assert client.llamadas[0][1]["fechaDesde"] == "01/08/2026"
    assert client.llamadas[0][1]["fechaHasta"] == "31/08/2026"
    assert client.llamadas[1][1]["page"] == 1
    assert client.llamadas[2][1]["page"] == 2


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
    totales, totales_organismo, sin_asignar, concesiones_aecid, num_paginas = ingesta_bdns.procesar_mes(2026, 8, FlakyClient(), raw_writer)

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


def test_procesar_mes_arranca_desde_pagina_inicial_con_acumuladores_previos(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)

    class ClienteDesdePagina5:
        def __init__(self):
            self.llamadas = []

        def get(self, url, params=None):
            self.llamadas.append(dict(params))
            if params["page"] == 5:
                return FakeResponsePagina(content=[
                    {"id": 1, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Departamento C", "importe": 10.0},
                ], last=True)
            return FakeResponsePagina(content=[], last=True)

    client = ClienteDesdePagina5()
    raw_writer = io.StringIO()
    totales_previos = {"09": {"importe_total_eur": 100.0, "n_concesiones": 1}}

    totales, totales_org, sin_asignar, concesiones_aecid, num_paginas = ingesta_bdns.procesar_mes(
        2026, 8, client, raw_writer,
        totales_ccaa=totales_previos, pagina_inicial=5,
    )

    assert len(client.llamadas) == 2
    assert client.llamadas[0]["page"] == 5
    assert client.llamadas[1]["page"] == 6
    assert totales["09"] == {"importe_total_eur": 110.0, "n_concesiones": 2}
    assert num_paginas == 2


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


def test_escribir_salidas_crea_el_archivo_agregado_aecid(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "OUTPUT_DIR", tmp_path)

    concesiones_aecid = [{
        "id": 156033296, "nivel1": "ESTADO",
        "nivel3": "Agencia Estatal Agencia Española de Cooperación Internacional para el Desarrollo",
        "beneficiario": "FUNDECOR", "convocatoria": "COSTA RICA. GRANDES BOSQUES 2026 (FUNDECOR)",
        "numeroConvocatoria": "914029", "importe": 56501.4, "fechaConcesion": "2026-07-21",
    }]

    ingesta_bdns.escribir_salidas(2026, 8, {}, {}, [], concesiones_aecid)

    aecid_path = tmp_path / "agregado_aecid_2026-08.jsonl"
    with open(aecid_path, encoding="utf-8") as f:
        filas = [json.loads(linea) for linea in f]
    assert filas == [{
        "concesion_id": 156033296,
        "numero_convocatoria": "914029",
        "iso_alpha3": "CRI",
        "beneficiario": "FUNDECOR",
        "titulo": "COSTA RICA. GRANDES BOSQUES 2026 (FUNDECOR)",
        "importe_eur": 56501.4,
        "fecha_concesion": "2026-07-21",
    }]


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


def test_ruta_marcador_completo(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "RAW_DIR", tmp_path)

    assert ingesta_bdns._ruta_marcador_completo("2026-08") == tmp_path / "2026-08.completo"


def test_cargar_checkpoint_sin_raw_devuelve_vacio(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "RAW_DIR", tmp_path)

    assert ingesta_bdns._cargar_checkpoint("2026-08") == ({}, {}, [], [], set(), 0)


def test_cargar_checkpoint_retoma_desde_paginas_completas(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "RAW_DIR", tmp_path)
    monkeypatch.setattr(ingesta_bdns, "PAGE_SIZE", 2)

    filas = [
        {"id": 1, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Departamento A", "importe": 10.0},
        {"id": 2, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Departamento B", "importe": 20.0},
        {"id": 3, "nivel1": "LOCAL", "nivel2": "CABILDO DE TENERIFE", "nivel3": "Cabildo", "importe": 30.0},
        {"id": 4, "nivel1": "ESTATAL", "nivel2": None, "importe": 999.0},
    ]
    with gzip.open(tmp_path / "2026-08.jsonl.gz", "wt", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")

    totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, ids_vistos, pagina_inicial = ingesta_bdns._cargar_checkpoint("2026-08")

    assert pagina_inicial == 2  # 4 filas / PAGE_SIZE(2)
    assert totales_ccaa["09"] == {"importe_total_eur": 30.0, "n_concesiones": 2}
    assert totales_ccaa["05"] == {"importe_total_eur": 30.0, "n_concesiones": 1}
    assert len(sin_asignar) == 1
    assert ids_vistos == {1, 2, 3, 4}


def test_cargar_checkpoint_menos_de_una_pagina_completa_arranca_de_cero(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "RAW_DIR", tmp_path)

    with gzip.open(tmp_path / "2026-08.jsonl.gz", "wt", encoding="utf-8") as f:
        f.write(json.dumps(
            {"nivel1": "AUTONOMICA", "nivel2": "Cataluña", "importe": 10.0}, ensure_ascii=False,
        ) + "\n")

    assert ingesta_bdns._cargar_checkpoint("2026-08") == ({}, {}, [], [], set(), 0)


def test_cargar_checkpoint_raw_illegible_arranca_de_cero(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "RAW_DIR", tmp_path)
    (tmp_path / "2026-08.jsonl.gz").write_bytes(b"esto no es un gzip valido")

    assert ingesta_bdns._cargar_checkpoint("2026-08") == ({}, {}, [], [], set(), 0)


def test_reprocesar_desde_raw_lanza_si_no_existe_el_raw(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(ingesta_bdns, "RAW_DIR", tmp_path / "raw")

    with pytest.raises(SystemExit):
        ingesta_bdns.reprocesar_desde_raw(2026, 8)


def test_reprocesar_desde_raw_lanza_si_falta_el_marcador_de_completo(tmp_path, monkeypatch):
    """El bug real que este chequeo existe para evitar: un raw que quedo parcial por una corrida
    interrumpida es un gzip perfectamente legible -- sin el marcador, reprocesarlo produciria un
    agregado incompleto sin ningun aviso."""
    monkeypatch.setattr(ingesta_bdns, "OUTPUT_DIR", tmp_path)
    raw_dir = tmp_path / "raw"
    monkeypatch.setattr(ingesta_bdns, "RAW_DIR", raw_dir)
    raw_dir.mkdir()
    with gzip.open(raw_dir / "2026-08.jsonl.gz", "wt", encoding="utf-8") as f:
        f.write(json.dumps({"nivel1": "ESTATAL", "nivel2": None, "importe": 1.0}) + "\n")
    # deliberadamente sin crear raw_dir / "2026-08.completo"

    with pytest.raises(SystemExit, match="marcador de mes completo"):
        ingesta_bdns.reprocesar_desde_raw(2026, 8)


def test_reprocesar_desde_raw_lanza_mensaje_claro_si_el_raw_esta_corrupto(tmp_path, monkeypatch):
    monkeypatch.setattr(ingesta_bdns, "OUTPUT_DIR", tmp_path)
    raw_dir = tmp_path / "raw"
    monkeypatch.setattr(ingesta_bdns, "RAW_DIR", raw_dir)
    raw_dir.mkdir()
    (raw_dir / "2026-08.jsonl.gz").write_bytes(b"esto no es un gzip valido, quedo cortado a medias")
    (raw_dir / "2026-08.completo").touch()

    with pytest.raises(SystemExit, match="corrupto"):
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
    (raw_dir / "2026-08.completo").touch()

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


def test_resolver_pais_aecid_un_pais_mencionado():
    assert ingesta_bdns.resolver_pais_aecid("EGIPTO 2026 HELIOPOLIS Economia Circular") == "EGY"


def test_resolver_pais_aecid_sin_pais_mencionado():
    texto = "Resolución de la Presidencia de la AECID: Acciones Humanitarias 2024"
    assert ingesta_bdns.resolver_pais_aecid(texto) is None


def test_resolver_pais_aecid_dos_paises_mencionados_es_ambiguo():
    assert ingesta_bdns.resolver_pais_aecid("Cooperación entre Costa Rica y Guatemala") is None


def test_resolver_pais_aecid_no_matchea_pais_dentro_de_otra_palabra():
    # "Cisjordania" no debe matchear "Jordania" (limite de palabra)
    texto = "Mejora de la resiliencia en las laderas orientales de Cisjordania"
    assert ingesta_bdns.resolver_pais_aecid(texto) is None


def test_resolver_pais_aecid_prefiere_el_nombre_mas_largo_que_matchea():
    # "Guinea-Bisau" no debe contar como "Guinea" + "Guinea-Bisau" (dos paises => ambiguo);
    # debe resolverse al pais mas especifico que efectivamente aparece.
    assert ingesta_bdns.resolver_pais_aecid("Apoyo a comunidades rurales de Guinea-Bisáu") == "GNB"


def test_resolver_pais_aecid_texto_vacio():
    assert ingesta_bdns.resolver_pais_aecid(None) is None
    assert ingesta_bdns.resolver_pais_aecid("") is None


def test_resolver_pais_aecid_no_matchea_espana_como_pais_destino():
    texto = "SUBVENCIÓN DIRECTA A LA COORDINADORA DE ONGD ESPAÑA PARA LA FINANCIACION DE LOS GASTOS"
    assert ingesta_bdns.resolver_pais_aecid(texto) is None


def test_resolver_pais_aecid_no_matchea_granada_universidad():
    texto = "Convocatoria Universidad de Granada para cooperación internacional"
    assert ingesta_bdns.resolver_pais_aecid(texto) is None


def test_resolver_pais_aecid_no_matchea_santa_lucia_de_tirajana():
    texto = "Ayuntamiento de Santa Lucía de Tirajana, actividades de sensibilización"
    assert ingesta_bdns.resolver_pais_aecid(texto) is None


def test_es_concesion_aecid_nivel1_estado_y_nivel3_aecid():
    fila = {"nivel1": "ESTADO", "nivel3": "Agencia Estatal Agencia Española de Cooperación Internacional para el Desarrollo"}
    assert ingesta_bdns.es_concesion_aecid(fila) is True


def test_es_concesion_aecid_otro_organismo_estatal_no_cuenta():
    fila = {"nivel1": "ESTADO", "nivel3": "DIRECCIÓN GENERAL DE COOPERACIÓN AUTONÓMICA Y LOCAL"}
    assert ingesta_bdns.es_concesion_aecid(fila) is False


def test_es_concesion_aecid_nivel1_autonomica_no_cuenta_aunque_nivel3_coincida():
    fila = {"nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Agencia Estatal Agencia Española de Cooperación Internacional para el Desarrollo"}
    assert ingesta_bdns.es_concesion_aecid(fila) is False


def test_acumular_fila_agrega_concesiones_aecid_sin_afectar_ccaa():
    totales_ccaa, totales_organismo, sin_asignar, concesiones_aecid, ids_vistos = {}, {}, [], [], set()
    fila_aecid = {
        "id": 156033296, "nivel1": "ESTADO",
        "nivel3": "Agencia Estatal Agencia Española de Cooperación Internacional para el Desarrollo",
        "beneficiario": "FUNDECOR", "convocatoria": "COSTA RICA. GRANDES BOSQUES 2026 (FUNDECOR)",
        "numeroConvocatoria": "914029", "importe": 56501.4, "fechaConcesion": "2026-07-21",
    }
    fila_otro_estado = {"id": 2, "nivel1": "ESTADO", "nivel2": None, "importe": 999.0}
    fila_autonomica = {"id": 3, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 10.0}

    for fila in (fila_aecid, fila_otro_estado, fila_autonomica):
        ingesta_bdns._acumular_fila(fila, totales_ccaa, totales_organismo, sin_asignar, ids_vistos, concesiones_aecid)

    assert concesiones_aecid == [fila_aecid]
    # fila_aecid y fila_otro_estado no matchean ninguna CCAA -> ambas van a sin_asignar tambien,
    # sin cambios respecto al comportamiento actual (concesiones_aecid es un canal ADICIONAL).
    assert len(sin_asignar) == 2
    assert totales_ccaa == {"09": {"importe_total_eur": 10.0, "n_concesiones": 1}}


def test_acumular_fila_ignora_una_fila_con_id_ya_visto():
    totales_ccaa, totales_organismo, sin_asignar, ids_vistos = {}, {}, [], set()
    fila = {"id": 42, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 10.0}
    fila_duplicada = {"id": 42, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 10.0}

    es_duplicada_1 = ingesta_bdns._acumular_fila(fila, totales_ccaa, totales_organismo, sin_asignar, ids_vistos)
    es_duplicada_2 = ingesta_bdns._acumular_fila(fila_duplicada, totales_ccaa, totales_organismo, sin_asignar, ids_vistos)

    assert es_duplicada_1 is False
    assert es_duplicada_2 is True
    assert totales_ccaa == {"09": {"importe_total_eur": 10.0, "n_concesiones": 1}}


def test_acumular_fila_sin_id_nunca_se_considera_duplicada():
    totales_ccaa, totales_organismo, sin_asignar, ids_vistos = {}, {}, [], set()
    fila = {"nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 10.0}

    for _ in range(2):
        es_duplicada = ingesta_bdns._acumular_fila(fila, totales_ccaa, totales_organismo, sin_asignar, ids_vistos)
        assert es_duplicada is False

    assert totales_ccaa == {"09": {"importe_total_eur": 20.0, "n_concesiones": 2}}


def test_procesar_mes_agrega_concesiones_aecid(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    fila_aecid = {
        "id": 1, "nivel1": "ESTADO",
        "nivel3": "Agencia Estatal Agencia Española de Cooperación Internacional para el Desarrollo",
        "beneficiario": "FUNDECOR", "convocatoria": "COSTA RICA", "numeroConvocatoria": "1",
        "importe": 100.0, "fechaConcesion": "2026-07-21",
    }
    paginas = [
        FakeResponsePagina(content=[fila_aecid], last=True),
        FakeResponsePagina(content=[], last=True),
    ]
    client = FakeClientPaginado(paginas)
    raw_writer = io.StringIO()

    totales, totales_organismo, sin_asignar, concesiones_aecid, num_paginas = ingesta_bdns.procesar_mes(
        2026, 8, client, raw_writer
    )

    assert concesiones_aecid == [fila_aecid]


def test_procesar_mes_ignora_last_y_corta_solo_con_pagina_vacia(monkeypatch):
    """Regresion del hallazgo 2026-09-03: el "last" que devuelve la API no es fiable a partir de
    cierto volumen, asi que procesar_mes debe seguir pidiendo paginas aunque "last" diga True,
    hasta que una pagina realmente vuelva sin contenido."""
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    paginas = [
        FakeResponsePagina(content=[{"id": 1, "nivel1": "ESTATAL", "nivel2": None, "importe": 1.0}], last=True),
        FakeResponsePagina(content=[{"id": 2, "nivel1": "ESTATAL", "nivel2": None, "importe": 1.0}], last=True),
        FakeResponsePagina(content=[], last=False),
    ]
    client = FakeClientPaginado(paginas)

    _, _, sin_asignar, _, num_paginas = ingesta_bdns.procesar_mes(2026, 8, client, io.StringIO())

    assert num_paginas == 3
    assert len(sin_asignar) == 2


def test_procesar_mes_deduplica_una_fila_repetida_en_paginas_distintas(monkeypatch):
    """Regresion del hallazgo 2026-09-03: sin orden explicito, la misma concesion puede aparecer en
    mas de una pagina si el dataset se reordena mientras se pagina. procesar_mes no debe contarla
    dos veces."""
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    fila = {"id": 99, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 10.0}
    paginas = [
        FakeResponsePagina(content=[fila], last=False),
        FakeResponsePagina(content=[dict(fila)], last=False),  # misma concesion, pagina distinta
        FakeResponsePagina(content=[], last=True),
    ]
    client = FakeClientPaginado(paginas)

    totales, _, _, _, num_paginas = ingesta_bdns.procesar_mes(2026, 8, client, io.StringIO())

    assert totales == {"09": {"importe_total_eur": 10.0, "n_concesiones": 1}}
    assert num_paginas == 3


def test_procesar_mes_corta_con_systemexit_si_supera_el_tope_de_paginas(monkeypatch):
    """Regresion del hallazgo 2026-09-03: si la API nunca devuelve una pagina vacia (el conteo
    totalElements/last se desestabiliza), procesar_mes no debe paginar indefinidamente."""
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    monkeypatch.setattr(ingesta_bdns, "MAX_PAGINAS_POR_MES", 3)

    class ClienteQueNuncaTerminaria:
        def __init__(self):
            self.n_llamadas = 0

        def get(self, url, params=None):
            self.n_llamadas += 1
            return FakeResponsePagina(
                content=[{"id": self.n_llamadas, "nivel1": "ESTATAL", "nivel2": None, "importe": 1.0}],
                last=False,
            )

    client = ClienteQueNuncaTerminaria()

    with pytest.raises(SystemExit):
        ingesta_bdns.procesar_mes(2026, 8, client, io.StringIO())

    assert client.n_llamadas == 3


def test_procesar_incremental_corta_apenas_ve_un_id_ya_procesado(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    paginas = [
        FakeResponsePagina(content=[
            {"id": 105, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 100.0, "fechaConcesion": "2026-09-05"},
            {"id": 104, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 50.0, "fechaConcesion": "2026-09-04"},
            {"id": 100, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 999.0, "fechaConcesion": "2026-08-01"},
        ], last=False),
    ]
    client = FakeClientPaginado(paginas)
    raw_writer = io.StringIO()

    totales, totales_org, sin_asignar, concesiones_aecid, max_id_visto, num_paginas = ingesta_bdns.procesar_incremental(
        client, raw_writer, ultimo_id_procesado=100,
    )

    assert totales == {("09", 2026, 9): {"importe_total_eur": 150.0, "n_concesiones": 2}}
    assert max_id_visto == 105
    assert num_paginas == 1
    filas_escritas = [json.loads(linea) for linea in raw_writer.getvalue().splitlines()]
    assert len(filas_escritas) == 2  # la fila con id=100 (ya vista) no se vuelve a escribir al raw
    assert len(client.llamadas) == 1  # corta sin pedir una segunda pagina


def test_procesar_incremental_sin_filas_nuevas_devuelve_max_id_none(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    paginas = [
        FakeResponsePagina(content=[
            {"id": 100, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 10.0, "fechaConcesion": "2026-08-01"},
        ], last=False),
    ]
    client = FakeClientPaginado(paginas)

    totales, totales_org, sin_asignar, concesiones_aecid, max_id_visto, num_paginas = ingesta_bdns.procesar_incremental(
        client, io.StringIO(), ultimo_id_procesado=100,
    )

    assert totales == {}
    assert max_id_visto is None
    assert num_paginas == 1


def test_procesar_incremental_pide_varias_paginas_hasta_el_watermark(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    paginas = [
        FakeResponsePagina(content=[
            {"id": 3, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 10.0, "fechaConcesion": "2026-09-05"},
        ], last=False),
        FakeResponsePagina(content=[
            {"id": 2, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 20.0, "fechaConcesion": "2026-09-05"},
            {"id": 1, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 999.0, "fechaConcesion": "2026-09-04"},
        ], last=False),
    ]
    client = FakeClientPaginado(paginas)

    totales, totales_org, sin_asignar, concesiones_aecid, max_id_visto, num_paginas = ingesta_bdns.procesar_incremental(
        client, io.StringIO(), ultimo_id_procesado=1,
    )

    assert totales == {("09", 2026, 9): {"importe_total_eur": 30.0, "n_concesiones": 2}}
    assert max_id_visto == 3
    assert num_paginas == 2


def test_procesar_incremental_agrupa_por_codigo_ine_anio_mes(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    paginas = [
        FakeResponsePagina(content=[
            {"id": 10, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 100.0, "fechaConcesion": "2026-09-05"},
            {"id": 9, "nivel1": "AUTONOMICA", "nivel2": "Cataluña", "nivel3": "Depto A", "importe": 200.0, "fechaConcesion": "2026-07-20"},
        ], last=False),
        FakeResponsePagina(content=[], last=False),
    ]
    client = FakeClientPaginado(paginas)

    totales, totales_org, sin_asignar, concesiones_aecid, max_id_visto, num_paginas = ingesta_bdns.procesar_incremental(
        client, io.StringIO(), ultimo_id_procesado=0,
    )

    assert totales == {
        ("09", 2026, 9): {"importe_total_eur": 100.0, "n_concesiones": 1},
        ("09", 2026, 7): {"importe_total_eur": 200.0, "n_concesiones": 1},
    }


def test_procesar_incremental_agrega_concesiones_aecid(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    fila_aecid = {
        "id": 5, "nivel1": "ESTADO",
        "nivel3": "Agencia Estatal Agencia Española de Cooperación Internacional para el Desarrollo",
        "beneficiario": "FUNDECOR", "convocatoria": "COSTA RICA", "numeroConvocatoria": "1",
        "importe": 100.0, "fechaConcesion": "2026-09-05",
    }
    paginas = [
        FakeResponsePagina(content=[fila_aecid], last=False),
        FakeResponsePagina(content=[], last=False),
    ]
    client = FakeClientPaginado(paginas)

    _, _, sin_asignar, concesiones_aecid, _, _ = ingesta_bdns.procesar_incremental(
        client, io.StringIO(), ultimo_id_procesado=0,
    )

    assert concesiones_aecid == [fila_aecid]
    assert len(sin_asignar) == 1  # ESTADO nunca matchea una CCAA, sigue yendo tambien a sin_asignar


def test_procesar_incremental_corta_con_systemexit_si_supera_el_tope_de_paginas(monkeypatch):
    monkeypatch.setattr(ingesta_bdns.time, "sleep", lambda s: None)
    monkeypatch.setattr(ingesta_bdns, "MAX_PAGINAS_INCREMENTAL", 3)

    class ClienteQueNuncaLlegaAlWatermark:
        def __init__(self):
            self.n_llamadas = 0

        def get(self, url, params=None):
            self.n_llamadas += 1
            id_fila = 10_000 - self.n_llamadas
            return FakeResponsePagina(
                content=[{"id": id_fila, "nivel1": "ESTATAL", "nivel2": None, "importe": 1.0, "fechaConcesion": "2026-09-01"}],
                last=False,
            )

    client = ClienteQueNuncaLlegaAlWatermark()

    with pytest.raises(SystemExit):
        ingesta_bdns.procesar_incremental(client, io.StringIO(), ultimo_id_procesado=0)

    assert client.n_llamadas == 3
