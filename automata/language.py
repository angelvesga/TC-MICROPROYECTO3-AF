"""Modalidad A: construcción de un AFD a partir de un alfabeto y las reglas del lenguaje.

Las reglas se escriben una por línea, como en los enunciados de clase
(«toda W inicia y finaliza en 0», «la longitud máxima de W es 5»…). Cada regla
se traduce a un AFD pequeño cuyos estados tienen un significado («suma 3»,
«último símbolo 2»…). El autómata del lenguaje es el producto de todos ellos:
un estado combina el estado de cada regla y es final si todas aceptan. Si alguna
regla queda violada se pasa al estado ERROR, que no es final y vuelve a sí mismo.

Sintaxis documentada (una regla por línea; mayúsculas y tildes opcionales; se
admite el prefijo «- toda W», «toda palabra» o «la palabra»; # inicia un comentario):

    inicia en S                 la palabra comienza con un símbolo de S
    finaliza en S               la palabra termina con un símbolo de S
    inicia y finaliza en S      ambas condiciones
    no consecutivos S [excepto xy, zw]
                                dos símbolos seguidos de S están prohibidos, salvo los pares indicados
    no repetidos S              un símbolo de S no puede aparecer dos veces seguidas
    contiene w / no contiene w  la subcadena w debe aparecer / no puede aparecer
    cantidad de x par|impar [si existe]
                                paridad del número de x («si existe» admite que no aparezca)
    longitud maxima n / longitud minima n
    suma maxima n / suma menor a n      (alfabeto numérico)
    x seguido de S [y precedido de T]   cada x va seguido de un símbolo de S (y precedido de T)
    x precedido de T                    cada x va precedido de un símbolo de T
    bloque maximo de x n        x puede repetirse seguido como máximo n veces

S es una lista de símbolos separados por comas, o las palabras «vocal»,
«consonante» o «cualquier simbolo».
"""
from collections import deque
from dataclasses import dataclass
import re
from typing import Callable

from .core import ERROR_STATE, Automaton, InputError, state_names

MAX_RULES = 12
MAX_PRODUCT_STATES = 256
VOWELS = set("aeiou")
DEAD = object()  # Una regla violada: el producto pasa a ERROR.

SYNTAX_HELP = ("Use una de las formas documentadas: inicia en S, finaliza en S, inicia y finaliza en S, "
               "no consecutivos S [excepto xy], no repetidos S, contiene w, no contiene w, "
               "cantidad de x par|impar [si existe], longitud maxima n, longitud minima n, suma maxima n, "
               "suma menor a n, x seguido de S [y precedido de T], x precedido de T, bloque maximo de x n.")


@dataclass
class Rule:
    """AFD de una regla: estado inicial, transición, aceptación y descripción de cada estado."""
    text: str
    start: object
    step: Callable[[object, str], object]
    accept: Callable[[object], bool]
    describe: Callable[[object], str]
    meaning: str


