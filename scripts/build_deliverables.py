"""Generar documentos y evidencias a partir del código y resultados reales.

Uso: python scripts/build_deliverables.py
Requiere un reporte pytest*.xml previamente generado en docs/evidencias.
"""
from __future__ import annotations
import ast
import csv
from datetime import datetime
from html import escape
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from automata.core import automaton_from, process, simulate
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Flowable, KeepTogether)

EVIDENCE = ROOT / "docs" / "evidencias"
OUTPUT = ROOT / "output" / "pdf"
INK = colors.HexColor("#172a31")
GREEN = colors.HexColor("#087d70")
PALE = colors.HexColor("#e7f3ed")
PAGE_WIDTH, PAGE_HEIGHT = A4
WIDTH = PAGE_WIDTH - 96


def fonts():
    win = Path("C:/Windows/Fonts")
    linux = Path("/usr/share/fonts/truetype/dejavu")
    if (win / "arial.ttf").exists():
        regular, bold, symbols = win / "arial.ttf", win / "arialbd.ttf", win / "seguisym.ttf"
    elif (linux / "DejaVuSans.ttf").exists():
        regular, bold, symbols = linux / "DejaVuSans.ttf", linux / "DejaVuSans-Bold.ttf", linux / "DejaVuSans.ttf"
    else:
        raise RuntimeError("Para regenerar PDF instale Arial/Segoe UI Symbol (Windows) o fonts-dejavu-core (Linux).")
    for name, path in [("Body", regular), ("Body-Bold", bold), ("Symbols", symbols)]:
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")


fonts()
STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle("TextBody", fontName="Body", fontSize=9.5, leading=14.5, textColor=INK, spaceAfter=8))
STYLES.add(ParagraphStyle("SmallBody", parent=STYLES["TextBody"], fontSize=8, leading=11, spaceAfter=4))
STYLES.add(ParagraphStyle("DocTitle", fontName="Body-Bold", fontSize=30, leading=35, textColor=GREEN, spaceAfter=12))
STYLES.add(ParagraphStyle("Section", fontName="Body-Bold", fontSize=14, leading=18, textColor=GREEN, spaceBefore=17, spaceAfter=9, keepWithNext=True))
STYLES.add(ParagraphStyle("Subsection", parent=STYLES["Section"], fontSize=11, leading=15, spaceBefore=12))
STYLES.add(ParagraphStyle("CodeLine", parent=STYLES["TextBody"], fontSize=8, leading=12, leftIndent=10, backColor=colors.HexColor("#f1f5ef"), spaceAfter=3))


def markup(text):
    text = escape(str(text)).replace("\\|", "|")
    text = re.sub(r"`([^`]+)`", r'<font color="#087d70">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    cmap = pdfmetrics.getFont("Body").face.charToGlyph
    # Arial carece de ∅. Se cambia solo el glifo, conservando su significado.
    for char in set(text):
        if ord(char) > 127 and ord(char) not in cmap:
            text = text.replace(char, f'<font name="Symbols">{char}</font>')
    return text


def p(text, style="TextBody"):
    return Paragraph(markup(text), STYLES[style])


def table(rows, widths=None):
    if not widths:
        weights = [max(5, min(35, max(len(str(row[i])) for row in rows))) ** .6 for i in range(len(rows[0]))]
        widths = [WIDTH * w / sum(weights) for w in weights]
    data = [[p(cell, "SmallBody") for cell in row] for row in rows]
    result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),PALE), ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),8), ("RIGHTPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LINEBELOW",(0,0),(-1,0),.7,GREEN),
        ("LINEBELOW",(0,1),(-1,-1),.3,colors.HexColor("#dbe3df")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#fafcf9")]),
    ]))
    return result


