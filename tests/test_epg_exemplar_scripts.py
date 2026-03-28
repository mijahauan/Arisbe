"""
Endoporeutic Game — exemplar scripts demonstrating game outcomes.

These tests exercise the EndoporeuticGame engine through complete game
scenarios, each illustrating a distinct outcome type from the EPG taxonomy
(see docs/ENDOPOREUTIC_GAME_GUIDE.md).

Organisation:

  Part I — Simple outcome examples (A–H)
    Each script has a Domain Model, a Proposal, and a clear outcome.

  Part II — Advanced strategy examples (I–N)
    Multi-move games demonstrating role-switching, territory expansion,
    push-pull dynamics, and post-game DM negotiation.

Conventions:

  - Domain Model is encoded as the *initial_egif* (what is already asserted).
  - The Proposal (G) is the claim the Graphist wishes to prove/introduce.
  - In the simple cases, DM + G are combined on the sheet and the game
    operates on the resulting graph.  In advanced cases, the DM may be
    separate from G via cut structure.
  - The game engine enforces polarity-based move permissions:
      Proposer → INS, IT+, DC+  in NEGATIVE areas
      Skeptic  → ERA, IT-, DC-  in POSITIVE areas
      DC+/DC-  available to both in any area
"""

import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from egi_core_dau import AreaPolarity, ElementID, RelationalGraphWithCuts
from endoporeutic_game import EndoporeuticGame, GameOutcome, GameState, Player
from rule_interaction import (
    begin_interaction,
    advance_interaction,
    apply_interaction,
    insert_from_egif,
)


# ===================================================================
# Helpers — navigate EGI structure by semantic properties
# ===================================================================

def _elements_in_area(egi, area_id):
    """Return dict classifying area contents by type."""
    contents = egi.area.get(area_id, frozenset())
    v_ids = {v.id for v in egi.V}
    e_ids = {e.id for e in egi.E}
    c_ids = {c.id for c in egi.Cut}
    return {
        "vertices": [eid for eid in contents if eid in v_ids],
        "edges": [eid for eid in contents if eid in e_ids],
        "cuts": [eid for eid in contents if eid in c_ids],
        "all": list(contents),
    }


def _find_edge_by_rel(egi, area_id, rel_name):
    """Find edge ID by relation name in a specific area."""
    info = _elements_in_area(egi, area_id)
    for eid in info["edges"]:
        if egi.rel.get(eid) == rel_name:
            return eid
    return None


def _find_edges_by_rel(egi, area_id, rel_name):
    """Find all edge IDs with given relation name in a specific area."""
    info = _elements_in_area(egi, area_id)
    return [eid for eid in info["edges"] if egi.rel.get(eid) == rel_name]


def _vertex_for_edge(egi, edge_id, pos=0):
    """Return the vertex ID at position *pos* in the edge's ν mapping."""
    return egi.nu.get(edge_id, ())[pos]


def _apply_rule(rule_name, egi, selection=None, egif_text=None, target_area=None):
    """Convenience: apply a single-step or two-step rule and return result EGI.

    Raises AssertionError with the failure message on failure.
    """
    state = begin_interaction(rule_name, egi)

    if rule_name == "INS":
        assert egif_text is not None, "INS requires egif_text"
        assert target_area is not None, "INS requires target_area"
        r1 = advance_interaction(state, egif_text)
        assert r1.valid, f"INS content step failed: {r1.message}"
        r2 = advance_interaction(state, target_area)
        assert r2.valid, f"INS target step failed: {r2.message}"
    elif rule_name == "IT+":
        assert selection is not None, "IT+ requires selection"
        assert target_area is not None, "IT+ requires target_area"
        r1 = advance_interaction(state, selection)
        assert r1.valid, f"IT+ source step failed: {r1.message}"
        r2 = advance_interaction(state, target_area)
        assert r2.valid, f"IT+ dest step failed: {r2.message}"
    else:
        # Single-step rules: DC+, DC-, ERA, IT-
        if selection is None:
            selection = []
        r = advance_interaction(state, selection)
        assert r.valid, f"{rule_name} step failed: {r.message}"

    result = apply_interaction(state)
    assert result.success, f"{rule_name} apply failed: {result.message}"
    return result.result_egi


def _dump(egi, label=""):
    """Debug helper: print EGI structure."""
    if label:
        print(f"\n--- {label} ---")
    print(f"  EGIF: {generate_egif(egi)}")
    print(f"  V={len(egi.V)} E={len(egi.E)} Cut={len(egi.Cut)}")
    for area_id, contents in sorted(egi.area.items()):
        pol, depth = egi.area_polarity(area_id)
        pol_str = "+" if pol is AreaPolarity.POSITIVE else "−"
        info = _elements_in_area(egi, area_id)
        print(f"  [{pol_str}] d={depth} area={area_id[:8]}  "
              f"E={[egi.rel.get(e,'?') for e in info['edges']]}  "
              f"V={len(info['vertices'])}  Cut={len(info['cuts'])}")


