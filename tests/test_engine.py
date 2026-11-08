"""Pruebas del motor; cada función corresponde a una fila de la matriz."""
import copy
import json
from pathlib import Path
import random
import pytest
from automata.core import (InputError, alphabet_from, automaton_from, classify,
                          closure, minimize, process, simulate)
from tests.oracles import accepts, assert_equivalent_and_minimal, words

ROOT = Path(__file__).resolve().parents[1]


def example(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


def pipeline(payload, predicate=None, limit=6):
    """Procesa la entrada y verifica que todas las etapas acepten el mismo lenguaje."""
    result = process(payload)
    stages = [automaton_from(s["automaton"], 256, generated=True) for s in result["stages"]]
    for word in words(stages[0].alphabet, limit):
        expected = accepts(stages[0], word)
        if predicate is not None:
            assert expected == predicate(word), (payload.get("rules"), word)
        for stage in stages:
            assert simulate(stage, word)["accepted"] == expected, word
    assert_equivalent_and_minimal(stages[-2], stages[-1])
    return result, stages


def vowels_rule(w):
    """Σ = {a,e,i,p}: inicia y finaliza en a; vocales consecutivas no pueden repetirse."""
    return bool(w) and w[0] == "a" and w[-1] == "a" and not any(x == y and x in "aei" for x, y in zip(w, w[1:]))


def digits_rule(w):
    """Σ = {0,1,2}: inicia y finaliza en 0; cada 2 precedido de 1 y seguido de 0; suma ≤ 6; longitud ≤ 5."""
    twos_ok = all(0 < i < len(w) - 1 and w[i - 1] == "1" and w[i + 1] == "0" for i, c in enumerate(w) if c == "2")
    return bool(w) and w[0] == "0" and w[-1] == "0" and twos_ok and sum(map(int, w)) <= 6 and len(w) <= 5


def consonants_rule(w):
    """Σ = {a,e,m,b,p}: finaliza en vocal; sin consonantes consecutivas salvo mb y mp; longitud ≤ 6."""
    pairs_ok = all(not (x in "mbp" and y in "mbp") or x + y in ("mb", "mp") for x, y in zip(w, w[1:]))
    return bool(w) and w[-1] in "ae" and pairs_ok and len(w) <= 6


def test_language_vowels():
    """RF-01,02,03,09,12: lenguaje de clase Σ={a,e,i,p}: inicia y finaliza en a, vocales seguidas no se repiten."""
    result, stages = pipeline(example("01_lenguaje_vocales.json"), vowels_rule)
    assert result["classification"] == "AFD"
    assert result["language"][:4] == ["a", "aea", "aia", "apa"]
    minimum = stages[-1]
    assert minimum.initial == "A" and "ERROR" in minimum.states
    for word, expected in [("a", True), ("apa", True), ("aeia", True), ("aeeia", False), ("aa", False)]:
        assert simulate(minimum, word)["accepted"] == expected


def test_language_digits():
    """RF-02,03,09,12: lenguaje de clase Σ={0,1,2}: 2 precedido de 1 y seguido de 0, suma ≤ 6, longitud ≤ 5."""
    result, stages = pipeline(example("05_lenguaje_digitos.json"), digits_rule)
    minimum = stages[-1]
    assert minimum.states[:2] == ("A", "B") and minimum.states[-1] == "ERROR"
    assert simulate(minimum, "01120")["accepted"] and simulate(minimum, "01110")["accepted"]
    assert not simulate(minimum, "0210")["accepted"]


def test_language_consonants():
    """RF-02,03,09,12: lenguaje de clase Σ={a,e,m,b,p}: finaliza en vocal, consonantes seguidas solo mb y mp."""
    _, stages = pipeline(example("06_lenguaje_consonantes.json"), consonants_rule)
    for word in ["a", "e", "aeaeae", "ampa", "mapa"]:
        assert simulate(stages[-1], word)["accepted"]
    assert not simulate(stages[-1], "mbpa")["accepted"]


def test_rule_kinds():
    """RF-02,03: cada forma documentada de regla reconoce exactamente su lenguaje."""
    cases = [
        (["a", "b", "c"], "inicia en a,b", lambda w: w[:1] in ("a", "b") and bool(w)),
        (["a", "b"], "finaliza en b", lambda w: w.endswith("b")),
        (["a", "b"], "contiene ab", lambda w: "ab" in w),
        (["a", "b"], "no contiene aba", lambda w: "aba" not in w),
        (["a", "b"], "cantidad de a impar", lambda w: w.count("a") % 2 == 1),
        (["a", "b"], "el numero de a debe ser par", lambda w: w.count("a") % 2 == 0),
        (["a", "b"], "cantidad de a impar si existe", lambda w: w.count("a") == 0 or w.count("a") % 2 == 1),
        (["a", "b"], "longitud minima 3", lambda w: len(w) >= 3),
        (["a", "b"], "la longitud maxima de W debe ser de 4", lambda w: len(w) <= 4),
        (["a", "b"], "bloque maximo de a 2", lambda w: "aaa" not in w),
        (["a", "b"], "b precedido de a", lambda w: all(i > 0 and w[i - 1] == "a" for i, c in enumerate(w) if c == "b")),
        (["a", "b"], "a seguido de b", lambda w: all(i + 1 < len(w) and w[i + 1] == "b" for i, c in enumerate(w) if c == "a")),
        (["a", "b", "c"], "no consecutivos a,b", lambda w: not any(x in "ab" and y in "ab" for x, y in zip(w, w[1:]))),
        (["a", "b", "c"], "no repetidos a,b", lambda w: not any(x == y and x in "ab" for x, y in zip(w, w[1:]))),
        (["0", "1", "2"], "suma menor a 4", lambda w: sum(map(int, w)) < 4),
        (["a", "e", "p"], "- toda W inicia con cualquier símbolo y finaliza en vocal # comentario",
         lambda w: bool(w) and w[-1] in "ae"),
    ]
    for sigma, rules, predicate in cases:
        result, _ = pipeline({"mode": "language", "alphabet": sigma, "rules": rules}, predicate)
        assert result["classification"] == "AFD"


def test_manual_nfa():
    """RF-04,05,06: el AFND de clase da exactamente la tabla AFD de la docente (A, B, BC, D, BCD, CD, ABCD, AD, AB)."""
    result, stages = pipeline(example("02_afnd_clase.json"))
    assert result["classification"] == "AFND"
    assert any("B,0→B,C" in step and "MÁS" in step for step in result["stages"][0]["steps"])
    expected = {"A": ("B", "A"), "B": ("BC", "D"), "BC": ("BCD", "CD"), "D": ("A", "B"), "CD": ("AD", "BC"),
                "BCD": ("ABCD", "BCD"), "AD": ("AB", "AB"), "ABCD": ("ABCD", "ABCD"), "AB": ("BC", "AD")}
    dfa = result["stages"][2]["automaton"]
    assert set(dfa["states"]) == set(expected) and dfa["initial"] == "A"
    assert {q: (dfa["transitions"][q]["0"][0], dfa["transitions"][q]["1"][0]) for q in dfa["states"]} == expected
    assert set(dfa["finals"]) == {"A", "AD", "ABCD", "AB"}
    assert any(step.startswith("BC,0→BCD") and "B,0→B,C · C,0→D" in step for step in result["stages"][2]["steps"])


def test_equivalent_unreachable():
    """RF-07,09: elimina D (inaccesible) y fusiona B,C en B; el AFD mínimo tiene dos estados."""
    result, stages = pipeline(example("03_afd_equivalentes.json"))
    assert result["classification"] == "AFD"
    assert "D" not in stages[1].states
    assert len(stages[-1].states) == 2
    assert any("omite" in step for step in result["stages"][2]["steps"])
    assert result["stages"][-1]["mapping"]["B"] == ["B", "C"]


def test_epsilon_cycle():
    """RF-05,06,12: la API también admite transiciones ε; los ciclos ε terminan."""
    payload = {"mode":"manual", "automaton":{"states":["p","q"], "alphabet":["a"], "initial":"p", "finals":["q"],
               "transitions":{"p":{"ε":["q"]}, "q":{"ε":["p"], "a":["q"]}}}}
    result, stages = pipeline(payload)
    assert result["classification"] == "AFND-ε"
    assert closure(stages[0], {"p"}) == {"p", "q"}
    assert len(stages[-1].states) == 1


def test_no_finals_and_all_finals():
    """RF-09: particiones vacías no fallan; lenguajes vacío y universal tienen un estado."""
    for finals in [[], ["p", "q"]]:
        _, stages = pipeline({"mode":"manual", "automaton":{"states":["p","q"],"alphabet":["a"],"initial":"p","finals":finals,
                             "transitions":{"p":{"a":["q"]},"q":{"a":["p"]}}}})
        assert len(stages[-1].states) == 1
        assert accepts(stages[-1], "aaa") == bool(finals)


def test_partial_sink():
    """RF-05,09: un AFD incompleto sigue siendo determinista y se completa con el estado ERROR sin colisiones."""
    payload = {"mode":"manual","automaton":{"states":["ERROR","q"],"alphabet":["a","b"],"initial":"ERROR","finals":["q"],
               "transitions":{"ERROR":{"a":["q"]}}}}
    result, stages = pipeline(payload)
    assert result["classification"] == "AFD incompleto"
    assert "ERROR_1" in stages[2].states
    assert result["stages"][2]["mapping"]["ERROR_1"] == []


def test_alphabet_validation():
    """RF-01: rechaza duplicados, símbolos reservados, espacios y símbolos múltiples."""
    for bad in [None, [], "ab", ["a", "a"], ["ab"], [" "], ["ε"], ["∅"], ["|"], ["*"], ["("], [","], ["#"], ["\\"], [1], list("abcdefghijklm")]:
        with pytest.raises(InputError):
            alphabet_from(bad)
    assert alphabet_from(["0", "1"]) == ("0", "1")
    assert alphabet_from(["ñ", "🙂"]) == ("ñ", "🙂")


def test_rule_validation():
    """RF-02: reglas desconocidas o con símbolos fuera de Σ producen errores con el número de regla."""
    sigma = ["a", "b"]
    for bad, message in [("", "al menos una regla"), (None, "reglas"), ("hola mundo", "Regla 1: no se reconoce"),
                         ("inicia en a\ninicia en x", "Regla 2: «x» no pertenece"), ("suma maxima 3", "dígitos"),
                         ("no consecutivos a,b excepto abc", "par de símbolos"), ("longitud maxima 99", "entre 0 y 60"),
                         ("cantidad de c par", "«c» no pertenece"), ("contiene ac", "símbolos de Σ"),
                         ("\n".join(["inicia en a"] * 13), "12 reglas")]:
        with pytest.raises(InputError, match=message):
            process({"mode": "language", "alphabet": sigma, "rules": bad})


def test_manual_validation():
    """RF-04: valida nombres, inicial, finales, destinos, símbolos y estructura de transiciones."""
    original = example("02_afnd_clase.json")["automaton"]
    changes = [{"states":[]}, {"states":["A","A"]}, {"states":["<script>"]}, {"states":[3]},
               {"initial":"missing"}, {"initial":[]}, {"finals":["missing"]}, {"finals":["A","A"]},
               {"transitions":[]}, {"transitions":{"missing":{}}}, {"transitions":{"A":{"c":["B"]}}},
               {"transitions":{"A":{"0":["missing"]}}}, {"transitions":{"A":{"0":"B"}}},
               {"transitions":{"A":{"0":["B","B"]}}}]
    for change in changes:
        with pytest.raises(InputError):
            automaton_from({**original, **change})


def test_simulation_validation():
    """RF-12: rechaza símbolos externos y distingue campo vacío de ε literal."""
    _, stages = pipeline(example("01_lenguaje_vocales.json"))
    for bad in ["abc", "ε", " ", None, "a"*1001]:
        with pytest.raises(InputError):
            simulate(stages[-1], bad)
    assert simulate(stages[-1], "apa")["path"][-1]["position"] == 3


def test_resource_limits():
    """RF-01,04,06: límites explícitos evitan explosión de estados sin resultados truncados."""
    with pytest.raises(InputError):
        automaton_from({"states":[f"q{i}" for i in range(81)], "alphabet":["a"],"initial":"q0","finals":[],"transitions":{}})
    # «El octavo símbolo desde el final es a»: su AFD necesita 256 estados.
    states = [f"q{i}" for i in range(9)]
    transitions = {"q0": {"a": ["q0", "q1"], "b": ["q0"]}, **{f"q{i}": {"a": [f"q{i+1}"], "b": [f"q{i+1}"]} for i in range(1, 8)}}
    with pytest.raises(InputError, match="128"):
        process({"mode":"manual","automaton":{"states":states,"alphabet":["a","b"],"initial":"q0","finals":["q8"],"transitions":transitions}})
    with pytest.raises(InputError, match="256"):
        process({"mode":"language","alphabet":["0","1"],"rules":"longitud maxima 60\nsuma maxima 60"})


def test_traces_mapping_stability():
    """RF-10,11,13: etapas consultables, trazas, particiones y nombres reproducibles."""
    payload = example("05_lenguaje_digitos.json")
    before = copy.deepcopy(payload)
    result = process(payload)
    assert result == process(payload)
    assert payload == before
    assert [s["id"] for s in result["stages"]] == ["input", "reachable", "dfa", "minimal"]
    for stage in result["stages"]:
        assert stage["steps"]
        assert set(stage["mapping"]) == set(stage["automaton"]["states"])
    assert result["stages"][-1]["partitions"][-1] == result["stages"][-1]["partitions"][-2]
    steps = result["stages"][0]["steps"]
    assert any(step.startswith("Regla 2 «2 seguido de 0 y precedido de 1»") for step in steps)
    assert any("→ERROR  (incumple la regla 2: cada 2 va seguido de {0} y precedido de 1)" in step for step in steps)
    assert all(line.startswith("R") for members in result["stages"][0]["mapping"].values() for line in members)


def test_generated_automata():
    """RF-06,09,12: 30 AFND aleatorios reproducibles preservan lenguaje y generan AFD mínimos."""
    rng = random.Random(202602)
    for _ in range(30):
        states = [f"q{i}" for i in range(rng.randint(1, 5))]
        transitions = {q:{s:[t for t in states if rng.random()<.22] for s in ["a","b","ε"]} for q in states}
        pipeline({"mode":"manual","automaton":{"states":states,"alphabet":["a","b"],"initial":states[0],
                 "finals":[q for q in states if rng.random()<.5],"transitions":transitions}})


def test_already_minimal_and_roundtrip():
    """RF-09,11: minimizar dos veces conserva el lenguaje y el número mínimo de estados."""
    _, stages = pipeline(example("05_lenguaje_digitos.json"))
    minimum, _, _, _ = minimize(stages[-1])
    assert len(minimum.states) == len(stages[-1].states)
    assert_equivalent_and_minimal(stages[-1], minimum)
    assert automaton_from(minimum.to_dict(), generated=True).to_dict() == minimum.to_dict()


def test_class_notation():
    """RF-03,05,06,10: notación de clase: estados A, B, C…; X,a→Y; subconjuntos concatenados; ERROR; L = {…}."""
    built = process({"mode":"language","alphabet":["a","b"],"rules":"inicia en a"})
    first = built["stages"][0]["automaton"]
    assert first["states"] == ["A", "B", "ERROR"] and first["initial"] == "A" and first["finals"] == ["B"]
    assert "A,b→ERROR  (incumple la regla 1: el primer símbolo pertenece a {a})." in built["stages"][0]["steps"]
    kind, reasons = classify(automaton_from(example("02_afnd_clase.json")["automaton"]))
    assert kind == "AFND" and reasons == ["B,0→B,C: el símbolo 0 va a MÁS de un estado."]
    result = process({"mode":"manual","automaton":{"states":["A","B"],"alphabet":["0","1"],"initial":"A","finals":["B"],
                      "transitions":{"A":{"0":["A","B"]}}}})
    dfa = result["stages"][2]["automaton"]
    assert dfa["states"] == ["A", "AB", "ERROR"] and dfa["transitions"]["A"]["1"] == ["ERROR"]
    assert "A,1→ERROR   ⟸ A,1→error." in result["stages"][2]["steps"]
    assert result["language"][:2] == ["0", "00"]
    # {A,B} y el estado manual {AB} se llamarían AB: el segundo recibe un sufijo.
    clash = process({"mode":"manual","automaton":{"states":["A","AB","B"],"alphabet":["a","b"],"initial":"A",
                     "finals":["B"],"transitions":{"A":{"a":["A","B"],"b":["AB"]},"AB":{},"B":{}}}})
    names = clash["stages"][2]["automaton"]["states"]
    assert len(names) == len(set(names)) and {"AB", "AB_2"} <= set(names)
