"""Pruebas del motor; cada función corresponde a una fila de la matriz."""
import copy
import json
from pathlib import Path
import random
import re
import pytest
from automata.core import (InputError, alphabet_from, automaton_from, classify,
                          closure, complete, determinize, minimize, process, simulate, thompson)
from tests.oracles import accepts, assert_equivalent_and_minimal, words

ROOT = Path(__file__).resolve().parents[1]


def example(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


def pipeline(payload):
    result = process(payload)
    stages = [automaton_from(s["automaton"], 256, generated=True) for s in result["stages"]]
    for word in words(stages[0].alphabet):
        expected = accepts(stages[0], word)
        for stage in stages:
            assert simulate(stage, word)["accepted"] == expected, word
    assert_equivalent_and_minimal(stages[-2], stages[-1])
    return result, stages


def test_suffix_abb():
    """RF-02,03,06,09,12: abb produce cuatro estados y reconoce exactamente el sufijo."""
    result, stages = pipeline(example("01_expresion_abb.json"))
    assert len(stages[-1].states) == 4
    for word in words("ab", 8):
        assert accepts(stages[-1], word) == word.endswith("abb")
    assert result["classification"] == "AFND-ε"
    assert result["language"][:3] == ["abb", "aabb", "babb"]


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
    assert any(set(group) == {"B", "C"} for group in result["stages"][-1]["mapping"].values())
    assert any("omite" in step for step in result["stages"][2]["steps"])
    assert result["stages"][-1]["mapping"]["B"] == ["B", "C"]


def test_regex_precedence():
    """RF-02,03: estrella, concatenación, unión y paréntesis respetan la precedencia."""
    for expression in ["a|bb*", "(ab)*", "a(b|a)*b", "(a|b)*", "ab|ba", "a**", "(a|ε)b", "∅|a"]:
        _, stages = pipeline({"mode":"regex", "alphabet":["a","b"], "expression":expression})
        python_regex = expression.replace("ε", "").replace("∅", "(?!)").replace("**", "*")
        for word in words("ab", 6):
            assert accepts(stages[-1], word) == bool(re.fullmatch(python_regex, word))


def test_empty_word_language():
    """RF-03,09,12: ε acepta solo cadena vacía; ∅ no acepta ninguna cadena."""
    for expression, count in [("ε", 2), ("∅", 1), ("∅*", 2), ("a∅", 1), ("ε*", 2)]:
        _, stages = pipeline({"mode":"regex", "alphabet":["a"], "expression":expression})
        assert len(stages[-1].states) == count
        assert accepts(stages[-1], "") == (expression in ["ε", "∅*", "ε*"])
        assert not accepts(stages[-1], "a")


def test_epsilon_cycle():
    """RF-05,06,12: ciclos ε terminan y reconocen aceptación sin consumir entrada."""
    payload = {"mode":"manual", "automaton":{"states":["p","q"], "alphabet":["a"], "initial":"p", "finals":["q"],
               "transitions":{"p":{"ε":["q"]}, "q":{"ε":["p"], "a":["q"]}}}}
    result, stages = pipeline(payload)
    assert result["classification"] == "AFND-ε"
    assert closure(stages[0], {"p"}) == {"p", "q"}
    assert len(stages[-1].states) == 1
    assert accepts(stages[-1], "aaaa")


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
    """RF-01: rechaza duplicados, operadores reservados, espacios y símbolos múltiples."""
    for bad in [None, [], "ab", ["a", "a"], ["ab"], [" "], ["ε"], ["∅"], ["|"], ["*"], ["("], [","] , ["\\"], [1], list("abcdefghijklm")]:
        with pytest.raises(InputError):
            alphabet_from(bad)
    assert alphabet_from(["0", "1"]) == ("0", "1")
    assert alphabet_from(["ñ", "🙂"]) == ("ñ", "🙂")


def test_regex_validation():
    """RF-02: expresiones inválidas y símbolos externos producen errores con posición."""
    for bad in ["", None, "a|", "|a", "()", "(a", "a)", "*a", "a b", "c", "a||b", "a"*121]:
        with pytest.raises(InputError):
            process({"mode":"regex", "alphabet":["a","b"], "expression":bad})
    with pytest.raises(InputError, match="posición 2"):
        process({"mode":"regex", "alphabet":["a"], "expression":"ab"})


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
    _, stages = pipeline(example("01_expresion_abb.json"))
    for bad in ["abc", "ε", " ", None, "a"*1001]:
        with pytest.raises(InputError):
            simulate(stages[-1], bad)
    assert simulate(stages[-1], "aabb")["path"][-1]["position"] == 4


def test_resource_limits():
    """RF-01,04,06: límites explícitos evitan explosión de estados sin resultados truncados."""
    with pytest.raises(InputError):
        automaton_from({"states":[f"q{i}" for i in range(81)], "alphabet":["a"],"initial":"q0","finals":[],"transitions":{}})
    # El octavo símbolo desde el final es a: requiere 256 estados deterministas.
    with pytest.raises(InputError, match="128"):
        process({"mode":"regex","alphabet":["a","b"],"expression":"(a|b)*a"+"(a|b)"*7})


def test_traces_mapping_stability():
    """RF-10,11,13: etapas consultables, trazas, particiones y nombres reproducibles."""
    payload = example("01_expresion_abb.json")
    before = copy.deepcopy(payload)
    result = process(payload)
    assert result == process(payload)
    assert payload == before
    assert [s["id"] for s in result["stages"]] == ["input", "reachable", "dfa", "minimal"]
    for stage in result["stages"]:
        assert stage["steps"]
        assert set(stage["mapping"]) == set(stage["automaton"]["states"])
    assert result["stages"][-1]["partitions"][-1] == result["stages"][-1]["partitions"][-2]
    assert result["stages"][0]["automaton"]["states"][:3] == ["A", "B", "C"]
    assert result["stages"][2]["automaton"]["initial"] == "ABCEGI"
    assert result["stages"][-1]["mapping"]["ABCEGI"] == ["ABCEGI", "BCDEGHI"]


def test_generated_automata():
    """RF-06,09,12: 30 AFN aleatorios reproducibles preservan lenguaje y generan AFD mínimos."""
    rng = random.Random(202602)
    for _ in range(30):
        states = [f"q{i}" for i in range(rng.randint(1, 5))]
        transitions = {q:{s:[t for t in states if rng.random()<.22] for s in ["a","b","ε"]} for q in states}
        pipeline({"mode":"manual","automaton":{"states":states,"alphabet":["a","b"],"initial":states[0],
                 "finals":[q for q in states if rng.random()<.5],"transitions":transitions}})


def test_already_minimal_and_roundtrip():
    """RF-09,11: minimizar dos veces conserva el lenguaje y el número mínimo de estados."""
    _, stages = pipeline(example("01_expresion_abb.json"))
    minimum, _, _, _ = minimize(stages[-1])
    assert len(minimum.states) == len(stages[-1].states)
    assert_equivalent_and_minimal(stages[-1], minimum)
    assert automaton_from(minimum.to_dict(), generated=True).to_dict() == minimum.to_dict()


def test_class_notation():
    """RF-03,05,06,10: notación de clase: estados A, B, C…; X,a→Y; subconjuntos concatenados; ERROR; L = {…}."""
    a, log = thompson("ab", ("a", "b"))
    assert a.states == ("A", "B", "C", "D") and a.initial == "A" and a.finals == {"D"}
    assert "Fragmento a: A,a→B." in log
    big, _ = thompson("a" * 14, ("a",))
    assert big.states[0] == "q0" and len(big.states) == 28
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