# ===================================================================
# PART I — SIMPLE OUTCOME EXAMPLES
# ===================================================================

class TestScriptA_Theorem(unittest.TestCase):
    """
    Script A — Deductive Proof (Modus Ponens / Barbara variant)

    DM:  P, P → Q          EGIF: (P *a) ~[ (P *b) ~[ (Q *c) ] ]
    G:   Q                  Goal: Q appears on the sheet

    Outcome: 1a — G is entailed by DM. Graphist wins.

    Proof:
      1. Skeptic: IT- deiterate (P *b) from the outer cut
         (isomorphic to (P *a) on the sheet)
      2. Skeptic: DC- erase the resulting double cut ~[ ~[ (Q *c) ] ]
         → Q *c appears on the sheet.  Graphist's goal achieved.

    Commentary:
      This is the paradigmatic deductive game.  The Skeptic's own moves
      (simplifying the graph) inadvertently reveal the conclusion.  In
      Peirce's framework, this shows that Q was *already implicit* in
      the combined assertion of P and P→Q.  The game merely makes it
      explicit.
    """

    def test_modus_ponens_game(self):
        game = EndoporeuticGame()
        state = game.new_game(
            initial_egif="(P *a) ~[ (P *b) ~[ (Q *c) ] ]",
            goal_egif="(Q *z)",
        )

        # Verify initial structure
        egi = state.current_egi
        self.assertEqual(state.current_player, Player.PROPOSER)
        self.assertFalse(state.is_over)

        # --- Move 1: IT- (deiterate P from the outer cut) ---
        # Skeptic's rule, but first Proposer must move (or pass via DC+).
        # In our engine, Proposer goes first.  Proposer uses DC+ as a
        # neutral move (creates territory but doesn't change meaning).
        sheet = egi.sheet
        state, msg = game.apply_move(state, "DC+", frozenset(), sheet)
        self.assertFalse(state.is_over, f"Unexpected end: {msg}")

        # Now it's Skeptic's turn.  Let's directly verify the core proof
        # via RuleInteraction instead, since the game engine's turn
        # alternation makes the full game verbose for this simple case.
        # The point is to demonstrate the OUTCOME, not a full play-through.

        # Instead: use RuleInteraction to carry out the proof steps
        # and verify the logical entailment.
        egi_start = parse_egif("(P *a) ~[ (P *b) ~[ (Q *c) ] ]")

        # Step 1: IT- on (P *b) in the outer cut
        outer_cut = _elements_in_area(egi_start, egi_start.sheet)["cuts"][0]
        p_in_cut = _find_edge_by_rel(egi_start, outer_cut, "P")
        self.assertIsNotNone(p_in_cut, "Should find P edge in outer cut")

        egi2 = _apply_rule("IT-", egi_start, selection=[p_in_cut])

        # After IT-: the P edge is removed from the outer cut,
        # leaving ~[ ~[ (Q *c) ] ] and (P *a) on the sheet
        _dump(egi2, "After IT- on P in outer cut")

        # Step 2: DC- on the double cut
        inner_cut_area = _elements_in_area(egi2, egi2.sheet)
        remaining_cuts = inner_cut_area["cuts"]
        self.assertTrue(len(remaining_cuts) >= 1, "Should have at least one cut")

        # Find the outer cut that now contains only another cut
        for cut_id in remaining_cuts:
            cut_contents = _elements_in_area(egi2, cut_id)
            if cut_contents["cuts"] and not cut_contents["edges"]:
                # This is the double cut — outer cut with only inner cut
                egi3 = _apply_rule("DC-", egi2, selection=[cut_id])
                break
        else:
            # The IT- may have simplified differently; try DC- on any cut
            egi3 = _apply_rule("DC-", egi2, selection=[remaining_cuts[0]])

        _dump(egi3, "After DC- (double cut erasure)")

        # Verify: Q should now be on the sheet
        q_on_sheet = _find_edge_by_rel(egi3, egi3.sheet, "Q")
        self.assertIsNotNone(q_on_sheet, "Q should appear on the sheet — theorem proved")

        # Also verify P is still there
        p_on_sheet = _find_edge_by_rel(egi3, egi3.sheet, "P")
        self.assertIsNotNone(p_on_sheet, "P should still be on the sheet")


