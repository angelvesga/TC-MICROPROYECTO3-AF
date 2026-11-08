"""Crear ZIP mediante una lista permitida de entregables, sin datos del entorno."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=["README.md","app.py","requirements.txt","requirements-dev.txt","render.yaml",".python-version",".gitignore","pytest.ini"]
FOLDERS=["automata","templates","static","examples","tests","docs","scripts",".github/workflows"]
# Entregables: documentos Word en normas APA, matriz en Excel y presentación en PDF.
DELIVERABLES=["output/word/documento_tecnico_APA.docx","output/word/manual_usuario_APA.docx",
              "output/excel/matriz_pruebas.xlsx","output/pdf/presentacion_sustentacion.pdf"]


def main():
    required=[ROOT/name for name in DELIVERABLES]
    missing=[p.relative_to(ROOT).as_posix() for p in required if not p.is_file()]
    if missing:
        raise SystemExit("Genere primero los entregables: "+", ".join(missing))
    files={ROOT/name for name in FILES}|set(required)
    for folder in FOLDERS:
        files.update(p for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc")
    out=ROOT/"dist";out.mkdir(exist_ok=True)
    archive=out/"TC-MICROPROYECTO3-AF-entrega.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            z.write(path,"TC-MICROPROYECTO3-AF/"+path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError("ZIP con error de integridad")
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (out/(archive.name+".sha256")).write_text(digest+"  "+archive.name+"\n",encoding="ascii")
    print(json.dumps({"archive":str(archive),"files":len(files),"bytes":archive.stat().st_size,"sha256":digest}))


if __name__=="__main__":
    main()
