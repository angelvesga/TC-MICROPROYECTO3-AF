# Autómata Lab
## Documento técnico y funcional

Microproyecto 3 · Teoría de la Computación · 2026/02

## 1. Propósito y alcance

El software permite estudiar cómo distintas representaciones describen el mismo lenguaje regular. A partir de una expresión regular o de un autómata registrado manualmente, obtiene un AFD mínimo y permite revisar las operaciones realizadas, su tabla de transición, su diagrama de transición y sus simulaciones.

El público son estudiantes y docentes de Teoría de la Computación. Las dos modalidades comparten el mismo motor Python. Se admiten AFD completos, AFD con casillas en error, AFND y AFND con transiciones ε. La aplicación se ejecuta localmente o como servicio web en Render; no requiere cuentas de usuario ni base de datos.

Se excluyen expresiones regulares avanzadas de programación (capturas, referencias, rangos y lookahead), autómatas de pila, máquinas de Turing, almacenamiento de sesiones y edición gráfica por arrastre. El diagrama acompaña las transformaciones; la tabla de transición es la referencia exacta para revisar cada transición.

El documento de referencia tiene una errata en RF-06: se implementa AFND → AFD, conforme a los objetivos. RF-01 queda incompleto después de «reservando»; esta implementación reserva ε, ∅ y los operadores. No existe RF-08 en la lista original. Python fue el lenguaje solicitado para esta entrega.

## 2. Notación de clase

La presentación de resultados sigue la notación y la forma de desarrollar ejercicios del material del curso («Autómatas de Estados Finitos» y «Conversión de AFND a AFD»), para que la lectura resulte familiar:

| Elemento | Notación en el software |
| --- | --- |
| Definición formal | AF = { {Q}, q0, Σ, {Qt}, δ }, mostrada en cada etapa |
| Estados | Letras mayúsculas A, B, C…; con más de 26 estados, q0, q1, q2… |
| Transición | A,0→B; si el símbolo va a MÁS de un estado, A,1→A,C |
| Tabla de transición | Columna Q, una columna por símbolo, → en el estado inicial y círculo en los terminales |
| Casilla sin destino | error |
| Estado del AFD | Concatenación de los estados del subconjunto: AC, ABC, BCD |
| Subconjunto vacío | Estado ERROR, no terminal, que vuelve a sí mismo con todo símbolo |
| Clasificación | AFD (cada símbolo va a un solo estado) o AFND (algún símbolo va a MÁS de un estado; AFND-ε si hay transiciones vacías) |
| Lenguaje | L = {…} con las primeras palabras W aceptadas |

En la conversión, cada transición del AFD se justifica como en clase: AC,0→B ⟸ A,0→B · C,0→error. El estado inicial del AFD es el mismo q0 del AFND y son terminales los estados que contienen algún terminal del AFND.

## 3. Casos de uso

| Caso | Entrada y acción | Resultado observable |
| --- | --- | --- |
| CU-01 Construir | Registrar alfabeto y expresión; pulsar Construir y minimizar | Construcción de Thompson, accesibles, conversión AFND → AFD y AFD mínimo |
| CU-02 Registrar | Registrar Q, q0, Qt y la tabla de transición | Clasificación AFD/AFND justificada y procesamiento |
| CU-03 Explorar | Seleccionar una de las cuatro etapas | Definición formal, tabla, diagrama, correspondencias y operaciones |
| CU-04 Simular | Elegir etapa y escribir una palabra W | Recorrido A,a→B… y aceptación o rechazo |
| CU-05 Comparar | Abrir la comparación con el AFD mínimo | Número de estados y tabla final, sin perder la etapa seleccionada |
| CU-06 Exportar | Descargar resultado o SVG | JSON de todas las etapas o diagrama de la etapa actual |

Si la entrada es inválida se informa qué debe corregirse y no se entrega un resultado parcial. Si el autómata ya es determinista se indica expresamente y se continúa con su minimización. Al editar la entrada se descartan los resultados anteriores para evitar asociarlos a datos nuevos.

## 4. Sintaxis, entradas y restricciones

El alfabeto Σ es una lista no vacía de hasta 12 caracteres Unicode visibles. Cada símbolo ocupa un carácter; no se permiten duplicados, espacios, coma, barra inversa, paréntesis, |, *, ε ni ∅. En la interfaz se escribe, por ejemplo, `0, 1`; en la API, `["0", "1"]`.