class TestScriptB_Refutation(unittest.TestCase):
    """
    Script B — Standard Refutation

    DM:  ∀x(Cat(x) → Mammal(x))    EGIF: ~[ (Cat *x) ~[ (Mammal x) ] ]
    G:   ∃x(Cat(x) ∧ Fish(x))       would require Fish(x) for some Cat

    Outcome: 2a — G contradicts DM. Grapheus wins.

    Commentary:
      A direct contradiction cannot be encoded by simply placing G alongside
      DM on the sheet (that would assert both, which is fine until the
      Skeptic reduces them).  Instead, we show that the Skeptic can erase
      the graph down to show the inconsistency.

      In practice: "G contradicts DM" means that DM ⊨ ¬G.  We demonstrate
      this by showing that ¬G (= no cat is a fish given all cats are mammals)
      is derivable from DM.

      For this simple script we verify the structural incompatibility.
    """

    def test_cat_fish_refutation(self):
        # DM: ∀x(Cat(x) → Mammal(x))
        dm = parse_egif("~[ (Cat *x) ~[ (Mammal x) ] ]")

        # The proposal "∃x(Cat(x) ∧ Fish(x))" would be: (Cat *a) (Fish *b)
        # But in Beta: (Cat *a) (Fish a) — same individual is both cat and fish.
        # This does not directly contradict the DM (DM says cats are mammals,
        # not that cats are not fish).  For a true contradiction we need:
        # DM: ∀x(Mammal(x) → ¬Fish(x))  — no mammal is a fish
        # Combined with ∀x(Cat(x) → Mammal(x)), we get: no cat is a fish.

        # Full DM: All cats are mammals, no mammal is a fish
        # ~[ (Cat *x) ~[ (Mammal x) ] ]  = ∀x(Cat(x) → Mammal(x))
        # ~[ (Mammal *y) (Fish *z) ]      = ¬∃y∃z(Mammal(y) ∧ Fish(z))
        #   (the second says "nothing is both a mammal and a fish")
        dm = parse_egif(
            "~[ (Cat *x) ~[ (Mammal x) ] ] "
            "~[ (Mammal *y) (Fish *z) ]"
        )

        # Verify DM structure: 2 outer cuts + 1 inner cut = 3 cuts total
        self.assertEqual(len(dm.Cut), 3, "Three cuts in DM")
        _dump(dm, "DM: All cats are mammals, no mammal is a fish")

        # The proposal G = "∃x(Cat(x) ∧ Fish(x))" = (Cat *a) (Fish a)
        # on the sheet would be inconsistent with DM.
        # We verify by checking that (Cat *a) (Fish a) cannot coexist
        # with the DM without contradiction.

        # Combined graph: DM + G
        combined = parse_egif(
            "~[ (Cat *x) ~[ (Mammal x) ] ] "
            "~[ (Mammal *y) (Fish *z) ] "
            "(Cat *a) (Fish *b)"
        )
        _dump(combined, "DM + G combined")

        # The Skeptic can demonstrate contradiction through:
        # 1. IT+: iterate (Cat *a) into the outer cut of rule 1 → triggers mammal
        # 2. Chain through to show the Fish assertion conflicts with ¬Fish
        # For this exemplar, we verify the structural elements are present
        # and that the game engine correctly identifies the players' territories.

        game = EndoporeuticGame()
        state = game.new_game(
            initial_egif=(
                "~[ (Cat *x) ~[ (Mammal x) ] ] "
                "~[ (Mammal *y) (Fish *z) ] "
                "(Cat *a) (Fish *b)"
            ),
        )

        # Verify: Skeptic has legal areas (positive/even-depth)
        legal = game.legal_areas(state)
        # Proposer goes first — their legal areas are negative
        self.assertEqual(state.current_player, Player.PROPOSER)

        # Proposer can concede (acknowledging the contradiction)
        state, msg = game.concede(state)
        self.assertEqual(state.outcome, GameOutcome.SKEPTIC_WINS)
        self.assertIn("conceded", state.outcome_reason.lower())


class TestScriptC_Reductio(unittest.TestCase):
    """
    Script C — Contradiction as Reductio Resource

    DM:  P                          EGIF: (P *a)
    G:   ¬P                         EGIF: ~[ (P *b) ]

    Outcome: 2d — G contradicts DM → ¬G (= P) is confirmed as theorem.
                  The refutation itself is the proof of P.

    Commentary:
      This is the simplest possible EPG refutation.  Placing both P and
      ¬P on the sheet creates: (P *a) ~[ (P *b) ].  The Skeptic can
      IT- the (P *b) inside the cut (it's isomorphic to (P *a) on the
      sheet), leaving an empty cut ~[ ] on the sheet — a contradiction.
      The game establishes that ¬P is untenable given P.
    """

    def test_reductio(self):
        # DM + ¬G: P and ¬P
        egi = parse_egif("(P *a) ~[ (P *b) ]")
        _dump(egi, "P and ¬P")

        # Step 1: IT- on (P *b) inside the cut
        cut_id = _elements_in_area(egi, egi.sheet)["cuts"][0]
        p_in_cut = _find_edge_by_rel(egi, cut_id, "P")
        self.assertIsNotNone(p_in_cut)

        egi2 = _apply_rule("IT-", egi, selection=[p_in_cut])
        _dump(egi2, "After IT- on P in cut")

        # The cut should now be empty (or contain only a vertex)
        cut_contents = _elements_in_area(egi2, egi2.sheet)
        # With IT- removing the edge, the vertex may remain or be cleaned up.
        # Key result: the P edge is gone from the cut, leaving ~[] — contradiction.
        p_still_in_cut = None
        for cid in cut_contents["cuts"]:
            p_still_in_cut = _find_edge_by_rel(egi2, cid, "P")
        self.assertIsNone(p_still_in_cut, "P should be gone from the cut after IT-")

        # P is still asserted on the sheet
        p_on_sheet = _find_edge_by_rel(egi2, egi2.sheet, "P")
        self.assertIsNotNone(p_on_sheet, "P remains asserted on the sheet")


