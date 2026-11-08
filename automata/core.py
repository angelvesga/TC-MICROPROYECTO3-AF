"""Validación, construcción, determinización, minimización y simulación.

Las transiciones usan conjuntos: incluso un AFD tiene destinos de tamaño uno.
Ningún algoritmo modifica el autómata recibido ni utiliza estado global mutable.

Notación (la usada en clase): AF = { {Q}, q0, Σ, {Qt}, δ }. Los estados se nombran
con letras mayúsculas; una transición se escribe «A,0→B»; un estado del AFD
obtenido por subconjuntos se nombra concatenando sus estados («AC», «ABC») y el
subconjunto vacío es el estado ERROR.
"""
from collections import deque
from dataclasses import dataclass
import re

EPSILON = "ε"
RESERVED = set("|*()ε∅,#\\")
MAX_ALPHABET = 12
MAX_INPUT_STATES = 80
MAX_STATES = 256
MAX_DFA_STATES = 128
MAX_WORD = 1000
ERROR_STATE = "ERROR"
STRICT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{0,31}")
# Los estados generados (AC, q0q2, ERROR…) pueden ser más largos que los manuales.
GENERATED_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{0,599}")


class InputError(ValueError):
    """Entrada corregible o límite educativo excedido."""


def alphabet_from(value):
    if not isinstance(value, list) or not value:
        raise InputError("El alfabeto debe ser una lista no vacía de símbolos.")
    if len(value) > MAX_ALPHABET:
        raise InputError(f"El alfabeto admite como máximo {MAX_ALPHABET} símbolos.")
    for symbol in value:
        if (not isinstance(symbol, str) or len(symbol) != 1
                or not symbol.isprintable() or symbol.isspace() or symbol in RESERVED):
            raise InputError("Cada símbolo debe ser un carácter visible; no use espacios, comas, #, \\, |, *, (, ), ε o ∅.")
    if len(set(value)) != len(value):
        raise InputError("El alfabeto contiene símbolos duplicados.")
    return tuple(value)


@dataclass
class Automaton:
    states: tuple[str, ...]
    alphabet: tuple[str, ...]
    initial: str
    finals: frozenset[str]
    transitions: dict[str, dict[str, frozenset[str]]]

    def targets(self, state, symbol):
        return self.transitions.get(state, {}).get(symbol, frozenset())

    def to_dict(self):
        rank = {q: i for i, q in enumerate(self.states)}
        return {
            "states": list(self.states), "alphabet": list(self.alphabet),
            "initial": self.initial,
            "finals": [q for q in self.states if q in self.finals],
            "transitions": {q: {s: sorted(self.targets(q, s), key=rank.get)
                                for s in (*self.alphabet, EPSILON) if self.targets(q, s)}
                            for q in self.states},
        }


def automaton_from(data, max_states=MAX_INPUT_STATES, generated=False):
    if not isinstance(data, dict):
        raise InputError("El autómata debe ser un objeto con estados y transiciones.")
    alphabet = alphabet_from(data.get("alphabet"))
    states = data.get("states")
    if not isinstance(states, list) or not 1 <= len(states) <= max_states:
        raise InputError(f"Ingrese entre 1 y {max_states} estados.")
    pattern = GENERATED_NAME if generated else STRICT_NAME
    if any(not isinstance(q, str) or not pattern.fullmatch(q) for q in states):
        raise InputError("Los estados deben comenzar por letra o _, y usar hasta 32 letras ASCII, números, _ o -.")
    if len(states) != len(set(states)):
        raise InputError("Hay estados duplicados.")
    initial = data.get("initial")
    if not isinstance(initial, str) or initial not in states:
        raise InputError("Seleccione un estado inicial existente.")
    finals = data.get("finals")
    if not isinstance(finals, list) or any(not isinstance(q, str) or q not in states for q in finals):
        raise InputError("Los estados finales deben ser una lista de estados existentes (puede estar vacía).")
    if len(finals) != len(set(finals)):
        raise InputError("Hay estados finales duplicados.")
    transitions = data.get("transitions")
    if not isinstance(transitions, dict):
        raise InputError("Las transiciones deben organizarse por estado y símbolo.")
    clean = {}
    count = 0
    for q, edges in transitions.items():
        if q not in states or not isinstance(edges, dict):
            raise InputError(f"Origen de transición inválido: {q}.")
        clean[q] = {}
        for symbol, targets in edges.items():
            if symbol not in (*alphabet, EPSILON):
                raise InputError(f"Símbolo de transición fuera del alfabeto: {symbol}.")
            if not isinstance(targets, list) or any(not isinstance(t, str) or t not in states for t in targets):
                raise InputError(f"Revise los destinos de ({q}, {symbol}); deben ser estados existentes.")
            if len(targets) != len(set(targets)):
                raise InputError(f"Destino duplicado en ({q}, {symbol}).")
            count += len(targets)
            if count > 4000:
                raise InputError("Se permiten como máximo 4000 aristas de transición.")
            clean[q][symbol] = frozenset(targets)
    return Automaton(tuple(states), alphabet, initial, frozenset(finals), clean)


