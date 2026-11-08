# Autómata Lab
## Documento técnico y funcional

Microproyecto 3 · Teoría de la Computación · 2026/02

## 1. Propósito y alcance

El software permite estudiar cómo distintas representaciones describen el mismo lenguaje regular. A partir de un lenguaje descrito con reglas o de un autómata registrado manualmente, obtiene un AFD mínimo y permite revisar las operaciones realizadas, su tabla de transición, su diagrama de transición y sus simulaciones.

El público son estudiantes y docentes de Teoría de la Computación. Las dos modalidades del enunciado comparten el mismo motor Python: A, a partir de un lenguaje (alfabeto y reglas del lenguaje, escritas como en los enunciados de clase), y B, a partir de un autómata (estados, alfabeto, estado inicial, estados finales y transiciones). En la modalidad B la interfaz admite AFD completos, AFD con casillas en error y AFND; la API acepta además transiciones ε. La aplicación se ejecuta localmente o como servicio web en Render; no requiere cuentas de usuario ni base de datos.

Se excluyen lenguajes que no son regulares (por ejemplo, comparar sin límite la cantidad de dos símbolos), autómatas de pila, máquinas de Turing, almacenamiento de sesiones y edición gráfica por arrastre. El diagrama acompaña las transformaciones; la tabla de transición es la referencia exacta para revisar cada transición.

El documento de referencia tiene una errata en RF-06: se implementa AFND → AFD, conforme a los objetivos. RF-01 queda incompleto después de «reservando»; esta implementación reserva ε, ∅, # y los operadores. No existe RF-08 en la lista original. Python fue el lenguaje solicitado para esta entrega.

## 2. Notación de clase

La presentación de resultados sigue la notación y la forma de desarrollar ejercicios del material del curso («Autómatas de Estados Finitos» y «Conversión de AFND a AFD»), para que la lectura resulte familiar:

| Elemento | Notación en el software |
| --- | --- |
| Definición formal | AF = { {Q}, q0, Σ, {Qt}, δ }, mostrada en cada etapa |
| Lenguaje | Σ = {…} y L = { reglas }, una regla por línea; W designa una palabra |
| Estados | Letras mayúsculas A, B, C…; con más de 26 estados, q0, q1, q2… |
| Transición | A,0→B; si el símbolo va a MÁS de un estado, A,1→A,C |
| Tabla de transición | Columna Q, una columna por símbolo, → en el estado inicial y círculo en los finales |
| Casilla sin destino | error |
| Estado del AFD | Concatenación de los estados del subconjunto: AC, ABC, BCD |
| Estado sin salida | ERROR, no final, que vuelve a sí mismo con todo símbolo |
| Clasificación | AFD (cada símbolo va a un solo estado) o AFND (algún símbolo va a MÁS de un estado) |
| Palabras aceptadas | L = {…} con las primeras palabras W aceptadas |

En la conversión, cada transición del AFD se justifica como en clase: AC,0→B ⟸ A,0→B · C,0→error. El estado inicial del AFD es el mismo q0 del AFND y son finales los estados que contienen algún estado final del AFND.

## 3. Modalidades y casos de uso

| Modalidad | Información ingresada | Procesamiento esperado |
| --- | --- | --- |
| A. A partir de un lenguaje | Alfabeto y reglas del lenguaje | Construcción de un autómata, conversión y minimización |
| B. A partir de un autómata | Estados, alfabeto, estado inicial, estados finales y transiciones | Identificación del tipo, conversión a determinista cuando corresponda y minimización |

| Caso | Entrada y acción | Resultado observable |
| --- | --- | --- |
| CU-01 Modalidad A | Registrar Σ y las reglas de L; pulsar Construir, convertir y minimizar | Significado de cada regla, autómata del lenguaje, accesibles, AFD y AFD mínimo |
| CU-02 Modalidad B | Registrar Q, Σ, q0, Qt y la tabla de transición; pulsar Identificar, convertir y minimizar | Clasificación AFD/AFND justificada, conversión cuando corresponde y AFD mínimo |
| CU-03 Explorar | Seleccionar una de las cuatro etapas | Definición formal, tabla, diagrama, correspondencias y operaciones |
| CU-04 Simular | Elegir etapa y escribir una palabra W | Recorrido A,a→B… y aceptación o rechazo |
| CU-05 Comparar | Abrir la comparación con el AFD mínimo | Número de estados y tabla final, sin perder la etapa seleccionada |
| CU-06 Exportar | Descargar resultado o SVG | JSON de todas las etapas o diagrama de la etapa actual |

