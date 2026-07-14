"""**Mathematics from the sheet** — the arithmetic ladder + the character of a proof
(docs/MATHEMATICS_FROM_THE_SHEET.md; `src/peirce_arithmetic.py`,
`src/proof_character.py`).

The claim under test is pedagogical as much as formal: each rung teaches one device
of the graphs and *earns* one piece of mathematics with it. So the tests walk the
rungs — the order draws, the numeral folds conservatively, two drawn laws grow the
addition table, `2 + 3 = 5` is read off the diagram — and then pin the two results
that carry the weight:

* **Peirce's corollarial/theorematic distinction is decidable from the chain.** A
  derivation is theorematic exactly when it needs INSERTION — the one rule that can
  scribe what the premisses do not contain (the auxiliary line). Checked against the
  *real* corpus proofs: Peirce's Law and Leibniz's Praeclarum need it; modus ponens
  and de Morgan do not.
* **A doc that teaches EGIF must teach EGIF that parses.** The math docs' code
  blocks are executed against the real parser — the failure that this work found
  (every fixture in MATH_FIXTURES was in a dialect the parser rejects, and the
  addition laws were not range-restricted, so they could not fire).
"""

import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

import peirce_arithmetic as pa  # noqa: E402
import proof_character as pc  # noqa: E402
from definitions import Definition, DefinitionRegistry, expand  # noqa: E402
from eg_navigation import same_graph  # noqa: E402
from egif_parser_dau import parse_egif  # noqa: E402


# --- rungs 2–3: the order draws, and cut depth is quantifier alternation ----- #

def test_every_1881_axiom_is_a_real_graph():
    """Peirce's six axioms (Shields' reconstruction) are ordinary Beta graphs —
    no extension, no annotation. The order comes before the numbers."""
    for name, egif, _gloss in pa.ORDER_AXIOMS:
        g = parse_egif(egif)
        assert g.V, f"{name}: no lines of identity"
        rels = set(g.rel.values())
        assert rels <= {"lt", "="}, f"{name}: unexpected vocabulary {rels}"


def test_cut_depth_is_quantifier_alternation():
    """The pedagogical claim of rung 3, made checkable: discreteness (∀x ∃y ¬∃z)
    is the deepest axiom, because its quantifier alternation IS its nesting."""
    depths = {name: len(parse_egif(egif).Cut) for name, egif, _ in pa.ORDER_AXIOMS}
    assert depths["P4 discreteness"] > depths["P1 irreflexivity"]
    assert depths["P4 discreteness"] >= 3      # ∀ ∃ ¬∃ — three cuts of nesting


# --- rung 6: the numeral is a place, folded into a name --------------------- #

def test_numeral_unfolds_to_the_position_and_adds_nothing():
    """'three' is not an object but the third place in the order. The definition
    is a conservative abbreviation: unfolding returns exactly the succ-chain."""
    three = Definition("three", ["n"], pa.NUMERAL_DEFINITIONS["three"])
    reg = DefinitionRegistry([three])
    unfolded = expand(parse_egif("(three *k) (num k)"), reg)
    raw = parse_egif('(succ "0" *a) (succ a *b) (succ b *k) (num k)')
    assert same_graph(unfolded, raw), "the numeral must add a NAME, never content"


# --- rung 7: two drawn laws grow the table; the sum is read off the diagram -- #

def test_two_laws_grow_the_addition_table():
    """Nobody types in 2+3=5. Forward-chaining the two scrolls over the succ-chain
    produces the whole table — Peirce's 'experimenting on the diagram'."""
    table, _egi = pa.derive_sums(5)
    assert len(table) >= 21
    facts = {str(f) for f in table}
    assert "2 + 3 = 5" in facts and "0 + 5 = 5" in facts and "5 + 0 = 5" in facts


def test_the_sum_is_read_off_the_diagram():
    assert pa.check(pa.sum_claim(2, 3, 5)) == "true"
    assert pa.check(pa.sum_claim(2, 3, 6)) == "false"


def test_commutativity_is_SEEN_but_not_PROVED():
    """The rung-9 hinge, made concrete. Commutativity peels TRUE across the drawn
    stretch — you can *see* it. That is verification on a finite model, NOT proof
    for every number: to get there you need induction, and induction is the one
    thing the sheet cannot hold (it quantifies over propositions → a schema)."""
    assert pa.check("~[ (sum *x *y *z) ~[ (sum y x z) ] ]") == "true"
    # …and the honest note that says so is carried with the code, not just the doc.
    assert "schema" in pa.INDUCTION_NOTE and "cannot" in pa.INDUCTION_NOTE


# --- rung 8: Peirce's distinction, decided by machine ------------------------ #

def test_insertion_is_the_auxiliary_line():
    """The thesis: a derivation is THEOREMATIC iff it needs INS — the one rule that
    can scribe what the premisses do not contain. Everything else only rearranges,
    copies or deletes what is already there."""
    assert pc.CONTENT_ADDING == {"INS"}
    assert "ERA" in pc.CONTENT_PRESERVING and "IT+" in pc.CONTENT_PRESERVING


class _Step:
    def __init__(self, rule, sid="s", derived=False):
        self.rule_name, self.step_id = rule, sid
        self.parameters = {"derived": True} if derived else {}