Gramática de expresiones:

```text
expresion     := concatenacion ("|" concatenacion)*
concatenacion := repeticion+
repeticion    := atomo ("*")*
atomo         := simbolo | "ε" | "∅" | "(" expresion ")"
```

La prioridad descendente es estrella, concatenación y unión. `ab|c` significa `(ab)|c`. `ε` representa únicamente la palabra vacía y `∅` el lenguaje sin palabras. Las expresiones no admiten espacios ni operandos implícitamente vacíos: use `a|ε`, no `a|`. Los caracteres + y ? son literales solo si se incluyen en el alfabeto. La longitud máxima de expresión es 120 caracteres.

Los autómatas manuales admiten de 1 a 80 estados y hasta 4000 aristas. Los nombres comienzan con letra ASCII o _, seguidos de letras ASCII, números, _ o -, hasta 32 caracteres; se recomiendan letras mayúsculas como en clase. Hay exactamente un estado inicial q0 y cualquier cantidad de terminales Qt, incluso cero. En cada casilla se escriben los destinos separados por comas (C,F). Una casilla vacía o con la palabra error representa ausencia de transición, no una transición ε.

La construcción interna admite 256 estados; la conversión AFND → AFD se detiene con un error explícito antes de superar 128. Las palabras tienen hasta 1000 caracteres. En el simulador, el campo vacío representa ε. Las solicitudes HTTP se limitan a 256 KiB. Estos límites son educativos y protegen frente al crecimiento exponencial de la conversión.

## 5. Arquitectura y estructuras de datos

La aplicación tiene tres capas: motor matemático independiente en Python, adaptador HTTP Flask e interfaz HTML/CSS/JavaScript. El motor puede probarse sin navegador ni servidor. JavaScript gestiona formularios, tablas y diagramas SVG, pero las transformaciones y simulaciones se calculan en Python.

`Automaton` es una dataclass con `states` (Q) y `alphabet` (Σ) como tuplas ordenadas, `initial` (q0) como cadena, `finals` (Qt) como frozenset y `transitions` (δ) como diccionario de origen a símbolo a frozenset de destinos. Incluso en un AFD cada destino es un conjunto de un elemento. La serialización JSON convierte conjuntos a listas ordenadas según Q; ε se representa con la clave `"ε"`.

La cola de accesibilidad y la de conversión usan `deque`. Un subconjunto se almacena como `frozenset`, lo que permite usarlo como clave del diccionario que le asigna su nombre concatenado (AC, ABC). El nombrador garantiza unicidad: si dos subconjuntos produjeran el mismo nombre, lo que solo es posible con nombres de varios caracteres, el segundo se separa con guiones o recibe un sufijo. Los bloques de Moore son tuplas de estados.

Cada función devuelve un autómata nuevo o conserva el original cuando no necesita cambiarlo; no modifica los datos recibidos. Los registros de operaciones son listas de texto producidas durante los cálculos con la notación A,0→B. No hay estado mutable compartido entre solicitudes.

## 6. Construcción de Thompson

El analizador de descenso recursivo genera un árbol de operaciones según la gramática. Cada nodo se transforma en un fragmento con una entrada y una salida. Para un literal se crean dos estados y una arista con ese símbolo (A,a→B). Para ε se usa una arista vacía; para ∅ se crean dos estados sin conectarlos.

La concatenación conecta por ε la salida del primer fragmento con la entrada del segundo. La unión crea una entrada que bifurca por ε y una salida que reúne ambos fragmentos. La estrella crea caminos para cero repeticiones, para entrar al fragmento, para repetirlo y para salir. Al terminar, los estados se nombran A, B, C… en el orden de creación y la traza muestra cada conexión con esos nombres.

La corrección se justifica por inducción sobre el árbol: los fragmentos base reconocen su símbolo, ε o ningún lenguaje; las conexiones realizan respectivamente producto, unión y cierre de Kleene. El análisis y la construcción son lineales en la longitud de la expresión.

## 7. Clasificación y accesibilidad

