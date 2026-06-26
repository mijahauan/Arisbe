"""The diagram↔narration correspondence check — a minimal scorer.

This is the prototype of the validation harness designed in
``docs/THE_MINIMAL_IN_VIEW_SET.md`` §10: the keystone that turns the
in-view rules of §9 from *assertions about how people reason* into
*tested claims*.

The thesis (§10): **a line of thought, narrated by an expert, is the
serialized trace of the same reasoning a diagram-chain records** — so the
sets Arisbe computes along a proof's diagram-chain (what is *in focus*,
what is merely *referenced*) should track the expert's narrated
present/referenced sets along the matching narration-chain.  Where they
disagree across a corpus, the §9 rule is wrong.

Why a *worked proof chain* is the right first fixture rather than a single
large graph: the spatial overview budget (S1) only bites once a graph
exceeds ~4 visible chunks, and the ground-truth fixture
(``tomos/universes/theorem_praeclarum``) is a four-cut Alpha derivation that
sits *under* budget — so nothing collapses spatially.  What the fixture
*does* exercise, step by step, is the **diachronic** half: each move has a
narrated locus ("iterate (P⊃R) into the inner cut") and an independently
computable diagram delta (the rule's added / removed / operated elements).
This module checks that the narration's salient set tracks that delta — the
operational EG↔DRT step-update bridge in miniature (a narrated proof step is
a DRS update; its new vs. reused discourse referents are the rule's added vs.
reused graph elements; Kamp & Reyle).

Each narration mention is bucketed into one of **three Centering/DRT roles**
(a structure the corpus run *forced* — a first two-role parse failed
systematically on every eliminative/macro chain, the misses all a third role):
the utterance's **operated** center (must land in the focal set Φ), its
spatial/back-referential **locative** anchor (must resolve to standing Ρ), and
the *discourse-old* **restatement** of the resulting proposition (must be
in-view V).  Run across the corpus of narrated worked chains, all three roles
hold (100 %); the one residual — a squashed macro move whose narrated stance no
longer matches its net delta — is the D4 squash phenomenon, reported not hidden.

**Honest scope of this prototype** (see ``honest_limits``):

* Alignment is **deterministic**, not the heuristic ``nl_to_logic`` LLM
  bridge — it keys narration tokens to graph elements by relation name
  (``egi.rel``).  That is sound for the controlled Peircean register of a
  transcribed Dau derivation (small alphabets like {P,Q,R,S} / {M,=}); free
  expert narration would need the LLM bridge, and its mapping errors must
  then be *reported, not hidden* (§10 honest limits).
* A **single** (transcribed) narration per step, not a corpus of narrators —
  so we report *alignment*, never *optimality*, and never inter-narrator
  agreement.
* Every corpus chain is sub-budget, so the **spatial** metrics (Centering
  overlap against a *collapsed* focal set) degenerate; we test the diachronic
  metrics the fixtures can actually falsify and say so.  Restatement-in-view is
  the metric that becomes discriminating on a super-budget chain.

The module is **read-only**: it observes immutable EGIs and the slim on-disk
``chain.jsonl`` narration.  It mutates nothing, asserts no truth, and is the
"fourth thing" — navigation/measurement over attested objects, never a
corpus-promotion source.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

from egi_core_dau import RelationalGraphWithCuts, ElementID
from egi_io import load_egi_json


# ----------------------------------------------------------------------------
# Loading a worked chain (states + per-step narration) from a tomos UoD dir.
# We parse the slim ``chain.jsonl`` directly rather than hydrating the protected
# history class — narration lives in ``parameters.description`` / the Peirce
# label / ``user_annotation``, exactly the §10 "already half-built" slots.
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class WorkedStep:
    """One move ``G_{i-1} →r G_i`` with its narration and the gold locus."""

    step_id: str
    rule_name: str
    peirce_label: Optional[str]
    narration: str
    selection: List[ElementID]
    from_state_id: str
    to_state_id: str
    from_egi: RelationalGraphWithCuts
    to_egi: RelationalGraphWithCuts


@dataclass(frozen=True)
class WorkedChain:
    name: str
    initial_state_id: str
    steps: List[WorkedStep]


def _state_path(uod_dir: Path, state_id: str) -> Path:
    return uod_dir / "history" / "states" / f"{state_id}.egi.json"


def load_worked_chain(uod_dir: str | Path) -> WorkedChain:
    """Load the ``chain.jsonl`` + per-state EGIs of a tomos UoD directory."""
    uod_dir = Path(uod_dir)
    chain_file = uod_dir / "history" / "chain.jsonl"
    if not chain_file.exists():
        raise FileNotFoundError(f"no worked chain at {chain_file}")

    records = [json.loads(line) for line in chain_file.read_text().splitlines() if line.strip()]
    initial = next((r for r in records if r.get("type") == "initial"), None)
    if initial is None:
        raise ValueError(f"{chain_file}: no initial record")
    initial_state_id = initial["initial_state_id"]

    cache: Dict[str, RelationalGraphWithCuts] = {}

    def egi(state_id: str) -> RelationalGraphWithCuts:
        if state_id not in cache:
            cache[state_id] = load_egi_json(_state_path(uod_dir, state_id))
        return cache[state_id]

    steps: List[WorkedStep] = []
    for r in records:
        if r.get("type") != "step":
            continue
        params = r.get("parameters", {})
        narration = params.get("description") or r.get("user_annotation") or ""
        steps.append(
            WorkedStep(
                step_id=r["step_id"],
                rule_name=r.get("rule_name", params.get("rule", "?")),
                peirce_label=params.get("peirce_label"),
                narration=narration,
                selection=list(params.get("selection") or []),
                from_state_id=r["from_state_id"],
                to_state_id=r["to_state_id"],
                from_egi=egi(r["from_state_id"]),
                to_egi=egi(r["to_state_id"]),
            )
        )

    return WorkedChain(name=uod_dir.name, initial_state_id=initial_state_id, steps=steps)


# ----------------------------------------------------------------------------
# Arisbe's side: the focal set Φ and the referenced set Ρ of a step.
# ----------------------------------------------------------------------------


def _all_ids(egi: RelationalGraphWithCuts) -> Set[ElementID]:
    return {v.id for v in egi.V} | {e.id for e in egi.E} | {c.id for c in egi.Cut}


def _parent_of(egi: RelationalGraphWithCuts) -> Dict[ElementID, ElementID]:
    parent: Dict[ElementID, ElementID] = {}
    for owner, children in egi.area.items():
        for child in children:
            parent[child] = owner
    return parent


def _enclosing_cut(eid: ElementID, parent: Dict[ElementID, ElementID],
                   sheet: ElementID) -> Optional[ElementID]:
    """The nearest *cut* ancestor of ``eid`` (S3 sticky ground), or None."""
    cur = parent.get(eid)
    while cur is not None and cur != sheet:
        return cur
    return None


def _subtree(egi: RelationalGraphWithCuts, root: ElementID) -> Set[ElementID]:
    """All elements transitively contained in ``root`` (excluding root)."""
    out: Set[ElementID] = set()
    stack = list(egi.area.get(root, []))
    while stack:
        eid = stack.pop()
        if eid in out:
            continue
        out.add(eid)
        stack.extend(egi.area.get(eid, []))
    return out


@dataclass(frozen=True)
class StepSets:
    """The structural decomposition of a step, all exact functions of the two
    EGIs and the recorded gold ``selection``."""

    added: Set[ElementID]       # in G_i, not in G_{i-1}
    removed: Set[ElementID]     # in G_{i-1}, not in G_i
    selection: Set[ElementID]   # the gold operated-on locus
    focal: Set[ElementID]       # Φ: delta ∪ selection ∪ sticky enclosing cut
    referenced: Set[ElementID]  # Ρ: standing material reused (iteration source)


def step_sets(step: WorkedStep) -> StepSets:
    """Compute Arisbe's focal Φ and referenced Ρ sets for ``step``.

    * Φ (focal) = the move's **delta** (added ∪ removed) ∪ the gold
      **selection** ∪ the **sticky enclosing cut** of each (S3: keep the
      enclosing scope co-present) ∪ the **effect set** (D3: survivors whose
      *enclosing scope changed* because a cut was inserted/erased around them
      — the elements an eliminative move is narratively *about*, e.g. "erase
      the double cut, landing Q on the sheet").  This is the predicted
      *attention center* — what a reader must be looking at to follow the move.
    * Ρ (referenced) = **standing material reused** by the move: any element
      that *persists* across the move and bears a relation name shared with a
      delta element (the iteration / deiteration source — "a copy of the
      enclosing Q").  Generic persisting context is *not* referenced; only
      what the move points back at.
    """
    from_ids = _all_ids(step.from_egi)
    to_ids = _all_ids(step.to_egi)
    added = to_ids - from_ids
    removed = from_ids - to_ids
    selection = set(step.selection)
    persisting = from_ids & to_ids

    # Sticky enclosing cut (S3) for each focal element, in whichever EGI holds it.
    focal: Set[ElementID] = set(added) | set(removed) | set(selection)
    for egi, ids in ((step.to_egi, added | selection), (step.from_egi, removed)):
        parent = _parent_of(egi)
        for eid in list(ids):
            enc = _enclosing_cut(eid, parent, egi.sheet)
            if enc is not None:
                focal.add(enc)

    # D3 effect set: when a cut is added or removed, the *surviving* elements it
    # contained have a changed enclosing scope (a DC+ encloses standing P,Q — even
    # nested inside ~[(Q)]; a DC- frees them onto a shallower sheet).  Those
    # scope-changed survivors are the narrative center of the move, so they belong
    # in Φ.  Scoped to the subtree of each changed cut, intersected with survivors
    # (inserted/erased structure is already in the delta) — the frame rule, not
    # "everything".
    added_cuts = {c.id for c in step.to_egi.Cut} & added
    removed_cuts = {c.id for c in step.from_egi.Cut} & removed
    for c in added_cuts:
        focal |= _subtree(step.to_egi, c) & persisting
    for c in removed_cuts:
        focal |= _subtree(step.from_egi, c) & persisting

    # Referenced Ρ: persisting edges whose relation name matches a delta edge's.
    delta_names = {
        step.to_egi.rel.get(e) for e in added if e in step.to_egi.rel
    } | {step.from_egi.rel.get(e) for e in removed if e in step.from_egi.rel}
    delta_names.discard(None)
    referenced: Set[ElementID] = {
        e.id for e in step.from_egi.E
        if e.id in persisting and step.from_egi.rel.get(e.id) in delta_names
    }

    return StepSets(added=added, removed=removed, selection=selection,
                    focal=focal, referenced=referenced)


# ----------------------------------------------------------------------------
# The narration side: salient relation tokens + reference vs. introduce cues.
# ----------------------------------------------------------------------------

# Cue lexicon (§10): words that mark a *back-reference* to material already in
# the discourse vs. words that *introduce* fresh material.  Deliberately small
# and transparent — the controlled register of a transcribed Dau derivation.
_REFERENCE_CUES = (
    "iterate", "iterated", "deiterate", "deiterated", "copy", "enclosing",
    "recall", "as before", "similarly", "around",
)
_INTRODUCE_CUES = (
    "insert", "empty double cut", "the antecedent", "place",
)
# Erasure is a *reference* to redundant standing material (you erase what is
# already there), so DC-/ERA/IT- narrations point back, not forward.
_ERASE_CUES = ("erase", "deiterate")

# A narrated proof step splits its mentions into THREE roles (a structure the
# corpus run forced — the two-role model failed systematically on eliminative and
# macro moves).  This is Centering + DRT: the utterance's *center* (operated), its
# spatial/back-referential *anchor* (locative), and *discourse-old restatement* of
# the resulting proposition (restatement).
#
# Locative markers — a token after the earliest is naming a *location/address*
# ("into the cut holding (P⊃R)", "around S", "a copy of the enclosing Q").
_LOCATIVE_MARKERS = ("into", "around", "holding", "enclosing", "copy of", "of the")
# Restatement markers — a token after the earliest is *restating the resulting
# proposition* ("→ every S is P", ", leaving (R)", "landing S on the sheet",
# "to complete (P⊃Q)⊃P", "the bare theorem e = f", "∎").  A dash/arrow or a
# result verb introduces the upshot, not a new operated object.
_RESTATEMENT_MARKERS = (
    "—", "→", " - ", "leaving", "landing", "reaching", "to complete",
    "completing", "asserted on the sheet", "the bare theorem", "∎",
)


@dataclass(frozen=True)
class NarrationParse:
    tokens: Set[str]                 # all relation names mentioned (e.g. {"P","R"})
    operated_tokens: Set[str]        # the move's object — should land in Φ
    locative_tokens: Set[str]        # address/back-reference — should land in Ρ
    restatement_tokens: Set[str]     # restated upshot — should be in-view (V)
    references_prior: bool           # narration carries a back-reference cue
    introduces: bool                 # narration carries an introduction cue


def _relation_alphabet(chain: WorkedChain) -> Set[str]:
    names: Set[str] = set()
    for step in chain.steps:
        names.update(step.from_egi.rel.values())
        names.update(step.to_egi.rel.values())
    return names


def _token_positions(text: str, name: str) -> List[int]:
    # A relation token is a whole word: not flanked by letters (so "S" never
    # matches inside "Insert"), and — for the identity relation "=" — not the
    # substitution operator ":=" (binding syntax, not a predicate occurrence).
    pat = rf"(?<![A-Za-z:]){re.escape(name)}(?![A-Za-z=])"
    return [m.start() for m in re.finditer(pat, text)]


def parse_narration(step: WorkedStep, alphabet: Set[str]) -> NarrationParse:
    """Deterministically parse one narration into its operated vs. locative
    relation tokens (keyed to ``egi.rel``) and its reference/introduce cues.

    The split is the heart of the prototype.  Each mentioned predicate is bucketed
    by the region of its **earliest** occurrence: before the first locative *and*
    restatement marker → **operated** (the move's object, must be in Φ); in the
    locative region → **locative** (the address, must resolve to standing Ρ); in
    the restatement region → **restatement** (the upshot proposition, must be
    in-view V).  Conflating these is exactly the error the first crude
    "mentioned ⊆ focal" metric made; the corpus run showed the two-role model
    failing on every eliminative/macro move, forcing the third role.
    """
    text = step.narration
    low = text.lower()

    def earliest(markers) -> int:
        hits = [low.find(m.lower()) for m in markers]
        hits = [h for h in hits if h >= 0]
        return min(hits) if hits else len(text)

    loc_start = earliest(_LOCATIVE_MARKERS)
    restate_start = earliest(_RESTATEMENT_MARKERS)

    tokens: Set[str] = set()
    operated: Set[str] = set()
    locative: Set[str] = set()
    restatement: Set[str] = set()
    for name in alphabet:
        positions = _token_positions(text, name)
        if not positions:
            continue
        tokens.add(name)
        pos = min(positions)  # the earliest occurrence decides the role
        if pos >= restate_start:
            restatement.add(name)
        elif pos >= loc_start:
            locative.add(name)
        else:
            operated.add(name)

    references_prior = any(c in low for c in _REFERENCE_CUES) or any(
        c in low for c in _ERASE_CUES
    )
    introduces = any(c in low for c in _INTRODUCE_CUES)

    return NarrationParse(tokens=tokens, operated_tokens=operated,
                          locative_tokens=locative, restatement_tokens=restatement,
                          references_prior=references_prior, introduces=introduces)


# ----------------------------------------------------------------------------
# Scoring.
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class StepScore:
    step_id: str
    rule_name: str
    narration: str
    operated_tokens: Set[str]
    locative_tokens: Set[str]
    restatement_tokens: Set[str]
    # Metric A — center coverage: each *operated* relation token has ≥1 bearer
    # in the focal set Φ.
    covered_operated: Set[str]
    uncovered_operated: Set[str]
    # Metric C — locative grounding: each *locative* token resolves to standing
    # material (a bearer that persists across the move), not to freshly-added
    # structure — the fold-matches-reference check (§10 metric 2).
    grounded_locative: Set[str]
    ungrounded_locative: Set[str]
    # Metric D — restatement-in-view: each *restated* token (the upshot
    # proposition) has a bearer in the visible graph V.  On a sub-budget graph V
    # is the whole graph, so this is ~always satisfied; it becomes discriminating
    # on a super-budget chain, where a restated item must NOT have been collapsed
    # (fold-matches-reference, restatement half).
    invview_restatement: Set[str]
    offview_restatement: Set[str]
    # Metric B — reference alignment: does the narration's introduce/reference
    # stance match the structural move (introduce → adds; reference → reuses or
    # removes standing material)?
    narr_references_prior: bool
    narr_introduces: bool
    struct_adds: bool
    struct_reuses_or_removes: bool
    reference_aligned: bool
    sets: StepSets = field(repr=False)

    @property
    def tokens(self) -> Set[str]:
        return self.operated_tokens | self.locative_tokens | self.restatement_tokens

    @property
    def center_coverage(self) -> float:
        n = len(self.covered_operated) + len(self.uncovered_operated)
        return 1.0 if n == 0 else len(self.covered_operated) / n

    @property
    def locative_grounding(self) -> float:
        n = len(self.grounded_locative) + len(self.ungrounded_locative)
        return 1.0 if n == 0 else len(self.grounded_locative) / n

    @property
    def restatement_in_view(self) -> float:
        n = len(self.invview_restatement) + len(self.offview_restatement)
        return 1.0 if n == 0 else len(self.invview_restatement) / n


def _bearers_in(ids: Set[ElementID], egis: Sequence[RelationalGraphWithCuts],
                token: str) -> bool:
    for egi in egis:
        for e in egi.E:
            if egi.rel.get(e.id) == token and e.id in ids:
                return True
    return False


def score_step(step: WorkedStep, alphabet: Set[str]) -> StepScore:
    sets = step_sets(step)
    parse = parse_narration(step, alphabet)

    egis = (step.from_egi, step.to_egi)
    # Metric A: operated tokens must have a bearer in the focal set Φ.
    covered = {t for t in parse.operated_tokens if _bearers_in(sets.focal, egis, t)}
    uncovered = parse.operated_tokens - covered

    # Metric C: locative tokens must resolve to standing material — a bearer
    # that persists across the move (present in both EGIs), i.e. pre-existing,
    # not something this move introduced.
    standing = _all_ids(step.from_egi) & _all_ids(step.to_egi)
    grounded = {t for t in parse.locative_tokens if _bearers_in(standing, egis, t)}
    ungrounded = parse.locative_tokens - grounded

    # Metric D: restated tokens must be in-view — a bearer somewhere in the
    # resulting visible graph V (the whole of G_i on a sub-budget chain).
    visible = _all_ids(step.to_egi)
    in_view = {t for t in parse.restatement_tokens
               if _bearers_in(visible, (step.to_egi,), t)}
    off_view = parse.restatement_tokens - in_view

    struct_adds = bool(sets.added)
    struct_reuses_or_removes = bool(sets.referenced) or bool(sets.removed)

    # Reference alignment: the narration's stance must be witnessed structurally.
    #  - if it introduces, the move must add structure;
    #  - if it references prior material, the move must reuse or remove standing
    #    structure.  A move can do both (e.g. INS adds while naming a locus).
    aligned = True
    if parse.introduces and not struct_adds:
        aligned = False
    if parse.references_prior and not struct_reuses_or_removes:
        aligned = False

    return StepScore(
        step_id=step.step_id,
        rule_name=step.rule_name,
        narration=step.narration,
        operated_tokens=parse.operated_tokens,
        locative_tokens=parse.locative_tokens,
        restatement_tokens=parse.restatement_tokens,
        covered_operated=covered,
        uncovered_operated=uncovered,
        grounded_locative=grounded,
        ungrounded_locative=ungrounded,
        invview_restatement=in_view,
        offview_restatement=off_view,
        narr_references_prior=parse.references_prior,
        narr_introduces=parse.introduces,
        struct_adds=struct_adds,
        struct_reuses_or_removes=struct_reuses_or_removes,
        reference_aligned=aligned,
        sets=sets,
    )


@dataclass(frozen=True)
class ChainReport:
    chain_name: str
    steps: List[StepScore]
    sub_budget: bool  # the graph never exceeds the in-view budget (spatial
                      # metrics degenerate; see honest_limits)

    @property
    def mean_center_coverage(self) -> float:
        if not self.steps:
            return 1.0
        return sum(s.center_coverage for s in self.steps) / len(self.steps)

    @property
    def mean_locative_grounding(self) -> float:
        if not self.steps:
            return 1.0
        return sum(s.locative_grounding for s in self.steps) / len(self.steps)

    @property
    def mean_restatement_in_view(self) -> float:
        if not self.steps:
            return 1.0
        return sum(s.restatement_in_view for s in self.steps) / len(self.steps)

    @property
    def reference_alignment_rate(self) -> float:
        if not self.steps:
            return 1.0
        return sum(1 for s in self.steps if s.reference_aligned) / len(self.steps)

    @property
    def center_continuity(self) -> float:
        """Centering's CONTINUE preference: fraction of adjacent step pairs
        whose salient relation-token sets overlap (the proof 'stays on topic').
        Descriptive, not a pass/fail metric."""
        if len(self.steps) < 2:
            return 1.0
        cont = 0
        for a, b in zip(self.steps, self.steps[1:]):
            if a.tokens & b.tokens:
                cont += 1
        return cont / (len(self.steps) - 1)


# The in-view budget (S1/S2): Cowan's ~4 chunks, ≤7 for browsing.  The spatial
# overview only bites when a single *area* presents more than this many sibling
# chunks, OR nesting runs deeper than this — a folded subgraph is one chunk
# (S2), so raw element counts overstate.  Below this the spatial metrics
# degenerate and only the diachronic metrics are live.
_BUDGET_CHUNKS = 7


def _max_fanout(egi: RelationalGraphWithCuts) -> int:
    return max((len(children) for children in egi.area.values()), default=0)


def _max_depth(egi: RelationalGraphWithCuts) -> int:
    parent = _parent_of(egi)
    depths = []
    for cut in egi.Cut:
        d, cur = 0, cut.id
        while cur in parent and cur != egi.sheet:
            cur = parent[cur]
            d += 1
        depths.append(d)
    return max(depths, default=0)


def check_chain(chain: WorkedChain) -> ChainReport:
    """Score every step of a worked chain against its narration."""
    alphabet = _relation_alphabet(chain)
    scores = [score_step(step, alphabet) for step in chain.steps]
    budget_pressure = max(
        (max(_max_fanout(s.to_egi), _max_depth(s.to_egi)) for s in chain.steps),
        default=0,
    )
    return ChainReport(chain_name=chain.name, steps=scores,
                       sub_budget=budget_pressure <= _BUDGET_CHUNKS)


def honest_limits(report: ChainReport) -> List[str]:
    """The standing caveats this prototype must surface, never hide (§10)."""
    limits = [
        "Deterministic relation-name alignment (egi.rel), not the nl_to_logic "
        "LLM bridge — sound only for the controlled Peircean register of a "
        "transcribed derivation; free narration needs the LLM bridge with "
        "reported mapping errors.",
        "A single transcribed narration per step, not a corpus — alignment is "
        "tested, not optimality, and inter-narrator agreement is untested.",
        "Token-level salience: a mentioned name is credited to any bearer, not "
        "to the specific copy a phrase points at ('the iterated (P⊃R)').",
    ]
    if report.sub_budget:
        limits.append(
            "This chain is sub-budget (≤7 visible chunks throughout), so the "
            "SPATIAL overview/collapse metrics degenerate: only the diachronic "
            "metrics (center coverage, reference alignment, continuity) are "
            "live here. A larger graph is needed to falsify S1."
        )
    return limits


__all__ = [
    "WorkedStep", "WorkedChain", "load_worked_chain",
    "StepSets", "step_sets",
    "NarrationParse", "parse_narration",
    "StepScore", "score_step",
    "ChainReport", "check_chain", "honest_limits",
    "_relation_alphabet",
]
