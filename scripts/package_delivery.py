"""Crear ZIP mediante una lista permitida de entregables, sin datos del entorno."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=["README.md","app.py","requirements.txt","requirements-dev.txt","render.yaml",".python-version",".gitignore","pytest.ini"]
FOLDERS=["automata","templates","static","examples","tests","docs","output/pdf","scripts",".github/workflows"]


def main():
    required=[ROOT/"output/pdf"/name for name in ["documento_tecnico.pdf","manual_usuario.pdf","matriz_pruebas.pdf"]]
    if not all(p.is_file() for p in required):
        raise SystemExit("Genere primero los tres PDF con scripts/build_deliverables.py")
    files={ROOT/name for name in FILES}
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
