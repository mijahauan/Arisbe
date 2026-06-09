"""The graph-with-holes (schema) node (``src/schema.py``).

Validates the three schema fixtures from
``docs/MATH_FIXTURES_ZFC_PEIRCE_1881.md`` (ZFC Separation/Replacement, Peirce
induction P7).  **Replacement is the acceptance test**: 2 ports, 3 occurrences,
per-occurrence port relabeling (``?y`` vs ``?y2``).  If it instantiates to a
hole-free graph that round-trips, the design holds.
"""

import pytest

from schema import Schema, desugar_holes, instantiate, instance_of_schema
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from eg_navigation import same_graph


# --- the three schema fixtures (⟨name: args⟩ holes; equality = `(= a b)`) ---- #

SEPARATION = (
    "~[ [*p] ~[ [*A] ~[ [*B] "
    "   ~[ [*x] ~[ ~[ (in x B) ~[ (in x A) ⟨phi: x⟩ ] ] "
    "              ~[ (in x A) ⟨phi: x⟩ ~[ (in x B) ] ] ] ] "
    "] ] ]"
)
REPLACEMENT = (
    "~[ [*A] "
    "   ~[ [*x] (in x A) ~[ [*y] ⟨phi: x y⟩ "
    "                       ~[ [*y2] ⟨phi: x y2⟩ ~[ (= y y2) ] ] ] ] "
    "   ~[ [*B] "
    "      ~[ [*xi] (in xi A) ~[ [*yi] (in yi B) ⟨phi: xi yi⟩ ] ] ] ]"
)
INDUCTION_P7 = (
    "~[ [*x] ⟨psi: x⟩ "
    "   ~[ [*u] ⟨psi: u⟩ "
    "      ~[ [*y] ⟨psi: y⟩ (lt y u) ] ] ]"
)


def counts(g):
    return (len(g.V), len(g.E), len(g.Cut))


def rel_count(g, name):
    return sum(1 for r in g.rel.values() if r == name)


# --- desugaring ------------------------------------------------------------- #

def test_desugar_collects_holes_and_arities():
    rewritten, holes = desugar_holes("~[ [*x] ⟨phi: x⟩ ~[ ⟨phi: x⟩ ] ]")
    assert holes == {"phi": 1}
    assert "⟨" not in rewritten and "(phi x)" in rewritten


def test_desugar_rejects_inconsistent_arity():
    with pytest.raises(ValueError, match="inconsistent arity"):
        desugar_holes("⟨phi: x⟩ ⟨phi: x y⟩")


# --- the fixtures parse as schemas ------------------------------------------ #

def test_fixtures_parse_with_expected_holes():
    sep = Schema.from_egif(SEPARATION)
    rep = Schema.from_egif(REPLACEMENT)
    ind = Schema.from_egif(INDUCTION_P7)
    assert sep.holes == {"phi": 1} and len(sep.occurrences("phi")) == 2
    assert rep.holes == {"phi": 2} and len(rep.occurrences("phi")) == 3
    assert ind.holes == {"psi": 1} and len(ind.occurrences("psi")) == 3
    # a schema is NOT complete — it carries holes
    assert not sep.is_complete()


# --- Separation: 1 port, 2 occurrences -------------------------------------- #

def test_separation_instantiates_hole_free():
    sep = Schema.from_egif(SEPARATION)
    # φ(x) := (red x)
    inst = instantiate(sep, "[*x] (red x)", ports=["x"])
    assert not isinstance(inst, Schema)  # single hole filled -> finished graph
    assert "phi" not in set(inst.rel.values())
    assert rel_count(inst, "red") == 2  # both occurrences filled
    reparsed = parse_egif(generate_egif(inst))
    assert same_graph(reparsed, inst)


