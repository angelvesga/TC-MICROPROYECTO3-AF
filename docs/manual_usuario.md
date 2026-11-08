# Autómata Lab
## Manual breve de usuario

Microproyecto 3 · Teoría de la Computación · 2026/02

## 1. Abrir el programa

Si el proyecto ya está desplegado en Render, abre la URL asignada por el servicio. Para ejecutarlo localmente sigue el README: crea el entorno virtual, instala requirements.txt y ejecuta app.py; después abre http://127.0.0.1:5000. En el plan gratuito de Render la primera visita puede tardar mientras el servicio vuelve a iniciar.

La pantalla tiene una zona de entrada y otra de resultados. Arriba de la zona de entrada eliges una de las dos modalidades del enunciado:

| Modalidad | Información ingresada | Procesamiento |
| --- | --- | --- |
| A. A partir de un lenguaje | Alfabeto y reglas del lenguaje | Construcción de un autómata, conversión y minimización |
| B. A partir de un autómata | Estados, alfabeto, estado inicial, estados finales y transiciones | Identificación del tipo (AFD o AFND), conversión a determinista cuando corresponda y minimización |

El resultado se abre en la etapa AFD mínimo y puedes volver a cualquiera de las cuatro etapas: Construcción (A) o Identificación (B), Accesibles, AFND → AFD (o AFD) y Mínimo.

La notación es la de clase: AF = { {Q}, q0, Σ, {Qt}, δ }. Los estados se nombran A, B, C…; una transición se escribe A,0→B; en la tabla de transición la columna Q lleva una flecha → en el estado inicial y un círculo en cada estado final (Qt); una casilla sin destino dice error.

## 2. Modalidad A: a partir de un lenguaje

El lenguaje se escribe como en los enunciados de clase: primero el alfabeto Σ y luego las reglas de L, una por línea. Ejemplo del material del curso, Σ = {a, e, i, p}:

1. Selecciona la pestaña «A. A partir de un lenguaje», o carga el ejemplo 01.
2. En 1. Alfabeto escribe `a, e, i, p`.
3. En 2. Lenguaje escribe las reglas, una por línea:

```text
toda W inicia y finaliza en a
no repetidos vocales
```

4. Pulsa Construir, convertir y minimizar.
5. Comprueba los indicadores: 6 estados de entrada, 6 accesibles, 6 en el AFD y 6 en el AFD mínimo, y la muestra del lenguaje L = {a, aea, aia, apa, aeia, …}.
6. En la etapa Construcción lee cada regla con su significado y cada transición justificada; en Mínimo verás las particiones P0, P1…
7. Simula apa (aceptada) y aeeia (rechazada, porque repite la e).

Debajo del área de reglas hay botones que agregan una regla de cada tipo usando los símbolos del alfabeto; después solo ajusta los símbolos o números.

| Regla | Significado |
| --- | --- |
| inicia en S | El primer símbolo pertenece a S |
| finaliza en S | El último símbolo pertenece a S |
| inicia y finaliza en S | Ambas condiciones |
| no consecutivos S excepto xy | No hay dos símbolos seguidos de S, salvo los pares indicados |
| no repetidos S | Un símbolo de S no aparece dos veces seguidas |
| contiene w · no contiene w | La subcadena w aparece / no aparece |
| cantidad de x par · cantidad de x impar | Paridad del número de x (agrega «si existe» para permitir que no aparezca) |
| longitud maxima n · longitud minima n | Límites de la longitud de W |
| suma maxima n · suma menor a n | Suma de los dígitos de W |
| x seguido de S y precedido de T | Cada x va seguido de S y precedido de T (puedes usar solo una parte) |
| bloque maximo de x n | x se repite seguido como máximo n veces |

S es una lista de símbolos separados por comas, o las palabras vocal, consonante o cualquier símbolo. Mayúsculas y tildes son opcionales y puedes empezar con «- toda W». También se aceptan redacciones de clase como «la longitud máxima de W debe ser de 5» o «siempre que exista un 2 debe estar seguida de un 0 y precedida de un 1».

Los ejemplos 05 y 06 cargan los otros enunciados del curso: Σ = {0, 1, 2} («toda W inicia y finaliza en 0», «2 seguido de 0 y precedido de 1», «suma maxima 6», «longitud maxima 5»), que acepta 01120 y 01110; y Σ = {a, e, m, b, p} («finaliza en vocal», «no consecutivos consonantes excepto mb, mp», «longitud maxima 6»), que acepta ampa y mapa.

## 3. Modalidad B: a partir de un autómata (AFND de clase)

Ejercicio de conversión AFND → AFD del material del curso:

1. Selecciona la pestaña «B. A partir de un autómata», o carga el ejemplo 02.
2. Llena los campos en el orden del enunciado: 1. Estados Q `A, B, C, D`; 2. Alfabeto Σ `0, 1`; 3. Estado inicial q0 `A`; 4. Estados finales Qt `A`.
3. En 5. Transiciones pulsa Generar / actualizar tabla de transiciones.
4. Llena la tabla de transición. Si el símbolo va a MÁS de un estado, escribe los destinos separados por coma. Deja vacía la casilla o escribe error si no hay transición.

