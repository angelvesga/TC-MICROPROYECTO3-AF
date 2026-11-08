# Autómata Lab · Microproyecto 3

Software educativo en **Python 3.13 + Flask** para construir un autómata desde una expresión regular, registrar AFD/AFN manualmente, determinizar, eliminar inaccesibles y minimizar. Cada etapa tiene tabla, diagrama, correspondencias y explicación del algoritmo; el simulador muestra el recorrido de cada cadena.

Los algoritmos de Thompson, subconjuntos con clausura épsilon y Moore están implementados en `automata/core.py`. No se usan bibliotecas que resuelvan autómatas.

## Entregables

- [Documento técnico, editable](docs/documento_tecnico.md) / [PDF](output/pdf/documento_tecnico.pdf).
- [Manual de usuario, editable](docs/manual_usuario.md) / [PDF](output/pdf/manual_usuario.pdf).
- [Matriz de pruebas](docs/matriz_pruebas.csv) / [PDF](output/pdf/matriz_pruebas.pdf).
- [Evidencias reproducibles](docs/evidencias/) y [casos de ejemplo](examples/).
- Código fuente, pruebas e instrucciones de instalación en este repositorio.

La sustentación es oral; no se incluyen diapositivas ni guion.

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

## Desplegar en Render (para el compañero)

El proyecto está preparado; no hay que modificar código ni proporcionar claves o base de datos.

1. En Render, conecta tu cuenta de GitHub con acceso a `angelvesga/TC-MICROPROYECTO3-AF`.
2. Selecciona **New > Blueprint**, elige el repositorio y la rama `main`.
3. Render leerá `render.yaml`. Revisa que sea un servicio web Python con plan **Free** y crea el servicio.
4. Espera a que termine el despliegue. Abre la URL `https://<nombre-asignado>.onrender.com` y verifica también `/health`, que debe responder `{"status":"ok"}`.
5. Carga el ejemplo «Palabras que terminan en abb»: el resultado debe tener 4 estados y aceptar `aabb`.

Si no tienes acceso al repositorio mediante la integración, tu compañero puede hacer un fork en su cuenta y conectar ese fork. No es necesario renombrar módulos ni cambiar los comandos.

Alternativa con **New > Web Service**:

| Campo | Valor |
| --- | --- |
| Repository | Este repositorio, o el fork del compañero |
| Branch | `main` |
| Language / Runtime | Python 3 |
| Root Directory | Dejar vacío |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 60` |
| Health Check Path | `/health` |
| Instance Type | Free |
| Python | `.python-version` fija 3.13.9 |

El arranque usa el puerto asignado por Render. El servicio no escribe resultados en disco ni depende de almacenamiento persistente. El plan gratuito puede suspender el servicio por inactividad y tardar en responder a la primera visita; espera al arranque antes de repetir la operación. El despliegue en Render queda a cargo del compañero; publicar el código no equivale a desplegarlo.

Documentación oficial: [Flask en Render](https://render.com/docs/deploy-flask), [Blueprint](https://render.com/docs/blueprint-spec), [versión de Python](https://render.com/docs/python-version), [plan gratuito](https://render.com/docs/free).

## Pruebas y evidencias

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q --junitxml=docs/evidencias/pytest-windows.xml
.\.venv\Scripts\python.exe scripts/build_deliverables.py
```

En Linux sustituye `.\.venv\Scripts\python.exe` por `.venv/bin/python` y usa `pytest-linux.xml` para conservar por separado la evidencia de cada plataforma. GitHub Actions prueba cada publicación en Linux, incluyendo el arranque real de Gunicorn. Consulta la [pestaña Actions](https://github.com/angelvesga/TC-MICROPROYECTO3-AF/actions).

El generador de documentos requiere las dependencias de desarrollo y fuentes Arial/Segoe UI Symbol en Windows o DejaVu Sans en Linux. No son necesarias para ejecutar el software. Las pruebas comparan simulación por configuraciones, enumeración de cadenas, equivalencia exacta por producto de AFD y distinguibilidad de cada par de estados del resultado mínimo.

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
output/pdf/            Tres documentos PDF para entregar
scripts/               Generación de documentos y ZIP
render.yaml            Despliegue en Render
.github/workflows/      Verificación automatizada en Linux
```

## Convenciones del enunciado

El archivo de referencia se llama `MICROPROYECTO1-AF.pdf`, pero su contenido indica **Microproyecto #3**. Se interpreta RF-06 como **AFN a AFD**, coherente con los objetivos. Se conserva la numeración original: el enunciado no contiene RF-08. Se reserva ε para las transiciones vacías y se documenta explícitamente la sintaxis del lenguaje.