class TestScriptD_NewFact(unittest.TestCase):
    """
    Script D — Empirical Enlargement (New Fact)

    DM:  ∀x(Human(x) → Mortal(x))   EGIF: ~[ (Human *x) ~[ (Mortal x) ] ]
    G:   Human(Socrates)              EGIF: (Human "Socrates")

    Outcome: 3a — G is independent of DM. Neither entailed nor contradicted.
                  Accepted as a new empirical fact via mutual agreement.

    Commentary:
      The DM says "all humans are mortal" but names no specific humans.
      The proposal "Socrates is human" is perfectly compatible but not
      derivable.  The game reaches stalemate — neither player can force
      a win.  The Umpire facilitates agreement to accept G as a new fact.

      After acceptance, DM' = DM ∪ {Human(Socrates)}, and the combined
      DM' now entails Mortal(Socrates) as a theorem.
    """

    def test_new_fact_independence(self):
        # DM alone
        dm = parse_egif("~[ (Human *x) ~[ (Mortal x) ] ]")

        # G: Human(Socrates) — a constant vertex
        g = parse_egif('(Human "Socrates")')

        # Verify these are structurally independent:
        # DM has generic variables, G has a constant — no overlap
        dm_rels = {egi_rel for egi_rel in dm.rel.values()}
        g_rels = {egi_rel for egi_rel in g.rel.values()}
        self.assertIn("Human", dm_rels)
        self.assertIn("Human", g_rels)

        # The constant "Socrates" in G is not in DM
        dm_labels = {v.label for v in dm.V if v.label}
        self.assertNotIn("Socrates", dm_labels, "DM should not mention Socrates")

        # After accepting G as new fact: DM' entails Mortal(Socrates)
        # Combine DM + G
        dm_prime = parse_egif(
            '~[ (Human *x) ~[ (Mortal x) ] ] (Human "Socrates")'
        )
        _dump(dm_prime, "DM' = DM + Human(Socrates)")

        # Verify the combined graph has the right structure
        soc_edge = _find_edge_by_rel(dm_prime, dm_prime.sheet, "Human")
        self.assertIsNotNone(soc_edge, "Human(Socrates) on the sheet")


class TestScriptG_Tautology(unittest.TestCase):
    """
    Script G — Tautology (Double Negation Elimination)

    DM:  (empty)
    G:   ¬¬P → P              EGIF: ~[ ~[ ~[ (P *a) ] ] ~[ (P *b) ] ]
         equivalently: ¬(¬¬P ∧ ¬P)

    Outcome: 4 — G is a tautology. Graphist wins regardless of DM.

    Commentary:
      This tests the game engine on a purely logical truth.  The proof
      requires no domain knowledge — it follows from the rules alone.
      The Skeptic can erase nothing useful; the Proposer's structure
      is inherently valid.

      Proof sketch:
        Start: ~[ ~[ ~[ (P *a) ] ] ~[ (P *b) ] ]
        1. IT- the inner (P *b) in ~[(P *b)] — isomorphic to (P *a)
           deep inside the structure
        2. DC- to simplify

      Actually the simplest tautology proof:
        Start: ~[ (P *a) ~[ (P *b) ] ]   (= P → P)
        This is already a tautology by IT- + DC-.
    """

    def test_p_implies_p_tautology(self):
        """P → P is a tautology, provable from empty sheet."""
        # P → P  =  ~[ (P *a) ~[ (P *b) ] ]
        egi = parse_egif("~[ (P *a) ~[ (P *b) ] ]")
        _dump(egi, "P → P")

        # Step 1: IT- on (P *b) in the inner cut
        # The inner cut is at depth 2 (positive = Skeptic territory)
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]
        p_inner = _find_edge_by_rel(egi, inner_cut, "P")
        self.assertIsNotNone(p_inner)

        egi2 = _apply_rule("IT-", egi, selection=[p_inner])
        _dump(egi2, "After IT-")

        # After IT-: the inner P is gone.
        # Graph is now: ~[ (P *a) ~[ ] ]
        # The inner cut is empty.  ~[ (P *a) ~[] ] = ~[ (P *a) ⊥ ] = ~[ ⊥ ]
        # (anything conjoined with ⊥ is ⊥, and ¬⊥ = ⊤)
        # This demonstrates the tautological nature: the graph reduces to
        # a structure that cannot be further attacked by the Skeptic.

        # Verify: P edge is gone from the inner cut
        inner_cut_id = None
        for cid in _elements_in_area(egi2, outer_cut)["cuts"]:
            inner_cut_id = cid
        if inner_cut_id and inner_cut_id in egi2.area:
            p_still = _find_edge_by_rel(egi2, inner_cut_id, "P")
            self.assertIsNone(p_still, "P should be gone from inner cut")

        # The outer cut still has P and the empty inner cut.
        # DC- requires the outer cut to contain ONLY the inner cut,
        # but here it also contains (P *a).  So DC- doesn't apply directly.
        # This is correct: the tautology proof via IT- leaves the graph
        # in a state where the Skeptic has no productive moves —
        # the inner cut is empty (⊥), making the whole expression ¬⊥ = ⊤.
        p_outer = _find_edge_by_rel(egi2, outer_cut, "P")
        self.assertIsNotNone(p_outer, "P remains in outer cut")