def ordered(a, states):
    """Estados de un conjunto en el orden de Q (A, B, C… o q0, q1…)."""
    rank = {q: i for i, q in enumerate(a.states)}
    return sorted(states, key=lambda q: (rank.get(q, len(rank)), q))


def targets_text(a, states, separator=","):
    return separator.join(ordered(a, states))


def classify(a):
    reasons = []
    for q in a.states:
        if a.targets(q, EPSILON):
            reasons.append(f"{q},ε→{targets_text(a, a.targets(q, EPSILON))}: transición vacía, no consume símbolo.")
        for symbol in a.alphabet:
            if len(a.targets(q, symbol)) > 1:
                reasons.append(f"{q},{symbol}→{targets_text(a, a.targets(q, symbol))}: el símbolo {symbol} va a MÁS de un estado.")
    if reasons:
        return "AFND-ε" if any(a.targets(q, EPSILON) for q in a.states) else "AFND", reasons
    missing = [(q, s) for q in a.states for s in a.alphabet if not a.targets(q, s)]
    if missing:
        return "AFD incompleto", [
            "Cada símbolo del alfabeto va a un solo estado (X,a→Y), pero hay casillas en error: "
            + ", ".join(f"{q},{s}→error" for q, s in missing[:8]) + ("…" if len(missing) > 8 else "") + ".",
            f"Se completarán con el estado {ERROR_STATE}."]
    return "AFD", ["Cada símbolo del alfabeto va a un solo estado (X,a→Y) y no hay transiciones ε."]


def closure(a, states):
    seen = set(states)
    pending = list(states)
    while pending:
        for nxt in a.targets(pending.pop(), EPSILON):
            if nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return frozenset(seen)


def reachable(a):
    seen = {a.initial}
    pending = deque([a.initial])
    log = [f"Se inicia la búsqueda en el estado inicial q0 = {a.initial}."]
    while pending:
        q = pending.popleft()
        for s in (*a.alphabet, EPSILON):
            for nxt in sorted(a.targets(q, s)):
                if nxt not in seen:
                    seen.add(nxt)
                    pending.append(nxt)
                    log.append(f"{q},{s}→{nxt}: {nxt} es accesible.")
    removed = [q for q in a.states if q not in seen]
    log.append("Estados inaccesibles eliminados: " + (", ".join(removed) if removed else "ninguno") + ".")
    return Automaton(tuple(q for q in a.states if q in seen), a.alphabet, a.initial,
                     a.finals & seen, {q: dict(a.transitions.get(q, {})) for q in a.states if q in seen}), log


def format_set(states, a=None):
    if not states:
        return "∅"
    return "{" + ", ".join(ordered(a, states) if a else sorted(states)) + "}"


def subset_namer(a):
    """Nombra cada subconjunto concatenando sus estados en el orden de Q: {A,C} → AC.

    El vacío es ERROR. Si dos subconjuntos producirían el mismo nombre (posible solo
    con nombres de varios caracteres) se separan con guiones y, si hace falta, sufijo.
    """
    used = {}

    def name(subset):
        members = ordered(a, subset)
        candidates = ["".join(members) if members else ERROR_STATE]
        if members:
            candidates.append("-".join(members))
        for candidate in candidates:
            if used.get(candidate, subset) == subset:
                used[candidate] = subset
                return candidate
        base, n = candidates[-1], 2
        while f"{base}_{n}" in used:
            n += 1
        used[f"{base}_{n}"] = subset
        return f"{base}_{n}"
    return name


