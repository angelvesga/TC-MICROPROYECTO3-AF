# Autómata Lab
## Manual breve de usuario

Microproyecto 3 · Teoría de la Computación · 2026/02

## 1. Abrir el programa

Si tu compañero ya desplegó el proyecto en Render, abre la URL que le asignó el servicio. Para ejecutarlo localmente sigue el README: crea el entorno virtual, instala requirements.txt y ejecuta app.py; después abre http://127.0.0.1:5000. En el plan gratuito de Render la primera visita puede tardar mientras el servicio vuelve a iniciar.

La pantalla tiene una zona de entrada y otra de resultados. Primero define el lenguaje o autómata; después pulsa Construir y minimizar. El resultado se abre en la etapa AFD mínimo. Puedes volver a cualquiera de las cuatro etapas con los botones Entrada, Accesibles, AFD y Mínimo.

## 2. Modalidad A: expresión regular

1. Selecciona Expresión regular.
2. En Alfabeto escribe `a, b`.
3. En Expresión regular escribe `(a|b)*abb`.
4. Pulsa Construir y minimizar.
5. Comprueba los indicadores: 14 estados originales, 14 accesibles, 5 del AFD y 4 del mínimo.
6. Abre cada etapa para leer las operaciones. En AFD revisa los movimientos y cierres; en Mínimo revisa firmas y particiones.

También puedes cargar el ejemplo «Palabras que terminan en abb» y pulsar el botón de procesamiento.

| Escritura | Significado | Ejemplo |
| --- | --- | --- |
| a | Símbolo del alfabeto | a acepta solo a |
| ab | Concatenación | a seguida de b |
| a\|b | Unión | a o b |
| a* | Cero o más repeticiones | ε, a, aa, ... |
| (a\|b)* | Agrupación y repetición | Todas las cadenas sobre a,b |
| ε | Cadena vacía | ε acepta solo la cadena vacía |
| ∅ | Lenguaje vacío | No acepta ninguna cadena |

La estrella tiene mayor prioridad que la concatenación y esta que la unión. No escribas espacios dentro de la expresión. El alfabeto debe contener todos sus símbolos literales y no debe incluir los operadores ni ε o ∅. La casilla Expresión no puede quedar vacía: para la cadena vacía escribe ε.

## 3. Modalidad B: autómata manual

Ejemplo AFN que acepta cadenas terminadas en ab:

1. Selecciona Autómata manual.
2. Escribe alfabeto `a, b`, estados `q0, q1, q2`, inicial `q0` y finales `q2`.
3. Pulsa Actualizar tabla de entrada.
4. Completa la tabla como se indica. Las celdas marcadas con «vacía» deben dejarse sin texto; no escribas esa palabra ni ∅.

| Estado | a | b | ε |
| --- | --- | --- | --- |
| q0 | q0, q1 | q0 | vacía |
| q1 | vacía | q2 | vacía |
| q2 | vacía | vacía | vacía |

5. Pulsa Construir y minimizar. La clasificación es AFN, porque q0 tiene dos destinos con a.
6. En la etapa AFD aparecen los subconjuntos {q0}, {q0,q1} y {q0,q2}. El mínimo tiene tres estados.
7. Simula `ab` y `aab`: se aceptan. Simula `aba`: se rechaza.

La columna ε permite transiciones que no consumen ningún símbolo. El campo Finales puede estar vacío. Si modificas los estados o el alfabeto, actualiza la tabla y revisa sus destinos antes de procesar. Puedes cargar el ejemplo «AFN con varios destinos» para llenar los campos automáticamente.

## 4. Minimizar un AFD existente

Carga «AFD con estados equivalentes» y pulsa Construir y minimizar. La entrada usa A,B,C,X, inicial A y finales B,C. Es determinista y completo. El estado X es inaccesible; B y C son equivalentes. Los indicadores deben ser 4 → 3 → 3 → 2.

En la etapa Accesibles comprueba que X desaparece. En AFD lee que no fue necesario determinizar. En Mínimo, Correspondencia de estados muestra M0={A} y M1={B,C}. La cadena vacía se rechaza y toda cadena no vacía sobre a,b se acepta.

Si tu AFD tiene transiciones faltantes, el programa lo informa como AFD incompleto y añade un sumidero no final antes de minimizar. La ausencia de una transición no se confunde con tener varios destinos.

## 5. Leer los resultados

- La flecha de entrada identifica el estado inicial; el doble círculo identifica un estado final.
- En la tabla, → marca el inicial y * marca los finales. ∅ en una celda significa que no hay destinos.
- Los botones + y − amplían o reducen el diagrama. El área permite desplazamiento cuando es grande.
- Tabla de transición muestra los destinos exactos. Correspondencia de estados explica qué estados forman cada nuevo estado.
- Explicación paso a paso registra las operaciones realizadas, no una descripción genérica del algoritmo.
- Comparar esta etapa con el AFD mínimo muestra los tamaños y la tabla final.
- Descargar resultado guarda todas las etapas en JSON. SVG guarda el diagrama visible como imagen vectorial.

En diagramas densos utiliza la tabla para revisar todas las transiciones. Los nombres largos pueden abreviarse en los círculos, pero se conservan completos en la tabla y en el título del nodo. La etiqueta ε significa transición vacía, no un símbolo que deba escribirse en una cadena.

## 6. Simular cadenas

Selecciona primero la etapa que deseas probar. Escribe una cadena en Comprueba una cadena y pulsa Simular. El recorrido empieza en el cierre-ε del inicial y registra el conjunto alcanzado después de cada símbolo. En un AFD cada conjunto contiene un único estado.

Para `(a|b)*abb`, `aabb` recorre M0 → M1 → M1 → M2 → M3 y se acepta; `abba` se rechaza. Para probar la cadena vacía deja la casilla sin contenido. No escribas ε literal en el simulador.

Se acepta si después de consumir toda la cadena queda al menos un estado final. Un símbolo ajeno al alfabeto produce un error con su posición. Al cambiar de etapa se limpia la simulación anterior para evitar confusiones.

## 7. Mensajes frecuentes

| Situación | Cómo corregirla |
| --- | --- |
| Símbolos duplicados | Usa a,b en vez de a,a,b |
| Símbolo fuera del alfabeto | Añádelo al alfabeto o corrige la expresión/cadena |
| Falta un operando | Reemplaza a\| por a\|ε si querías incluir la cadena vacía |
| Falta un paréntesis | Cierra todos los paréntesis abiertos |
| Estado inexistente | Regístralo o corrige el nombre del destino/inicial/final |
| Cambiaste estados o alfabeto | Pulsa Actualizar tabla de entrada y revisa destinos |
| Se supera el límite | Reduce el ejemplo; nunca se entrega una conversión incompleta |
| Sin conexión | Verifica que app.py siga ejecutándose o espera al arranque de Render |

Límites: alfabeto de 1 a 12 símbolos de un carácter; expresión de hasta 120 caracteres; 1 a 80 estados manuales; hasta 4000 aristas; 128 estados deterministas generados; 1000 caracteres por cadena. No hay guardado automático; descarga el resultado antes de cerrar o recargar la página.

## 8. Material de entrega y verificación

El repositorio incluye este manual, el documento técnico, la matriz de pruebas, tres entradas JSON, sus resultados y la suite automatizada. Los resultados esperados de los ejemplos están contrastados con pruebas. La revisión visual interactiva de la página quedó pendiente por una restricción del control del navegador de esta sesión; no se incluyen capturas simuladas ni se afirma haber realizado esa revisión.