def test_character_of_a_derivation():
    corollarial = pc.character_of([_Step("DC-"), _Step("IT-")])
    assert corollarial.character == pc.COROLLARIAL and not corollarial.provisional

    theorematic = pc.character_of([_Step("DC+"), _Step("INS", "s2"), _Step("IT+")])
    assert theorematic.character == pc.THEOREMATIC
    assert theorematic.insertions == ["s2"]        # names the auxiliary line
    assert not theorematic.provisional             # an insertion SEEN is proof enough


def test_a_derived_step_makes_a_corollarial_reading_provisional_never_silent():
    """Honesty rule: a collapsed step may hide an insertion, so it can never be
    read as silently corollarial."""
    r = pc.character_of([_Step("DC-"), _Step("UI", "s2", derived=True)])
    assert r.character == pc.COROLLARIAL and r.provisional
    assert r.opaque_steps == ["s2"]
    assert "PROVISIONAL" in r.summary.upper()


@pytest.mark.parametrize("uod_id,expected", [
    ("peirce_law", pc.THEOREMATIC),           # needs the insertion — the famous trick
    ("theorem_praeclarum", pc.THEOREMATIC),   # Leibniz's showpiece
    ("beta_modus_ponens", pc.COROLLARIAL),    # pure unpacking
    ("de_morgan", pc.COROLLARIAL),
])
def test_the_distinction_lands_where_a_mathematician_puts_it(uod_id, expected):
    """The headline, on the REAL corpus proofs: the theorems that need 'a trick' are
    exactly the ones that need an insertion."""
    from tomos_service import TomosService
    chain = TomosService(REPO / "tomos").load_chain(uod_id)
    if chain is None or not chain.steps:
        pytest.skip(f"{uod_id} carries no chain")
    assert pc.character_of_chain(chain).character == expected


# --- the ladder in the corpus ----------------------------------------------- #

def test_the_ladder_builds_and_the_claim_arrives():
    """The corpus exemplars: the audited claim 2+3=5 ARRIVES as the second law
    lands — and both readings of that arrival are honest (closed-world: the bare
    chain HAS no addition; open-world: it is merely silent)."""
    import build_arithmetic_ladder as ladder
    chain, uod = ladder.build_addition_chain()
    assert uod.uod_id == "arithmetic_from_two_laws"
    states = [chain.initial_state_id] + [s.to_state_id for s in chain.steps]
    closed = [ladder._verdict(chain.states[s]) for s in states]
    open_ = [ladder._verdict(chain.states[s], closed=False) for s in states]
    assert closed == ["false", "false", "true"]
    assert open_ == ["unknown", "unknown", "true"]
    # …and the ladder's own chains are corollarial (nothing entered from outside).
    assert pc.character_of_chain(chain).character == pc.COROLLARIAL


# --- a doc that teaches EGIF must teach EGIF that PARSES --------------------- #

def _egif_blocks(doc: Path):
    """The EGIF a doc actually teaches.

    Handles the two shapes the docs use: a **graph** (possibly spanning several
    lines — join them) and a **table** of `name  EGIF  % gloss` rows (one graph per
    row). Skips what is deliberately not EGIF: schema holes (`⟨…⟩` / `<…>` — an
    Arisbe extension the first-order parser has no syntax for, by design) and
    verdict lines (`→ TRUE`)."""
    for block in re.findall(r"```\n(.*?)```", doc.read_text(), re.S):
        if "⟨" in block or "<" in block:
            continue                                   # a schema, not a graph
        rows, plain = [], []
        for line in block.splitlines():
            s = line.strip()
            if not s or s.startswith("%") or "→" in s:
                continue
            if "%" in s:                               # a table row: strip the gloss
                s = s.split("%", 1)[0].strip()
                s = re.sub(r"^[A-Za-z_][\w]*\s{2,}", "", s)   # …and the row's name
                rows.append(s)
            else:
                plain.append(s)
        yield from (r for r in rows if r)
        joined = " ".join(plain).strip()
        if joined:
            yield joined


@pytest.mark.parametrize("doc_name", [
    "MATH_FIXTURES_ZFC_PEIRCE_1881.md",
    "MATHEMATICS_FROM_THE_SHEET.md",
])
def test_every_taught_egif_parses(doc_name):
    """The standing rule, enforced: teaching EGIF that the parser rejects is worse
    than teaching nothing. (This test would have failed before this work — every
    fixture in MATH_FIXTURES was written in a `?x` dialect the parser rejects.)"""
    doc = REPO / "docs" / doc_name
    lines = list(_egif_blocks(doc))
    assert lines, f"{doc_name}: no EGIF found to check"
    for egif in lines:
        try:
            parse_egif(egif)
        except Exception as exc:              # pragma: no cover - the failure path
            pytest.fail(f"{doc_name} teaches EGIF that does not parse:\n"
                        f"  {egif}\n  → {exc}")


def test_the_taught_addition_laws_actually_FIRE():
    """A law that cannot fire is not a law. The doc's plus/times laws must be
    range-restricted — every body variable bound by a relation — or
    materialization refuses them (existential head) and the table never grows.
    That defect was real and is now pinned."""
    from model_materialization import materialize_egi
    _facts, report = materialize_egi(parse_egif(pa.arithmetic_theory(5)))
    assert not report.skipped, f"a taught law was refused: {report.skipped}"
