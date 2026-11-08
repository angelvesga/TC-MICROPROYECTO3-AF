"""Validación, construcción, determinización, minimización y simulación.

Las transiciones usan conjuntos: incluso un AFD tiene destinos de tamaño uno.
Ningún algoritmo modifica el autómata recibido ni utiliza estado global mutable.
"""
from collections import deque
from dataclasses import dataclass
import re

EPSILON = "ε"
RESERVED = set("|*()ε∅,\\")
MAX_ALPHABET = 12
MAX_INPUT_STATES = 80
MAX_STATES = 256
MAX_DFA_STATES = 128
MAX_REGEX = 120
MAX_WORD = 1000


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
            raise InputError("Cada símbolo debe ser un carácter visible; no use espacios, comas, \\, |, *, (, ), ε o ∅.")
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


def automaton_from(data, max_states=MAX_INPUT_STATES):
    if not isinstance(data, dict):
        raise InputError("El autómata debe ser un objeto con estados y transiciones.")
    alphabet = alphabet_from(data.get("alphabet"))
    states = data.get("states")
    if not isinstance(states, list) or not 1 <= len(states) <= max_states:
        raise InputError(f"Ingrese entre 1 y {max_states} estados.")
    if any(not isinstance(q, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,31}", q) for q in states):
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


def classify(a):
    reasons = []
    for q in a.states:
        if a.targets(q, EPSILON):
            reasons.append(f"{q} tiene transición ε, que no consume símbolos.")
        for symbol in a.alphabet:
            if len(a.targets(q, symbol)) > 1:
                reasons.append(f"({q}, {symbol}) tiene varios destinos: {', '.join(sorted(a.targets(q, symbol)))}.")
    if reasons:
        return "AFN-ε" if any(a.targets(q, EPSILON) for q in a.states) else "AFN", reasons
    missing = [(q, s) for q in a.states for s in a.alphabet if not a.targets(q, s)]
    if missing:
        return "AFD incompleto", [f"No hay ε ni varios destinos. Faltan {len(missing)} transiciones; se completarán con un sumidero."]
    return "AFD", ["Cada estado tiene exactamente un destino por símbolo y no hay transiciones ε."]


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
    log = [f"Se inicia la búsqueda en {a.initial}."]
    while pending:
        q = pending.popleft()
        for s in (*a.alphabet, EPSILON):
            for nxt in sorted(a.targets(q, s)):
                if nxt not in seen:
                    seen.add(nxt)
                    pending.append(nxt)
                    log.append(f"{q} --{s}→ {nxt}: se descubre un estado accesible.")
    removed = [q for q in a.states if q not in seen]
    log.append("Estados inaccesibles eliminados: " + (", ".join(removed) if removed else "ninguno") + ".")
    return Automaton(tuple(q for q in a.states if q in seen), a.alphabet, a.initial,
                     a.finals & seen, {q: dict(a.transitions.get(q, {})) for q in a.states if q in seen}), log


def format_set(states):
    return "{" + ", ".join(sorted(states)) + "}" if states else "∅"


def determinize(a):
    start = closure(a, {a.initial})
    names = {start: "D0"}
    pending = deque([start])
    transitions, finals = {}, set()
    log = [f"D0 = cierre-ε({{{a.initial}}}) = {format_set(start)}."]
    while pending:
        subset = pending.popleft()
        q = names[subset]
        transitions[q] = {}
        if subset & a.finals:
            finals.add(q)
            log.append(f"{q} es final porque contiene {format_set(subset & a.finals)}.")
        for s in a.alphabet:
            moved = frozenset(t for state in subset for t in a.targets(state, s))
            target = closure(a, moved)
            if target not in names:
                if len(names) >= MAX_DFA_STATES:
                    raise InputError(f"La determinización supera {MAX_DFA_STATES} estados. Simplifique la entrada; no se entrega un resultado parcial.")
                names[target] = f"D{len(names)}"
                pending.append(target)
            transitions[q][s] = frozenset({names[target]})
            log.append(f"{q}, símbolo {s}: mover = {format_set(moved)}; cierre-ε = {format_set(target)} = {names[target]}.")
    result = Automaton(tuple(names.values()), a.alphabet, "D0", frozenset(finals), transitions)
    return result, log, {name: sorted(subset) for subset, name in names.items()}


def complete(a):
    missing = [(q, s) for q in a.states for s in a.alphabet if not a.targets(q, s)]
    if not missing:
        return a, ["El autómata ya es un AFD completo: se omite la construcción por subconjuntos."], {q: [q] for q in a.states}
    sink, suffix = "SUMIDERO", 0
    while sink in a.states:
        suffix += 1
        sink = f"SUMIDERO_{suffix}"
    transitions = {q: dict(a.transitions.get(q, {})) for q in a.states}
    transitions[sink] = {s: frozenset({sink}) for s in a.alphabet}
    log = [f"El autómata es determinista. Se añade {sink}, no final, con bucles para todos los símbolos."]
    for q, s in missing:
        transitions.setdefault(q, {})[s] = frozenset({sink})
        log.append(f"Se completa ({q}, {s}) → {sink}.")
    return Automaton((*a.states, sink), a.alphabet, a.initial, a.finals, transitions), log, {**{q: [q] for q in a.states}, sink: []}


def minimize(a):
    """Moore: separar bloques por sus firmas de destinos hasta un punto fijo."""
    if classify(a)[0] != "AFD":
        raise InputError("La minimización necesita un AFD completo.")
    blocks = [tuple(q for q in a.states if (q in a.finals) == final) for final in (False, True)]
    blocks = [b for b in blocks if b]
    partitions = [[list(b) for b in blocks]]
    log = ["P0 separa no finales y finales: " + " / ".join(format_set(b) for b in blocks) + "."]
    iteration = 0
    while True:
        block_of = {q: i for i, block in enumerate(blocks) for q in block}
        refined = []
        for block in blocks:
            groups = {}
            for q in block:
                signature = tuple(block_of[next(iter(a.targets(q, s)))] for s in a.alphabet)
                groups.setdefault(signature, []).append(q)
                log.append(f"{q}: firma {signature}, en el orden de símbolos {a.alphabet}.")
            refined.extend(tuple(group) for group in groups.values())
        iteration += 1
        partitions.append([list(b) for b in refined])
        log.append(f"P{iteration}: " + " / ".join(format_set(b) for b in refined) + ".")
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
    names = {old: f"M{i}" for i, old in enumerate(order)}
    transitions = {names[i]: {s: frozenset({names[block_of[next(iter(a.targets(blocks[i][0], s)))]]})
                              for s in a.alphabet} for i in order}
    result = Automaton(tuple(names.values()), a.alphabet, names[start],
                       frozenset(names[i] for i in order if set(blocks[i]) & a.finals), transitions)
    return result, log, {names[i]: list(blocks[i]) for i in order}, partitions


class RegexParser:
    """Descenso recursivo: unión < concatenación < estrella."""

    def __init__(self, expression, alphabet):
        if not isinstance(expression, str) or not expression:
            raise InputError("Ingrese una expresión; use ε para la cadena vacía.")
        if len(expression) > MAX_REGEX:
            raise InputError(f"La expresión admite como máximo {MAX_REGEX} caracteres.")
        self.text, self.alphabet, self.pos = expression, alphabet, 0

    def error(self, message):
        raise InputError(f"Expresión, posición {self.pos + 1}: {message}")

    def peek(self):
        return self.text[self.pos] if self.pos < len(self.text) else None

    def parse(self):
        result = self.union()
        if self.peek() is not None:
            self.error(f"símbolo inesperado '{self.peek()}'.")
        return result

    def union(self):
        left = self.concat()
        while self.peek() == "|":
            self.pos += 1
            left = ("union", left, self.concat())
        return left

    def concat(self):
        parts = []
        while self.peek() is not None and self.peek() not in ")|":
            parts.append(self.repeat())
        if not parts:
            self.error("falta un operando; use ε si desea representar la cadena vacía.")
        result = parts[0]
        for part in parts[1:]:
            result = ("concat", result, part)
        return result

    def repeat(self):
        atom = self.atom()
        while self.peek() == "*":
            self.pos += 1
            atom = ("star", atom)
        return atom

    def atom(self):
        token = self.peek()
        if token == "(":
            self.pos += 1
            result = self.union()
            if self.peek() != ")":
                self.error("falta cerrar el paréntesis.")
            self.pos += 1
            return result
        if token in self.alphabet or token in (EPSILON, "∅"):
            self.pos += 1
            return ("symbol", token)
        self.error(f"'{token}' no es un operando válido o no pertenece al alfabeto.")


def thompson(expression, alphabet):
    ast = RegexParser(expression, alphabet).parse()
    states, transitions, log = [], {}, []

    def state():
        if len(states) >= MAX_STATES:
            raise InputError(f"La construcción supera {MAX_STATES} estados.")
        q = f"q{len(states)}"
        states.append(q)
        transitions[q] = {}
        return q

    def edge(source, symbol, target):
        transitions[source].setdefault(symbol, set()).add(target)

    def build(node):
        op = node[0]
        if op == "symbol":
            start, end = state(), state()
            if node[1] != "∅":
                edge(start, node[1], end)
            log.append(f"Fragmento {node[1]}: entrada {start}, salida {end}; " +
                       ("sin transición (lenguaje vacío)." if node[1] == "∅" else f"{start} --{node[1]}→ {end}."))
        elif op == "concat":
            start, middle = build(node[1])
            other, end = build(node[2])
            edge(middle, EPSILON, other)
            log.append(f"Concatenación: {middle} --ε→ {other}; fragmento {start} a {end}.")
        elif op == "union":
            start, end = state(), state()
            a, b = build(node[1])
            c, d = build(node[2])
            for x, y in ((start, a), (start, c), (b, end), (d, end)):
                edge(x, EPSILON, y)
            log.append(f"Unión: {start} --ε→ {{{a}, {c}}}; {{{b}, {d}}} --ε→ {end}.")
        else:
            start, end = state(), state()
            a, b = build(node[1])
            for x, y in ((start, a), (start, end), (b, a), (b, end)):
                edge(x, EPSILON, y)
            log.append(f"Estrella: {start} --ε→ {{{a}, {end}}}; {b} --ε→ {{{a}, {end}}}; permite cero o más repeticiones.")
        return start, end

    start, end = build(ast)
    return Automaton(tuple(states), alphabet, start, frozenset({end}),
                     {q: {s: frozenset(t) for s, t in edges.items()} for q, edges in transitions.items()}), log


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


def process(data):
    if not isinstance(data, dict):
        raise InputError("Envíe un objeto JSON.")
    mode = data.get("mode")
    if mode == "regex":
        alphabet = alphabet_from(data.get("alphabet"))
        a, construction = thompson(data.get("expression"), alphabet)
    elif mode == "manual":
        a = automaton_from(data.get("automaton"))
        construction = ["Se registran los componentes ingresados sin cambiar sus nombres."]
    else:
        raise InputError("Seleccione la modalidad regex o manual.")
    kind, reasons = classify(a)

    def stage(key, title, automaton, steps, mapping=None, **extra):
        return {"id": key, "title": title, "automaton": automaton.to_dict(),
                "steps": steps, "mapping": mapping or {q: [q] for q in automaton.states}, **extra}

    stages = [stage("input", "Construcción y clasificación" if mode == "regex" else "Entrada y clasificación",
                    a, construction + [f"Clasificación: {kind}."] + reasons)]
    accessible, trace = reachable(a)
    stages.append(stage("reachable", "Estados accesibles", accessible, trace))
    if classify(accessible)[0].startswith("AFN"):
        dfa, trace, mapping = determinize(accessible)
    else:
        dfa, trace, mapping = complete(accessible)
    stages.append(stage("dfa", "AFD completo", dfa, trace, mapping))
    minimal, trace, groups, partitions = minimize(dfa)
    original = {q: sorted({original for member in members for original in mapping[member]}) for q, members in groups.items()}
    stages.append(stage("minimal", "AFD mínimo", minimal, trace, groups,
                        original_mapping=original, partitions=partitions))
    return {"classification": kind, "stages": stages,
            "summary": {"original_states": len(a.states), "reachable_states": len(accessible.states),
                        "dfa_states": len(dfa.states), "minimal_states": len(minimal.states)}}