def test_separation_with_shared_parameter():
    """The doc's sample φ(x) := (in x p): the parameter p is the SAME schema line
    in both occurrences (welded, not α-renamed)."""
    sep = Schema.from_egif(SEPARATION)
    inst = instantiate(
        sep, "[*x] [*pp] (in x pp)", ports=["x"], parameters={"pp": "p"}
    )
    assert not isinstance(inst, Schema)
    # two new (in _ p) edges both reference the schema's single p line
    p_id = next(vid for vid, n in sep.egi.variable_names.items() if n == "p")
    in_on_p = [
        eid for eid, r in inst.rel.items() if r == "in" and inst.nu[eid][1] == p_id
    ]
    assert len(in_on_p) == 2  # shared parameter, one per occurrence
    assert same_graph(parse_egif(generate_egif(inst)), inst)


# --- Replacement: THE acceptance test (2 ports, 3 occ, per-occ relabel) ----- #

def test_replacement_instantiates_hole_free_round_trips():
    rep = Schema.from_egif(REPLACEMENT)
    # φ(x, y) := (maps x y)
    inst = instantiate(rep, "[*x] [*y] (maps x y)", ports=["x", "y"])
    assert not isinstance(inst, Schema)
    assert "phi" not in set(inst.rel.values())
    assert rel_count(inst, "maps") == 3  # all three occurrences filled
    reparsed = parse_egif(generate_egif(inst))
    assert counts(reparsed) == counts(inst)
    assert same_graph(reparsed, inst)


def test_replacement_per_occurrence_ports_differ():
    """The 2nd occurrence binds y2, not y — each occurrence welds to ITS own args."""
    rep = Schema.from_egif(REPLACEMENT)
    inst = instantiate(rep, "[*x] [*y] (maps x y)", ports=["x", "y"])
    # the three maps edges have three distinct second arguments
    second_args = {inst.nu[eid][1] for eid, r in inst.rel.items() if r == "maps"}
    assert len(second_args) == 3


# --- Peirce induction P7: 1 port, 3 occurrences ----------------------------- #

def test_induction_p7_instantiates_hole_free():
    ind = Schema.from_egif(INDUCTION_P7)
    # ψ(n) := (even n)
    inst = instantiate(ind, "[*n] (even n)", ports=["n"])
    assert not isinstance(inst, Schema)
    assert "psi" not in set(inst.rel.values())
    assert rel_count(inst, "even") == 3
    assert same_graph(parse_egif(generate_egif(inst)), inst)


# --- the side-rule + guards ------------------------------------------------- #

def test_instance_of_schema_fills_all_holes():
    rep = Schema.from_egif(REPLACEMENT)
    inst = instance_of_schema(rep, {"phi": ("[*x] [*y] (maps x y)", ["x", "y"])})
    assert "phi" not in set(inst.rel.values())


def test_instance_of_schema_refuses_unfilled_hole():
    sep = Schema.from_egif(SEPARATION)
    with pytest.raises(ValueError, match="unfilled"):
        instance_of_schema(sep, {})


def test_wrong_port_count_raises():
    rep = Schema.from_egif(REPLACEMENT)  # arity 2
    with pytest.raises(ValueError, match="arity"):
        instantiate(rep, "[*x] (maps x x)", ports=["x"])  # only one port


def test_declared_hole_must_occur():
    g = parse_egif("[*x] (red x)")
    with pytest.raises(ValueError, match="does not occur"):
        Schema(g, {"phi": 1})


# --- round-trip contract (III-bis, rule 2) ---------------------------------- #

def test_schema_round_trips_as_native_egif():
    rep = Schema.from_egif(REPLACEMENT)
    back = Schema.from_egif(rep.to_egif())
    assert back.holes == rep.holes
    assert len(back.occurrences("phi")) == len(rep.occurrences("phi"))
    assert same_graph(back.egi, rep.egi)


def test_schema_refuses_first_order_clif_export():
    """A schema must never be exported as a counterfeit first-order sentence."""
    sep = Schema.from_egif(SEPARATION)
    with pytest.raises(ValueError, match="metalevel"):
        sep.to_clif()
    with pytest.raises(ValueError, match="metalevel"):
        sep.to_cgif()