Si existe alguna transición ε, la entrada es AFND-ε. Sin ε, si algún símbolo va a MÁS de un estado (X,a→Y,Z), es AFND. Si cada símbolo va a un solo estado (X,a→Y) en todas las casillas, es AFD. Si ninguna casilla tiene más de un destino pero algunas están en error, se informa AFD incompleto y se indican esas casillas.

Una búsqueda desde q0 recorre todas las aristas, incluidas ε. Los estados no visitados se eliminan junto con sus transiciones y su condición de terminales. El lenguaje no cambia porque ninguna ejecución iniciada en q0 puede llegar a ellos. El coste es O(n + e), con n estados y e aristas.

## 8. Conversión AFND → AFD

El cierre-ε(S) contiene los estados alcanzables desde S mediante cero o más transiciones ε. Se calcula con un conjunto de visitados, por lo que los ciclos ε terminan. El estado inicial del AFD es el q0 del AFND (o su cierre-ε si tiene transiciones vacías). Para cada estado T del AFD y símbolo a se calcula:

```text
mover(T, a) = unión de los destinos por a de cada estado de T
δAFD(T, a) = cierre-ε(mover(T, a))
```

Se crean solo los estados alcanzables, en orden de anchura. Cada uno se nombra concatenando sus estados en el orden de Q y el conjunto vacío es el estado ERROR. Un estado es terminal si contiene algún terminal del AFND. Se conserva el diccionario nombre → subconjunto original para la pestaña de correspondencia.

El invariante es que, después de leer cualquier prefijo, el estado del AFD contiene exactamente los posibles estados del AFND tras consumirlo y cerrar por ε. Por tanto ambos aceptan las mismas palabras. Si el AFND tiene n estados pueden aparecer hasta 2^n subconjuntos; una cota conservadora es O(k · 2^n · (n + e)), con k símbolos.

Si el autómata accesible ya es determinista, se indica y no se aplica la conversión. Si tiene casillas en error, se añade el estado ERROR, no terminal, se dirigen a él las casillas vacías y se añaden sus bucles. Completar no cambia el lenguaje: las ejecuciones antes indefinidas siguen rechazándose.

## 9. Minimización de Moore

Se parte de P0 formada por estados terminales y no terminales, omitiendo bloques vacíos. Para cada estado se registra a qué bloque va con cada símbolo (por ejemplo, B,0→BC (bloque 2)). Dentro de cada bloque se agrupan estados que van a los mismos bloques. Se repite hasta que la partición no cambia.

Cada separación revela una diferencia observable: inicialmente la aceptación de ε y después la aceptación de alguna continuación. En el punto fijo, los estados de un mismo bloque son equivalentes para cualquier continuación. Como el AFD era accesible y completo, su cociente es un AFD mínimo.

Cada clase conserva el nombre de su primer estado, de modo que el AFD mínimo se lee con los mismos nombres de la etapa anterior: si B y C son equivalentes, se fusionan en B y la correspondencia muestra B = {B, C}. El estado inicial del mínimo es la clase que contiene q0. Una cota del algoritmo es O(k · n²).

## 10. Ejemplos desarrollados

### 10.1 Expresión (a|b)*abb

El lenguaje contiene las palabras sobre Σ = {a, b} que terminan en abb: L = {abb, aabb, babb, aaabb, …}. La construcción de Thompson genera 14 estados, de A a N, con q0 = A y Qt = {N}; todos son accesibles y la entrada se clasifica AFND-ε.

La conversión parte de cierre-ε(A) = {A, B, C, E, G, I}, que se nombra ABCEGI, y alcanza 5 estados: ABCEGI, BCDEFGIJK, BCDEGHI, BCDEGHILM y BCDEGHIN. Por ejemplo, ABCEGI,a→BCDEFGIJK porque E,a→F e I,a→J, y el cierre-ε añade los estados del bucle. BCDEGHIN es terminal porque contiene N.

Moore separa primero BCDEGHIN, luego BCDEGHILM (con b llega al bloque terminal) y después BCDEFGIJK (con b llega a BCDEGHILM). ABCEGI y BCDEGHI quedan equivalentes y se fusionan en ABCEGI.

| Q | a | b | Interpretación |
| --- | --- | --- | --- |
| → ABCEGI | BCDEFGIJK | ABCEGI | No hay prefijo útil de abb |
| BCDEFGIJK | BCDEFGIJK | BCDEGHILM | Se leyó a |
| BCDEGHILM | BCDEFGIJK | BCDEGHIN | Se leyó ab |
| (BCDEGHIN) | BCDEFGIJK | ABCEGI | Se leyó abb: terminal |

