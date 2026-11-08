# Autómata Lab
## Matriz de pruebas y evidencias

Microproyecto 3 · Teoría de la Computación · 2026/02

Registros: 27 aprobados, 1 omitidos y 0 pendientes. Los resultados proceden de reportes reales; consulte el CSV y XML para los identificadores completos.

La suite local corre en Windows con Python 3.13.9. Gunicorn se verifica únicamente en Linux. La comprobación exacta de equivalencia usa el producto de AFD y la minimalidad se verifica por distinguibilidad de pares. Los ensayos con AFND incluyen 30 casos reproducibles de semilla 202602.

La interfaz web se revisó visualmente en Chrome de escritorio; las capturas reales están en docs/evidencias/capturas/. También se revisó en un teléfono emulado de 390 px (V02). Las imágenes de este informe son diagramas vectoriales generados de los resultados reales.

## Casos

- P01 · APROBADO · RF-11: página y recursos disponibles, control de salud y políticas HTTP. Evidencia: docs/evidencias/pytest-windows.xml (test_home_and_health).
- P02 · APROBADO · RF-03,06,09,12: contrato completo desde petición de construcción hasta simulación. Evidencia: docs/evidencias/pytest-windows.xml (test_process_and_simulate).
- P03 · APROBADO · RF-01,02,04: JSON malformado, tipos incorrectos y entradas inválidas devuelven 400. Evidencia: docs/evidencias/pytest-windows.xml (test_api_invalid_requests).
- P04 · APROBADO · RF-12,13: solicitudes concurrentes de usuarios distintos no comparten resultados. Evidencia: docs/evidencias/pytest-windows.xml (test_isolation).
- P05 · APROBADO · RF-03,04,13: los seis ejemplos de entrega (lenguajes y autómatas de clase) son utilizables a través de la API. Evidencia: docs/evidencias/pytest-windows.xml (test_shipped_examples).
- P06 · APROBADO · RF-01,02,03,09,12: lenguaje de clase Σ={a,e,i,p}: inicia y finaliza en a, vocales seguidas no se repiten. Evidencia: docs/evidencias/pytest-windows.xml (test_language_vowels).
- P07 · APROBADO · RF-02,03,09,12: lenguaje de clase Σ={0,1,2}: 2 precedido de 1 y seguido de 0, suma ≤ 6, longitud ≤ 5. Evidencia: docs/evidencias/pytest-windows.xml (test_language_digits).
- P08 · APROBADO · RF-02,03,09,12: lenguaje de clase Σ={a,e,m,b,p}: finaliza en vocal, consonantes seguidas solo mb y mp. Evidencia: docs/evidencias/pytest-windows.xml (test_language_consonants).
- P09 · APROBADO · RF-02,03: cada forma documentada de regla reconoce exactamente su lenguaje. Evidencia: docs/evidencias/pytest-windows.xml (test_rule_kinds).
- P10 · APROBADO · RF-04,05,06: el AFND de clase da exactamente la tabla AFD de la docente (A, B, BC, D, BCD, CD, ABCD, AD, AB). Evidencia: docs/evidencias/pytest-windows.xml (test_manual_nfa).
- P11 · APROBADO · RF-07,09: elimina D (inaccesible) y fusiona B,C en B; el AFD mínimo tiene dos estados. Evidencia: docs/evidencias/pytest-windows.xml (test_equivalent_unreachable).
- P12 · APROBADO · RF-05,06,12: la API también admite transiciones ε; los ciclos ε terminan. Evidencia: docs/evidencias/pytest-windows.xml (test_epsilon_cycle).
- P13 · APROBADO · RF-09: particiones vacías no fallan; lenguajes vacío y universal tienen un estado. Evidencia: docs/evidencias/pytest-windows.xml (test_no_finals_and_all_finals).
- P14 · APROBADO · RF-05,09: un AFD incompleto sigue siendo determinista y se completa con el estado ERROR sin colisiones. Evidencia: docs/evidencias/pytest-windows.xml (test_partial_sink).
- P15 · APROBADO · RF-01: rechaza duplicados, símbolos reservados, espacios y símbolos múltiples. Evidencia: docs/evidencias/pytest-windows.xml (test_alphabet_validation).
- P16 · APROBADO · RF-02: reglas desconocidas o con símbolos fuera de Σ producen errores con el número de regla. Evidencia: docs/evidencias/pytest-windows.xml (test_rule_validation).
- P17 · APROBADO · RF-04: valida nombres, inicial, finales, destinos, símbolos y estructura de transiciones. Evidencia: docs/evidencias/pytest-windows.xml (test_manual_validation).
- P18 · APROBADO · RF-12: rechaza símbolos externos y distingue campo vacío de ε literal. Evidencia: docs/evidencias/pytest-windows.xml (test_simulation_validation).
- P19 · APROBADO · RF-01,04,06: límites explícitos evitan explosión de estados sin resultados truncados. Evidencia: docs/evidencias/pytest-windows.xml (test_resource_limits).
- P20 · APROBADO · RF-10,11,13: etapas consultables, trazas, particiones y nombres reproducibles. Evidencia: docs/evidencias/pytest-windows.xml (test_traces_mapping_stability).
- P21 · APROBADO · RF-06,09,12: 30 AFND aleatorios reproducibles preservan lenguaje y generan AFD mínimos. Evidencia: docs/evidencias/pytest-windows.xml (test_generated_automata).
- P22 · APROBADO · RF-09,11: minimizar dos veces conserva el lenguaje y el número mínimo de estados. Evidencia: docs/evidencias/pytest-windows.xml (test_already_minimal_and_roundtrip).
- P23 · APROBADO · RF-03,05,06,10: notación de clase: estados A, B, C…; X,a→Y; subconjuntos concatenados; ERROR; L = {…}. Evidencia: docs/evidencias/pytest-windows.xml (test_class_notation).
- P24 · OMITIDO · Despliegue: Gunicorn escucha en 0.0.0.0 y sirve salud, interfaz y procesamiento real. Evidencia: docs/evidencias/pytest-windows.xml (test_gunicorn_linux).
- P25 · APROBADO · Despliegue Linux: Instalación limpia, suite completa y arranque real de Gunicorn. Evidencia: https://github.com/angelvesga/TC-MICROPROYECTO3-AF/actions/runs/42500246595 (github_actions).
- P26 · APROBADO · RF-11,13 / formato: Tabla con caracteres escapados, SVG sin coordenadas inválidas, estados con nombres especiales y limpieza al cambiar de modalidad. Evidencia: docs/evidencias/frontend.json (check_frontend.cjs).
- V01 · APROBADO · RF-05,11,12,13 / interfaz: En Chrome de escritorio (1366 px): modalidad A con alfabeto y reglas del lenguaje (botones de reglas, construcción justificada, AFD mínimo A, B, C… con ERROR al final); modalidad B con el AFND de clase, cuya conversión reproduce la tabla A, B, BC, D, BCD, CD, ABCD, AD, AB; notación de clase (Q, q0, Σ, Qt; A,0→B); las cuatro etapas son consultables; sin errores de la aplicación en consola. Evidencia: docs/evidencias/capturas/ (revision_visual_web).
- V02 · APROBADO · RF-11 / interfaz móvil: Teléfono emulado de 390 px (protocolo de depuración de Chrome): una sola columna, sin desplazamiento horizontal (scrollWidth = 390); el ejemplo 01 se construye y apa se acepta con su recorrido. Evidencia: docs/evidencias/capturas/07_vista_movil_390px.jpg (revision_visual_movil).