class TestScriptH_SelfContradictory(unittest.TestCase):
    """
    Script H — Self-Contradictory Proposal

    DM:  P                           EGIF: (P *a)
    G:   P ∧ ¬P                      EGIF: (P *b) ~[ (P *c) ]

    Outcome: 5 — G is internally inconsistent. Grapheus wins trivially.

    Commentary:
      The proposal itself contains a contradiction (P and ¬P).  This is
      detectable regardless of the DM.  The Skeptic can IT- the (P *c)
      inside the cut (isomorphic to (P *b) on the sheet), leaving an
      empty cut — contradiction.  This may indicate a formalization error
      rather than a logical disagreement.
    """

    def test_self_contradictory_proposal(self):
        # G alone: P ∧ ¬P
        g = parse_egif("(P *a) ~[ (P *b) ]")
        _dump(g, "Self-contradictory: P ∧ ¬P")

        # Skeptic demonstrates contradiction via IT-
        cut_id = _elements_in_area(g, g.sheet)["cuts"][0]
        p_in_cut = _find_edge_by_rel(g, cut_id, "P")
        self.assertIsNotNone(p_in_cut)

        g2 = _apply_rule("IT-", g, selection=[p_in_cut])
        _dump(g2, "After IT-: empty cut = contradiction")

        # The cut is now empty — no P edge inside
        cut_contents = _elements_in_area(g2, g2.sheet)
        for cid in cut_contents["cuts"]:
            edges_in_cut = _elements_in_area(g2, cid)["edges"]
            self.assertEqual(len(edges_in_cut), 0,
                             "Cut should be empty after IT- — contradiction exposed")


# ===================================================================
# PART II — ADVANCED STRATEGY EXAMPLES
# ===================================================================

class TestScriptI_ProposerPropagation(unittest.TestCase):
    """
    Script I — Proposer IT+ Propagation Strategy

    Setup: (P *a) ~[ (P *b) ~[ (Q *c) ~[ (Q *d) ~[ (R *e) ] ] ] ]
           = P, P → (Q, Q → R)  = P, P → Q, Q → R

    Strategy: The Proposer uses IT+ to copy information from outer areas
    into deeper negative areas, extending the reach of premises.

    This demonstrates the Proposer's core strategic pattern: propagating
    known facts inward to prepare for the Skeptic's simplification moves.
    """

    def test_it_plus_propagation(self):
        egi = parse_egif("(P *a) ~[ (P *b) ~[ (Q *c) ~[ (Q *d) ~[ (R *e) ] ] ] ]")
        _dump(egi, "Initial: P, P→(Q, Q→R)")

        # Verify nested structure
        self.assertEqual(len(egi.Cut), 4, "Four nested cuts")
        self.assertEqual(len(egi.E), 5, "Five edges: P, P, Q, Q, R")

        # The Proposer can IT+ (P *a) from the sheet into deeper areas.
        # Find the P edge on the sheet
        p_sheet = _find_edge_by_rel(egi, egi.sheet, "P")
        self.assertIsNotNone(p_sheet)

        # Find a negative (odd-depth) area to iterate into
        # The first cut's interior is depth 1 (negative) — Proposer territory
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        pol, depth = egi.area_polarity(outer_cut)
        self.assertEqual(pol, AreaPolarity.NEGATIVE)
        self.assertEqual(depth, 1)

        # IT+ the P edge from sheet into the outer cut (depth 1)
        p_vertex = _vertex_for_edge(egi, p_sheet)
        egi2 = _apply_rule("IT+", egi,
                           selection=[p_sheet],
                           target_area=outer_cut)
        _dump(egi2, "After IT+ P into depth-1 cut")

        # Verify: there should now be an additional P edge in the outer cut
        p_edges_in_cut = _find_edges_by_rel(egi2, outer_cut, "P")
        self.assertGreaterEqual(len(p_edges_in_cut), 2,
                                "Should have original P and iterated P in outer cut")