def _plain(text):
    return text.translate(str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU"))


def _symbols(text, alphabet, line):
    """Conjunto S: lista de símbolos o vocal / consonante / cualquier símbolo."""
    raw = text.strip().strip(".").strip()
    word = raw.lower()
    if word in ("vocal", "vocales"):
        found = {s for s in alphabet if s.lower() in VOWELS}
    elif word in ("consonante", "consonantes"):
        found = {s for s in alphabet if s.lower() not in VOWELS}
    elif word in ("cualquier simbolo", "cualquier símbolo", "cualquiera", "cualquier"):
        found = set(alphabet)
    else:
        parts = [p for p in re.split(r"\s*,\s*|\s+o\s+|\s+", raw) if p]
        if not parts:
            raise InputError(f"Regla {line}: falta indicar los símbolos.")
        for p in parts:
            if p not in alphabet:
                raise InputError(f"Regla {line}: «{p}» no pertenece al alfabeto Σ = {{{', '.join(alphabet)}}}.")
        found = set(parts)
    if not found:
        raise InputError(f"Regla {line}: «{raw}» no corresponde a ningún símbolo de Σ.")
    return frozenset(found)


def _symbol(text, alphabet, line):
    value = text.strip()
    if value not in alphabet:
        raise InputError(f"Regla {line}: «{value}» no pertenece al alfabeto Σ = {{{', '.join(alphabet)}}}.")
    return value


def _number(text, line, top=60):
    value = int(text)
    if not 0 <= value <= top:
        raise InputError(f"Regla {line}: el número debe estar entre 0 y {top}.")
    return value


def _show(symbols):
    return ",".join(sorted(symbols))


def _word(text, alphabet, line):
    w = text.strip()
    if not w or any(c not in alphabet for c in w):
        raise InputError(f"Regla {line}: la subcadena «{w}» debe formarse con símbolos de Σ.")
    if len(w) > 12:
        raise InputError(f"Regla {line}: la subcadena admite como máximo 12 símbolos.")
    return w


def _kmp_step(w):
    """Autómata de búsqueda de w: estado = longitud del mayor prefijo de w que es sufijo de lo leído."""
    def step(k, s):
        read = w[:k] + s
        return next(j for j in range(min(len(w), len(read)), -1, -1) if read.endswith(w[:j]))
    return step


def _rule(text, alphabet, line):
    plain = _plain(text).strip()
    plain = re.sub(r"^[-•*]\s*", "", plain)
    plain = re.sub(r"^(toda\s+(palabra|w)\s+|la\s+palabra\s+|cada\s+palabra\s+)", "", plain, flags=re.I)
    plain = re.sub(r"^debe\s+", "", plain, flags=re.I).rstrip(".")
    # «siempre que exista un 2 debe estar seguida de un 0 y precedida de un 1» → «2 seguido de 0 y precedido de 1»
    plain = re.sub(r"^siempre\s+que\s+(?:exista|aparezca|haya)\s+(?:un|una|el|la)?\s*(\S+)\s+", r"\1 ", plain, flags=re.I)
    plain = re.sub(r"(seguid[oa]|precedid[oa])\s+de\s+(?:un|una|el|la)\s+", r"\1 de ", plain, flags=re.I)
    m = lambda pattern: re.fullmatch(pattern, plain, flags=re.I)

    if r := m(r"(?:inicia|empieza|comienza)\s+(?:en|con)\s+(.+?)\s+y\s+(?:finaliza|termina)\s+(?:en|con)\s+(.+)"):
        first = _rule(f"inicia en {r[1]}", alphabet, line)
        last = _rule(f"finaliza en {r[2]}", alphabet, line)
        return Rule(text, (first.start, last.start),
                    lambda q, s: DEAD if (a := first.step(q[0], s)) is DEAD else (a, last.step(q[1], s)),
                    lambda q: first.accept(q[0]) and last.accept(q[1]),
                    lambda q: f"{first.describe(q[0])}; {last.describe(q[1])}",
                    f"{first.meaning} y {last.meaning}")
    if r := m(r"inicia\s+y\s+(?:finaliza|termina)\s+(?:en|con)\s+(.+)"):
        S = _symbols(r[1], alphabet, line)
        first = _rule(f"inicia en {_show(S)}", alphabet, line)
        last = _rule(f"finaliza en {_show(S)}", alphabet, line)
        return Rule(text, (first.start, last.start),
                    lambda q, s: DEAD if (a := first.step(q[0], s)) is DEAD else (a, last.step(q[1], s)),
                    lambda q: first.accept(q[0]) and last.accept(q[1]),
                    lambda q: f"{first.describe(q[0])}; {last.describe(q[1])}",
                    f"la palabra inicia y finaliza con {_show(S)}")
    if r := m(r"(?:inicia|empieza|comienza)\s+(?:en|con)\s+(.+)"):
        S = _symbols(r[1], alphabet, line)
        return Rule(text, "inicio", lambda q, s: q if q == "ok" else ("ok" if s in S else DEAD),
                    lambda q: q == "ok", lambda q: "aún no lee símbolos" if q == "inicio" else f"inició con {_show(S)}",
                    f"el primer símbolo pertenece a {{{_show(S)}}}")
    if r := m(r"(?:finaliza|termina)\s+(?:en|con)\s+(.+)"):
        S = _symbols(r[1], alphabet, line)
        return Rule(text, False, lambda q, s: s in S, lambda q: q,
                    lambda q: f"último símbolo en {{{_show(S)}}}" if q else f"último símbolo fuera de {{{_show(S)}}}",
                    f"el último símbolo pertenece a {{{_show(S)}}}")
    if r := m(r"no\s+consecutiv[oa]s\s+(.+?)(?:\s+excepto\s+(.+))?"):
        S = _symbols(r[1], alphabet, line)
        allowed = set()
        for pair in [p for p in re.split(r"\s*,\s*|\s+", r[2] or "") if p]:
            if len(pair) != 2 or any(c not in alphabet for c in pair):
                raise InputError(f"Regla {line}: cada excepción debe ser un par de símbolos de Σ, como mb.")
            allowed.add(pair)
        return Rule(text, "", lambda q, s: DEAD if q in S and s in S and q + s not in allowed else (s if s in S else ""),
                    lambda q: True, lambda q: f"último símbolo {q}" if q else "último símbolo fuera del conjunto",
                    f"no hay dos símbolos seguidos de {{{_show(S)}}}" + (f", salvo {', '.join(sorted(allowed))}" if allowed else ""))
    if r := m(r"no\s+repetid[oa]s\s+(.+)"):
        S = _symbols(r[1], alphabet, line)
        return Rule(text, "", lambda q, s: DEAD if s in S and q == s else s, lambda q: True,
                    lambda q: f"último símbolo {q}" if q else "sin símbolos leídos",
                    f"ningún símbolo de {{{_show(S)}}} aparece dos veces seguidas")
    if r := m(r"no\s+contiene\s+(\S+)"):
        w = _word(r[1], alphabet, line)
        step = _kmp_step(w)
        return Rule(text, 0, lambda k, s: DEAD if (n := step(k, s)) == len(w) else n, lambda k: True,
                    lambda k: f"lleva «{w[:k]}» de {w}" if k else f"sin prefijo de {w}", f"la subcadena {w} no aparece")
    if r := m(r"contiene\s+(\S+)"):
        w = _word(r[1], alphabet, line)
        step = _kmp_step(w)
        return Rule(text, 0, lambda k, s: k if k == len(w) else step(k, s), lambda k: k == len(w),
                    lambda k: "ya contiene " + w if k == len(w) else (f"lleva «{w[:k]}»" if k else f"sin prefijo de {w}"),
                    f"la subcadena {w} aparece")
    if r := m(r"(?:el\s+)?(?:cantidad|numero)\s+de\s+(\S+?)(?:'?s)?\s+(?:debe\s+ser\s+|es\s+)?(par|impar)(\s+si\s+existe)?"):
        x = _symbol(r[1], alphabet, line)
        odd, optional = r[2].lower() == "impar", bool(r[3])
        return Rule(text, (0, False), lambda q, s: ((q[0] + (s == x)) % 2, q[1] or s == x),
                    lambda q: (q[0] == 1 if odd else q[0] == 0) or (optional and not q[1]),
                    lambda q: f"cantidad de {x} {'impar' if q[0] else 'par'}" + ("" if q[1] else " (aún no aparece)"),
                    f"la cantidad de {x} es {'impar' if odd else 'par'}" + (" cuando aparece" if optional else ""))
    of_word = r"(?:de\s+(?:la\s+palabra|w)\s+)?(?:es\s+|debe\s+ser\s+)?"
    if r := m(r"(?:la\s+)?longitud\s+" + of_word + r"(maxim[ao]|minim[ao])\s+" + of_word
              + r"(?:de\s+)?(\d+)(?:\s+(?:caracteres|simbolos))?"):
        n = _number(r[2], line)
        if r[1].lower().startswith("max"):
            return Rule(text, 0, lambda k, s: DEAD if k + 1 > n else k + 1, lambda k: True,
                        lambda k: f"longitud {k}", f"la longitud es como máximo {n}")
        return Rule(text, 0, lambda k, s: min(k + 1, n), lambda k: k >= n,
                    lambda k: f"longitud {k}" if k < n else f"longitud ≥ {n}", f"la longitud es como mínimo {n}")
    if r := m(r"(?:la\s+)?suma\s+" + of_word + r"(maxim[ao]|menor\s+a|menor\s+que)\s+(?:de\s+)?(\d+)"):
        if any(not s.isdigit() for s in alphabet):
            raise InputError(f"Regla {line}: la suma solo se admite si todos los símbolos de Σ son dígitos.")
        n = _number(r[2], line, 200)
        top = n if r[1].lower().startswith("max") else n - 1
        if top < 0:
            raise InputError(f"Regla {line}: ninguna palabra tiene suma menor a 0.")
        return Rule(text, 0, lambda k, s: DEAD if k + int(s) > top else k + int(s), lambda k: True,
                    lambda k: f"suma {k}", f"la suma de los símbolos es como máximo {top}")
    if r := m(r"(\S+)\s+(?:debe\s+estar\s+|va\s+)?seguid[oa]\s+de\s+(.+?)(?:\s+y\s+precedid[oa]\s+de\s+(.+))?"):
        x = _symbol(r[1], alphabet, line)
        S = _symbols(r[2], alphabet, line)
        after = Rule(text, False, lambda q, s: DEAD if q and s not in S else s == x, lambda q: not q,
                     lambda q: f"espera {{{_show(S)}}} después de {x}" if q else "sin pendientes",
                     f"cada {x} va seguido de {{{_show(S)}}}")
        if not r[3]:
            return after
        before = _rule(f"{x} precedido de {r[3]}", alphabet, line)
        return Rule(text, (after.start, before.start),
                    lambda q, s: DEAD if DEAD in (a := after.step(q[0], s), b := before.step(q[1], s)) else (a, b),
                    lambda q: after.accept(q[0]) and before.accept(q[1]),
                    lambda q: f"{after.describe(q[0])}; {before.describe(q[1])}",
                    f"{after.meaning} y precedido de {r[3].strip()}")
    if r := m(r"(\S+)\s+(?:debe\s+estar\s+|va\s+)?precedid[oa]\s+de\s+(.+)"):
        x = _symbol(r[1], alphabet, line)
        T = _symbols(r[2], alphabet, line)
        return Rule(text, False, lambda q, s: DEAD if s == x and not q else s in T, lambda q: True,
                    lambda q: f"último símbolo en {{{_show(T)}}}" if q else f"último símbolo fuera de {{{_show(T)}}}",
                    f"cada {x} va precedido de {{{_show(T)}}}")
    if r := m(r"bloque\s+maximo\s+de\s+(\S+?)(?:'?s)?\s+(\d+)"):
        x = _symbol(r[1], alphabet, line)
        n = _number(r[2], line)
        return Rule(text, 0, lambda k, s: (DEAD if k + 1 > n else k + 1) if s == x else 0, lambda k: True,
                    lambda k: f"{k} {x} seguidos", f"{x} aparece seguido como máximo {n} veces")
    raise InputError(f"Regla {line}: no se reconoce «{text.strip()}». {SYNTAX_HELP}")


def parse_rules(text, alphabet):
    if not isinstance(text, str):
        raise InputError("Escriba las reglas del lenguaje, una por línea.")
    rules = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        rules.append(_rule(line, alphabet, number))
    if not rules:
        raise InputError("Escriba al menos una regla del lenguaje, por ejemplo: inicia en a.")
    if len(rules) > MAX_RULES:
        raise InputError(f"Se admiten como máximo {MAX_RULES} reglas.")
    return rules


def build_from_rules(alphabet, text):
    """Construye el AFD del lenguaje por producto de los AFD de cada regla."""
    rules = parse_rules(text, alphabet)
    log = [f"Σ = {{{', '.join(alphabet)}}}. Se construye un AFD por regla y luego su producto."]
    for i, rule in enumerate(rules, 1):
        log.append(f"Regla {i} «{rule.text}»: {rule.meaning}.")
    start = tuple(rule.start for rule in rules)
    order, index, pending = [start], {start: 0}, deque([start])
    edges, broken, dead_used = {}, {}, False
    while pending:
        q = pending.popleft()
        for s in alphabet:
            nxt = tuple(rule.step(c, s) for rule, c in zip(rules, q))
            if any(c is DEAD for c in nxt):
                edges[(q, s)] = DEAD
                broken[(q, s)] = next(i for i, c in enumerate(nxt, 1) if c is DEAD)
                dead_used = True
                continue
            if nxt not in index:
                if len(index) >= MAX_PRODUCT_STATES:
                    raise InputError(f"Las reglas generan más de {MAX_PRODUCT_STATES} estados. "
                                     "Reduzca las longitudes o sumas máximas; no se entrega un resultado parcial.")
                index[nxt] = len(order)
                order.append(nxt)
                pending.append(nxt)
            edges[(q, s)] = nxt
    names = state_names(len(order))
    name = {q: names[i] for i, q in enumerate(order)}
    states = list(names) + ([ERROR_STATE] if dead_used else [])
    target = lambda t: ERROR_STATE if t is DEAD else name[t]
    transitions = {name[q]: {s: frozenset({target(edges[(q, s)])}) for s in alphabet} for q in order}
    if dead_used:
        transitions[ERROR_STATE] = {s: frozenset({ERROR_STATE}) for s in alphabet}
    finals = frozenset(name[q] for q in order if all(r.accept(c) for r, c in zip(rules, q)))
    mapping = {name[q]: [f"R{i}: {r.describe(c)}" for i, (r, c) in enumerate(zip(rules, q), 1)] for q in order}
    if dead_used:
        mapping[ERROR_STATE] = []
    log.append(f"Estado inicial q0 = {name[start]}: ninguna regla ha leído símbolos.")
    shown = 0
    for q in order:
        for s in alphabet:
            if shown < 150:
                t = edges[(q, s)]
                if t is DEAD:
                    k = broken[(q, s)]
                    why = f"incumple la regla {k}: {rules[k - 1].meaning}"
                else:
                    why = "; ".join(r.describe(c) for r, c in zip(rules, t))
                log.append(f"{name[q]},{s}→{target(t)}  ({why}).")
            shown += 1
    if shown > 150:
        log.append(f"… {shown - 150} transiciones más en la tabla de transición.")
    log.append(f"Son finales los estados en que todas las reglas aceptan: Qt = {{{', '.join(n for n in states if n in finals)}}}.")
    if dead_used:
        log.append(f"{ERROR_STATE} recibe toda palabra que viola alguna regla; no es final y vuelve a sí mismo.")
    log.append(f"Resultado: AFD de {len(states)} estados.")
    return Automaton(tuple(states), tuple(alphabet), name[start], finals, transitions), log, mapping
