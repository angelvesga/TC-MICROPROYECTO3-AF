# Autómata Lab
## Manual breve de usuario

Microproyecto 3 · Teoría de la Computación · 2026/02

## 1. Abrir el programa

Si el proyecto ya está desplegado en Render, abre la URL asignada por el servicio. Para ejecutarlo localmente sigue el README: crea el entorno virtual, instala requirements.txt y ejecuta app.py; después abre http://127.0.0.1:5000. En el plan gratuito de Render la primera visita puede tardar mientras el servicio vuelve a iniciar.

La pantalla tiene una zona de entrada y otra de resultados. Primero define el lenguaje o el autómata; después pulsa Construir y minimizar. El resultado se abre en la etapa AFD mínimo y puedes volver a cualquiera de las cuatro etapas: Entrada, Accesibles, AFND → AFD (o AFD) y Mínimo.

La notación es la de clase: AF = { {Q}, q0, Σ, {Qt}, δ }. Los estados se nombran A, B, C…; una transición se escribe A,0→B; en la tabla de transición la columna Q lleva una flecha → en el estado inicial y un círculo en cada estado terminal; una casilla sin destino dice error.

## 2. Modalidad A: expresión regular

1. Selecciona Expresión regular.
2. En Alfabeto escribe `a, b` (Σ = {a, b}).
3. En Expresión regular escribe `(a|b)*abb`.
4. Pulsa Construir y minimizar.
5. Comprueba los indicadores: 14 estados de entrada (A a N), 14 accesibles, 5 en el AFD y 4 en el AFD mínimo, y la muestra del lenguaje L = {abb, aabb, babb, …}.
6. Abre cada etapa para leer las operaciones. En AFND → AFD verás líneas como ABCEGI,a→BCDEFGIJK con su justificación; en Mínimo verás las particiones P0, P1…

También puedes cargar el ejemplo «Expresión (a|b)*abb» o el ejemplo 05, «Σ = {a,e,i,p}: inicia y finaliza en a», que corresponde a la expresión a|a(a|e|i|p)*a y acepta L = {a, aa, aea, aia, apa, …}.

| Escritura | Significado | Ejemplo |
| --- | --- | --- |
| a | Símbolo del alfabeto | a acepta solo a |
| ab | Concatenación | a seguida de b |
| a\|b | Unión | a o b |
| a* | Cero o más repeticiones | ε, a, aa, ... |
| (a\|b)* | Agrupación y repetición | Todas las palabras sobre a,b |
| ε | Palabra vacía | ε acepta solo la palabra vacía |
| ∅ | Lenguaje vacío | No acepta ninguna palabra |

La estrella tiene mayor prioridad que la concatenación y esta que la unión. No escribas espacios dentro de la expresión. El alfabeto debe contener todos los símbolos de la expresión y no puede incluir los operadores ni ε o ∅. Para la palabra vacía escribe ε.

## 3. Modalidad B: autómata manual (AFND de clase)

Ejercicio de conversión AFND → AFD del material del curso:

1. Selecciona Autómata manual, o carga el ejemplo «AFND de clase: conversión AFND → AFD».
2. Escribe Σ `0, 1`, estados Q `A, B, C, D`, estado inicial q0 `A` y estados terminales Qt `A`.
3. Pulsa Actualizar tabla de entrada.
4. Llena la tabla de transición. Si el símbolo va a MÁS de un estado, escribe los destinos separados por coma. Deja vacía la casilla o escribe error si no hay transición.

| Q | 0 | 1 | ε |
| --- | --- | --- | --- |
| A | B | A | error |
| B | B,C | D | error |
| C | D | C | error |
| D | A | B | error |

5. Pulsa Construir y minimizar. La clasificación es AFND porque B,0→B,C.
6. En la etapa AFND → AFD aparecen los estados A, B, BC, D, BCD, CD, ABCD, AD y AB, iguales a la tabla del material. Cada línea se justifica como en clase, por ejemplo BC,0→BCD ⟸ B,0→B,C · C,0→D.
7. Son terminales A, AD, ABCD y AB porque contienen A. El AFD ya es mínimo: tiene 9 estados.
8. Simula 010 (aceptada) y 0 (rechazada).

La columna ε permite transiciones que no consumen símbolo. El campo de terminales puede quedar vacío. Si modificas Q o Σ, pulsa Actualizar tabla de entrada y revisa los destinos antes de procesar.

