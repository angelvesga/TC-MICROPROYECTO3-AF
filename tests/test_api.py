"""Contrato HTTP, errores y ausencia de estado compartido."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import pytest
from app import app


def payload():
    return {"mode":"language","alphabet":["a","e","i","p"],"rules":"toda W inicia y finaliza en a\nno repetidos vocales"}


def test_home_and_health():
    """RF-11: página y recursos disponibles, control de salud y políticas HTTP."""
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        assert b"Aut" in response.data and b"process-form" in response.data
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]
        assert client.get("/health").json == {"status":"ok"}
        for asset in ["/static/app.js", "/static/style.css"]:
            assert client.get(asset).status_code == 200


def test_process_and_simulate():
    """RF-03,06,09,12: contrato completo desde petición de construcción hasta simulación."""
    with app.test_client() as client:
        response = client.post("/api/process", json=payload())
        assert response.status_code == 200
        minimum = response.json["stages"][-1]["automaton"]
        assert minimum["initial"] == "A"
        for word, expected in [("a",True),("apa",True),("aa",False),("",False)]:
            sim = client.post("/api/simulate", json={"automaton":minimum,"word":word})
            assert sim.status_code == 200 and sim.json["accepted"] == expected


def test_api_invalid_requests():
    """RF-01,02,04: JSON malformado, tipos incorrectos y entradas inválidas devuelven 400."""
    with app.test_client() as client:
        for body in [None, [], {}, {"mode":"unknown"}, {"mode":"language","alphabet":["a"],"rules":"inicia en b"}]:
            response = client.post("/api/process", data=json.dumps(body), content_type="application/json")
            assert response.status_code == 400 and response.json.get("error")
        assert client.post("/api/process", data="{", content_type="application/json").status_code == 400
        assert client.post("/api/process", data="abc").status_code == 400
        assert client.post("/api/simulate", json={}).status_code == 400
        assert client.post("/api/process", data="x"*262145, content_type="application/json").status_code == 413


def test_isolation():
    """RF-12,13: solicitudes concurrentes de usuarios distintos no comparten resultados."""
    def run(rules):
        with app.test_client() as client:
            response = client.post("/api/process", json={"mode":"language","alphabet":["a"],"rules":rules})
            minimum = response.json["stages"][-1]["automaton"]
            return client.post("/api/simulate", json={"automaton":minimum,"word":""}).json["accepted"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(run, ["longitud maxima 0","inicia en a"]*6)) == [True,False]*6


def test_shipped_examples():
    """RF-03,04,13: los seis ejemplos de entrega (lenguajes y autómatas de clase) son utilizables a través de la API."""
    with app.test_client() as client:
        for path in sorted((Path(__file__).resolve().parents[1]/"examples").glob("*.json")):
            response = client.post("/api/process", json=json.loads(path.read_text(encoding="utf-8")))
            assert response.status_code == 200, response.json
            assert len(response.json["stages"]) == 4
            minimum = response.json["stages"][-1]["automaton"]
            sim = client.post("/api/simulate", json={"automaton":minimum,"word":""})
            assert sim.status_code == 200, sim.json
