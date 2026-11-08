"""Prueba real de Gunicorn; solo se ejecuta en Linux (incluido GitHub Actions)."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import json
import pytest


@pytest.mark.skipif(sys.platform != "linux", reason="Gunicorn necesita Linux; ver ejecución de GitHub Actions.")
def test_gunicorn_linux():
    """Despliegue: Gunicorn escucha en 0.0.0.0 y sirve salud, interfaz y procesamiento real."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "PORT":str(port)}
    process = subprocess.Popen([sys.executable,"-m","gunicorn","app:app","--bind",f"0.0.0.0:{port}","--workers","1","--threads","4"],
                               cwd=Path(__file__).resolve().parents[1], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic()+20
        while True:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as r:
                    assert json.load(r) == {"status":"ok"}
                break
            except OSError:
                if process.poll() is not None or time.monotonic()>deadline:
                    raise AssertionError("Gunicorn no arrancó")
                time.sleep(.1)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/",timeout=3) as r:
            assert r.status == 200
        request=urllib.request.Request(f"http://127.0.0.1:{port}/api/process",data=json.dumps({"mode":"regex","alphabet":["a","b"],"expression":"(a|b)*abb"}).encode(),headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(request,timeout=5) as r:
            assert json.load(r)["summary"]["minimal_states"] == 4
    finally:
        process.terminate()
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