La palabra aabb recorre ABCEGI,a→BCDEFGIJK,a→BCDEFGIJK,b→BCDEGHILM,b→BCDEGHIN y se acepta; abba termina en BCDEFGIJK y se rechaza.

### 10.2 AFND de clase: conversión AFND → AFD

Es el ejercicio de conversión del material del curso: Q = {A, B, C, D}, Σ = {0, 1}, q0 = A, Qt = {A}.

| Q | 0 | 1 |
| --- | --- | --- |
| → (A) | B | A |
| B | B,C | D |
| C | D | C |
| D | A | B |

Es AFND porque B,0→B,C: el símbolo 0 va a MÁS de un estado. La conversión reproduce la tabla del material:

| Q | 0 | 1 | Justificación de la primera columna |
| --- | --- | --- | --- |
| → (A) | B | A | A,0→B |
| B | BC | D | B,0→B,C |
| BC | BCD | CD | B,0→B,C · C,0→D |
| D | A | B | D,0→A |
| BCD | ABCD | BCD | B,0→B,C · C,0→D · D,0→A |
| CD | AD | BC | C,0→D · D,0→A |
| (ABCD) | ABCD | ABCD | A,0→B · B,0→B,C · C,0→D · D,0→A |
| (AD) | AB | AB | A,0→B · D,0→A |
| (AB) | BC | AD | A,0→B · B,0→B,C |

A, AD, ABCD y AB son terminales porque contienen A. Moore no fusiona ningún par: los 9 estados son distinguibles y el AFD ya es mínimo. L = {ε, 1, 11, 010, 111, 0000, …}.

### 10.3 AFD con un inaccesible y estados equivalentes

Q = {A, B, C, D}, Σ = {a, b}, q0 = A, Qt = {B, C}. A, B y C tienen a→B y b→C; D vuelve a sí mismo con ambos símbolos. Es AFD: cada símbolo va a un solo estado. Desde A nunca se llega a D, por lo que se elimina.

Al ser AFD completo se indica y se continúa con la minimización. P0 = {A} / {B, C}; B y C van con a y con b al mismo bloque, así que se fusionan en B. El AFD mínimo tiene A (a→B, b→B) y el terminal B (a→B, b→B): acepta toda palabra no vacía sobre {a, b} y rechaza ε.

### 10.4 AFD de clase con estados X, Y, Z, W

Es la tabla de transición del material del curso: Σ = {0, 1, 2}, q0 = X, Qt = {Z}; X: Y, Z, W; Y: Z, Y, X; Z: W, Y, W; W: X, W, Y. Ya es AFD y Moore separa los cuatro estados en la primera ronda, por lo que también es mínimo. L = {1, 00, 010, 021, 110, 201, 220, …}, que incluye las palabras 00 y 1 del ejemplo del curso.

## 11. Interfaz HTTP y representación gráfica

| Ruta | Contrato |
| --- | --- |
| GET / | Página HTML de la aplicación |
| GET /health | HTTP 200, objeto con status igual a ok |
| POST /api/process | Objeto con mode regex, alphabet y expression; o mode manual y automaton |
| POST /api/simulate | Objeto con automaton y word; devuelve word, accepted y path |

`automaton` contiene `states`, `alphabet`, `initial`, `finals` y `transitions`. Cada fila de `transitions` es un objeto símbolo → lista de destinos. Consulte los cinco archivos JSON de `examples/` para solicitudes completas. `process` devuelve `classification`, `summary`, `language` (primeras palabras de L) y cuatro `stages`: input, reachable, dfa y minimal. Cada etapa contiene automaton, steps y mapping; la mínima añade original_mapping y partitions.

Una entrada inválida devuelve HTTP 400 con `error`; una solicitud demasiado grande devuelve 413. No se utiliza eval ni se interpreta código enviado por el usuario, y las etiquetas se escapan antes de insertarse en HTML.

