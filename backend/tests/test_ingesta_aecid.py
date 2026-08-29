import ingesta_aecid


class FakeResponse:
    def __init__(self, text="", json_data=None):
        self.text = text
        self._json_data = json_data or {}

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


def test_get_bdns_info_returns_none_when_no_url_fuente():
    assert ingesta_aecid.get_bdns_info(None) == (None, None)


def test_get_bdns_info_returns_none_when_page_has_no_bdns_link(monkeypatch):
    calls = []

    def fake_get(url, *args, **kwargs):
        calls.append(url)
        return FakeResponse(text="<html><body>sin enlaces BDNS</body></html>")

    monkeypatch.setattr(ingesta_aecid.httpx, "get", fake_get)

    result = ingesta_aecid.get_bdns_info("https://datos.aecid.es/w/ejemplo")

    assert result == (None, None)
    assert len(calls) == 1  # never calls the BDNS API if no link was found


def test_get_bdns_info_extracts_link_and_tipo_convocatoria(monkeypatch):
    html = (
        '<a href="https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias/867523" '
        'class="logoExt">BDNS</a>'
    )
    calls = []

    def fake_get(url, *args, **kwargs):
        calls.append((url, kwargs))
        if url == "https://www.pap.hacienda.gob.es/bdnstrans/api/convocatorias":
            return FakeResponse(json_data={"tipoConvocatoria": "Concesión directa - instrumental"})
        return FakeResponse(text=html)

    monkeypatch.setattr(ingesta_aecid.httpx, "get", fake_get)

    url_bdns, tipo = ingesta_aecid.get_bdns_info("https://datos.aecid.es/w/ejemplo")

    assert url_bdns == "https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias/867523"
    assert tipo == "Concesión directa - instrumental"
    assert len(calls) == 2
    api_call_kwargs = calls[1][1]
    assert api_call_kwargs["params"] == {"vpd": "GE", "numConv": "867523"}


def test_get_bdns_info_returns_none_when_page_request_fails(monkeypatch):
    def fake_get(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(ingesta_aecid.httpx, "get", fake_get)

    assert ingesta_aecid.get_bdns_info("https://datos.aecid.es/w/ejemplo") == (None, None)


def test_get_bdns_info_returns_none_when_bdns_api_call_fails(monkeypatch):
    html = (
        '<a href="https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias/867523">BDNS</a>'
    )

    def fake_get(url, *args, **kwargs):
        if url == "https://www.pap.hacienda.gob.es/bdnstrans/api/convocatorias":
            raise RuntimeError("timeout")
        return FakeResponse(text=html)

    monkeypatch.setattr(ingesta_aecid.httpx, "get", fake_get)

    assert ingesta_aecid.get_bdns_info("https://datos.aecid.es/w/ejemplo") == (None, None)
