import backfill_bdns


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
