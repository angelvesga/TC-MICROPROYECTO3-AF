"""Genera versiones en normas APA (7.ª edición) de los documentos Word.

- output/word/documento_tecnico_APA.docx   (desde docs/documento_tecnico.md)
- output/word/manual_usuario_APA.docx      (desde docs/manual_usuario.md)

Formato aplicado (trabajo de estudiante, APA 7):
- Papel carta, márgenes de 2,54 cm, Times New Roman 12, interlineado doble,
  sin espacio adicional entre párrafos, sangría de primera línea de 1,27 cm
  y alineación a la izquierda.
- Número de página en el encabezado, a la derecha, desde la portada.
- Portada de estudiante: título, autor, afiliación, curso, docente y fecha.
- Títulos sin numeración: nivel 1 centrado en negrita, nivel 2 a la izquierda
  en negrita.
- Tablas y figuras numeradas con su título en cursiva; tablas sin líneas
  verticales.
- Citas en el texto y lista de referencias con sangría francesa.

Requiere: python-docx (requirements-dev.txt).
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CAPTURES = DOCS / "evidencias" / "capturas"
OUT_WORD = ROOT / "output" / "word"

FONT = "Times New Roman"
MONO = "Courier New"
BLACK = RGBColor(0, 0, 0)
INDENT = Cm(1.27)

AUTHOR = "Angel Johany Vesga Sarmiento"
AFFILIATION = "Programa de Ingeniería de Sistemas, Facultad de Ingeniería, Universidad Francisco de Paula Santander"
COURSE = "Teoría de la Computación: Microproyecto 3"
INSTRUCTOR = "MSc. Carmen Janeth Parada"
DATE = "8 de noviembre de 2026"

# Figuras que se insertan al final de una sección concreta (encabezado del markdown).
FIGURES = {
    "manual_usuario": {
        "2. Modalidad A: expresión regular": [("01_abb_afd_minimo.jpg", "AFD mínimo de (a|b)*abb con cuatro estados y su definición formal AF = { {Q}, q0, Σ, {Qt}, δ }")],
        "3. Modalidad B: autómata manual (AFND de clase)": [
            ("02_afnd_conversion_tabla.jpg", "Conversión AFND → AFD del ejercicio de clase: estados A, B, BC, D, BCD, CD, ABCD, AD y AB"),
            ("02_afnd_conversion_pasos.jpg", "Explicación paso a paso con la notación de clase: BC,0→BCD ⟸ B,0→B,C · C,0→D")],
        "4. Minimizar un AFD existente": [("04_afd_clase_xyzw.jpg", "AFD de clase con estados X, Y, Z y W, que ya es mínimo")],
        "6. Simular palabras": [("01_abb_simulacion.jpg", "Tabla de transición y simulación de la palabra aabb, aceptada, con su recorrido")],
    },
    "documento_tecnico": {
        "10.1 Expresión (a|b)*abb": [("01_abb_afd_minimo.jpg", "Diagrama de transición del AFD mínimo generado por la aplicación")],
        "10.2 AFND de clase: conversión AFND → AFD": [("02_afnd_conversion_pasos.jpg", "Conversión justificada con la notación del material del curso")],
        "10.4 AFD de clase con estados X, Y, Z, W": [("04_afd_clase_xyzw.jpg", "Diagrama de transición con la presentación de clase")],
    },
}

NOTE_TRANSITIONS = "→ señala el estado inicial y los paréntesis, los estados terminales."

# Título y nota de cada tabla, en el orden en que aparecen en el markdown.
TABLES = {
    "documento_tecnico": [
        ("Notación de clase utilizada en el software", None),
        ("Casos de uso del software", None),
        ("Tabla de transición del AFD mínimo para (a|b)*abb", NOTE_TRANSITIONS),
        ("Tabla de transición del AFND de clase", NOTE_TRANSITIONS),
        ("AFD obtenido en la conversión del AFND de clase", NOTE_TRANSITIONS + " Adaptado de «Conversión de AFND a AFD», por C. J. Parada, s.f.-b."),
        ("Rutas de la interfaz HTTP", None),
        ("Trazabilidad de los requisitos del enunciado", "Los requisitos corresponden al enunciado del Microproyecto 3 (Universidad Francisco de Paula Santander [UFPS], 2026); el enunciado no contiene RF-08."),
    ],
    "manual_usuario": [
        ("Sintaxis de las expresiones regulares", None),
        ("Tabla de transición de entrada del AFND de clase", "Una casilla con error indica que no hay transición."),
        ("Mensajes frecuentes y cómo corregirlos", None),
    ],
}

# Citas en el texto (APA 7) que se insertan en el contenido original.
CITATIONS = {
    "documento_tecnico": [
        ("como servicio web en Render;", "como servicio web en Render (Render, s.f.-b);"),
        ("El documento de referencia tiene una errata",
         "El documento de referencia (Universidad Francisco de Paula Santander [UFPS], 2026) tiene una errata"),
        ("del material del curso («Autómatas de Estados Finitos» y «Conversión de AFND a AFD»), para que",
         "del material del curso, «Autómatas de Estados Finitos» y «Conversión de AFND a AFD» (Parada, s.f.-a, s.f.-b), para que"),
        ("adaptador HTTP Flask e interfaz", "adaptador HTTP Flask (Pallets, s.f.) e interfaz"),
        ("Es el ejercicio de conversión del material del curso:", "Es el ejercicio de conversión del material del curso (Parada, s.f.-b):"),
        ("Es la tabla de transición del material del curso:", "Es la tabla de transición del material del curso (Parada, s.f.-c):"),
        ("El despliegue usa `render.yaml`, Python 3.13.9,",
         "El despliegue usa `render.yaml` (Render, s.f.-a), Python 3.13.9 (Render, s.f.-c),"),
        ("Las instrucciones completas están en README.md.",
         "Las instrucciones completas están en el README.md del repositorio (Vesga Sarmiento, 2026)."),
    ],
    "manual_usuario": [
        ("Si el proyecto ya está desplegado en Render,", "Si el proyecto ya está desplegado en Render (Render, s.f.),"),
        ("sigue el README:", "sigue el README del repositorio (Vesga Sarmiento, 2026):"),
        ("La notación es la de clase:", "La notación es la de clase (Parada, s.f.-a):"),
        ("Ejercicio de conversión AFND → AFD del material del curso:",
         "Ejercicio de conversión AFND → AFD del material del curso (Parada, s.f.-b):"),
        ("del material del curso (Σ = {0, 1, 2}, q0 = X, Qt = {Z}).",
         "del material del curso (Parada, s.f.-c), con Σ = {0, 1, 2}, q0 = X y Qt = {Z}."),
    ],
}

SLIDES = "[Diapositivas de PowerPoint]. Teoría General de la Computación, Universidad Francisco de Paula Santander."
REPO = "Vesga Sarmiento, A. J. (2026). *TC-MICROPROYECTO3-AF* [Software]. GitHub. https://github.com/angelvesga/TC-MICROPROYECTO3-AF"

# Referencias en orden alfabético; *texto* va en cursiva.
REFERENCES = {
    "documento_tecnico": [
        "Pallets. (s.f.). *Flask documentation* (versión estable). https://flask.palletsprojects.com/en/stable/",
        f"Parada, C. J. (s.f.-a). *Autómatas de estados finitos* {SLIDES}",
        f"Parada, C. J. (s.f.-b). *Conversión de AFND a AFD* {SLIDES}",
        f"Parada, C. J. (s.f.-c). *Enunciados de ejercicios* {SLIDES}",
        "Render. (s.f.-a). *Blueprint YAML reference*. https://render.com/docs/blueprint-spec",
        "Render. (s.f.-b). *Deploy a Flask app on Render*. https://render.com/docs/deploy-flask",
        "Render. (s.f.-c). *Setting your Python version*. https://render.com/docs/python-version",
        "Universidad Francisco de Paula Santander. (2026). *Microproyecto #3* [Enunciado del proyecto, lineamientos 2026/02]. Teoría de la Computación.",
        REPO,
    ],
    "manual_usuario": [
        f"Parada, C. J. (s.f.-a). *Autómatas de estados finitos* {SLIDES}",
        f"Parada, C. J. (s.f.-b). *Conversión de AFND a AFD* {SLIDES}",
        f"Parada, C. J. (s.f.-c). *Enunciados de ejercicios* {SLIDES}",
        "Render. (s.f.). *Deploy a Flask app on Render*. https://render.com/docs/deploy-flask",
        REPO,
    ],
}


# ---------------------------------------------------------------- helpers
def set_font(target, name: str = FONT) -> None:
    """Fija la fuente en todas las variantes de escritura de un estilo o run."""
    el = getattr(target, "_r", None)
    r_pr = (el if el is not None else target.element).get_or_add_rPr()
    rfonts = r_pr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); r_pr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), name)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(attr)) is not None:
            del rfonts.attrib[qn(attr)]


def plain(paragraph, indent: bool = False, align=WD_ALIGN_PARAGRAPH.LEFT, double: bool = True):
    pf = paragraph.paragraph_format
    pf.first_line_indent = INDENT if indent else Cm(0)
    pf.alignment = align
    pf.space_before = Pt(0); pf.space_after = Pt(0)
    if double:
        pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    else:
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    return paragraph


INLINE = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*)")
INLINE_REF = re.compile(r"(\*[^*]+\*)")  # cursivas, solo en la lista de referencias


def add_inline(paragraph, text: str, size: float | None = None, bold: bool = False, italic: bool = False,
               ref: bool = False) -> None:
    text = text.replace("\\|", "|")
    for part in (INLINE_REF if ref else INLINE).split(text):
        if not part:
            continue
        if part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1]); set_font(run, MONO)
            run.font.size = Pt((size or 12) - 1)
        elif part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2]); run.bold = True
        elif ref and part.startswith("*") and part.endswith("*") and len(part) > 2:
            run = paragraph.add_run(part[1:-1]); run.italic = True
        else:
            run = paragraph.add_run(part)
        if size and not run.font.size:
            run.font.size = Pt(size)
        if bold: run.bold = True
        if italic: run.italic = True


def add_field(paragraph, instruction: str, placeholder: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = instruction
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t"); text.text = placeholder
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, sep, text, end):
        run._r.append(el)


def page_break(doc: Document) -> None:
    p = plain(doc.add_paragraph()); p.add_run().add_break(WD_BREAK.PAGE)


# ---------------------------------------------------------------- estilos
def configure(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21.59), Cm(27.94)  # Carta
    section.left_margin = section.right_margin = Cm(2.54)
    section.top_margin = section.bottom_margin = Cm(2.54)
    section.header_distance = section.footer_distance = Cm(1.27)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.size = Pt(12); normal.font.color.rgb = BLACK
    set_font(normal)
    pf = normal.paragraph_format
    pf.space_before = Pt(0); pf.space_after = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    pf.first_line_indent = INDENT
    pf.widow_control = True

    # Nivel 1: centrado, negrita. Nivel 2: alineado a la izquierda, negrita.
    for name, align in (("Heading 1", WD_ALIGN_PARAGRAPH.CENTER), ("Heading 2", WD_ALIGN_PARAGRAPH.LEFT)):
        st = styles[name]
        st.font.size = Pt(12); st.font.bold = True; st.font.italic = False
        st.font.color.rgb = BLACK
        set_font(st)
        hp = st.paragraph_format
        hp.alignment = align
        hp.space_before = Pt(0); hp.space_after = Pt(0)
        hp.line_spacing_rule = WD_LINE_SPACING.DOUBLE
        hp.first_line_indent = Cm(0); hp.left_indent = Cm(0)
        hp.keep_with_next = True

    # Entradas de la tabla de contenido con el mismo formato del texto.
    for level in (1, 2):
        try:
            st = styles[f"TOC {level}"]
        except KeyError:
            st = styles.add_style(f"TOC {level}", 1)
        st.base_style = normal
        st.font.size = Pt(12); set_font(st)
        st.paragraph_format.first_line_indent = Cm(0)
        st.paragraph_format.left_indent = Cm(0) if level == 1 else INDENT

    bullet = styles["List Bullet"]
    set_font(bullet); bullet.font.size = Pt(12)


def header(doc: Document) -> None:
    """Número de página en el margen superior derecho de todas las páginas."""
    section = doc.sections[0]
    section.different_first_page_header_footer = False
    hp = plain(section.header.paragraphs[0], align=WD_ALIGN_PARAGRAPH.RIGHT, double=False)
    add_field(hp, "PAGE", "1")
    for r in hp.runs:
        r.font.size = Pt(12); set_font(r)


def title_page(doc: Document, title: str) -> None:
    for _ in range(3):
        plain(doc.add_paragraph())
    p = plain(doc.add_paragraph(), align=WD_ALIGN_PARAGRAPH.CENTER)
    add_inline(p, title, bold=True)
    plain(doc.add_paragraph())
    for line in (AUTHOR, AFFILIATION, COURSE, INSTRUCTOR, DATE):
        add_inline(plain(doc.add_paragraph(), align=WD_ALIGN_PARAGRAPH.CENTER), line)
    page_break(doc)


def contents(doc: Document) -> None:
    p = plain(doc.add_paragraph(), align=WD_ALIGN_PARAGRAPH.CENTER)
    add_inline(p, "Tabla de contenido", bold=True)
    add_field(plain(doc.add_paragraph()), 'TOC \\o "1-2" \\h \\z \\u', "Actualice el campo (F9) para ver la tabla de contenido.")
    page_break(doc)


# ---------------------------------------------------------------- tablas y figuras
def border(el_pr, tag: str, edges: dict[str, int]) -> None:
    borders = OxmlElement(tag)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{edge}")
        size = edges.get(edge, 0)
        b.set(qn("w:val"), "single" if size else "nil")
        if size:
            b.set(qn("w:sz"), str(size)); b.set(qn("w:space"), "0"); b.set(qn("w:color"), "000000")
        borders.append(b)
    el_pr.append(borders)


def add_table(doc: Document, rows: list[list[str]], number: int, title: str, note: str | None) -> None:
    p = plain(doc.add_paragraph()); p.paragraph_format.keep_with_next = True
    add_inline(p, f"Tabla {number}", bold=True)
    p = plain(doc.add_paragraph()); p.paragraph_format.keep_with_next = True
    add_inline(p, title, italic=True)

    header_row, body = rows[0], rows[1:]
    table = doc.add_table(rows=1, cols=len(header_row))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_pr = table._tbl.tblPr
    for old in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(old)
    # Solo líneas horizontales: borde superior e inferior de la tabla.
    border(tbl_pr, "w:tblBorders", {"top": 8, "bottom": 8})

    def fill(cell, text, bold=False):
        par = cell.paragraphs[0]
        plain(par, double=False)
        par.paragraph_format.space_before = Pt(3); par.paragraph_format.space_after = Pt(3)
        add_inline(par, text, size=10.5, bold=bold)

    for i, text in enumerate(header_row):
        cell = table.rows[0].cells[i]
        fill(cell, text, bold=True)
        border(cell._tc.get_or_add_tcPr(), "w:tcBorders", {"top": 8, "bottom": 4})
    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); tr_pr.append(th)
    for row in body:
        cells = table.add_row().cells
        for i, text in enumerate(row):
            fill(cells[i], text)
    for row in table.rows:
        cant = OxmlElement("w:cantSplit"); cant.set(qn("w:val"), "true")
        row._tr.get_or_add_trPr().append(cant)
        for cell in row.cells[:]:
            for par in cell.paragraphs:
                par.paragraph_format.keep_with_next = True

    if note:
        p = plain(doc.add_paragraph())
        p.paragraph_format.space_before = Pt(6)
        add_inline(p, "Nota.", italic=True); add_inline(p, " " + note)
    plain(doc.add_paragraph())


def add_figure(doc: Document, filename: str, number: int, title: str) -> bool:
    path = CAPTURES / filename
    if not path.exists():
        return False
    p = plain(doc.add_paragraph()); p.paragraph_format.keep_with_next = True
    add_inline(p, f"Figura {number}", bold=True)
    p = plain(doc.add_paragraph()); p.paragraph_format.keep_with_next = True
    add_inline(p, title, italic=True)
    p = plain(doc.add_paragraph(), align=WD_ALIGN_PARAGRAPH.CENTER, double=False)
    p.add_run().add_picture(str(path), width=Cm(15.5))
    plain(doc.add_paragraph())
    return True


def add_code(doc: Document, lines: list[str]) -> None:
    for i, line in enumerate(lines):
        p = plain(doc.add_paragraph(), double=False)
        p.paragraph_format.left_indent = INDENT
        p.paragraph_format.keep_with_next = i < len(lines) - 1
        if i == len(lines) - 1:
            p.paragraph_format.space_after = Pt(12)
        run = p.add_run(line); set_font(run, MONO); run.font.size = Pt(10)


def list_item(doc: Document, marker: str, text: str) -> None:
    p = plain(doc.add_paragraph())
    p.paragraph_format.left_indent = INDENT
    p.paragraph_format.first_line_indent = Cm(-0.63)
    p.paragraph_format.tab_stops.add_tab_stop(INDENT, WD_TAB_ALIGNMENT.LEFT)
    p.add_run(f"{marker}\t")
    add_inline(p, text)


# ---------------------------------------------------------------- documento
def references(doc: Document, entries: list[str]) -> None:
    page_break(doc)
    doc.add_heading("Referencias", level=1)
    for entry in entries:
        p = plain(doc.add_paragraph())
        p.paragraph_format.left_indent = INDENT
        p.paragraph_format.first_line_indent = -INDENT
        add_inline(p, entry, ref=True)


def markdown_to_apa(name: str, title: str) -> Path:
    text = (DOCS / f"{name}.md").read_text(encoding="utf-8")
    for old, new in CITATIONS[name]:
        if old not in text:
            raise ValueError(f"{name}: no se encontró el texto para la cita: {old!r}")
        text = text.replace(old, new, 1)
    lines = text.splitlines()

    doc = Document()
    configure(doc)
    header(doc)
    title_page(doc, title)
    contents(doc)

    # Primera página del texto: se repite el título del trabajo.
    add_inline(plain(doc.add_paragraph(), align=WD_ALIGN_PARAGRAPH.CENTER), title, bold=True)

    figures = FIGURES.get(name, {})
    tables = iter(TABLES[name])
    pending: list[tuple[str, str]] = []
    n_table = n_figure = 0

    def flush_figures():
        nonlocal n_figure
        for filename, caption in pending:
            if add_figure(doc, filename, n_figure + 1, caption):
                n_figure += 1
        pending.clear()

    i = 0
    while i < len(lines) and not lines[i].startswith("## 1."):
        i += 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("## ") or line.startswith("### "):
            flush_figures()
            raw = line.lstrip("#").strip()
            if raw.endswith("Fuentes"):
                break  # Se sustituye por la lista de referencias en APA.
            level = 2 if line.startswith("### ") else 1
            heading = re.sub(r"^\d+(\.\d+)*\.?\s+", "", raw)
            doc.add_heading(heading, level=level)
            pending.extend(figures.get(raw, []))
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
            n_table += 1
            t_title, t_note = next(tables)
            add_table(doc, rows, n_table, t_title, t_note)
        elif m := re.match(r"^(\d+)\. (.*)", line):
            list_item(doc, f"{m.group(1)}.", m.group(2)); i += 1
        elif line.startswith("- "):
            list_item(doc, "•", line[2:]); i += 1
        elif line.strip():
            add_inline(plain(doc.add_paragraph(), indent=True), line); i += 1
        else:
            i += 1
    flush_figures()
    references(doc, REFERENCES[name])

    doc.core_properties.title = title
    doc.core_properties.author = AUTHOR
    OUT_WORD.mkdir(parents=True, exist_ok=True)
    target = OUT_WORD / f"{name}_APA.docx"
    doc.save(target)
    return target


def main() -> None:
    for name, title in (("documento_tecnico", "Autómata Lab: Documento técnico y funcional"),
                        ("manual_usuario", "Autómata Lab: Manual de usuario")):
        print(markdown_to_apa(name, title).relative_to(ROOT))


if __name__ == "__main__":
    main()
