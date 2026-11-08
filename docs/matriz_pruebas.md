# Autómata Lab
## Matriz de pruebas y evidencias

Microproyecto 3 · Teoría de la Computación · 2026/02

Registros: 25 aprobados, 1 omitidos y 0 pendientes. Los resultados proceden de reportes reales; consulte el CSV y XML para los identificadores completos.

La suite local corre en Windows con Python 3.13.9. Gunicorn se verifica únicamente en Linux. La comprobación exacta de equivalencia usa el producto de AFD y la minimalidad se verifica por distinguibilidad de pares. Los ensayos con AFN incluyen 30 casos reproducibles de semilla 202602.

La interfaz web se revisó visualmente en Chrome de escritorio; las capturas reales están en docs/evidencias/capturas/. También se revisó con el diseño móvil activo (657 px de ancho visible). Las imágenes de este informe son diagramas vectoriales generados de los resultados reales.

## Casos

- P01 · APROBADO · RF-11: página y recursos disponibles, control de salud y políticas HTTP. Evidencia: docs/evidencias/pytest-windows.xml (test_home_and_health).
- P02 · APROBADO · RF-03,06,09,12: contrato completo desde petición de construcción hasta simulación. Evidencia: docs/evidencias/pytest-windows.xml (test_process_and_simulate).
- P03 · APROBADO · RF-01,02,04: JSON malformado, tipos incorrectos y entradas inválidas devuelven 400. Evidencia: docs/evidencias/pytest-windows.xml (test_api_invalid_requests).
- P04 · APROBADO · RF-12,13: solicitudes concurrentes de usuarios distintos no comparten resultados. Evidencia: docs/evidencias/pytest-windows.xml (test_isolation).
- P05 · APROBADO · RF-03,04,13: los tres ejemplos de entrega son utilizables a través de la API. Evidencia: docs/evidencias/pytest-windows.xml (test_shipped_examples).
- P06 · APROBADO · RF-02,03,06,09,12: abb produce cuatro estados y reconoce exactamente el sufijo. Evidencia: docs/evidencias/pytest-windows.xml (test_suffix_abb).
- P07 · APROBADO · RF-04,05,06: varios destinos se identifican y determinizar preserva el lenguaje. Evidencia: docs/evidencias/pytest-windows.xml (test_manual_nfa).
- P08 · APROBADO · RF-07,09: elimina X y fusiona B,C; el AFD mínimo tiene dos estados. Evidencia: docs/evidencias/pytest-windows.xml (test_equivalent_unreachable).
- P09 · APROBADO · RF-02,03: estrella, concatenación, unión y paréntesis respetan la precedencia. Evidencia: docs/evidencias/pytest-windows.xml (test_regex_precedence).
- P10 · APROBADO · RF-03,09,12: ε acepta solo cadena vacía; ∅ no acepta ninguna cadena. Evidencia: docs/evidencias/pytest-windows.xml (test_empty_word_language).
- P11 · APROBADO · RF-05,06,12: ciclos ε terminan y reconocen aceptación sin consumir entrada. Evidencia: docs/evidencias/pytest-windows.xml (test_epsilon_cycle).
- P12 · APROBADO · RF-09: particiones vacías no fallan; lenguajes vacío y universal tienen un estado. Evidencia: docs/evidencias/pytest-windows.xml (test_no_finals_and_all_finals).
- P13 · APROBADO · RF-05,09: un AFD incompleto sigue siendo determinista y se completa sin colisiones. Evidencia: docs/evidencias/pytest-windows.xml (test_partial_sink).
- P14 · APROBADO · RF-01: rechaza duplicados, operadores reservados, espacios y símbolos múltiples. Evidencia: docs/evidencias/pytest-windows.xml (test_alphabet_validation).
- P15 · APROBADO · RF-02: expresiones inválidas y símbolos externos producen errores con posición. Evidencia: docs/evidencias/pytest-windows.xml (test_regex_validation).
- P16 · APROBADO · RF-04: valida nombres, inicial, finales, destinos, símbolos y estructura de transiciones. Evidencia: docs/evidencias/pytest-windows.xml (test_manual_validation).
- P17 · APROBADO · RF-12: rechaza símbolos externos y distingue campo vacío de ε literal. Evidencia: docs/evidencias/pytest-windows.xml (test_simulation_validation).
- P18 · APROBADO · RF-01,04,06: límites explícitos evitan explosión de estados sin resultados truncados. Evidencia: docs/evidencias/pytest-windows.xml (test_resource_limits).
- P19 · APROBADO · RF-10,11,13: etapas consultables, trazas, particiones y nombres reproducibles. Evidencia: docs/evidencias/pytest-windows.xml (test_traces_mapping_stability).
- P20 · APROBADO · RF-06,09,12: 30 AFN aleatorios reproducibles preservan lenguaje y generan AFD mínimos. Evidencia: docs/evidencias/pytest-windows.xml (test_generated_automata).
- P21 · APROBADO · RF-09,11: minimizar dos veces conserva el lenguaje y el número mínimo de estados. Evidencia: docs/evidencias/pytest-windows.xml (test_already_minimal_and_roundtrip).
- P22 · OMITIDO · Despliegue: Gunicorn escucha en 0.0.0.0 y sirve salud, interfaz y procesamiento real. Evidencia: docs/evidencias/pytest-windows.xml (test_gunicorn_linux).
- P23 · APROBADO · Despliegue Linux: Instalación limpia, suite completa y arranque real de Gunicorn. Evidencia: https://github.com/angelvesga/TC-MICROPROYECTO3-AF/actions/runs/42500246595 (github_actions).
- P24 · APROBADO · RF-11,13 / formato: Tabla con caracteres escapados, SVG sin coordenadas inválidas, estados con nombres especiales y limpieza al cambiar de modalidad. Evidencia: docs/evidencias/frontend.json (check_frontend.cjs).
- V01 · APROBADO · RF-05,11,12,13 / interfaz: En Chrome de escritorio (1366 px): ejemplo 01 da AFD mínimo de 4 estados con diagrama y tabla; aabb se acepta con recorrido M0→M1→M1→M2→M3; ejemplo 02 se clasifica como AFN; las cuatro etapas son consultables; cambiar de modalidad limpia resultados; sin errores de la aplicación en consola. Evidencia: docs/evidencias/capturas/ (revision_visual_web).
- V02 · APROBADO · RF-11 / interfaz móvil: Con área visible de 657 px (mínimo de ventana de Chrome; activa el corte móvil de 760 px): diseño en una columna, ejemplo 01 construido y simulado, sin desbordamiento horizontal. Evidencia: docs/evidencias/capturas/04_vista_movil_657px.jpg (revision_visual_movil).
