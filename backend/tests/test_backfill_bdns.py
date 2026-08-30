import pytest

import backfill_bdns


class ResultadoFake:
    def __init__(self, returncode):
        self.returncode = returncode


def test_parse_mes():
    assert backfill_bdns.parse_mes("2022-01") == (2022, 1)
    assert backfill_bdns.parse_mes("2026-08") == (2026, 8)


def test_generar_meses_dentro_de_un_anio():
    assert list(backfill_bdns.generar_meses((2023, 5), (2023, 8))) == [
        (2023, 5), (2023, 6), (2023, 7), (2023, 8),
    ]


def test_generar_meses_cruza_de_anio():
    assert list(backfill_bdns.generar_meses((2022, 11), (2023, 2))) == [
        (2022, 11), (2022, 12), (2023, 1), (2023, 2),
    ]


def test_generar_meses_mismo_mes():
    assert list(backfill_bdns.generar_meses((2024, 3), (2024, 3))) == [(2024, 3)]


def test_generar_meses_rango_completo_2022_a_2026_08():
    meses = list(backfill_bdns.generar_meses((2022, 1), (2026, 8)))
    assert meses[0] == (2022, 1)
    assert meses[-1] == (2026, 8)
    assert len(meses) == 56  # 12 meses de 2022 + 12*3 (2023-2025) + 8 meses de 2026


def test_ejecutar_mes_exito_al_primer_intento(monkeypatch):
    llamadas = []

    def fake_run(cmd, cwd):
        llamadas.append(cmd)
        return ResultadoFake(0)

    monkeypatch.setattr(backfill_bdns.subprocess, "run", fake_run)
    monkeypatch.setattr(backfill_bdns.time, "sleep", lambda s: pytest.fail("no deberia dormir"))

    assert backfill_bdns.ejecutar_mes("2026-08") is True
    assert len(llamadas) == 1


def test_ejecutar_mes_reintenta_tras_fallo_y_luego_tiene_exito(monkeypatch):
    resultados = iter([ResultadoFake(1), ResultadoFake(1), ResultadoFake(0)])
    monkeypatch.setattr(backfill_bdns.subprocess, "run", lambda cmd, cwd: next(resultados))
    dormido = []
    monkeypatch.setattr(backfill_bdns.time, "sleep", lambda s: dormido.append(s))

    assert backfill_bdns.ejecutar_mes("2026-08") is True
    assert dormido == [backfill_bdns.PAUSA_ENTRE_REINTENTOS_MES] * 2


def test_ejecutar_mes_agota_reintentos_y_devuelve_false(monkeypatch):
    llamadas = []

    def fake_run(cmd, cwd):
        llamadas.append(cmd)
        return ResultadoFake(1)

    monkeypatch.setattr(backfill_bdns.subprocess, "run", fake_run)
    monkeypatch.setattr(backfill_bdns.time, "sleep", lambda s: None)

    assert backfill_bdns.ejecutar_mes("2026-08") is False
    assert len(llamadas) == backfill_bdns.REINTENTOS_MES


def test_ejecutar_backfill_salta_meses_ya_procesados(tmp_path, monkeypatch):
    monkeypatch.setattr(backfill_bdns, "OUTPUT_DIR", tmp_path)
    (tmp_path / "agregado_ccaa_2023-01.jsonl").write_text("")

    llamados = []
    monkeypatch.setattr(backfill_bdns, "ejecutar_mes", lambda sufijo: (llamados.append(sufijo), True)[1])

    backfill_bdns.ejecutar_backfill((2023, 1), (2023, 2), forzar=False)

    assert llamados == ["2023-02"]


def test_ejecutar_backfill_reprocesa_con_forzar(tmp_path, monkeypatch):
    monkeypatch.setattr(backfill_bdns, "OUTPUT_DIR", tmp_path)
    (tmp_path / "agregado_ccaa_2023-01.jsonl").write_text("")

    llamados = []
    monkeypatch.setattr(backfill_bdns, "ejecutar_mes", lambda sufijo: (llamados.append(sufijo), True)[1])

    backfill_bdns.ejecutar_backfill((2023, 1), (2023, 1), forzar=True)

    assert llamados == ["2023-01"]


def test_ejecutar_backfill_se_detiene_en_el_primer_mes_que_falla(tmp_path, monkeypatch):
    monkeypatch.setattr(backfill_bdns, "OUTPUT_DIR", tmp_path)

    llamados = []

    def fake_ejecutar_mes(sufijo):
        llamados.append(sufijo)
        return sufijo != "2023-02"

    monkeypatch.setattr(backfill_bdns, "ejecutar_mes", fake_ejecutar_mes)

    with pytest.raises(SystemExit):
        backfill_bdns.ejecutar_backfill((2023, 1), (2023, 3), forzar=False)

    assert llamados == ["2023-01", "2023-02"]