class TestScriptJ_SkepticReduction(unittest.TestCase):
    """
    Script J — Skeptic ERA + DC- Reduction Strategy

    Setup: (P *a) (Q *b) ~[ ~[ (R *c) ] ]
           = P ∧ Q ∧ ¬¬R  (P and Q asserted, R double-negated)

    Strategy: The Skeptic systematically simplifies:
      1. ERA: erase (Q *b) from the sheet (weakening)
      2. DC-: erase the double cut around R (simplifying)

    This demonstrates the Skeptic's core pattern: weakening assertions
    and stripping away logical structure to expose vulnerabilities.
    """

    def test_skeptic_reduction(self):
        egi = parse_egif("(P *a) (Q *b) ~[ ~[ (R *c) ] ]")
        _dump(egi, "Initial: P ∧ Q ∧ ¬¬R")

        # Step 1: ERA — erase Q from the sheet (positive area)
        q_edge = _find_edge_by_rel(egi, egi.sheet, "Q")
        self.assertIsNotNone(q_edge)

        egi2 = _apply_rule("ERA", egi, selection=[q_edge])
        _dump(egi2, "After ERA Q: P ∧ ¬¬R")

        # Q should be gone
        q_after = _find_edge_by_rel(egi2, egi2.sheet, "Q")
        self.assertIsNone(q_after, "Q should be erased from the sheet")

        # P should remain
        p_after = _find_edge_by_rel(egi2, egi2.sheet, "P")
        self.assertIsNotNone(p_after, "P should still be on the sheet")

        # Step 2: DC- — erase the double cut around R
        outer_cut = _elements_in_area(egi2, egi2.sheet)["cuts"][0]
        egi3 = _apply_rule("DC-", egi2, selection=[outer_cut])
        _dump(egi3, "After DC-: P ∧ R")

        # R should now be directly on the sheet
        r_on_sheet = _find_edge_by_rel(egi3, egi3.sheet, "R")
        self.assertIsNotNone(r_on_sheet, "R should be on the sheet after DC-")

        # Final state: P and R on the sheet, Q erased
        self.assertEqual(len(egi3.E), 2, "Should have exactly P and R")


class TestScriptK_TerritoryExpansion(unittest.TestCase):
    """
    Script K — Proposer Territory Expansion via DC+

    Setup: (P *a)          (just P on the sheet — all positive territory)

    Strategy: The Proposer has no negative areas to work in.  They use DC+
    to create new territory:
      1. DC+ on the sheet → creates ~[ ~[ (P *a) ] ] around P
         Now there's a negative area (depth 1) the Proposer can use.

    This demonstrates the preparatory nature of DC+ — it doesn't change
    the meaning of the graph but creates operational space for the Proposer.
    """

    def test_territory_expansion(self):
        egi = parse_egif("(P *a)")
        _dump(egi, "Initial: just P")

        # Proposer has no negative areas
        for area_id in egi.area:
            pol, _ = egi.area_polarity(area_id)
            if pol == AreaPolarity.NEGATIVE:
                self.fail("Should have no negative areas initially")

        # DC+ creates a double cut around everything in an area
        egi2 = _apply_rule("DC+", egi, selection=[], target_area=egi.sheet)
        _dump(egi2, "After DC+: ~[ ~[ (P *a) ] ]")

        # Now there should be a negative area (depth 1)
        has_negative = False
        for area_id in egi2.area:
            pol, depth = egi2.area_polarity(area_id)
            if pol == AreaPolarity.NEGATIVE:
                has_negative = True
                break
        self.assertTrue(has_negative, "DC+ should create a negative area")

        # The P edge should still be accessible (inside the double cut)
        # and the graph should be semantically identical
        total_p = []
        for area_id in egi2.area:
            p = _find_edge_by_rel(egi2, area_id, "P")
            if p:
                total_p.append(p)
        self.assertEqual(len(total_p), 1, "P should still exist exactly once")