| Q | 0 | 1 |
| --- | --- | --- |
| A | B | A |
| B | B,C | D |
| C | D | C |
| D | A | B |

5. Pulsa Identificar, convertir y minimizar. La clasificación es AFND porque B,0→B,C.
6. En la etapa AFND → AFD aparecen los estados A, B, BC, D, BCD, CD, ABCD, AD y AB, iguales a la tabla del material. Cada línea se justifica como en clase, por ejemplo BC,0→BCD ⟸ B,0→B,C · C,0→D.
7. Son finales A, AD, ABCD y AB porque contienen A. El AFD ya es mínimo: tiene 9 estados.
8. Simula 010 (aceptada) y 0 (rechazada).

Como indica el enunciado, en la modalidad B se admiten AFD y AFND. El campo de estados finales puede quedar vacío. Si modificas Q o Σ, pulsa Generar / actualizar tabla de transiciones y revisa los destinos antes de procesar.

## 4. Minimizar un AFD existente

Carga el ejemplo 03, «AFD con estados equivalentes», y pulsa Identificar, convertir y minimizar. La entrada usa Q = {A, B, C, D}, q0 = A y Qt = {B, C}. Es AFD porque cada símbolo va a un solo estado; el programa lo indica y continúa con la minimización. Los indicadores deben ser 4 → 3 → 3 → 2.

En la etapa Accesibles comprueba que D desaparece: desde A nunca se llega a él. En Mínimo, la línea «B, C son equivalentes: se fusionan en B» y la pestaña Correspondencia de estados (B = {B, C}) explican la fusión.

El ejemplo 04, «AFD de clase con estados X, Y, Z, W», carga la tabla de transición del material del curso (Σ = {0, 1, 2}, q0 = X, Qt = {Z}). Ya es AFD y ya es mínimo; acepta, por ejemplo, 00 y 1.

Si tu AFD tiene casillas en error, el programa lo informa como AFD incompleto y añade el estado ERROR, no final, antes de minimizar.

## 5. Leer los resultados

- La definición formal AF = { {Q}, q0, Σ, {Qt}, δ } aparece encima del diagrama con los valores de la etapa.
- En el diagrama, la flecha de entrada marca q0 y el doble círculo marca los estados finales.
- En la tabla, → marca el inicial, el círculo marca los finales y error indica que no hay destino.
- Los botones + y − amplían o reducen el diagrama; el área se desplaza cuando es grande.
- Correspondencia de estados indica qué representa cada estado: en la modalidad A, el estado de cada regla (R1, R2…); en la conversión, los estados que forman cada estado nuevo (BC = {B, C}).
- Explicación paso a paso registra las operaciones realizadas con la notación X,a→Y.
- L = {…} muestra las primeras palabras aceptadas por el AFD mínimo.
- Comparar esta etapa con el AFD mínimo muestra los tamaños y la tabla final.
- Descargar resultado guarda todas las etapas en JSON; SVG guarda el diagrama visible.

En diagramas densos utiliza la tabla para revisar todas las transiciones.

## 6. Simular palabras

Selecciona primero la etapa que deseas probar. Escribe la palabra W en Comprueba una palabra W y pulsa Simular. El recorrido se muestra como en clase: estado, símbolo y destino, por ejemplo A,0→B,1→D,1→F,2→I,0→J para 01120 en el ejemplo 05. En un AFND cada paso puede ser un conjunto de estados, mostrado entre llaves.

Se acepta si después de leer toda la palabra queda al menos un estado final. Un símbolo ajeno a Σ produce un error con su posición. Para probar la palabra vacía deja la casilla sin contenido. Al cambiar de etapa se limpia la simulación anterior.

## 7. Mensajes frecuentes

| Situación | Cómo corregirla |
| --- | --- |
| Símbolos duplicados | Usa a,b en vez de a,a,b |
| Regla n: no se reconoce | Escribe la regla con una de las formas de la tabla de la sección 2 |
| Regla n: un símbolo no pertenece al alfabeto | Añádelo a Σ o corrige la regla |
| La suma solo se admite con dígitos | Usa la regla de suma solo si Σ tiene únicamente dígitos |
| Las reglas generan más de 256 estados | Reduce las longitudes o sumas máximas |
| Estado inexistente | Regístralo en Q o corrige el destino, q0 o Qt |
| Cambiaste Q o Σ | Pulsa Generar / actualizar tabla de transiciones y revisa destinos |
| Sin conexión | Verifica que app.py siga ejecutándose o espera al arranque de Render |

Límites: alfabeto de 1 a 12 símbolos de un carácter; 12 reglas; 256 estados al combinar las reglas; 1 a 80 estados manuales; hasta 4000 aristas; 128 estados en la conversión AFND → AFD; 1000 caracteres por palabra. No hay guardado automático: descarga el resultado antes de cerrar o recargar la página.

## 8. Material de entrega y verificación

El repositorio incluye este manual, el documento técnico, la matriz de pruebas, seis entradas JSON (cinco de ellas tomadas del material del curso), sus resultados y la suite automatizada. La interfaz se revisó en Chrome de escritorio y en un teléfono emulado de 390 px; las capturas reales están en docs/evidencias/capturas/.
