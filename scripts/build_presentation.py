"""Genera la presentación de la sustentación en PDF (output/pdf/presentacion_sustentacion.pdf).

Las diapositivas se escriben en HTML de 1920×1080 con los datos reales del motor y las
capturas de docs/evidencias/capturas; Google Chrome (modo headless) las imprime a PDF.
Uso: python scripts/build_presentation.py
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from automata.core import process  # noqa: E402

OUT_DIR = ROOT / "output" / "pdf"
BUILD = ROOT / "output" / ".presentacion"
CAPTURES = ROOT / "docs" / "evidencias" / "capturas"
CHROME_PATHS = [Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
                Path("/usr/bin/google-chrome"), Path("/usr/bin/chromium")]

AUTHOR = "Angel Johany Vesga Sarmiento"
INSTRUCTOR = "MSc. Carmen Janeth Parada"


def example(name):
    return json.loads((ROOT / "examples" / f"{name}.json").read_text(encoding="utf-8"))


def table(automaton, highlight_finals=True):
    """Tabla de transición con la notación de clase: → inicial, (X) final, error sin destino."""
    a = automaton
    head = "".join(f"<th>{escape(s)}</th>" for s in a["alphabet"])
    rows = []
    for q in a["states"]:
        name = f"({q})" if q in a["finals"] and highlight_finals else q
        name = ("→ " if q == a["initial"] else "") + name
        cells = "".join(f"<td>{escape(','.join(a['transitions'][q].get(s, [])) or 'error')}</td>" for s in a["alphabet"])
        rows.append(f"<tr><td class='q'>{escape(name)}</td>{cells}</tr>")
    return f"<table class='class'><tr><th>Q</th>{head}</tr>{''.join(rows)}</table>"


def slide(content, dark=False, number=None, cls=""):
    footer = "" if number is None else (
        f"<div class='foot'><span>Autómata Lab · Microproyecto 3</span><span>{number:02d}</span></div>")
    return f"<section class='slide {'dark' if dark else ''} {cls}'>{content}{footer}</section>"


def head(eyebrow, title):
    return f"<div class='head'><p class='eyebrow'>{escape(eyebrow)}</p><h2>{title}</h2></div>"


def build_html():
    vowels = process(example("01_lenguaje_vocales"))
    digits = process(example("05_lenguaje_digitos"))
    nfa = process(example("02_afnd_clase"))
    dfa = process(example("03_afd_equivalentes"))
    with (ROOT / "docs" / "matriz_pruebas.csv").open(encoding="utf-8-sig") as fh:
        matrix = list(csv.DictReader(fh))
    approved = sum(r["resultado"] == "APROBADO" for r in matrix)
    pending = sum(r["resultado"] == "PENDIENTE" for r in matrix)
    steps = vowels["stages"][0]["steps"]
    shown_steps = [s for s in steps if "→" in s][:6]
    nfa_steps = [s for s in nfa["stages"][2]["steps"] if "⟸" in s][:4]
    dfa_min = dfa["stages"][-1]
    slides = []
    n = 1

    slides.append(slide(f"""
      <p class='eyebrow light'>Teoría de la Computación · Microproyecto 3 · 2026/02</p>
      <div class='cover-title'><h1>Autómata Lab</h1>
      <p class='subtitle'>Del lenguaje al autómata finito determinista mínimo, paso a paso y con la notación de clase.</p></div>
      <div class='cover-meta'><p>{escape(AUTHOR)}</p><p>Docente: {escape(INSTRUCTOR)}</p><p>Universidad Francisco de Paula Santander</p></div>
      <div class='cover-art'><span class='n'>A</span><span class='arrow'>→</span><span class='n'>B</span><span class='arrow'>→</span><span class='n final'>C</span></div>
    """, dark=True, cls="cover"))

    n += 1
    slides.append(slide(head("Objetivo", "Un software educativo con las dos modalidades del enunciado") + """
      <div class='two'>
        <div class='card'><p class='tag'>Modalidad A</p><h3>A partir de un lenguaje</h3>
          <p>Información ingresada: <b>alfabeto y reglas del lenguaje</b>, escritas como en los enunciados de clase.</p>
          <p class='code'>reglas → AFD → AFD mínimo</p></div>
        <div class='card'><p class='tag'>Modalidad B</p><h3>A partir de un autómata</h3>
          <p>Información ingresada: <b>estados, alfabeto, estado inicial, estados finales y transiciones</b>. Se admiten AFD y AFND.</p>
          <p class='code'>AFD o AFND → AFD → AFD mínimo</p></div>
      </div>
      <p class='lead'><b>Salida final:</b> tabla y diagrama de transición del AFD mínimo, con cada operación explicada y cada etapa consultable.</p>
    """, number=n))

    n += 1
    slides.append(slide(head("Notación de clase", "Los resultados se leen como en el tablero") + """
      <div class='two wide-right'>
        <div><div class='formula'>AF = { {Q}, q0, Σ, {Qt}, δ }</div>
          <p class='lead'>Cada etapa muestra su definición formal, su tabla de transición y su diagrama de transición.</p></div>
        <table class='plain'>
          <tr><th>Elemento</th><th>En Autómata Lab</th></tr>
          <tr><td>Lenguaje</td><td>Σ = {…} y L = { reglas }; W es una palabra</td></tr>
          <tr><td>Estados</td><td>A, B, C… (q0, q1… si son más de 26)</td></tr>
          <tr><td>Transición</td><td>A,0→B · si va a MÁS de uno: B,0→B,C</td></tr>
          <tr><td>Tabla</td><td>Columna Q, → en q0, círculo en Qt</td></tr>
          <tr><td>Sin destino</td><td>error · estado ERROR</td></tr>
          <tr><td>Estado del AFD</td><td>Concatenación: AC, ABC, BCD</td></tr>
          <tr><td>Clasificación</td><td>AFD o AFND</td></tr>
        </table>
      </div>
    """, number=n))

    n += 1
    slides.append(slide(head("Flujo de transformación", "Cuatro etapas, todas consultables") + """
      <div class='flow'>
        <div class='card'><p class='tag'>1 · Entrada</p><h3>Reglas o registro</h3><p>A: producto de las reglas. B: se clasifica AFD o AFND.</p></div><span class='big-arrow'>→</span>
        <div class='card'><p class='tag'>2 · Accesibles</p><h3>Búsqueda desde q0</h3><p>Se eliminan los estados inaccesibles.</p></div><span class='big-arrow'>→</span>
        <div class='card'><p class='tag'>3 · AFND → AFD</p><h3>Subconjuntos</h3><p>AC,0→B ⟸ A,0→B · C,0→error.</p></div><span class='big-arrow'>→</span>
        <div class='card darkcard'><p class='tag'>4 · Mínimo</p><h3>Moore</h3><p>Particiones hasta el punto fijo.</p></div>
      </div>
      <p class='lead'>Si el autómata ya es determinista, el software lo indica y continúa con la minimización, como pide el enunciado.</p>
    """, number=n))

    n += 1
    slides.append(slide(head("Modalidad A · sintaxis documentada", "El lenguaje se escribe con reglas, como en los enunciados") + """
      <div class='two wide-right'>
        <div><div class='formula small'>Σ = {0, 1, 2}<br>L = {<br>&nbsp;toda W inicia y finaliza en 0<br>&nbsp;2 seguido de 0 y precedido de 1<br>&nbsp;suma maxima 6<br>&nbsp;longitud maxima 5<br>}</div>
          <p class='note'>También se aceptan redacciones de clase: «la longitud máxima de W debe ser de 5», «siempre que exista un 2 debe estar seguida de un 0…».</p></div>
        <table class='plain compact'>
          <tr><th>Regla</th><th>Significado</th></tr>
          <tr><td>inicia en S · finaliza en S</td><td>primer / último símbolo en S</td></tr>
          <tr><td>no consecutivos S excepto xy</td><td>sin dos símbolos seguidos de S</td></tr>
          <tr><td>no repetidos S</td><td>un símbolo de S no se repite seguido</td></tr>
          <tr><td>contiene w · no contiene w</td><td>la subcadena w aparece / no</td></tr>
          <tr><td>cantidad de x par | impar</td><td>paridad del número de x</td></tr>
          <tr><td>longitud maxima n · minima n</td><td>límites de longitud</td></tr>
          <tr><td>suma maxima n · menor a n</td><td>suma de los dígitos</td></tr>
          <tr><td>x seguido de S y precedido de T</td><td>contexto de cada x</td></tr>
          <tr><td>bloque maximo de x n</td><td>repeticiones seguidas de x</td></tr>
        </table>
      </div>
    """, number=n))

    n += 1
    step_items = "".join(f"<li>{escape(s)}</li>" for s in shown_steps)
    slides.append(slide(head("Demostración 1 · construcción", "Cada regla es un AFD; el lenguaje es su producto") + f"""
      <div class='two'>
        <div><div class='formula small'>Σ = {{a, e, i, p}}<br>L = {{<br>&nbsp;toda W inicia y finaliza en a<br>&nbsp;no repetidos vocales<br>}}</div>
          <p class='lead'>Un estado combina el estado de cada regla y es <b>final</b> si todas aceptan. Si una regla se incumple, la palabra va a <b>ERROR</b>.</p></div>
        <ol class='steps'>{step_items}</ol>
      </div>
    """, number=n))

    n += 1
    m = vowels["stages"][-1]["automaton"]
    slides.append(slide(head("Demostración 1 · resultado", "Ejemplo de clase Σ = {a, e, i, p}: seis estados") + f"""
      <div class='two'>
        <img src='{(CAPTURES / "01_lenguaje_afd_minimo.jpg").as_uri()}' alt='Diagrama del AFD mínimo'>
        <div>{table(m)}
          <p class='lead'>L = {{{escape(", ".join(vowels["language"][:6]))}, …}}</p>
          <p class='note'>apa: A,a→B,p→E,a→B · aceptada. aeeia y aa se rechazan porque repiten una vocal.</p></div>
      </div>
    """, number=n))

    n += 1
    dm = digits["stages"][-1]["automaton"]
    slides.append(slide(head("Demostración 1 · ejercicio de clase", "Σ = {0, 1, 2}: el producto de 31 estados se reduce a 11") + f"""
      <div class='two'>
        <img src='{(CAPTURES / "05_lenguaje_digitos_tabla.jpg").as_uri()}' alt='Tabla del AFD mínimo'>
        <div class='stack'>
          <div class='metrics'><div><b>{digits["summary"]["original_states"]}</b><span>producto de reglas</span></div><div><b>{digits["summary"]["minimal_states"]}</b><span>AFD mínimo</span></div></div>
          <p class='lead'>Qt = {{{escape(", ".join(dm["finals"]))}}}</p>
          <p class='lead'>01120: A,0→B,1→D,1→F,2→I,0→J · <b>aceptada</b></p>
          <p class='lead'>01110 · <b>aceptada</b> &nbsp; 0210 · <b>rechazada</b> (el 2 no va precedido de 1)</p>
        </div>
      </div>
    """, number=n))

    n += 1
    nfa_in = nfa["stages"][0]["automaton"]
    nfa_dfa = nfa["stages"][2]["automaton"]
    just = "".join(f"<li>{escape(s)}</li>" for s in nfa_steps)
    slides.append(slide(head("Demostración 2 · conversión AFND → AFD", "El ejercicio de clase, resuelto por el software") + f"""
      <div class='three'>
        <div>{table(nfa_in)}<p class='note'><b>AFND:</b> B,0→B,C, el 0 va a MÁS de un estado.</p></div>
        <div>{table(nfa_dfa)}</div>
        <ol class='steps small'>{just}</ol>
      </div>
    """, number=n))

    n += 1
    partitions = dfa_min["partitions"]
    p_lines = "".join(f"<li>P{i} = {' / '.join('{' + ', '.join(b) + '}' for b in part)}</li>" for i, part in enumerate(partitions))
    slides.append(slide(head("Demostración 3 · minimización de Moore", "Un inaccesible y dos estados equivalentes") + f"""
      <div class='three'>
        <div>{table(dfa["stages"][0]["automaton"])}<p class='note'>Es AFD: se indica y se continúa con la minimización.</p></div>
        <div class='stack'><p class='lead'>1. Desde A se visitan A, B y C: <b>D se elimina</b>.</p>
          <ol class='steps'>{p_lines}</ol>
          <p class='lead'>B y C van a los mismos bloques: <b>se fusionan en B</b>.</p></div>
        <div>{table(dfa_min["automaton"])}<p class='note'>4 → 3 → 3 → 2 estados. B = {{B, C}}.</p></div>
      </div>
    """, number=n))

    n += 1
    slides.append(slide(head("Arquitectura y estructuras de datos", "El motor es Python puro; la interfaz solo dibuja") + """
      <div class='two'>
        <div class='stack'>
          <div class='card'><h3>Interfaz</h3><p>HTML, CSS y diagramas SVG propios</p></div>
          <div class='card'><h3>API Flask</h3><p>/api/process y /api/simulate</p></div>
          <div class='card darkcard'><h3>Motor</h3><p>language.py: reglas y producto · core.py: subconjuntos, Moore, simulación</p></div>
        </div>
        <table class='plain'>
          <tr><th>Concepto</th><th>Estructura</th></tr>
          <tr><td>Autómata</td><td>dataclass Automaton</td></tr>
          <tr><td>Regla del lenguaje</td><td>Rule: inicio, transición, aceptación</td></tr>
          <tr><td>Estado del producto</td><td>tupla con un estado por regla</td></tr>
          <tr><td>Transiciones δ</td><td>dict origen → símbolo → frozenset</td></tr>
          <tr><td>Subconjunto del AFD</td><td>frozenset, clave del nombre AC, ABC</td></tr>
          <tr><td>Recorridos</td><td>collections.deque</td></tr>
        </table>
      </div>
    """, number=n))

    n += 1
    slides.append(slide(head("Requerimientos", "Los doce requisitos, cubiertos y probados") + """
      <div class='two'>
        <table class='plain'>
          <tr><th>RF</th><th>Cómo se cumple</th></tr>
          <tr><td>RF-01</td><td>Σ sin duplicados ni reservados</td></tr>
          <tr><td>RF-02</td><td>Reglas validadas contra Σ, con número de regla</td></tr>
          <tr><td>RF-03</td><td>Autómata por producto de reglas</td></tr>
          <tr><td>RF-04</td><td>Registro de Q, Σ, q0, Qt y δ</td></tr>
          <tr><td>RF-05</td><td>AFD o AFND, con X,a→Y,Z</td></tr>
          <tr><td>RF-06</td><td>AFND → AFD: AC, ABC, ERROR</td></tr>
        </table>
        <table class='plain'>
          <tr><th>RF</th><th>Cómo se cumple</th></tr>
          <tr><td>RF-07</td><td>Búsqueda desde q0; se eliminan</td></tr>
          <tr><td>RF-09</td><td>Moore hasta el punto fijo</td></tr>
          <tr><td>RF-10</td><td>Operaciones paso a paso</td></tr>
          <tr><td>RF-11</td><td>Tabla y diagrama de transición</td></tr>
          <tr><td>RF-12</td><td>Simulación de W con recorrido</td></tr>
          <tr><td>RF-13</td><td>Cuatro etapas comparables</td></tr>
        </table>
      </div>
      <p class='note'>El enunciado no incluye RF-08; RF-06 se interpreta como AFND → AFD, coherente con los objetivos.</p>
    """, number=n))

    n += 1
    slides.append(slide(head("Validación", "Resultados comprobados, no solo mostrados") + f"""
      <div class='metrics four'>
        <div><b>{approved}</b><span>casos aprobados en la matriz</span></div>
        <div><b>3</b><span>lenguajes de clase comparados palabra por palabra</span></div>
        <div><b>9/9</b><span>estados de la tabla AFD de clase reproducidos</span></div>
        <div><b>{pending}</b><span>casos pendientes</span></div>
      </div>
      <p class='lead'>Cada lenguaje se compara con un predicado escrito a partir del enunciado para todas las palabras hasta longitud 6; la equivalencia se verifica por producto de AFD y la minimalidad buscando una palabra que distinga cada par de estados.</p>
    """, number=n))

    n += 1
    slides.append(slide(f"""
      <p class='eyebrow light'>Autómata Lab · Microproyecto 3</p>
      <div class='cover-title'><h1>Gracias.</h1>
      <p class='subtitle'>Del lenguaje al AFD mínimo, con la misma notación del tablero.</p></div>
      <div class='cover-meta'><p>github.com/angelvesga/TC-MICROPROYECTO3-AF</p><p>Documento técnico y manual (Word, APA) · Matriz de pruebas (Excel)</p></div>
    """, dark=True, cls="cover"))

    style = """
    @page { size: 1920px 1080px; margin: 0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', Arial, sans-serif; color: #14262A; }
    .slide { width: 1920px; height: 1080px; padding: 110px 128px 150px; background: #F6F5F0; position: relative;
             page-break-after: always; display: flex; flex-direction: column; gap: 44px; overflow: hidden; }
    .slide.dark { background: #14262A; color: #F6F5F0; justify-content: space-between; padding: 128px; }
    .head h2 { font-size: 64px; line-height: 1.1; font-weight: 700; }
    .eyebrow { font-size: 24px; letter-spacing: 3px; text-transform: uppercase; color: #0F6B5C; font-weight: 600; margin-bottom: 14px; }
    .eyebrow.light { color: #7FB8AC; }
    .cover h1 { font-size: 132px; line-height: 1.05; }
    .subtitle { font-size: 44px; color: #BFD8D5; max-width: 1150px; margin-top: 24px; line-height: 1.3; }
    .cover-meta p { font-size: 32px; color: #BFD8D5; line-height: 1.5; }
    .cover-art { position: absolute; right: 128px; top: 300px; display: flex; align-items: center; gap: 28px; }
    .cover-art .n { width: 130px; height: 130px; border: 6px solid #E09F3E; border-radius: 50%; display: flex; align-items: center;
                    justify-content: center; font-size: 56px; color: #F6F5F0; }
    .cover-art .final { box-shadow: 0 0 0 10px #14262A, 0 0 0 16px #E09F3E; }
    .cover-art .arrow { font-size: 56px; color: #7FB8AC; }
    .two { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: start; }
    .two.wide-right { grid-template-columns: 0.85fr 1.15fr; }
    .three { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 40px; align-items: start; }
    .stack { display: flex; flex-direction: column; gap: 22px; }
    .card { background: #fff; border: 1px solid #D9E3E0; border-radius: 20px; padding: 36px; display: flex; flex-direction: column; gap: 14px; }
    .card h3 { font-size: 38px; }
    .card p { font-size: 28px; line-height: 1.4; color: #4A5568; }
    .darkcard { background: #14262A; border: none; }
    .darkcard h3, .darkcard p { color: #F6F5F0; }
    .tag { font-size: 24px !important; text-transform: uppercase; letter-spacing: 2px; color: #0F6B5C !important; font-weight: 600; }
    .darkcard .tag { color: #E09F3E !important; }
    .code { font-family: Consolas, monospace; background: #EAF1EE; padding: 14px 20px; border-radius: 10px; color: #14262A !important; }
    .lead { font-size: 30px; line-height: 1.45; }
    .note { font-size: 24px; line-height: 1.45; color: #4A5568; margin-top: 16px; }
    .formula { font-family: Consolas, monospace; font-size: 36px; background: #14262A; color: #E09F3E; padding: 36px 40px; border-radius: 20px; line-height: 1.5; margin-bottom: 24px; }
    .formula.small { font-size: 28px; color: #F6F5F0; }
    .flow { display: flex; align-items: stretch; gap: 20px; }
    .flow .card { flex: 1; }
    .big-arrow { font-size: 56px; color: #0F6B5C; align-self: center; }
    table { border-collapse: collapse; width: 100%; font-size: 26px; }
    table.plain th { background: #0F6B5C; color: #F6F5F0; text-align: left; padding: 12px 18px; }
    table.plain td { padding: 12px 18px; border-bottom: 1px solid #D9E3E0; background: #fff; }
    table.plain tr:nth-child(odd) td { background: #EAF1EE; }
    table.compact { font-size: 23px; }
    table.compact td, table.compact th { padding: 9px 14px; }
    table.class { font-family: Arial, sans-serif; font-size: 24px; text-align: center; }
    table.class th { background: #F4A940; color: #3B2F1E; padding: 10px; }
    table.class td { padding: 8px 10px; color: #C0392B; border-bottom: 2px solid #fff; background: #FBE3D3; }
    table.class tr:nth-child(odd) td { background: #FDF0E8; }
    table.class td.q { color: #1E7A3A; font-weight: 700; text-align: left; }
    img { width: 100%; max-height: 640px; object-fit: contain; background: #fff; border: 1px solid #C9D6D3; border-radius: 16px; }
    .steps { font-family: Consolas, monospace; font-size: 27px; line-height: 1.5; padding-left: 36px; display: flex; flex-direction: column; gap: 10px; }
    .steps.small { font-size: 25px; }
    .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
    .metrics.four { grid-template-columns: repeat(4, 1fr); }
    .metrics div { background: #fff; border: 1px solid #D9E3E0; border-radius: 18px; padding: 32px; display: flex; flex-direction: column; gap: 10px; }
    .metrics b { font-size: 88px; color: #0F6B5C; line-height: 1; }
    .metrics span { font-size: 26px; color: #4A5568; line-height: 1.35; }
    .foot { position: absolute; left: 128px; right: 128px; bottom: 56px; display: flex; justify-content: space-between; font-size: 24px; color: #5B6B6E; }
    """
    return f"<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Sustentación Autómata Lab</title><style>{style}</style></head><body>{''.join(slides)}</body></html>"


def main():
    chrome = next((p for p in CHROME_PATHS if p.exists()), None)
    if chrome is None:
        raise SystemExit("No se encontró Google Chrome para imprimir el PDF.")
    BUILD.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    html = BUILD / "presentacion.html"
    html.write_text(build_html(), encoding="utf-8")
    target = OUT_DIR / "presentacion_sustentacion.pdf"
    profile = BUILD / "chrome-profile"
    subprocess.run([str(chrome), "--headless=new", "--disable-gpu", f"--user-data-dir={profile}",
                    "--no-pdf-header-footer", "--allow-file-access-from-files",
                    f"--print-to-pdf={target}", html.as_uri()], check=True, capture_output=True, timeout=120)
    shutil.rmtree(BUILD, ignore_errors=True)
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
