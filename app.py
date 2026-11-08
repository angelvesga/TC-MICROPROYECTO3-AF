"""Adaptador HTTP sin persistencia: cada solicitud contiene toda su entrada."""
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
from automata.core import InputError, MAX_STATES, automaton_from, process, simulate

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
app.json.ensure_ascii = False


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(status="ok")


def json_body():
    if not request.is_json:
        raise InputError("Utilice Content-Type: application/json.")
    data = request.get_json()
    if not isinstance(data, dict):
        raise InputError("Envíe un objeto JSON.")
    return data


@app.post("/api/process")
def process_route():
    return jsonify(process(json_body()))


@app.post("/api/simulate")
def simulate_route():
    data = json_body()
    return jsonify(simulate(automaton_from(data.get("automaton"), MAX_STATES, generated=True), data.get("word")))


@app.errorhandler(InputError)
def input_error(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(BadRequest)
def malformed_json(error):
    return jsonify(error="El JSON no es válido. Revise su estructura."), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify(error="La solicitud supera el límite de 256 KiB."), 413


@app.after_request
def headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