Si la entrada es inválida se informa qué debe corregirse, con el número de regla cuando corresponde, y no se entrega un resultado parcial. Si el autómata ya es determinista se indica expresamente y se continúa con su minimización. Al editar la entrada se descartan los resultados anteriores.

## 4. Sintaxis del lenguaje y restricciones

El alfabeto Σ es una lista no vacía de hasta 12 caracteres visibles. Cada símbolo ocupa un carácter; no se permiten duplicados, espacios, coma, #, barra inversa, paréntesis, |, *, ε ni ∅. En la interfaz se escribe, por ejemplo, `0, 1, 2`; en la API, `["0", "1", "2"]`.

El lenguaje se escribe con una regla por línea. Mayúsculas y tildes son opcionales, se admite el prefijo «- toda W», «toda palabra» o «la palabra», y # inicia un comentario. En las reglas, S y T son listas de símbolos separados por comas, o las palabras vocal, consonante o cualquier símbolo; x es un símbolo, w una subcadena y n un número natural.

| Regla | Significado |
| --- | --- |
| inicia en S | El primer símbolo de W pertenece a S |
| finaliza en S | El último símbolo de W pertenece a S |
| inicia y finaliza en S · inicia en S y finaliza en T | Ambas condiciones |
| no consecutivos S [excepto xy, zw] | No hay dos símbolos seguidos de S, salvo los pares indicados |
| no repetidos S | Un símbolo de S no aparece dos veces seguidas |
| contiene w · no contiene w | La subcadena w aparece / no aparece |
| cantidad de x par · cantidad de x impar [si existe] | Paridad del número de x; «si existe» admite que x no aparezca |
| longitud maxima n · longitud minima n | Límites de la longitud de W |
| suma maxima n · suma menor a n | Suma de los dígitos de W (Σ numérico) |
| x seguido de S [y precedido de T] | Cada x va seguido de un símbolo de S (y precedido de uno de T) |
| x precedido de T | Cada x va precedido de un símbolo de T |
| bloque maximo de x n | x se repite seguido como máximo n veces |

También se aceptan las redacciones de los enunciados de clase, por ejemplo: «toda W inicia con cualquier símbolo y finaliza en vocal», «la longitud máxima de W debe ser de 5», «la suma de W debe ser máximo de 6» y «siempre que exista un 2 debe estar seguida de un 0 y precedida de un 1». Una línea que no corresponde a ninguna forma produce el error «Regla n: no se reconoce…» con la lista de formas válidas.

Los autómatas manuales admiten de 1 a 80 estados y hasta 4000 aristas. Los nombres comienzan con letra ASCII o _, seguidos de letras ASCII, números, _ o -, hasta 32 caracteres. Hay exactamente un estado inicial y cualquier cantidad de finales. En cada casilla se escriben los destinos separados por comas (C,F); una casilla vacía o con error representa ausencia de transición.

Límites: 12 reglas por lenguaje, 256 estados al combinar las reglas, 128 estados en la conversión AFND → AFD y 1000 caracteres por palabra. Son límites educativos que protegen frente al crecimiento exponencial; nunca se entrega un resultado truncado.

## 5. Arquitectura y estructuras de datos

La aplicación tiene tres capas: motor matemático independiente en Python, adaptador HTTP Flask e interfaz HTML/CSS/JavaScript. El motor puede probarse sin navegador ni servidor. JavaScript gestiona formularios, tablas y diagramas SVG, pero las transformaciones y simulaciones se calculan en Python.

`Automaton` es una dataclass con `states` (Q) y `alphabet` (Σ) como tuplas ordenadas, `initial` (q0) como cadena, `finals` (Qt) como frozenset y `transitions` (δ) como diccionario de origen a símbolo a frozenset de destinos. Incluso en un AFD cada destino es un conjunto de un elemento.