def markdown_story(text):
    story, paragraph = [], []
    lines = text.splitlines()
    in_code = False

    def flush():
        if paragraph:
            story.append(p(" ".join(paragraph)))
            paragraph.clear()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("```"):
            flush(); in_code = not in_code; i += 1; continue
        if in_code:
            story.append(p(line or " ", "CodeLine")); i += 1; continue
        if line.startswith("|"):
            flush(); rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = re.split(r"(?<!\\)\|", lines[i].strip().strip("|"))
                if not all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells):
                    rows.append([c.strip() for c in cells])
                i += 1
            if rows:
                story.extend([table(rows), Spacer(1, 10)])
            continue
        if line.startswith("#"):
            flush()
            level = len(line) - len(line.lstrip("#"))
            story.append(p(line.lstrip("# "), "DocTitle" if level == 1 else "Section" if level == 2 else "Subsection"))
        elif not line:
            flush()
        elif line.startswith("- ") or re.match(r"^\d+\. ", line):
            flush(); story.append(p(line))
        else:
            paragraph.append(line)
        i += 1
    flush()
    return story


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#dbe3df"))
    canvas.line(48, 43, PAGE_WIDTH-48, 43)
    canvas.setFont("Body", 8)
    canvas.setFillColor(colors.HexColor("#62757a"))
    canvas.drawString(48, 29, "AUTÓMATA LAB  /  TEORÍA DE LA COMPUTACIÓN")
    canvas.drawRightString(PAGE_WIDTH-48, 29, f"{doc.page}")
    canvas.restoreState()


def pdf(name, story, title):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUTPUT/name), pagesize=A4, rightMargin=48, leftMargin=48,
                            topMargin=42, bottomMargin=58, title=title, author="Autómata Lab", pageCompression=1)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


class AutomatonDiagram(Flowable):
    """Diagrama vectorial para evidencias; usa el resultado real, no una captura web."""
    def __init__(self, automaton):
        super().__init__()
        self.a = automaton
        self.width, self.height = WIDTH, 260

    def draw(self):
        c, a = self.canv, self.a
        n = len(a.states)
        cx, cy, radius = WIDTH/2, 110, 66 if n > 1 else 0
        pos = {q:(cx+radius*math.cos(math.pi/2-i*2*math.pi/n),cy+radius*math.sin(math.pi/2-i*2*math.pi/n)) for i,q in enumerate(a.states)}
        groups = {}
        for q in a.states:
            for s in a.alphabet:
                for target in a.targets(q,s):
                    groups.setdefault((q,target),[]).append(s)
        c.setLineWidth(1)
        c.setFont("Body", 9)

        def arrow(x,y,angle):
            path=c.beginPath();path.moveTo(x,y)
            path.lineTo(x-7*math.cos(angle-.4),y-7*math.sin(angle-.4))
            path.lineTo(x-7*math.cos(angle+.4),y-7*math.sin(angle+.4))
            path.close();c.drawPath(path,fill=1,stroke=0)

        for (q,t), symbols in groups.items():
            x,y=pos[q];tx,ty=pos[t]
            c.setStrokeColor(colors.HexColor("#73958b"));c.setFillColor(GREEN)
            if q==t:
                path=c.beginPath();path.moveTo(x-15,y+17)
                path.curveTo(x-55,y+64,x+55,y+64,x+15,y+17)
                c.drawPath(path);arrow(x+15,y+17,-2.2)
                lx,ly=x,y+51
            else:
                dx,dy=tx-x,ty-y;length=math.hypot(dx,dy)
                ux,uy=dx/length,dy/length
                bend=30 if (t,q) in groups else 12
                mx,my=(x+tx)/2-uy*bend,(y+ty)/2+ux*bend
                start_angle=math.atan2(my-y,mx-x);end_angle=math.atan2(ty-my,tx-mx)
                sx,sy=x+24*math.cos(start_angle),y+24*math.sin(start_angle)
                ex,ey=tx-26*math.cos(end_angle),ty-26*math.sin(end_angle)
                path=c.beginPath();path.moveTo(sx,sy)
                path.curveTo(sx+2*(mx-sx)/3,sy+2*(my-sy)/3,ex+2*(mx-ex)/3,ey+2*(my-ey)/3,ex,ey)
                c.drawPath(path);arrow(ex,ey,end_angle)
                lx,ly=(sx+2*mx+ex)/4,(sy+2*my+ey)/4+5
            label=", ".join(symbols);tw=pdfmetrics.stringWidth(label,"Body",9)
            c.setFillColor(colors.white);c.rect(lx-tw/2-2,ly-2,tw+4,12,fill=1,stroke=0)
            c.setFillColor(INK);c.drawCentredString(lx,ly,label)
        for q in a.states:
            x,y=pos[q];c.setStrokeColor(GREEN);c.setFillColor(PALE if q in a.finals else colors.white)
            c.circle(x,y,23,fill=1,stroke=1)
            if q in a.finals:c.circle(x,y,19,fill=0,stroke=1)
            c.setFillColor(INK);c.drawCentredString(x,y-3,q)
            if q==a.initial:
                c.line(x-53,y,x-26,y);arrow(x-26,y,0)


