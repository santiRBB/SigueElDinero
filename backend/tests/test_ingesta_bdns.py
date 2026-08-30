import ingesta_bdns


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