Cada regla del lenguaje se representa con una estructura `Rule` que contiene su estado inicial, su función de transición, su condición de aceptación y una descripción legible de cada estado. Los estados de una regla son valores simples (un número para la suma o la longitud, el último símbolo leído, la paridad), de modo que su significado se puede explicar. El producto usa tuplas con un estado por regla como claves de diccionario y una cola `deque` para el recorrido en anchura.

En la conversión, un subconjunto se almacena como `frozenset` y se usa como clave del diccionario que le asigna su nombre concatenado (AC, ABC). Los bloques de Moore son tuplas de estados. Cada función devuelve un autómata nuevo; no hay estado mutable compartido entre solicitudes.

## 6. Construcción del autómata desde el lenguaje

Cada regla se traduce a un AFD pequeño sobre Σ. Por ejemplo, «inicia en 0» tiene los estados «aún no lee símbolos» e «inició con 0»; «suma maxima 6» guarda la suma acumulada de 0 a 6; «2 seguido de 0» recuerda si el último símbolo fue un 2 que espera un 0; «no contiene w» guarda el mayor prefijo de w leído. Cuando una regla queda violada, la palabra ya no puede pertenecer a L.

El autómata del lenguaje es el producto de los AFD de las reglas. Su estado inicial combina los estados iniciales de todas las reglas. Para cada estado alcanzado y cada símbolo se avanza cada regla con ese símbolo: si alguna queda violada, el destino es ERROR; si no, el destino es la combinación resultante. Un estado es final cuando todas las reglas aceptan. Solo se crean los estados alcanzables, en orden de anchura, y se nombran A, B, C…

La explicación registra cada regla con su significado y cada transición con su justificación, por ejemplo «A,0→B (inició con 0; suma 0; longitud 1)». La pestaña Correspondencia de estados muestra el estado de cada regla (R1, R2…) dentro de cada estado del producto.

La corrección se justifica porque una palabra lleva el producto al estado formado por los estados que alcanza en cada regla; es final si y solo si cada regla acepta la palabra, es decir, si cumple todas las condiciones de L. El resultado es un AFD completo, por lo que el software lo indica y continúa con la minimización.

## 7. Clasificación y accesibilidad

Si existe alguna transición ε, la entrada es AFND-ε. Sin ε, si algún símbolo va a MÁS de un estado (X,a→Y,Z), es AFND. Si cada símbolo va a un solo estado (X,a→Y) en todas las casillas, es AFD. Si ninguna casilla tiene más de un destino pero algunas están en error, se informa AFD incompleto.

Una búsqueda desde q0 recorre todas las aristas. Los estados no visitados se eliminan junto con sus transiciones. El lenguaje no cambia porque ninguna ejecución iniciada en q0 puede llegar a ellos. El coste es O(n + e), con n estados y e aristas.

## 8. Conversión AFND → AFD

El estado inicial del AFD es el q0 del AFND (o su cierre-ε si tiene transiciones vacías). Para cada estado T del AFD y símbolo a se calcula:

```text
mover(T, a) = unión de los destinos por a de cada estado de T
δAFD(T, a) = cierre-ε(mover(T, a))
```

Se crean solo los estados alcanzables, en orden de anchura. Cada uno se nombra concatenando sus estados en el orden de Q y el conjunto vacío es el estado ERROR. Un estado es final si contiene algún estado final del AFND. Después de leer cualquier prefijo, el estado del AFD contiene exactamente los posibles estados del AFND, por lo que ambos aceptan las mismas palabras. Pueden aparecer hasta 2^n subconjuntos.

Si el autómata accesible ya es determinista, se indica y no se aplica la conversión. Si tiene casillas en error, se añade el estado ERROR, no final, y se dirigen a él las casillas vacías; las ejecuciones antes indefinidas siguen rechazándose.

## 9. Minimización de Moore