## 4. Minimizar un AFD existente

Carga «AFD con estados equivalentes» y pulsa Construir y minimizar. La entrada usa Q = {A, B, C, D}, q0 = A y Qt = {B, C}. Es AFD porque cada símbolo va a un solo estado; el programa lo indica y continúa con la minimización. Los indicadores deben ser 4 → 3 → 3 → 2.

En la etapa Accesibles comprueba que D desaparece: desde A nunca se llega a él. En Mínimo, la línea «B, C son equivalentes: se fusionan en B» y la pestaña Correspondencia de estados (B = {B, C}) explican la fusión. La palabra vacía se rechaza y toda palabra no vacía sobre a,b se acepta.

El ejemplo 04, «AFD de clase con estados X, Y, Z, W», carga la tabla de transición del material del curso (Σ = {0, 1, 2}, q0 = X, Qt = {Z}). Ya es AFD y ya es mínimo; acepta, por ejemplo, 00 y 1.

Si tu AFD tiene casillas en error, el programa lo informa como AFD incompleto y añade el estado ERROR, no terminal, antes de minimizar.

## 5. Leer los resultados

- La definición formal AF = { {Q}, q0, Σ, {Qt}, δ } aparece encima del diagrama con los valores de la etapa.
- En el diagrama, la flecha de entrada marca q0 y el doble círculo marca los estados terminales.
- En la tabla, → marca el inicial, el círculo marca los terminales y error indica que no hay destino.
- Los botones + y − amplían o reducen el diagrama; el área se desplaza cuando es grande.
- Correspondencia de estados indica qué estados forman cada estado nuevo (BC = {B, C}).
- Explicación paso a paso registra las operaciones realizadas con la notación X,a→Y.
- L = {…} muestra las primeras palabras aceptadas por el AFD mínimo.
- Comparar esta etapa con el AFD mínimo muestra los tamaños y la tabla final.
- Descargar resultado guarda todas las etapas en JSON; SVG guarda el diagrama visible.

En diagramas densos utiliza la tabla para revisar todas las transiciones. La etiqueta ε significa transición vacía, no un símbolo que deba escribirse en una palabra.

## 6. Simular palabras

Selecciona primero la etapa que deseas probar. Escribe la palabra W en Comprueba una palabra W y pulsa Simular. El recorrido se muestra como en clase: estado, símbolo y destino, por ejemplo A,0→B,1→D,0→A. En un AFND cada paso puede ser un conjunto de estados, mostrado entre llaves.

Para `(a|b)*abb`, aabb recorre ABCEGI,a→BCDEFGIJK,a→BCDEFGIJK,b→BCDEGHILM,b→BCDEGHIN y se acepta; abba se rechaza. Para probar la palabra vacía deja la casilla sin contenido.

Se acepta si después de leer toda la palabra queda al menos un estado terminal. Un símbolo ajeno a Σ produce un error con su posición. Al cambiar de etapa se limpia la simulación anterior.

## 7. Mensajes frecuentes

| Situación | Cómo corregirla |
| --- | --- |
| Símbolos duplicados | Usa a,b en vez de a,a,b |
| Símbolo fuera del alfabeto | Añádelo a Σ o corrige la expresión o palabra |
| Falta un operando | Reemplaza a\| por a\|ε si querías incluir la palabra vacía |
| Falta un paréntesis | Cierra todos los paréntesis abiertos |
| Estado inexistente | Regístralo en Q o corrige el destino, q0 o Qt |
| Cambiaste Q o Σ | Pulsa Actualizar tabla de entrada y revisa destinos |
| Se supera el límite | Reduce el ejemplo; nunca se entrega una conversión incompleta |
| Sin conexión | Verifica que app.py siga ejecutándose o espera al arranque de Render |

Límites: alfabeto de 1 a 12 símbolos de un carácter; expresión de hasta 120 caracteres; 1 a 80 estados manuales; hasta 4000 aristas; 128 estados en la conversión AFND → AFD; 1000 caracteres por palabra. No hay guardado automático: descarga el resultado antes de cerrar o recargar la página.

## 8. Material de entrega y verificación

El repositorio incluye este manual, el documento técnico, la matriz de pruebas, cinco entradas JSON (dos de ellas tomadas del material del curso), sus resultados y la suite automatizada. La interfaz se revisó en Chrome de escritorio; las capturas reales están en docs/evidencias/capturas/.
