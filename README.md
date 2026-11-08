# Autómata Lab · Microproyecto 3

Software educativo en **Python 3.13 + Flask** para construir un autómata desde una expresión regular, registrar AFD/AFND manualmente, convertir AFND → AFD, eliminar inaccesibles y minimizar. Cada etapa tiene tabla de transición, diagrama de transición, correspondencias y explicación del algoritmo; el simulador muestra el recorrido de cada palabra.

Los resultados usan la notación de clase: AF = { {Q}, q0, Σ, {Qt}, δ }, estados A, B, C…, transiciones A,0→B, estados del AFD con nombres concatenados (AC, ABC), estado ERROR y casillas «error». El ejemplo 02 reproduce la conversión AFND → AFD del material del curso.

Los algoritmos de Thompson, subconjuntos con cierre-ε y Moore están implementados en `automata/core.py`. No se usan bibliotecas que resuelvan autómatas.

## Entregables

- Documento técnico: [Word, normas APA](output/word/documento_tecnico_APA.docx) / [fuente](docs/documento_tecnico.md).
- Manual de usuario: [Word, normas APA](output/word/manual_usuario_APA.docx) / [fuente](docs/manual_usuario.md).
- Matriz de pruebas: [Excel](output/excel/matriz_pruebas.xlsx) / [CSV](docs/matriz_pruebas.csv).
- [Evidencias reproducibles](docs/evidencias/) y [casos de ejemplo](examples/).
- Código fuente, pruebas e instrucciones de instalación en este repositorio.

Los documentos Word en normas APA se generan con `scripts/build_office_apa.py`; la matriz en Excel, con `scripts/build_office.py`.

## Ejecutar en Windows

Instala Python 3.13 (versión de referencia: 3.13.9). Abre PowerShell en la carpeta del proyecto:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Abre **http://127.0.0.1:5000**. Detén el servidor con `Ctrl+C` en esa consola. No necesitas activar el entorno virtual ni cambiar la política de ejecución de PowerShell. Si `py` no existe, utiliza la ruta de tu `python.exe` para crear el entorno.

Gunicorn se instala como dependencia de producción, pero se ejecuta en Linux. En Windows utiliza `python app.py` para desarrollo local.

## Ejecutar en Linux/macOS

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Para producción Linux:

```bash
.venv/bin/gunicorn app:app --bind 0.0.0.0:10000 --workers 1 --threads 4 --timeout 60
```

## Pruebas y evidencias

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q --junitxml=docs/evidencias/pytest-windows.xml
.\.venv\Scripts\python.exe scripts/build_deliverables.py
.\.venv\Scripts\python.exe scripts/build_office.py
.\.venv\Scripts\python.exe scripts/build_office_apa.py
powershell -ExecutionPolicy Bypass -File scripts/finalize_office.ps1
```

En Linux sustituye `.\.venv\Scripts\python.exe` por `.venv/bin/python` y usa `pytest-linux.xml` para conservar por separado la evidencia de cada plataforma. GitHub Actions prueba cada publicación en Linux, incluyendo el arranque real de Gunicorn. Consulta la [pestaña Actions](https://github.com/angelvesga/TC-MICROPROYECTO3-AF/actions).

El generador de documentos requiere las dependencias de desarrollo y fuentes Arial/Segoe UI Symbol en Windows o DejaVu Sans en Linux. No son necesarias para ejecutar el software. Las pruebas comparan simulación por configuraciones, enumeración de palabras, equivalencia exacta por producto de AFD y distinguibilidad de cada par de estados del resultado mínimo.

La validación registrada en `docs/evidencias/ci-linux.json` pasó **22 pruebas en Linux**, incluido Gunicorn. `node tests/check_frontend.cjs` añade **4 comprobaciones de formato** de tabla/SVG y cambios de modalidad, sin abrir un navegador. La interfaz con la notación de clase se revisó visualmente en Chrome de escritorio (capturas en `docs/evidencias/capturas/`); la revisión en ancho de teléfono de esta versión está pendiente.

Para preparar el archivo de entrega después de generar documentos:

```powershell
.\.venv\Scripts\python.exe scripts/package_delivery.py
```

El ZIP se crea en `dist/TC-MICROPROYECTO3-AF-entrega.zip`; excluye entornos, cachés, credenciales, archivos temporales y metadatos Git.

## Estructura

```text
app.py                 Rutas Flask y validación HTTP
automata/core.py        Modelo y algoritmos propios
templates/             Interfaz HTML
static/                Estilos, interacción y diagramas SVG
examples/              Entradas JSON reproducibles
tests/                 Pruebas y oráculos independientes
docs/                  Documentos editables, matriz y evidencias
output/                Documentos Word (APA) y matriz en Excel para entregar
scripts/               Generación de documentos y ZIP
render.yaml            Despliegue en Render
.github/workflows/      Verificación automatizada en Linux
```

## Convenciones del enunciado

El enunciado de referencia es `MICROPROYECTO3-AF.pdf` (**Microproyecto #3**). Se interpreta RF-06 como **AFND a AFD**, coherente con los objetivos. Se conserva la numeración original: el enunciado no contiene RF-08. Se reserva ε para las transiciones vacías y se documenta explícitamente la sintaxis del lenguaje.
