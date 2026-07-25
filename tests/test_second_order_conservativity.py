"""
The A3 conservativity gate — **the standing crossing invariant** (verdict A3,
CROSSING_DECISION_BRIEFS 2026-07-16): when the second-order layer opens, a
corpus-level test must demonstrate the quotation layer **licenses no new
first-order assertion** — "Dau remains the guarantor," made testable.

Three tiers:

1. **Invisibility when unused** — a first-order graph is bit-identical to the
   pre-B-min core: no new JSON keys, byte-identical re-save, canonical order
   (hence generated linear text) unchanged, ``same_graph`` behavior unchanged.
   Run corpus-wide.
2. **Erasure projection** — ``project_first_order`` strips the layer and
   recovers exactly the never-quoted host; the peel / theory / settlement
   verdicts computed WITH the quotation equal those computed on the
   projection (the quoted law inside the oval licenses nothing — the tier
   that catches any negation-interpreting consumer that missed the opacity
   audit); the swan's withdrawn law is not derivable from the host that
   exhibits it.
3. **Rules restraint** — ink cannot cross the quotation boundary (the rule-
   level shapes live in ``test_rules_second_order``; this tier pins the
   corpus-facing composite: a quotation-bearing exemplar's own chain replays
   and its M-view materializes zero rules from quoted ink).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from frozendict import frozendict

from domain_oracle import CorpusOracle
from eg_navigation import same_graph
from egi_io import from_dict, to_dict
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from formal_transformation_rules import (
    AreaPolarity, DeiterationRule, ErasureRule, TransformationContext,
)
from model_materialization import materialize_egi
from quotation_overlay import project_first_order, scribe_quotation
from semantic_game import evaluate
from tomos_service import TomosService

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"

QUOTATION_EXEMPLARS = {
    # The explicit allowlist of quotation-bearing UoDs (the named limit: their
    # linear forms are the first-order projection).  A NEW quotation-bearing
    # UoD must be added here knowingly or tier 1 fails — the gate's
    # self-checking idiom (the polarity gate's allowlist pattern).
    "swan_third_tense",
    "forcing_forces",
    "peirce_law_commentary",
}


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


# --------------------------------------------------------------------------- #
# Tier 1 — invisibility when unused                                           #
# --------------------------------------------------------------------------- #


class TestTier1Invisibility:
    def test_corpus_json_carries_no_stray_second_order_keys(self, tomos):
        """Every corpus EGI re-saves byte-identically (modulo the known
        pre-existing layout_deltas extra key), and only the allowlisted
        exemplars carry sort/quotation keys."""
        bearers = set()
        for p in TOMOS_ROOT.rglob("*.egi.json"):
            raw = json.loads(p.read_text())
            egi = from_dict(raw)
            again = to_dict(egi)
            raw_cmp = {k: v for k, v in raw.items() if k != "layout_deltas"}
            assert json.dumps(raw_cmp, sort_keys=True) == json.dumps(
                again, sort_keys=True
            ), f"{p} does not re-save byte-identically"
            if "sort" in raw or "quotation" in raw:
                # resolve the owning UoD directory (the ancestor carrying
                # uod.meta.json), so chain state files attribute correctly
                owner = p.parent
                while owner != TOMOS_ROOT and not (owner / "uod.meta.json").exists():
                    owner = owner.parent
                bearers.add(owner.name)
        unknown = {
            b for b in bearers
            if not any(x in b for x in QUOTATION_EXEMPLARS)
        }
        assert not unknown, (
            f"quotation-bearing record(s) outside the named allowlist: "
            f"{sorted(unknown)} — add knowingly or investigate"
        )

    def test_first_order_generation_and_identity_unchanged(self):
        src = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ] (P *x) (Q x)'
        egi = parse_egif(src)
        text = generate_egif(egi)
        assert generate_egif(parse_egif(text)) == text
        assert same_graph(egi, parse_egif(text))


# --------------------------------------------------------------------------- #
# Tier 2 — erasure projection: the layer licenses nothing                     #
# --------------------------------------------------------------------------- #


def _verdict(egi, proposal: str, *, closed=True) -> str:
    facts, _ = materialize_egi(egi)
    oracle = CorpusOracle([("M", facts)], closed=closed)
    return evaluate(parse_egif(proposal), oracle, closed=closed).verdict.value


class TestTier2ErasureProjection:
    def test_projection_recovers_the_never_quoted_host(self):
        host = parse_egif('(swan "Alba") (white "Alba")')
        law = parse_egif('~[ (swan *x) ~[ (black x) ] ]')
        quoted, _mark, _cut = scribe_quotation(host, "old_law", law)
        assert same_graph(project_first_order(quoted), host)

    def test_quoted_law_licenses_no_new_assertion(self):
        """The heart of A3: M with a quoted subsumption law derives exactly
        what M without it derives — the oval fires no rule, changes no
        verdict."""
        m = parse_egif('(swan "Alba")')
        law = parse_egif('~[ (swan *x) ~[ (white x) ] ]')
        quoted_m, _mark, _cut = scribe_quotation(m, "law_exhibit", law)

        # the same law ASSERTED (first-order ink) does license the derivation
        asserted_m = parse_egif('(swan "Alba") ~[ (swan *x) ~[ (white x) ] ]')
        assert _verdict(asserted_m, '(white "Alba")') == "true"

        # quoted, it licenses nothing: verdicts equal the projection's
        for proposal in ['(white "Alba")', '(swan "Alba")']:
            assert _verdict(quoted_m, proposal) == _verdict(
                project_first_order(quoted_m), proposal
            )
        assert _verdict(quoted_m, '(white "Alba")') == "false"  # closed world

    def test_swan_exemplar_does_not_derive_its_exhibited_law(self, tomos):
        """The corpus case: swan_third_tense EXHIBITS the withdrawn law; its
        M-view must not apply it. Alba-style consequence stays undirected."""
        uod = tomos.load_uod("swan_third_tense", attest=False)
        assert uod is not None
        egi = uod.current_egi
        assert egi.quotation, "the exemplar should carry a core quotation"
        facts, report = materialize_egi(egi)
        assert report.rules_applied == 0
        assert any(s.reason == "quotation" for s in report.skipped)
        # and the projection's verdicts equal the exhibit-bearing graph's
        for proposal in ['(superseded "M_swan_law" "Nox")']:
            assert _verdict(egi, proposal) == _verdict(
                project_first_order(egi), proposal
            )

    def test_settlement_reading_ignores_quoted_ink(self, tomos):
        """modal reading: a relation scribed ONLY inside an oval is not
        scribed — the forcing exemplar's φ shapes must not leak into the
        modal columns."""
        from modal_query import scribes_relation

        uod = tomos.load_uod("forcing_forces", attest=False)
        egi = uod.current_egi
        # 'one'/'zero'/'two' live only inside the quotation ovals
        for quoted_rel in ("one", "zero", "two"):
            assert not scribes_relation(quoted_rel)(egi)
        assert scribes_relation("forces")(egi)  # host ink counts


# --------------------------------------------------------------------------- #
# Tier 3 — the corpus-facing rules restraint                                  #
# --------------------------------------------------------------------------- #


class TestTier3RulesRestraint:
    def test_exemplar_chains_replay_and_attest(self, tomos):
        """Each quotation exemplar's chain loads with its QUOTE step recorded
        as a neutral act, and the final state equals the saved current EGI —
        the record is earned, not asserted."""
        from proof_character import NEUTRAL_RULES

        assert "QUOTE" in NEUTRAL_RULES
        for uod_id in sorted(QUOTATION_EXEMPLARS):
            chain = tomos.load_chain(uod_id)
            assert chain is not None, uod_id
            quote_steps = [s for s in chain.steps if s.rule_name == "QUOTE"]
            assert quote_steps, f"{uod_id} carries no explicit QUOTE step"
            for s in quote_steps:
                assert s.parameters.get("act") == "quotation"
                assert s.parameters.get("earned") is True
            uod = tomos.load_uod(uod_id, attest=False)
            assert same_graph(chain.current_egi, uod.current_egi)

    def test_ins_into_an_exemplars_oval_refused(self, tomos):
        from rule_interaction import insert_from_egif

        uod = tomos.load_uod("swan_third_tense", attest=False)
        egi = uod.current_egi
        oval_id = next(iter(egi.quotation))
        r = insert_from_egif(egi, oval_id, "(Sneak *s)")
        assert not r.success

    def test_linear_generators_refuse_the_bearing_graph(self, tomos):
        from second_order_limits import SecondOrderNotInLinearForm

        uod = tomos.load_uod("swan_third_tense", attest=False)
        with pytest.raises(SecondOrderNotInLinearForm):
            generate_egif(uod.current_egi)
        # ...and accept its projection, with the exhibit erased
        text = generate_egif(project_first_order(uod.current_egi))
        assert "superseded" in text

    def test_linear_forms_service_serves_the_projection_with_named_limit(
        self, tomos
    ):
        from web_api.services.linear_forms import linear_forms

        uod = tomos.load_uod("swan_third_tense", attest=False)
        payload = linear_forms(uod.current_egi)
        assert "second_order_limit" in payload
        assert payload["forms"]["egif"]["ok"] is True
        assert "superseded" in payload["forms"]["egif"]["text"]
        # a first-order graph's payload carries no limit note
        plain = linear_forms(parse_egif("(P *x)"))
        assert "second_order_limit" not in plain


    def test_reduction_forcing_forces_uses_only_bmin_machinery(self, tomos):
        """**Reduction Theorem Test 1:** Verify that `forcing_forces` exemplar
        reduces to B-min's quotation device (no B-full features needed).

        B-min machinery includes:
        - sort: vertex can carry "proposition" | "abstraction" (default individual)
        - quotation: cut can hold a graph-valued area (one oval per name, no nesting)
        - Six Dau rules (ERA, INS, IT+, IT-, DC+, DC-) sort-preserving
        - QUOTE step recording the quotation as neutral act

        The claim: `forcing_forces` uses only this machinery. Test verifies:
        1. Every chain step is either a Dau rule or QUOTE (no B-full ops)
        2. No quotation-in-quotation (B-min limit)
        3. Peel verdicts identical on quotation-bearing vs. projected graphs
        4. No rules derive from quoted ink (erasure projection property)
        """
        from proof_character import NEUTRAL_RULES

        uod = tomos.load_uod("forcing_forces", attest=False)
        egi = uod.current_egi
        chain = tomos.load_chain("forcing_forces")

        assert chain is not None
        assert egi.quotation, "forcing_forces should carry core quotations"

        # 1. Verify chain steps use only Dau rules + QUOTE
        dau_rules = {"ERA", "INS", "IT+", "IT-", "DC+", "DC-"}
        for step in chain.steps:
            rule_name = step.rule_name
            assert (
                rule_name in dau_rules or rule_name == "QUOTE"
            ), f"Unexpected rule {rule_name} — not a Dau rule or QUOTE"
            # QUOTE steps must be marked neutral
            if rule_name == "QUOTE":
                assert rule_name in NEUTRAL_RULES
                assert step.parameters.get("act") == "quotation"

        # 2. Verify no quotation-in-quotation (B-min named limit)
        # The core validation already rejects nested quotations during load.
        # If we got here, this property holds.
        # Verify: for each quotation-cut, its parent context is not also a quotation
        for cut_id in egi.quotation:
            parent = egi.get_context(cut_id)
            assert (
                parent not in egi.quotation
            ), f"Quotation cut {cut_id} nests inside quotation {parent}"

        # 3. Verify peel verdicts are identical on both graphs
        # The projection removes quotation ink; verdicts should not change
        proj = project_first_order(egi)
        proposal = '(forces "Rock" "Paper")'  # The base relation in forcing_forces
        verdict_with_quotation = _verdict(egi, proposal)
        verdict_projected = _verdict(proj, proposal)
        assert (
            verdict_with_quotation == verdict_projected
        ), f"Verdicts differ: {verdict_with_quotation} vs {verdict_projected}"

        # 4. Verify projection's verdicts are robust across multiple proposals
        # If verdicts are stable under projection, the quotation ink is not licensing new inferences
        test_proposals = [
            '(forces "Rock" "Paper")',
            '(forces "Paper" "Scissors")',
            '(one "s1")',  # Inside quotation — should be false in closed world
        ]
        for prop in test_proposals:
            v_with = _verdict(egi, prop)
            v_without = _verdict(proj, prop)
            assert v_with == v_without, (
                f"Verdict differs for {prop}: "
                f"with quotation={v_with}, projected={v_without}"
            )

        # **CONCLUSION: Reduction theorem verified for `forcing_forces`**
        # forcing_forces is fully expressible using only B-min machinery:
        # - sort on vertices (for propositional naming)
        # - quotation cuts (one oval per name, no nesting)
        # - Six Dau rules (sort-preserving)
        # - QUOTE steps marking the quotation as earned neutral act
        # No B-full features required.

    def test_reduction_swan_third_tense_uses_only_bmin_machinery(self, tomos):
        """**Reduction Theorem Test 2:** Verify `swan_third_tense` exemplar
        reduces to B-min machinery. Same checks as Test 1."""
        from proof_character import NEUTRAL_RULES

        uod = tomos.load_uod("swan_third_tense", attest=False)
        egi = uod.current_egi
        chain = tomos.load_chain("swan_third_tense")

        assert chain is not None
        assert egi.quotation, "swan_third_tense should carry core quotations"

        # 1. Verify chain steps use only Dau rules + QUOTE
        dau_rules = {"ERA", "INS", "IT+", "IT-", "DC+", "DC-"}
        for step in chain.steps:
            rule_name = step.rule_name
            assert (
                rule_name in dau_rules or rule_name == "QUOTE"
            ), f"Unexpected rule {rule_name}"
            if rule_name == "QUOTE":
                assert rule_name in NEUTRAL_RULES
                assert step.parameters.get("act") == "quotation"

        # 2. Verify no quotation-in-quotation
        for cut_id in egi.quotation:
            parent = egi.get_context(cut_id)
            assert parent not in egi.quotation

        # 3. Verify peel verdicts identical on both graphs
        proj = project_first_order(egi)
        test_proposals = [
            '(superseded "M_swan_law" "Nox")',
            '(swan "Alba")',
            '(white "Alba")',
        ]
        for prop in test_proposals:
            v_with = _verdict(egi, prop)
            v_without = _verdict(proj, prop)
            assert v_with == v_without

        # **CONCLUSION: Reduction theorem verified for `swan_third_tense`**

    def test_reduction_peirce_law_commentary_uses_only_bmin_machinery(self, tomos):
        """**Reduction Theorem Test 3:** Verify `peirce_law_commentary` exemplar
        uses only B-min (core) or Stage ⓪ (overlay) machinery.

        NOTE: This exemplar uses the Stage ⓪ overlay, not B-min core quotations.
        Both are considered part of the B-min+ denominator (core sort + quotation,
        or overlay marks). Test verifies it does NOT use B-full (nested quotations,
        multi-name ovals, etc.)."""
        from proof_character import NEUTRAL_RULES

        uod = tomos.load_uod("peirce_law_commentary", attest=False)
        egi = uod.current_egi
        chain = tomos.load_chain("peirce_law_commentary")
        overlay_quotations = tomos.load_quotations("peirce_law_commentary")

        assert chain is not None
        # Either core quotation or overlay quotations should exist
        has_core_quotation = bool(egi.quotation)
        has_overlay = bool(overlay_quotations)
        assert has_core_quotation or has_overlay, (
            "peirce_law_commentary should carry quotations (core or overlay)"
        )

        # 1. Verify chain steps use only Dau rules + QUOTE
        dau_rules = {"ERA", "INS", "IT+", "IT-", "DC+", "DC-"}
        for step in chain.steps:
            rule_name = step.rule_name
            assert (
                rule_name in dau_rules or rule_name == "QUOTE"
            ), f"Unexpected rule {rule_name}"
            if rule_name == "QUOTE":
                assert rule_name in NEUTRAL_RULES
                assert step.parameters.get("act") == "quotation"

        # 2. Verify no quotation-in-quotation (core only; overlay has no nesting)
        if has_core_quotation:
            for cut_id in egi.quotation:
                parent = egi.get_context(cut_id)
                assert parent not in egi.quotation

        # 3. Verify peel verdicts identical on both graphs (if core quotations exist)
        if has_core_quotation:
            proj = project_first_order(egi)
            test_proposals = [
                '(cites "peirce_law" "Peirce-1885")',
            ]
            for prop in test_proposals:
                v_with = _verdict(egi, prop)
                v_without = _verdict(proj, prop)
                assert v_with == v_without

        # 4. Verify overlay quotations are simple (no B-full features)
        if has_overlay:
            for mark in overlay_quotations:
                # Overlay quotations should not nest (no impredicative flag set)
                assert mark.get("impredicative") is None, (
                    f"Overlay quotation {mark['element_id']} has impredicative set"
                )
                # Should be single-name (kind in {uod, defn, etc})
                assert mark.get("kind") in (
                    "uod",
                    "defn",
                    "mention",
                ), f"Unexpected overlay quotation kind: {mark.get('kind')}"

        # **CONCLUSION: Reduction theorem verified for `peirce_law_commentary`**
        # Uses Stage ⓪ overlay (part of B-min+ denominator), no B-full features.


class TestClosureGuardOnExpandedSet:
    """Docket ①: the guard must see what will actually be erased (Examination IV).

    A direct-engine ERA of ordinary host ink (the ``superseded`` edge on
    ``swan_third_tense``) closes over the quoting name — the for-erasure
    expansion pulls a vertex argument into the erasure set from outside the
    raw selection, without pulling in the vertex's oval. Left unrefused, the
    oval survives with its quoting-name entry silently pruned: a mention
    demoted to an asserted negation."""

    def test_direct_engine_era_of_host_ink_refuses_via_expanded_closure(self, tomos):
        uod = tomos.load_uod("swan_third_tense", attest=False)
        egi = uod.current_egi
        superseded = next(e for e in egi.E if egi.rel.get(e.id) == "superseded")
        ctx = TransformationContext(
            source_egi=egi,
            target_area=egi.get_context(superseded.id),
            selected_subgraph=frozenset({superseded.id}),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0,
        )
        result = ErasureRule().apply_transformation(ctx)
        assert not result.success
        assert "quotation" in (result.error_message or "").lower()

    def test_deiteration_delegating_path_cannot_demote_the_oval(self, tomos):
        uod = tomos.load_uod("swan_third_tense", attest=False)
        egi = uod.current_egi
        superseded = next(e for e in egi.E if egi.rel.get(e.id) == "superseded")
        ctx = TransformationContext(
            source_egi=egi,
            target_area=egi.get_context(superseded.id),
            selected_subgraph=frozenset({superseded.id}),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0,
        )
        result = DeiterationRule().apply_transformation(ctx)
        assert not result.success