Se parte de P0 formada por estados finales y no finales. Para cada estado se registra a qué bloque va con cada símbolo (por ejemplo, B,0→BC (bloque 2)). Dentro de cada bloque se agrupan los estados que van a los mismos bloques. Se repite hasta que la partición no cambia; en el punto fijo, los estados de un mismo bloque son equivalentes y el cociente es un AFD mínimo.

En la modalidad B cada clase conserva el nombre de su primer estado (si B y C son equivalentes, se fusionan en B). En la modalidad A, donde el producto puede tener muchos estados, las clases se nombran A, B, C… en orden de recorrido desde q0 y ERROR queda al final de Q; la correspondencia muestra qué estados agrupa cada letra. Una cota del algoritmo es O(k · n²).

## 10. Ejemplos desarrollados

### 10.1 Lenguaje Σ = {a, e, i, p}

Es el ejemplo del material del curso: toda palabra inicia y finaliza en a, y si hay vocales consecutivas no pueden repetirse. Se escribe así:

```text
toda W inicia y finaliza en a
no repetidos vocales
```

El producto tiene 6 estados y ya es mínimo. B es el único final; C, D y E recuerdan la última vocal o la p leída, y ERROR recibe toda palabra que viola una regla. L = {a, aea, aia, apa, aeia, aepa, …}; aeeia y aa se rechazan porque repiten una vocal.

| Q | a | e | i | p |
| --- | --- | --- | --- | --- |
| → A | B | ERROR | ERROR | ERROR |
| (B) | ERROR | C | D | E |
| C | B | ERROR | D | E |
| D | B | C | ERROR | E |
| E | B | C | D | E |
| ERROR | ERROR | ERROR | ERROR | ERROR |

### 10.2 Lenguaje Σ = {0, 1, 2}

Es el enunciado de ejercicios del curso: toda W inicia y finaliza en 0; siempre que exista un 2 debe estar seguido de un 0 y precedido de un 1; la suma de W es como máximo 6; la longitud máxima es 5.

```text
toda W inicia y finaliza en 0
2 seguido de 0 y precedido de 1
suma maxima 6
longitud maxima 5
```

El producto de las cuatro reglas alcanza 31 estados (q0 a q29 y ERROR). Moore los reduce a 11: A a J y ERROR, con Qt = {B, C, E, H, J}. Las palabras 01120 y 01110 del ejemplo de clase se aceptan; 01120 recorre A,0→B,1→D,1→F,2→I,0→J. La palabra 0210 se rechaza porque el 2 no está precedido de 1.

### 10.3 AFND de clase: conversión AFND → AFD

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

A, AD, ABCD y AB son finales porque contienen A. Moore no fusiona ningún par: el AFD ya es mínimo con 9 estados.

### 10.4 AFD con un inaccesible y estados equivalentes

Q = {A, B, C, D}, Σ = {a, b}, q0 = A, Qt = {B, C}. A, B y C tienen a→B y b→C; D vuelve a sí mismo con ambos símbolos. Es AFD y desde A nunca se llega a D, por lo que se elimina. P0 = {A} / {B, C}; B y C van al mismo bloque con cada símbolo y se fusionan en B. El AFD mínimo acepta toda palabra no vacía sobre {a, b}.

### 10.5 AFD de clase con estados X, Y, Z, W

Es la tabla de transición del material del curso: Σ = {0, 1, 2}, q0 = X, Qt = {Z}; X: Y, Z, W; Y: Z, Y, X; Z: W, Y, W; W: X, W, Y. Ya es AFD y Moore separa los cuatro estados en la primera ronda, por lo que también es mínimo. L = {1, 00, 010, 021, …} incluye las palabras 00 y 1 del ejemplo del curso.

## 11. Interfaz HTTP y representación gráfica

| Ruta | Contrato |
| --- | --- |
| GET / | Página HTML de la aplicación |
| GET /health | HTTP 200, objeto con status igual a ok |
| POST /api/process | Objeto con mode language, alphabet y rules; o mode manual y automaton |
| POST /api/simulate | Objeto con automaton y word; devuelve word, accepted y path |