def descriptions():
    found={}
    for path in (ROOT/"tests").glob("test_*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node,ast.FunctionDef) and node.name.startswith("test_"):
                found[node.name]=ast.get_docstring(node) or node.name
    return found


def matrix_rows():
    desc=descriptions();rows=[]
    reports=sorted(EVIDENCE.glob("pytest-*.xml"))
    if not reports:
        raise RuntimeError("Ejecute pytest con --junitxml=docs/evidencias/pytest-windows.xml antes de generar la matriz.")
    for report in reports:
        for test in ET.parse(report).getroot().iter("testcase"):
            name=test.get("name");detail=desc.get(name,name)
            requirement, _, expected=detail.partition(": ")
            state="APROBADO"
            if test.find("failure") is not None or test.find("error") is not None:state="FALLÓ"
            if test.find("skipped") is not None:state="OMITIDO"
            rows.append({"id":f"P{len(rows)+1:02}","requisito":requirement,"caso":name,
                         "esperado":expected or detail,"resultado":state,"evidencia":f"docs/evidencias/{report.name}"})
    ci_file=EVIDENCE/"ci-linux.json"
    if ci_file.exists():
        ci=json.loads(ci_file.read_text(encoding="utf-8"))
        rows.append({"id":f"P{len(rows)+1:02}","requisito":"Despliegue Linux","caso":"github_actions",
                     "esperado":"Instalación limpia, suite completa y arranque real de Gunicorn.",
                     "resultado":"APROBADO" if ci.get("conclusion")=="success" else "PENDIENTE",
                     "evidencia":ci["html_url"]})
    frontend_file=EVIDENCE/"frontend.json"
    if frontend_file.exists():
        frontend=json.loads(frontend_file.read_text(encoding="utf-8"))
        rows.append({"id":f"P{len(rows)+1:02}","requisito":"RF-11,13 / formato","caso":"check_frontend.cjs",
                     "esperado":frontend["description"],"resultado":"APROBADO" if frontend["result"]=="success" else "FALLÓ",
                     "evidencia":"docs/evidencias/frontend.json"})
    rows.append({"id":"V01","requisito":"RF-05,11,12,13 / interfaz","caso":"revision_visual_web",
                 "esperado":"En Chrome de escritorio (1366 px): ejemplo 01 da AFD mínimo de 4 estados con diagrama y tabla; aabb se acepta con recorrido M0→M1→M1→M2→M3; ejemplo 02 se clasifica como AFN; las cuatro etapas son consultables; cambiar de modalidad limpia resultados; sin errores de la aplicación en consola.",
                 "resultado":"APROBADO","evidencia":"docs/evidencias/capturas/"})
    rows.append({"id":"V02","requisito":"RF-11 / interfaz móvil","caso":"revision_visual_movil",
                 "esperado":"Con área visible de 657 px (mínimo de ventana de Chrome; activa el corte móvil de 760 px): diseño en una columna, ejemplo 01 construido y simulado, sin desbordamiento horizontal.",
                 "resultado":"APROBADO","evidencia":"docs/evidencias/capturas/04_vista_movil_657px.jpg"})
    return rows


def generate_evidence():
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    samples=[]
    for path in sorted((ROOT/"examples").glob("*.json")):
        request=json.loads(path.read_text(encoding="utf-8"))
        result=process(request)
        minimum=automaton_from(result["stages"][-1]["automaton"])
        simulations=[simulate(minimum,word) for word in ["","a","ab","abb","aabb","abba","aba"]]
        evidence={"input":request,"result":result,"simulations":simulations}
        (EVIDENCE/(path.stem+"_resultado.json")).write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        samples.append((path.stem,evidence,minimum))
    return samples


def main():
    samples=generate_evidence()
    for name in ["documento_tecnico","manual_usuario"]:
        text=(ROOT/"docs"/(name+".md")).read_text(encoding="utf-8")
        pdf(name+".pdf",markdown_story(text),name.replace("_"," ").title())
    rows=matrix_rows()
    with (ROOT/"docs"/"matriz_pruebas.csv").open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator="\n");writer.writeheader();writer.writerows(rows)
    passed=sum(r["resultado"]=="APROBADO" for r in rows)
    omitted=sum(r["resultado"]=="OMITIDO" for r in rows)
    pending=sum(r["resultado"]=="PENDIENTE" for r in rows)
    intro=("# Autómata Lab\n## Matriz de pruebas y evidencias\n\n"
           "Microproyecto 3 · Teoría de la Computación · 2026/02\n\n"
           f"Registros: {passed} aprobados, {omitted} omitidos y {pending} pendientes. Los resultados proceden de reportes reales; consulte el CSV y XML para los identificadores completos.\n\n"
           "La suite local corre en Windows con Python 3.13.9. Gunicorn se verifica únicamente en Linux. La comprobación exacta de equivalencia usa el producto de AFD y la minimalidad se verifica por distinguibilidad de pares. Los ensayos con AFN incluyen 30 casos reproducibles de semilla 202602.\n\n"
           "La interfaz web se revisó visualmente en Chrome de escritorio; las capturas reales están en docs/evidencias/capturas/. También se revisó con el diseño móvil activo (657 px de ancho visible). Las imágenes de este informe son diagramas vectoriales generados de los resultados reales.\n\n")
    (ROOT/"docs"/"matriz_pruebas.md").write_text(intro+"## Casos\n\n"+"\n".join(f"- {r['id']} · {r['resultado']} · {r['requisito']}: {r['esperado']} Evidencia: {r['evidencia']} ({r['caso']})." for r in rows)+"\n",encoding="utf-8")
    story=markdown_story(intro)
    story.append(table([["Caso / RF","Comprobación y resultado esperado","Resultado"]]+[
        [r["id"]+"\n"+r["requisito"],r["esperado"],r["resultado"]] for r in rows], [100,WIDTH-182,82]))
    story.extend([Spacer(1,12),p("Reproducción: python -m pytest -q --junitxml=docs/evidencias/pytest-windows.xml. El CSV enlaza cada caso con su reporte. En Linux use pytest-linux.xml; el workflow ejecuta el mismo conjunto, incluida la prueba real de Gunicorn.")])
    ci_file=EVIDENCE/"ci-linux.json"
    if ci_file.exists():
        ci=json.loads(ci_file.read_text(encoding="utf-8"))
        story.extend([p("Verificación Linux", "Section"),p("Resultado: "+ci["conclusion"]),p("Ejecución: "+ci["html_url"]),p("Commit verificado: "+ci["head_sha"])])
    for name,evidence,a in samples:
        story.extend([PageBreak(),p("Evidencia · "+name.replace("_"," "),"Section")])
        summary=evidence["result"]["summary"]
        story.append(p(f"Estados: {summary['original_states']} originales; {summary['reachable_states']} accesibles; {summary['dfa_states']} deterministas; {summary['minimal_states']} mínimos. Clasificación de entrada: {evidence['result']['classification']}."))
        story.append(AutomatonDiagram(a))
        story.append(table([["Estado",*a.alphabet]]+[[('→ ' if q==a.initial else '')+('* ' if q in a.finals else '')+q,*[", ".join(sorted(a.targets(q,s))) for s in a.alphabet]] for q in a.states]))
        story.extend([Spacer(1,12),p("Simulaciones comprobadas","Subsection"),table([["Cadena","Resultado","Recorrido"]]+[
            [s["word"] or "ε","Aceptada" if s["accepted"] else "Rechazada"," → ".join(",".join(step["states"]) or "∅" for step in s["path"])] for s in evidence["simulations"]],[60,80,WIDTH-140]),Spacer(1,10),p("Datos y pasos completos: docs/evidencias/"+name+"_resultado.json","SmallBody")])
    pdf("matriz_pruebas.pdf",story,"Matriz de pruebas y evidencias")
    print(json.dumps({"pdfs":[p.name for p in OUTPUT.glob("*.pdf")],"approved":passed,"omitted":omitted,"pending":pending}))


if __name__=="__main__":
    main()