def determinize(a):
    """Construcción por subconjuntos, explicada con la notación de clase."""
    start = closure(a, {a.initial})
    namer = subset_namer(a)
    names = {start: namer(start)}
    pending = deque([start])
    transitions, finals = {}, set()
    if start == {a.initial}:
        log = [f"Estado inicial del AFD = estado inicial del AFND: {names[start]}."]
    else:
        log = [f"Estado inicial del AFD = cierre-ε({a.initial}) = {format_set(start, a)} → se nombra {names[start]}."]
    while pending:
        subset = pending.popleft()
        q = names[subset]
        transitions[q] = {}
        if subset & a.finals:
            finals.add(q)
            log.append(f"{q} es terminal porque contiene {targets_text(a, subset & a.finals, ', ')}, terminal del AFND.")
        for s in a.alphabet:
            moved = frozenset(t for state in subset for t in a.targets(state, s))
            target = closure(a, moved)
            if target not in names:
                if len(names) >= MAX_DFA_STATES:
                    raise InputError(f"La determinización supera {MAX_DFA_STATES} estados. Simplifique la entrada; no se entrega un resultado parcial.")
                names[target] = namer(target)
                pending.append(target)
            transitions[q][s] = frozenset({names[target]})
            parts = " · ".join(f"{m},{s}→{targets_text(a, a.targets(m, s)) or 'error'}" for m in ordered(a, subset))
            extra = target - moved
            note = f"; cierre-ε añade {targets_text(a, extra, ', ')}" if extra else ""
            if len(subset) == 1 and not extra and parts == f"{q},{s}→{names[target]}":
                log.append(f"{q},{s}→{names[target]}.")
            else:
                log.append(f"{q},{s}→{names[target]}   ⟸ {parts}{note}.")
    result = Automaton(tuple(names.values()), a.alphabet, names[start], frozenset(finals), transitions)
    return result, log, {name: ordered(a, subset) for subset, name in names.items()}


def complete(a):
    missing = [(q, s) for q in a.states for s in a.alphabet if not a.targets(q, s)]
    if not missing:
        return a, ["El autómata ya es un AFD completo: se omite la conversión AFND → AFD y se continúa con la minimización."], {q: [q] for q in a.states}
    sink, suffix = ERROR_STATE, 0
    while sink in a.states:
        suffix += 1
        sink = f"{ERROR_STATE}_{suffix}"
    transitions = {q: dict(a.transitions.get(q, {})) for q in a.states}
    transitions[sink] = {s: frozenset({sink}) for s in a.alphabet}
    log = [f"El autómata es determinista pero tiene casillas en error. Se añade el estado {sink}, no terminal, que con todo símbolo vuelve a sí mismo."]
    for q, s in missing:
        transitions.setdefault(q, {})[s] = frozenset({sink})
        log.append(f"{q},{s}→{sink}.")
    return Automaton((*a.states, sink), a.alphabet, a.initial, a.finals, transitions), log, {**{q: [q] for q in a.states}, sink: []}


def minimize(a, rename=False):
    """Moore: separar bloques por sus firmas de destinos hasta un punto fijo.

    Con rename=True las clases se nombran A, B, C… en orden de recorrido (ERROR conserva
    su nombre); si no, cada clase conserva el nombre de su primer estado.
    """
    if classify(a)[0] != "AFD":
        raise InputError("La minimización necesita un AFD completo.")
    blocks = [tuple(q for q in a.states if (q in a.finals) == final) for final in (False, True)]
    blocks = [b for b in blocks if b]
    partitions = [[list(b) for b in blocks]]
    log = ["P0 separa estados no terminales y terminales: " + " / ".join(format_set(b, a) for b in blocks) + "."]
    iteration = 0
    while True:
        block_of = {q: i for i, block in enumerate(blocks) for q in block}
        refined = []
        for block in blocks:
            groups = {}
            for q in block:
                signature = tuple(block_of[next(iter(a.targets(q, s)))] for s in a.alphabet)
                groups.setdefault(signature, []).append(q)
                log.append(" · ".join(f"{q},{s}→{next(iter(a.targets(q, s)))} (bloque {i + 1})"
                                      for s, i in zip(a.alphabet, signature)) + ".")
            refined.extend(tuple(group) for group in groups.values())
        iteration += 1
        partitions.append([list(b) for b in refined])
        log.append(f"P{iteration}: " + " / ".join(format_set(b, a) for b in refined) + ".")
        if refined == blocks:
            log.append("La partición no cambia: sus bloques son las clases de equivalencia.")
            break
        blocks = refined
    # Enumeración BFS del cociente: M0 siempre contiene el estado inicial.
    block_of = {q: i for i, block in enumerate(blocks) for q in block}
    start = block_of[a.initial]
    order, pending, seen = [], deque([start]), {start}
    while pending:
        i = pending.popleft()
        order.append(i)
        for s in a.alphabet:
            target = block_of[next(iter(a.targets(blocks[i][0], s)))]
            if target not in seen:
                seen.add(target)
                pending.append(target)
    # Cada clase conserva el nombre de su primer estado: así el AFD mínimo se lee
    # con los mismos nombres de la etapa anterior.
    names = {i: blocks[i][0] for i in order}
    if rename:
        # ERROR va al final de Q, como en los ejercicios de clase.
        order = [i for i in order if ERROR_STATE not in blocks[i]] + [i for i in order if ERROR_STATE in blocks[i]]
        letters = iter(state_names(len(order)))
        names = {i: ERROR_STATE if ERROR_STATE in blocks[i] else next(letters) for i in order}
    for i in order:
        if len(blocks[i]) > 1:
            log.append(f"{', '.join(blocks[i])} son equivalentes: se fusionan en {names[i]}.")
    if rename:
        log.append("Los estados del AFD mínimo se nombran A, B, C… en orden de recorrido desde q0: "
                   + "; ".join(f"{names[i]} = {format_set(blocks[i], a)}" for i in order) + ".")
    transitions = {names[i]: {s: frozenset({names[block_of[next(iter(a.targets(blocks[i][0], s)))]]})
                              for s in a.alphabet} for i in order}
    result = Automaton(tuple(names.values()), a.alphabet, names[start],
                       frozenset(names[i] for i in order if set(blocks[i]) & a.finals), transitions)
    return result, log, {names[i]: list(blocks[i]) for i in order}, partitions