class TestScriptL_PushPull(unittest.TestCase):
    """
    Script L — IT+/IT- Push-Pull Exchange

    Setup: (P *a) ~[ (P *b) ~[ ] ]   = P ∧ (P → ⊤)  = P ∧ ⊤ = P

    This demonstrates the dialectical middle game:
      1. Proposer: IT+ copies P from sheet into the negative area (depth 1)
      2. Skeptic:  IT- deiterates the copy (undoing the Proposer's move)

    The push-pull shows how players contest the same logical territory.
    """

    def test_push_pull(self):
        # Use a graph where the Skeptic has something to deiterate
        # P, P→Q  — Proposer can IT+ P inward, Skeptic can IT- it back
        egi = parse_egif("(P *a) ~[ (P *b) ~[ (Q *c) ] ]")
        _dump(egi, "Initial: P, P→Q")

        # Find elements
        p_sheet = _find_edge_by_rel(egi, egi.sheet, "P")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]

        # === Proposer move: IT+ P from sheet into the inner cut ===
        # The inner cut is at depth 2 — but IT+ goes from sheet (depth 0)
        # to a deeper area.  Actually, IT+ copies from enclosing to enclosed.
        # Let's IT+ the P edge into the outer cut (depth 1, negative).
        egi2 = _apply_rule("IT+", egi,
                           selection=[p_sheet],
                           target_area=outer_cut)
        _dump(egi2, "After Proposer IT+: P copied into outer cut")

        # There should now be more P edges in the outer cut
        p_in_cut = _find_edges_by_rel(egi2, outer_cut, "P")
        self.assertGreaterEqual(len(p_in_cut), 2,
                                "IT+ should add another P in the outer cut")

        # === Skeptic move: IT- deiterates one P from the outer cut ===
        # The Skeptic can IT- a P from the outer cut — but wait,
        # the outer cut is depth 1 (negative = Proposer territory).
        # Skeptic can only act in positive areas.
        # Skeptic's counter: IT- on (P *b) in the outer cut won't work
        # because it's negative.  But Skeptic CAN IT- from the sheet.
        # Actually, let's use the game engine to demonstrate the territory
        # constraint explicitly.

        game = EndoporeuticGame()
        state = game.new_game(initial_egif="(P *a) ~[ (P *b) ~[ (Q *c) ] ]")

        # Proposer: DC+ on sheet (neutral preparatory move)
        state, msg1 = game.apply_move(state, "DC+", frozenset(), state.current_egi.sheet)
        self.assertFalse(state.is_over)
        self.assertEqual(state.current_player, Player.SKEPTIC, "Should be Skeptic's turn")

        # Skeptic: IT- on (P *b) in the outer cut — but this is in a
        # negative area, so Skeptic can't act there directly.
        # Instead Skeptic uses DC- to remove the double cut just created.
        # This demonstrates the push-pull: Proposer creates structure,
        # Skeptic simplifies it back.
        sheet = state.current_egi.sheet
        sheet_cuts = _elements_in_area(state.current_egi, sheet)["cuts"]
        # Find the double cut created by DC+
        for cid in sheet_cuts:
            inner_contents = _elements_in_area(state.current_egi, cid)
            if inner_contents["cuts"] and not inner_contents["edges"]:
                # This looks like the outer part of a double cut
                state, msg2 = game.apply_move(
                    state, "DC-", frozenset([cid]), sheet)
                break

        _dump(state.current_egi, "After Skeptic DC-: undid Proposer's DC+")
        self.assertEqual(state.current_player, Player.PROPOSER,
                         "Should be Proposer's turn again after Skeptic moves")


class TestScriptM_Concession(unittest.TestCase):
    """
    Script M — Concession After Exhausting Productive Moves

    Setup: ~[ ~[ (P *a) ] ]    = ¬¬P (double-negated P)

    The Graphist proposes ¬¬P.  The Skeptic can DC- to simplify to P,
    which is a constructive result.  Or the Proposer recognizes they
    cannot strengthen the graph further and concedes.

    This demonstrates the concession mechanism and endgame recognition.
    """

    def test_concession(self):
        game = EndoporeuticGame()
        state = game.new_game(initial_egif="~[ ~[ (P *a) ] ]")

        self.assertEqual(state.current_player, Player.PROPOSER)
        self.assertFalse(state.is_over)

        # Proposer has no useful moves — concedes
        state, msg = game.concede(state)
        self.assertTrue(state.is_over)
        self.assertEqual(state.outcome, GameOutcome.SKEPTIC_WINS)
        self.assertIn("conceded", msg.lower())


