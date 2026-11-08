"""Oráculos independientes del motor para validar lenguaje y minimalidad."""
from collections import deque
from itertools import product, combinations


def words(alphabet, limit=6):
    for length in range(limit + 1):
        yield from ("".join(w) for w in product(alphabet, repeat=length))


def accepts(a, word):
    """Exploración de configuraciones (estado, posición), sin closure del motor."""
    pending, seen = [(a.initial, 0)], set()
    while pending:
        q, i = pending.pop()
        if (q, i) in seen:
            continue
        seen.add((q, i))
        if i == len(word) and q in a.finals:
            return True
        pending.extend((t, i) for t in a.transitions.get(q, {}).get("ε", ()))
        if i < len(word):
            pending.extend((t, i + 1) for t in a.transitions.get(q, {}).get(word[i], ()))
    return False


def distinguish(a, start_a, b, start_b):
    """Testigo más corto por BFS del producto de dos AFD completos."""
    pending = deque([(start_a, start_b, "")])
    seen = {(start_a, start_b)}
    while pending:
        p, q, word = pending.popleft()
        if (p in a.finals) != (q in b.finals):
            return word
        for s in a.alphabet:
            left = next(iter(a.transitions[p][s]))
            right = next(iter(b.transitions[q][s]))
            if (left, right) not in seen:
                seen.add((left, right))
                pending.append((left, right, word + s))
    return None


def assert_equivalent_and_minimal(dfa, minimum):
    assert distinguish(dfa, dfa.initial, minimum, minimum.initial) is None
    for left, right in combinations(minimum.states, 2):
        assert distinguish(minimum, left, minimum, right) is not None, (left, right)