`rules` es un texto con una regla por línea. `automaton` contiene `states`, `alphabet`, `initial`, `finals` y `transitions`. Consulte los seis archivos JSON de `examples/`. `process` devuelve `classification`, `summary`, `language` (primeras palabras de L) y cuatro `stages`: input, reachable, dfa y minimal. Una entrada inválida devuelve HTTP 400 con `error`; una solicitud demasiado grande devuelve 413.

El diagrama de transición es un SVG producido por JavaScript con la presentación de clase: estados en círculos dorados con el nombre en rojo, flechas naranjas, flecha de entrada en q0 y doble círculo en los finales. La tabla usa encabezado Q naranja, filas en tonos durazno, → en el inicial, círculo en los finales y error en las casillas sin destino.

## 12. Dependencias y operación

Flask sirve HTML, recursos y API; Gunicorn ejecuta el servidor en Linux/Render. HTML, CSS y SVG usan capacidades nativas del navegador, sin bibliotecas gráficas externas ni Graphviz. Pytest se utiliza solo para verificar; python-docx y openpyxl generan los documentos Word y Excel. Ninguna dependencia implementa las transformaciones de autómatas.

El despliegue usa `render.yaml`, Python 3.13.9, el comando de instalación de requirements.txt y Gunicorn enlazado a 0.0.0.0:$PORT. `/health` comprueba que el proceso responde. Las instrucciones completas están en README.md.

## 13. Estrategia de validación

La matriz se genera a partir del XML real de pytest, sin inventar resultados. Cada lenguaje de la modalidad A se compara palabra por palabra con un predicado escrito en Python a partir del enunciado, para todas las palabras hasta longitud 6 y en las cuatro etapas. Así se comprueban los tres lenguajes de clase y cada forma documentada de regla.

En la modalidad B, el AFND de clase se compara transición por transición con la tabla AFD del material del curso, y 30 AFND generados con semilla 202602 se comparan con un oráculo independiente que explora configuraciones (estado, posición). La equivalencia entre AFD y mínimo se comprueba por el producto de autómatas y la minimalidad buscando una palabra que distinga cada par de estados.

Se verifican también errores de entrada con el número de regla, límites, trazas, la notación de clase, la API y solicitudes concurrentes. La prueba de Gunicorn solo corre en Linux; GitHub Actions instala desde cero y ejecuta toda la suite. La interfaz se revisó en Chrome de escritorio (V01) y en un teléfono emulado de 390 px (V02), con capturas reales en docs/evidencias/capturas/.

### 13.1 Trazabilidad con el enunciado

| Requisito | Implementación | Evidencia |
| --- | --- | --- |
| RF-01 | Validación de Σ y símbolos reservados | test_alphabet_validation |
| RF-02 | Reglas del lenguaje validadas contra Σ | test_rule_validation, test_rule_kinds |
| RF-03 | Construcción del autómata por producto de reglas | test_language_vowels, test_language_digits, test_language_consonants |
| RF-04 | Registro de Q, Σ, q0, Qt y tabla de transición | test_manual_nfa, test_manual_validation |
| RF-05 | Clasificación AFD/AFND justificada con X,a→Y | test_class_notation, test_partial_sink |
| RF-06 | Conversión AFND → AFD con nombres concatenados | test_manual_nfa, test_generated_automata |
| RF-07 | Búsqueda y eliminación de inaccesibles | test_equivalent_unreachable |
| RF-09 | Refinamiento de Moore y cociente | test_equivalent_unreachable, test_already_minimal_and_roundtrip |
| RF-10 | Trazas de construcción, conversión y particiones | test_traces_mapping_stability, test_class_notation |
| RF-11 | Tabla y diagrama de transición del AFD mínimo | revisión visual en Chrome (V01) |
| RF-12 | Simulación con recorrido y aceptación | test_simulation_validation, test_process_and_simulate |
| RF-13 | Cuatro etapas consultables y comparación final | test_traces_mapping_stability; revisión visual en Chrome (V01) |

## 14. Fuentes

Enunciado del Microproyecto 3, lineamientos 2026/02. Material del curso: «Autómatas de Estados Finitos», «Conversión de AFND a AFD» y «Enunciados de ejercicios». Documentación de Flask y de Render.