def state_names(count):
    """A, B, C… como en clase; con más de 26 estados se usa q0, q1, q2…"""
    if count <= 26:
        return [chr(ord("A") + i) for i in range(count)]
    return [f"q{i}" for i in range(count)]


def simulate(a, word):
    if not isinstance(word, str) or len(word) > MAX_WORD:
        raise InputError(f"La cadena debe ser texto de hasta {MAX_WORD} caracteres.")
    for i, symbol in enumerate(word):
        if symbol not in a.alphabet:
            raise InputError(f"Cadena, posición {i + 1}: '{symbol}' no pertenece al alfabeto. Para ε deje el campo vacío.")
    current = closure(a, {a.initial})
    path = [{"position": 0, "symbol": None, "states": sorted(current)}]
    for i, symbol in enumerate(word, 1):
        current = closure(a, {t for q in current for t in a.targets(q, symbol)})
        path.append({"position": i, "symbol": symbol, "states": sorted(current)})
    return {"word": word, "accepted": bool(current & a.finals), "path": path}


def language_sample(a, limit=8, max_length=10):
    """Primeras palabras aceptadas, en orden de longitud, para escribir L = {…}."""
    found, frontier = [], [("", closure(a, {a.initial}))]
    for _ in range(max_length + 1):
        nxt = []
        for word, current in frontier:
            if current & a.finals:
                found.append(word or EPSILON)
                if len(found) >= limit:
                    return found
            for s in a.alphabet:
                states = closure(a, {t for q in current for t in a.targets(q, s)})
                if states:
                    nxt.append((word + s, states))
        frontier = nxt[:4096]
    return found


def process(data):
    if not isinstance(data, dict):
        raise InputError("Envíe un objeto JSON.")
    mode = data.get("mode")
    meaning = None
    if mode == "language":
        from .language import build_from_rules  # Modalidad A: a partir de un lenguaje.
        alphabet = alphabet_from(data.get("alphabet"))
        a, construction, meaning = build_from_rules(alphabet, data.get("rules"))
    elif mode == "manual":
        a = automaton_from(data.get("automaton"))
        construction = ["Se registran los componentes ingresados sin cambiar sus nombres."]
    else:
        raise InputError("Seleccione la modalidad: language (A, a partir de un lenguaje) o manual (B, a partir de un autómata).")
    kind, reasons = classify(a)

    def stage(key, title, automaton, steps, mapping=None, **extra):
        return {"id": key, "title": title, "automaton": automaton.to_dict(),
                "steps": steps, "mapping": mapping or {q: [q] for q in automaton.states}, **extra}

    stages = [stage("input", "Construcción desde el lenguaje" if mode == "language" else "Identificación del autómata",
                    a, construction + [f"Clasificación: {kind}."] + reasons, meaning)]
    if kind == "AFD":
        stages[0]["steps"].append("El autómata ya es determinista: se indica y se continúa con su minimización.")
    accessible, trace = reachable(a)
    stages.append(stage("reachable", "Estados accesibles", accessible, trace))
    if classify(accessible)[0].startswith("AFND"):
        dfa, trace, mapping = determinize(accessible)
    else:
        dfa, trace, mapping = complete(accessible)
    stages.append(stage("dfa", "Conversión AFND → AFD" if kind.startswith("AFND") else "AFD completo", dfa, trace, mapping))
    minimal, trace, groups, partitions = minimize(dfa, rename=mode == "language")
    original = {q: sorted({original for member in members for original in mapping[member]}) for q, members in groups.items()}
    stages.append(stage("minimal", "AFD mínimo", minimal, trace, groups,
                        original_mapping=original, partitions=partitions))
    return {"classification": kind, "stages": stages, "language": language_sample(minimal),
            "summary": {"original_states": len(a.states), "reachable_states": len(accessible.states),
                        "dfa_states": len(dfa.states), "minimal_states": len(minimal.states)}}