El diagrama de transición es un SVG producido por JavaScript con los mismos datos de la tabla y con la presentación de clase: estados en círculos dorados con el nombre en rojo, flechas naranjas, flecha de entrada en q0 y doble círculo en los terminales. Los estados se disponen circularmente, las aristas opuestas se curvan, los bucles tienen trazado propio y los símbolos que comparten origen y destino se agrupan (0,1). El tamaño de cada círculo se adapta al largo del nombre. La tabla usa encabezado Q naranja, filas en tonos durazno, → en el inicial, círculo en los terminales y error en las casillas sin destino.

## 12. Dependencias y operación

Flask sirve HTML, recursos y API; Gunicorn ejecuta el servidor en Linux/Render. HTML, CSS y SVG usan capacidades nativas del navegador, sin bibliotecas gráficas externas, CDN ni Graphviz. Pytest se utiliza solo para verificar. ReportLab genera los PDF; python-docx y openpyxl generan los documentos Word y Excel. Ninguna dependencia implementa las transformaciones de autómatas.

El despliegue usa `render.yaml`, Python 3.13.9, el comando de instalación de requirements.txt y Gunicorn enlazado a 0.0.0.0:$PORT. `/health` comprueba que el proceso responde. No hay migraciones, secretos, almacenamiento permanente ni servicios adicionales. Las instrucciones completas están en README.md.

## 13. Estrategia de validación

La matriz se genera a partir del XML real de pytest, sin inventar resultados. Un oráculo independiente explora configuraciones (estado, posición), incluidos ciclos ε. Para los ejemplos y 30 AFND generados con semilla 202602, se enumeran todas las palabras hasta longitud 6 y se comparan todas las etapas. El ejemplo abb se compara además con el predicado de sufijo hasta longitud 8, y el AFND de clase se compara transición por transición con la tabla AFD del material del curso.

La equivalencia entre AFD completo y mínimo se comprueba exactamente mediante el producto de autómatas: una pareja con aceptación distinta sería un contraejemplo. La minimalidad se verifica buscando una palabra que distinga cada par de estados diferentes.

Se verifican errores de entrada, límites, trazas, la notación de clase, reproducibilidad, API y solicitudes concurrentes. La prueba de Gunicorn solo corre en Linux; GitHub Actions instala desde cero y ejecuta toda la suite. La interfaz web se revisó visualmente en Chrome de escritorio, con capturas reales en docs/evidencias/capturas/; la revisión en ancho de teléfono de esta versión está pendiente (V02).

### 13.1 Trazabilidad con el enunciado

| Requisito | Implementación | Evidencia |
| --- | --- | --- |
| RF-01 | Validación de Σ y símbolos reservados | test_alphabet_validation |
| RF-02 | Analizador de expresiones y pertenencia a Σ | test_regex_validation, test_regex_precedence |
| RF-03 | Construcción propia de Thompson con estados A, B, C… | test_suffix_abb, test_class_notation |
| RF-04 | Registro de Q, q0, Qt y tabla de transición | test_manual_nfa, test_manual_validation |
| RF-05 | Clasificación AFD/AFND justificada con X,a→Y | test_class_notation, test_partial_sink |
| RF-06 | Conversión AFND → AFD con nombres concatenados | test_manual_nfa, test_generated_automata |
| RF-07 | Búsqueda y eliminación de inaccesibles | test_equivalent_unreachable |
| RF-09 | Refinamiento de Moore y cociente | test_equivalent_unreachable, test_already_minimal_and_roundtrip |
| RF-10 | Trazas de construcción, conversión y particiones | test_traces_mapping_stability, test_class_notation |
| RF-11 | Tabla y diagrama de transición del AFD mínimo | check_frontend.cjs; revisión visual en Chrome (V01) |
| RF-12 | Simulación con recorrido y aceptación | test_simulation_validation, test_process_and_simulate |
| RF-13 | Cuatro etapas consultables y comparación final | test_traces_mapping_stability; revisión visual en Chrome (V01) |

## 14. Fuentes

Enunciado proporcionado: MICROPROYECTO3-AF.pdf, «Microproyecto #3», tres páginas, lineamientos 2026/02.

Material del curso usado como referencia de notación: «Autómatas de Estados Finitos», «Conversión de AFND a AFD» y «Enunciados de ejercicios», Teoría General de la Computación.

Documentación de Flask: https://flask.palletsprojects.com/en/stable/

Documentación de Render: https://render.com/docs/deploy-flask ; https://render.com/docs/blueprint-spec ; https://render.com/docs/python-version