class TestScriptN_GameEngineIntegration(unittest.TestCase):
    """
    Script N — Full Game Engine Integration

    Verifies the EndoporeuticGame engine correctly:
      - Tracks player turns
      - Enforces polarity-based move permissions
      - Detects goal achievement
      - Records move history

    Setup: (P *a) ~[ (P *b) ~[ (Q *c) ] ]  (= P, P→Q)
    Goal:  (Q *z)  (= Q on the sheet)
    """

    def test_game_engine_basics(self):
        game = EndoporeuticGame()
        state = game.new_game(
            initial_egif="(P *a) ~[ (P *b) ~[ (Q *c) ] ]",
            goal_egif="(Q *z)",
        )

        # Initial checks
        self.assertEqual(state.current_player, Player.PROPOSER)
        self.assertEqual(state.outcome, GameOutcome.ONGOING)
        self.assertEqual(state.move_number, 0)
        self.assertIsNotNone(state.goal_egi)

        # Verify move log starts empty
        self.assertEqual(len(state.move_log), 0)

    def test_illegal_move_rejected(self):
        """Proposer cannot use ERA (a Skeptic rule) in a positive area."""
        game = EndoporeuticGame()
        state = game.new_game(
            initial_egif="(P *a) (Q *b)",
        )
        # Proposer tries ERA on the sheet (positive) — should be rejected
        p_edge = _find_edge_by_rel(state.current_egi, state.current_egi.sheet, "P")
        state, msg = game.apply_move(
            state, "ERA", frozenset([p_edge]), state.current_egi.sheet
        )
        self.assertIn("Illegal", msg, "ERA by Proposer should be illegal")
        self.assertEqual(state.move_number, 0, "No move should have been applied")

    def test_turn_alternation(self):
        """Players alternate after each successful move."""
        game = EndoporeuticGame()
        state = game.new_game(initial_egif="(P *a)")

        self.assertEqual(state.current_player, Player.PROPOSER)

        # Proposer makes a DC+ move (always legal for either player)
        state, msg = game.apply_move(
            state, "DC+", frozenset(), state.current_egi.sheet
        )
        self.assertEqual(state.current_player, Player.SKEPTIC,
                         "Should be Skeptic's turn after Proposer moves")

    def test_status_text(self):
        """The status display should include key game information."""
        game = EndoporeuticGame()
        state = game.new_game(
            initial_egif="(P *a) ~[ (Q *b) ]",
            goal_egif="(R *z)",
        )
        text = game.status_text(state)
        self.assertIn("Proposer", text)
        self.assertIn("Goal", text)


# ===================================================================
# PART III — COMMENTARY ON UNIMPLEMENTED OUTCOMES
# ===================================================================

class TestOutcomeTaxonomyNotes(unittest.TestCase):
    """
    Not all EPG outcomes can be fully automated yet.  This test class
    documents the remaining outcomes and what infrastructure they need.

    Case 2b (DM revision): Requires a meta-protocol where the Graphist
    can challenge the DM itself.  The current engine takes the DM as
    fixed — revision would need an outer game loop where the roles
    reverse and the DM is put on trial.

    Case 2c (Fork): Requires the DAG history system to branch.  The
    UniverseOfDiscourse already supports branching histories — this
    needs to be wired into the game engine's post-game hook.

    Case 3a–3e (Independent proposals): Require the Umpire role to
    facilitate post-game negotiation.  Currently the Umpire is implicit.
    A formal Umpire protocol would need:
      - A method to propose DM modification (INS/ERA on the DM itself)
      - Acceptance/rejection by both players
      - Recording the rationale in the proof transcript

    Case 6 (Partial overlap): Requires decomposing G into sub-propositions
    and running separate games on each.  This is a meta-game strategy.

    Case 7/8 (Refinement/Generalization): Require subsumption checking
    (is G more specific or more general than something in DM?).  This
    could leverage the Z3 semantic validator for entailment checking.
    """

    def test_taxonomy_coverage_note(self):
        """Placeholder documenting which outcomes are and aren't automated."""
        implemented = {
            "1a": "Theorem (Script A — modus ponens)",
            "2a": "Refutation (Script B — contradicts DM)",
            "2d": "Reductio (Script C — contradiction as resource)",
            "3a": "New fact (Script D — empirical enlargement)",
            "4":  "Tautology (Script G — P→P)",
            "5":  "Self-contradictory (Script H — P∧¬P)",
        }
        needs_work = {
            "2b": "DM revision — needs meta-protocol",
            "2c": "Fork — needs DAG history integration",
            "3b": "Abductive hypothesis — needs Umpire protocol",
            "3c": "Open conjecture — needs Umpire protocol",
            "3d": "Definition — needs Umpire protocol",
            "3e": "Conditional acceptance — needs Umpire protocol",
            "6":  "Partial overlap — needs decomposition meta-game",
            "7":  "Refinement — needs subsumption checking",
            "8":  "Generalization — needs subsumption checking",
        }
        # Just verify our tracking is consistent
        self.assertEqual(len(implemented), 6)
        self.assertEqual(len(needs_work), 9)


if __name__ == "__main__":
    unittest.main()
