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


# --- Reintentos ante errores 5xx de d-portal -------------------------------

import http.server
import threading

import diterator.iterator
import pytest

ACTIVIDAD_XML = (
    "<iati-activities><iati-activity>"
    "<iati-identifier>XM-DAC-50-21-TEST-1</iati-identifier>"
    "</iati-activity></iati-activities>"
)
VACIO_XML = "<iati-activities></iati-activities>"


@pytest.fixture
def dportal_falso(monkeypatch):
    """Servidor local que imita d-portal: responde segun una cola de status por offset."""
    estado = {"respuestas": {}, "peticiones": []}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            from urllib.parse import parse_qs, urlparse

            offset = int(parse_qs(urlparse(self.path).query)["offset"][0])
            estado["peticiones"].append(offset)
            cola = estado["respuestas"].get(offset, [])
            status = cola.pop(0) if cola else 200
            body = (ACTIVIDAD_XML if offset == 0 else VACIO_XML).encode()
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setattr(
        diterator.iterator, "API_ENDPOINT", f"http://127.0.0.1:{server.server_port}/q"
    )
    # Restaurar el modulo requests real de diterator al terminar el test.
    monkeypatch.setattr(diterator.iterator, "requests", diterator.iterator.requests)
    yield estado
    server.shutdown()


def test_iterator_reintenta_ante_502_transitorio(dportal_falso):
    dportal_falso["respuestas"][0] = [502, 502]
    ingesta_aecid.instalar_reintentos_dportal(backoff_factor=0)

    ids = [a.identifier for a in diterator.iterator.Iterator({"reporting_ref": "X"})]

    assert ids == ["XM-DAC-50-21-TEST-1"]
    assert dportal_falso["peticiones"].count(0) == 3  # 2 fallos + 1 exito


def test_iterator_falla_si_el_5xx_persiste(dportal_falso):
    dportal_falso["respuestas"][0] = [502] * 20
    ingesta_aecid.instalar_reintentos_dportal(backoff_factor=0)

    with pytest.raises(ingesta_aecid.requests.exceptions.HTTPError):
        list(diterator.iterator.Iterator({"reporting_ref": "X"}))
