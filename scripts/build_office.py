"""Genera los entregables en formato Office a partir de los documentos fuente.

- output/excel/matriz_pruebas.xlsx     (desde docs/matriz_pruebas.csv)

Los documentos Word en normas APA se generan con scripts/build_office_apa.py.

Requiere: python-docx y openpyxl (requirements-dev.txt).
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CAPTURES = DOCS / "evidencias" / "capturas"
OUT_WORD = ROOT / "output" / "word"
OUT_EXCEL = ROOT / "output" / "excel"

TEAL = RGBColor(0x0F, 0x5C, 0x4F)
TEAL_HEX = "0F5C4F"
LIGHT_HEX = "E6F2EF"
INK = RGBColor(0x1E, 0x29, 0x2B)
MUTED = RGBColor(0x5B, 0x6B, 0x6E)
FONT = "Calibri"
MONO = "Consolas"

# Capturas que se insertan después de una sección concreta (documento, encabezado).
FIGURES = {
    "manual_usuario": {
        "2. Modalidad A: expresión regular": [("01_abb_afd_minimo.jpg", "Figura 1. AFD mínimo de (a|b)*abb: 4 estados, con la definición formal AF = { {Q}, q0, Σ, {Qt}, δ }.")],
        "3. Modalidad B: autómata manual (AFND de clase)": [
            ("02_afnd_conversion_tabla.jpg", "Figura 2. Conversión AFND → AFD del ejercicio de clase: A, B, BC, D, BCD, CD, ABCD, AD, AB."),
            ("02_afnd_conversion_pasos.jpg", "Figura 3. Explicación paso a paso con la notación de clase: BC,0→BCD ⟸ B,0→B,C · C,0→D.")],
        "4. Minimizar un AFD existente": [("04_afd_clase_xyzw.jpg", "Figura 4. AFD de clase con estados X, Y, Z, W: ya es mínimo.")],
        "6. Simular palabras": [("01_abb_simulacion.jpg", "Figura 5. Tabla de transición y simulación de aabb: palabra aceptada, con su recorrido.")],
    },
    "documento_tecnico": {
        "10.1 Expresión (a|b)*abb": [("01_abb_afd_minimo.jpg", "Figura 1. Diagrama de transición del AFD mínimo generado por la aplicación.")],
        "10.2 AFND de clase: conversión AFND → AFD": [("02_afnd_conversion_pasos.jpg", "Figura 2. Conversión justificada con la notación del material del curso.")],
        "10.4 AFD de clase con estados X, Y, Z, W": [("04_afd_clase_xyzw.jpg", "Figura 3. Diagrama de transición con la presentación de clase.")],
    },
}


# ---------------------------------------------------------------- Word helpers
def set_cell_shading(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def set_repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


def bottom_border(paragraph, color: str = TEAL_HEX, size: int = 12) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)
    borders.append(bottom)
    p_pr.append(borders)


def add_field(paragraph, instruction: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = instruction
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t"); text.text = "Actualice el campo (F9) para ver la tabla de contenido."
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, sep, text, end):
        run._r.append(el)


INLINE = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*)")


def add_inline(paragraph, text: str, size: float | None = None, bold: bool = False, color=None) -> None:
    text = text.replace("\\|", "|")
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1]); run.font.name = MONO
            run.font.color.rgb = TEAL
        elif part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2]); run.bold = True
        else:
            run = paragraph.add_run(part)
        if size: run.font.size = Pt(size)
        if bold: run.bold = True
        if color is not None: run.font.color.rgb = color


def configure(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21.59), Cm(27.94)  # Carta
    section.left_margin = section.right_margin = Cm(2.5)
    section.top_margin = section.bottom_margin = Cm(2.3)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = FONT; normal.font.size = Pt(11); normal.font.color.rgb = INK
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15
    for name, size, color, before, after in [("Heading 1", 16, TEAL, 18, 8), ("Heading 2", 13, TEAL, 12, 6), ("Heading 3", 11.5, INK, 10, 4)]:
        st = styles[name]
        st.font.name = FONT; st.font.size = Pt(size); st.font.bold = True; st.font.color.rgb = color
        rfonts = st.element.rPr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts"); st.element.rPr.append(rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(attr), FONT)
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rfonts.get(qn(attr)) is not None:
                del rfonts.attrib[qn(attr)]
        st.paragraph_format.space_before = Pt(before); st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True


def header_footer(doc: Document, title: str) -> None:
    section = doc.sections[0]
    section.different_first_page_header_footer = True
    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_inline(hp, f"Autómata Lab · {title}", size=8.5, color=MUTED)
    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run("Página "); run.font.size = Pt(8.5); run.font.color.rgb = MUTED
    add_field(fp, "PAGE")
    for r in fp.runs[1:]:
        r.font.size = Pt(8.5)
    # El campo PAGE no debe mostrar el texto de la tabla de contenido.
    for t in fp._p.iter(qn("w:t")):
        if t.text.startswith("Actualice"):
            t.text = "1"


def cover(doc: Document, title: str, subtitle: str, meta: str) -> None:
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph(); add_inline(p, "TEORÍA DE LA COMPUTACIÓN · MICROPROYECTO 3", size=10, bold=True, color=TEAL)
    p = doc.add_paragraph(); add_inline(p, "Autómata Lab", size=34, bold=True, color=INK)
    p.paragraph_format.space_after = Pt(2)
    p = doc.add_paragraph(); add_inline(p, title, size=20, color=TEAL)
    bottom_border(p, size=18)
    p = doc.add_paragraph(); add_inline(p, subtitle, size=12, color=MUTED)
    p.paragraph_format.space_before = Pt(12)
    for _ in range(10):
        doc.add_paragraph()
    p = doc.add_paragraph(); add_inline(p, meta, size=10, color=MUTED)
    p = doc.add_paragraph(); add_inline(p, "Repositorio: github.com/angelvesga/TC-MICROPROYECTO3-AF", size=10, color=MUTED)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_table(doc: Document, rows: list[list[str]]) -> None:
    header, body = rows[0], rows[1:]
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, text in enumerate(header):
        cell = table.rows[0].cells[i]
        cell.paragraphs[0].text = ""
        add_inline(cell.paragraphs[0], text, size=9.5, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        set_cell_shading(cell, TEAL_HEX)
    set_repeat_header(table.rows[0])
    for n, row in enumerate(body):
        cells = table.add_row().cells
        for i, text in enumerate(row):
            add_inline(cells[i].paragraphs[0], text, size=9.5)
            if n % 2:
                set_cell_shading(cells[i], "F3F7F6")
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit"); cant.set(qn("w:val"), "true"); tr_pr.append(cant)
        for cell in row.cells:
            for par in cell.paragraphs:
                par.paragraph_format.space_after = Pt(2)
                par.paragraph_format.space_before = Pt(2)
    doc.add_paragraph()


def add_code(doc: Document, lines: list[str]) -> None:
    table = doc.add_table(rows=1, cols=1)
    cell = table.rows[0].cells[0]
    set_cell_shading(cell, "F1F4F3")
    cell.paragraphs[0].text = ""
    for i, line in enumerate(lines):
        par = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        run = par.add_run(line); run.font.name = MONO; run.font.size = Pt(9.5)
        par.paragraph_format.space_after = Pt(0)
    doc.add_paragraph()


def add_figure(doc: Document, filename: str, caption: str) -> None:
    path = CAPTURES / filename
    if not path.exists():
        return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Cm(15.5))
    p.paragraph_format.keep_with_next = True
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_inline(c, caption, size=9, color=MUTED)


def markdown_to_docx(name: str, title: str, subtitle: str) -> Path:
    lines = (DOCS / f"{name}.md").read_text(encoding="utf-8").splitlines()
    doc = Document()
    configure(doc)
    header_footer(doc, title)
    cover(doc, title, subtitle, "Lineamientos 2026/02 · Python 3.13 + Flask")

    p = doc.add_paragraph(); add_inline(p, "Contenido", size=16, bold=True, color=TEAL)
    add_field(doc.add_paragraph(), 'TOC \\o "1-3" \\h \\z \\u')
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    figures = FIGURES.get(name, {})
    pending: list[tuple[str, str]] = []
    i = 0
    # Saltar el encabezado del markdown (título, subtítulo, línea de curso).
    while i < len(lines) and not lines[i].startswith("## 1."):
        i += 1

    def flush_figures():
        for f in pending:
            add_figure(doc, *f)
        pending.clear()

    while i < len(lines):
        line = lines[i]
        if line.startswith("### ") or line.startswith("## "):
            flush_figures()
            level = 2 if line.startswith("### ") else 1
            text = line.lstrip("#").strip()
            doc.add_heading(text, level=level)
            pending.extend(figures.get(text, []))
            i += 1
        elif line.startswith("```"):
            block = []; i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i]); i += 1
            add_code(doc, block); i += 1
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in re.split(r"(?<!\\)\|", lines[i].strip())[1:-1]]
                if not all(re.fullmatch(r"-+", c) for c in cells):
                    rows.append(cells)
                i += 1
            add_table(doc, rows)
        elif re.match(r"^\d+\. ", line):
            p = doc.add_paragraph(style="List Number")
            add_inline(p, re.sub(r"^\d+\. ", "", line)); i += 1
        elif line.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_inline(p, line[2:]); i += 1
        elif line.strip():
            p = doc.add_paragraph(); p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_inline(p, line); i += 1
        else:
            i += 1
    flush_figures()

    # Las listas numeradas de distintas secciones deben reiniciar en 1.
    restart_numbering(doc)
    OUT_WORD.mkdir(parents=True, exist_ok=True)
    target = OUT_WORD / f"{name}.docx"
    doc.save(target)
    return target


def restart_numbering(doc: Document) -> None:
    """Crea una instancia de numeración nueva para cada grupo de 'List Number'."""
    numbering = doc.part.numbering_part.element
    style_num = doc.styles["List Number"].element.pPr.numPr.numId.val
    abstract = numbering.num_having_numId(style_num).abstractNumId.val
    body = list(doc.element.body.iterchildren())
    in_group = False
    for el in body:
        is_item = el.tag == qn("w:p") and el.pPr is not None and el.pPr.pStyle is not None and el.pPr.pStyle.val in ("ListNumber", "List Number")
        if is_item and not in_group:
            num = numbering.add_num(abstract)
            override = num.add_lvlOverride(ilvl=0); override.add_startOverride(1)
            current = num.numId
        if is_item:
            num_pr = el.pPr.get_or_add_numPr()
            num_pr.get_or_add_ilvl().val = 0
            num_pr.get_or_add_numId().val = current
        in_group = is_item


# ---------------------------------------------------------------- Excel
def build_matrix() -> Path:
    with (DOCS / "matriz_pruebas.csv").open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    wb = Workbook()
    thin = Side(style="thin", color="C9D6D3")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    head_fill = PatternFill("solid", fgColor=TEAL_HEX)
    head_font = Font(name=FONT, bold=True, color="FFFFFF", size=11)
    wrap = Alignment(wrap_text=True, vertical="top")

    # --- Hoja Matriz
    ws = wb.active; ws.title = "Matriz"
    ws["A1"] = "Autómata Lab · Matriz de pruebas y evidencias"
    ws["A1"].font = Font(name=FONT, bold=True, size=16, color=TEAL_HEX)
    ws["A2"] = "Microproyecto 3 · Teoría de la Computación · 2026/02. Resultados tomados de reportes reales (pytest, GitHub Actions y revisión en navegador)."
    ws["A2"].font = Font(name=FONT, italic=True, size=10, color="5B6B6E")
    headers = ["ID", "Requisito (RF)", "Caso / prueba", "Comprobación y resultado esperado", "Resultado", "Evidencia"]
    keys = ["id", "requisito", "caso", "esperado", "resultado", "evidencia"]
    start = 4
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=start, column=c, value=h)
        cell.fill, cell.font, cell.border = head_fill, head_font, border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for r, row in enumerate(rows, start + 1):
        for c, k in enumerate(keys, 1):
            cell = ws.cell(row=r, column=c, value=row[k])
            cell.alignment, cell.border = wrap, border
            cell.font = Font(name=FONT, size=10, bold=(k in ("id", "resultado")))
        ws.cell(row=r, column=5).alignment = Alignment(horizontal="center", vertical="top")
        lines = max(len(row["esperado"]) // 78 + 1, len(row["evidencia"]) // 42 + 1, len(row["requisito"]) // 18 + 1)
        ws.row_dimensions[r].height = 14 * lines + 2
    last = start + len(rows)
    for col, width in zip("ABCDEF", [7, 18, 30, 70, 14, 40]):
        ws.column_dimensions[col].width = width
    ws.row_dimensions[start].height = 22
    ws.freeze_panes = ws.cell(row=start + 1, column=1)
    ws.auto_filter.ref = f"A{start}:F{last}"
    rng = f"E{start + 1}:E{last}"
    for value, fill, font in [("APROBADO", "D7EFE6", "0B6B4A"), ("OMITIDO", "FFF1CC", "8A6100"),
                              ("PENDIENTE", "FFE2CC", "9A4A00"), ("FALLÓ", "F9D6D5", "A12622")]:
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[f'"{value}"'],
                                      fill=PatternFill("solid", fgColor=fill), font=Font(bold=True, color=font)))
    ws.page_setup.orientation = "landscape"; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{start}:{start}"

    # --- Hoja Resumen
    rs = wb.create_sheet("Resumen")
    rs["A1"] = "Resumen de resultados"; rs["A1"].font = Font(name=FONT, bold=True, size=16, color=TEAL_HEX)
    rs["A3"], rs["B3"] = "Resultado", "Casos"
    for c in ("A3", "B3"):
        rs[c].fill, rs[c].font, rs[c].border = head_fill, head_font, border
    states = ["APROBADO", "OMITIDO", "PENDIENTE", "FALLÓ"]
    for i, s in enumerate(states, 4):
        rs.cell(row=i, column=1, value=s).border = border
        cell = rs.cell(row=i, column=2, value=f'=COUNTIF(Matriz!$E${start+1}:$E${last},A{i})'); cell.border = border
    tot = 4 + len(states)
    rs.cell(row=tot, column=1, value="Total").font = Font(bold=True)
    rs.cell(row=tot, column=2, value=f"=SUM(B4:B{tot-1})").font = Font(bold=True)
    rs.cell(row=tot + 1, column=1, value="% aprobado")
    pct = rs.cell(row=tot + 1, column=2, value=f"=B4/B{tot}"); pct.number_format = "0.0%"
    rs.cell(row=tot + 3, column=1, value="Nota: el caso omitido es la prueba de arranque con Gunicorn, que solo se ejecuta en Linux; en Linux (GitHub Actions) se aprobó.").font = Font(italic=True, size=9, color="5B6B6E")
    chart = BarChart(); chart.type = "bar"; chart.title = "Casos por resultado"; chart.legend = None
    chart.add_data(Reference(rs, min_col=2, min_row=3, max_row=tot - 1), titles_from_data=True)
    chart.set_categories(Reference(rs, min_col=1, min_row=4, max_row=tot - 1))
    chart.height, chart.width = 7, 13
    chart.x_axis.delete = False; chart.y_axis.delete = False
    chart.y_axis.majorGridlines = None; chart.y_axis.title = "Casos"
    from openpyxl.chart.label import DataLabelList
    chart.dataLabels = DataLabelList(); chart.dataLabels.showVal = True
    chart.dataLabels.showSerName = False; chart.dataLabels.showCatName = False
    chart.dataLabels.showLegendKey = False; chart.dataLabels.showPercent = False
    chart.series[0].graphicalProperties.solidFill = TEAL_HEX
    chart.series[0].graphicalProperties.line.solidFill = TEAL_HEX
    rs.add_chart(chart, "D3")

    # Cobertura por requisito
    rs.cell(row=tot + 6, column=1, value="Cobertura por requisito").font = Font(name=FONT, bold=True, size=13, color=TEAL_HEX)
    hr = tot + 7
    for c, h in enumerate(["Requisito", "Casos que lo cubren", "Aprobados"], 1):
        cell = rs.cell(row=hr, column=c, value=h); cell.fill, cell.font, cell.border = head_fill, head_font, border
    reqs = Counter(); ok = Counter()
    for row in rows:
        nums = re.findall(r"\d{2}", row["requisito"].split("/")[0]) if row["requisito"].startswith("RF") else []
        for n in nums:
            reqs[f"RF-{n}"] += 1
            ok[f"RF-{n}"] += row["resultado"] == "APROBADO"
    for i, rf in enumerate(sorted(reqs), hr + 1):
        for c, v in enumerate([rf, reqs[rf], ok[rf]], 1):
            rs.cell(row=i, column=c, value=v).border = border
    rs.column_dimensions["A"].width = 22; rs.column_dimensions["B"].width = 20; rs.column_dimensions["C"].width = 12

    # --- Hoja Requisitos (texto del enunciado)
    rq = wb.create_sheet("Requisitos")
    rq["A1"] = "Requerimientos funcionales del enunciado"; rq["A1"].font = Font(name=FONT, bold=True, size=16, color=TEAL_HEX)
    reqs_text = [
        ("RF-01", "Registrar y validar el alfabeto, evitando símbolos duplicados y reservando ε, ∅ y operadores."),
        ("RF-02", "Ingresar y validar el lenguaje, verificando que los símbolos pertenezcan al alfabeto."),
        ("RF-03", "Construir un autómata (Thompson desde la expresión regular)."),
        ("RF-04", "Registrar manualmente los componentes de un autómata finito."),
        ("RF-05", "Identificar si el autómata es determinista o no determinista y explicar el resultado."),
        ("RF-06", "Convertir un AFND a AFD equivalente (subconjuntos con cierre-ε)."),
        ("RF-07", "Identificar y eliminar los estados inaccesibles."),
        ("RF-09", "Minimizar el AFD mediante un algoritmo formal (Moore)."),
        ("RF-10", "Mostrar las operaciones y resultados intermedios de cada proceso."),
        ("RF-11", "Generar la tabla y el diagrama de transición del AFD mínimo."),
        ("RF-12", "Simular cadenas y mostrar su recorrido y aceptación o rechazo."),
        ("RF-13", "Consultar el resultado de cada etapa y compararlo con el resultado final."),
    ]
    for c, h in enumerate(["Código", "Requerimiento", "Casos en la matriz"], 1):
        cell = rq.cell(row=3, column=c, value=h); cell.fill, cell.font, cell.border = head_fill, head_font, border
    for i, (code, text) in enumerate(reqs_text, 4):
        rq.cell(row=i, column=1, value=code).font = Font(bold=True)
        rq.cell(row=i, column=2, value=text).alignment = wrap
        rq.cell(row=i, column=3, value=reqs.get(code, 0))
        for c in range(1, 4):
            rq.cell(row=i, column=c).border = border
    rq.cell(row=17, column=1, value="El enunciado no incluye RF-08; se conserva su numeración original.").font = Font(italic=True, size=9, color="5B6B6E")
    rq.column_dimensions["A"].width = 10; rq.column_dimensions["B"].width = 80; rq.column_dimensions["C"].width = 18

    for sheet in (rs, rq):
        sheet.page_setup.orientation = "landscape"; sheet.page_setup.fitToWidth = 1; sheet.page_setup.fitToHeight = 1
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
    OUT_EXCEL.mkdir(parents=True, exist_ok=True)
    target = OUT_EXCEL / "matriz_pruebas.xlsx"
    wb.save(target)
    return target


def main() -> None:
    # Los documentos Word se generan en normas APA con scripts/build_office_apa.py.
    print(build_matrix().relative_to(ROOT))


if __name__ == "__main__":
    main()
