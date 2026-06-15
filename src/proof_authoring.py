"""
proof_authoring — build a transformation chain by *applying* rules, with the
bookkeeping handled for you.

This is the action half of the authoring layer (the query half is
``eg_navigation``). ``ProofChain`` wraps the headless ``RuleInteraction``
protocol so that authoring a proof reads like the proof itself:

    chain = (
        ProofChain.from_blank()
        .apply("DC+", label="3i", note="Insert an empty double cut.")
        .apply("INS", insert="(P)", into=outer_cut, label="1i", note="…")
        .to_chain()
    )

Each ``apply`` resolves its selection/target **against the current state**
(so callers never thread ephemeral element ids between steps — they pass a
*locator*, a ``callable(egi) -> id``, typically built from ``eg_navigation``),
applies the rule through the engine (raising loudly on any rejected step), and
records a ``ChainStep`` with deterministic ids and timestamps. The result is a
``TransformationChain`` — a real Peircean reasoning episode
(``docs/CHAIN_OF_SEMIOSIS.md``), not a hand-authored sequence of states.

Why this exists: the Praeclarum dogfood
(``project-ergasterion-dogfood-findings``) showed that authoring a proof by
raw element id, with hand-written ``ChainStep`` construction per step, is the
real friction. The *logic* engine was solid; the *ergonomics* were the gap.
``ProofChain`` + ``eg_navigation`` close it.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from egif_parser_dau import parse_egif
from egi_core_dau import RelationalGraphWithCuts
from rule_interaction import (
    advance_interaction,
    apply_interaction,
    begin_interaction,
)
from tomos_service import ChainStep, TransformationChain
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)

# A locator resolves a selection/target against a concrete state at apply time.
Locator = Callable[[RelationalGraphWithCuts], Any]
Spec = Union[str, List[str], Locator, None]


def apply_rule(
    rule_name: str,
    egi: RelationalGraphWithCuts,
    *,
    selection=None,
    egif: Optional[str] = None,
    target: Optional[str] = None,
) -> RelationalGraphWithCuts:
    """Apply one Dau rule through the ``RuleInteraction`` protocol and return
    the resulting EGI. Raises ``AssertionError`` with the engine's own message
    on any rejected step — an unsound move fails loudly rather than silently
    producing a wrong graph.

    Calling conventions (mirroring the protocol):
      * ``INS`` — ``egif`` (content) + ``target`` (a negative area)
      * ``IT+`` — ``selection`` (source) + ``target`` (a nested area)
      * ``DC+`` — ``selection`` (elements to enclose) and/or ``target`` (the
        spot area); empty ``selection`` + a ``target`` inserts a truly empty
        double cut there; no ``target`` falls back to the whole/common-area wrap
      * ``DC-`` / ``ERA`` / ``IT-`` — ``selection`` only
    """
    state = begin_interaction(rule_name, egi)
    if rule_name == "INS":
        r1 = advance_interaction(state, egif)
        assert r1.valid, f"INS content rejected: {r1.message}"
        r2 = advance_interaction(state, target)
        assert r2.valid, f"INS target rejected: {r2.message}"
    elif rule_name == "IT+":
        r1 = advance_interaction(state, selection)
        assert r1.valid, f"IT+ source rejected: {r1.message}"
        r2 = advance_interaction(state, target)
        assert r2.valid, f"IT+ destination rejected: {r2.message}"
    elif rule_name == "DC+" and target is not None:
        # DC+ with an explicit spot (the SELECT_AREA step): an empty subject +
        # a target area inserts a truly empty double cut there (``enclose_empty``);
        # a non-empty selection encloses it in that area. Without a target this
        # falls through to the single-step path (legacy whole-area / common-area
        # wrap), so existing callers are unaffected.
        r1 = advance_interaction(state, selection or [])
        assert r1.valid, f"DC+ subject rejected: {r1.message}"
        r2 = advance_interaction(state, target)
        assert r2.valid, f"DC+ spot rejected: {r2.message}"
    else:  # DC+, DC-, IT-, ERA — single selection step
        r = advance_interaction(state, selection or [])
        assert r.valid, f"{rule_name} rejected: {r.message}"
    result = apply_interaction(state)
    assert result.success, f"{rule_name} apply failed: {result.message}"
    return result.result_egi


def replay_step(
    egi: RelationalGraphWithCuts, params: Dict
) -> RelationalGraphWithCuts:
    """Re-apply one persisted chain step to ``egi`` from its ``parameters``.

    The selection / target ids in ``parameters`` index into the step's
    ``from_state`` snapshot, so replay is faithful when ``egi`` is that
    snapshot. Used to verify a loaded chain is a genuine sequence of sound
    rule applications (each step reproduces its ``to_state``)."""
    return apply_rule(
        params["rule"],
        egi,
        selection=params.get("selection"),
        egif=params.get("egif_content"),
        target=params.get("target_area"),
    )


class ProofChain:
    """Accumulates a ``TransformationChain`` as rules are applied.

    Deterministic: state ids are ``s0, s1, …`` and timestamps step one second
    from a fixed base, so a built chain is byte-stable across runs (good for
    tests and reproducible corpus seeds)."""

    def __init__(
        self,
        initial_egi: RelationalGraphWithCuts,
        *,
        base_timestamp: str = "2026-06-03T00:00:00+00:00",
        initial_state_id: str = "s0",
    ):
        self._initial_id = initial_state_id
        self._states: Dict[str, RelationalGraphWithCuts] = {initial_state_id: initial_egi}
        self._steps: List[ChainStep] = []
        self._current_id = initial_state_id
        self._current = initial_egi
        self._base = datetime.fromisoformat(base_timestamp)

    @classmethod
    def from_blank(cls, **kw) -> "ProofChain":
        """Start from the blank sheet (⊤) — the context a theorem is proved
        against."""
        return cls(parse_egif(""), **kw)

    @classmethod
    def from_egif(cls, egif: str, **kw) -> "ProofChain":
        """Start from a graph given as EGIF (e.g. the conjunction of premises
        for a derivation)."""
        return cls(parse_egif(egif), **kw)

    @property
    def current(self) -> RelationalGraphWithCuts:
        """The current (most recently produced) state."""
        return self._current

    @property
    def current_state_id(self) -> str:
        return self._current_id

    def at(self, state_id: str) -> "ProofChain":
        """Move the cursor back to an already-recorded state, so the next
        ``apply`` **forks** a new line of development from there (two steps then
        share a ``from_state_id`` — the branch).  Returns ``self``."""
        if state_id not in self._states:
            raise KeyError(f"no recorded state '{state_id}' to branch from")
        self._current_id, self._current = state_id, self._states[state_id]
        return self

    def converge_last_into(self, state_id: str) -> "ProofChain":
        """Redirect the most recent step to an existing state it reproduces, so
        two lines of development **converge** (share a ``to_state_id``) — the
        alternate-proofs "diamond".  Refuses unless the produced graph is in fact
        the same graph (a genuine convergence, not a relabel)."""
        from eg_navigation import same_graph
        if not self._steps:
            raise ValueError("no step to converge")
        last = self._steps[-1]
        if state_id not in self._states:
            raise KeyError(f"no recorded state '{state_id}' to converge into")
        if not same_graph(self._states[last.to_state_id], self._states[state_id]):
            raise ValueError(
                f"refusing to converge: '{last.to_state_id}' is not the same graph "
                f"as '{state_id}'")
        import dataclasses
        orphan = last.to_state_id
        self._steps[-1] = dataclasses.replace(last, to_state_id=state_id)
        self._states.pop(orphan, None)
        self._current_id, self._current = state_id, self._states[state_id]
        return self

    def _resolve(self, spec: Spec):
        if spec is None:
            return None
        if callable(spec):
            spec = spec(self._current)
        return spec

    def apply(
        self,
        rule: str,
        *,
        select: Spec = None,
        insert: Optional[str] = None,
        into: Spec = None,
        label: Optional[str] = None,
        note: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> "ProofChain":
        """Apply one rule and record the step. Returns ``self`` for chaining.

        Args:
            rule: One of ``DC+ DC- ERA INS IT+ IT-``.
            select: The selection (source/candidate/outer-cut). An id, a list
                of ids, or a locator ``callable(egi) -> id|list`` resolved
                against the current state.
            insert: EGIF content for ``INS``.
            into: The target area (``INS`` target / ``IT+`` destination). An id
                or a locator resolved against the current state.
            label: Peirce's rule label for this move (e.g. ``"2i"``).
            note: Human description, kept as the step's annotation.
        """
        selection = self._resolve(select)
        if isinstance(selection, str):
            selection = [selection]
        target = self._resolve(into)

        new_egi = apply_rule(
            rule, self._current, selection=selection, egif=insert, target=target
        )

        i = len(self._steps)
        from_id, to_id = self._current_id, f"s{i + 1}"
        params: Dict[str, Any] = {"rule": rule}
        if label is not None:
            params["peirce_label"] = label
        if note is not None:
            params["description"] = note
        if selection is not None:
            params["selection"] = list(selection)
        if insert is not None:
            params["egif_content"] = insert
        if target is not None:
            params["target_area"] = target

        annotation = f"{label}: {note}" if (label and note) else note
        self._steps.append(ChainStep(
            step_id=f"step-{i + 1}",
            rule_name=rule,
            from_state_id=from_id,
            to_state_id=to_id,
            parameters=params,
            timestamp=(self._base + timedelta(seconds=i)).isoformat(),
            user_annotation=annotation,
            branch_id=branch,
        ))
        self._states[to_id] = new_egi
        self._current_id, self._current = to_id, new_egi
        return self

    def apply_derived(
        self,
        rule_name: str,
        transform: Callable[[RelationalGraphWithCuts], RelationalGraphWithCuts],
        *,
        label: Optional[str] = None,
        note: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> "ProofChain":
        """Apply a *derived* rule and record it as one ``ChainStep``.

        ``transform`` is a callable ``egi -> egi`` that composes primitive rules
        (e.g. ``derived_rules.universal_instantiation``), resolving its own
        locators against the current state.  The resulting state is recorded and
        is authoritative — a derived step is one move at the chain level, and is
        not re-expanded by the six-rule ``replay_step`` path (its sub-steps are
        Dau-formalized but collapsed here for readability, the same way a human
        proof writes "by universal instantiation").

        Use this for moves outside the six base rules (Beta ligature work);
        ``apply`` remains the path for the six primitives.
        """
        new_egi = transform(self._current)
        i = len(self._steps)
        from_id, to_id = self._current_id, f"s{i + 1}"
        p: Dict[str, Any] = {"rule": rule_name, "derived": True}
        if label is not None:
            p["peirce_label"] = label
        if note is not None:
            p["description"] = note
        if params:
            p.update(params)
        annotation = f"{label}: {note}" if (label and note) else note
        self._steps.append(ChainStep(
            step_id=f"step-{i + 1}",
            rule_name=rule_name,
            from_state_id=from_id,
            to_state_id=to_id,
            parameters=p,
            timestamp=(self._base + timedelta(seconds=i)).isoformat(),
            user_annotation=annotation,
        ))
        self._states[to_id] = new_egi
        self._current_id, self._current = to_id, new_egi
        return self

    def to_chain(self) -> TransformationChain:
        """The accumulated chain."""
        return TransformationChain(
            initial_state_id=self._initial_id,
            steps=list(self._steps),
            states=dict(self._states),
        )

    def to_uod(
        self,
        *,
        uod_id: str,
        name: str,
        description: str,
        category: UoDCategory = UoDCategory.THEOREM_PROOF,
        created: Optional[datetime] = None,
    ) -> Tuple[TransformationChain, UniverseOfDiscourse]:
        """Package the chain with a UoD whose ``current_egi`` is the
        conclusion — ready for ``TomosService.save_uod_with_chain``."""
        when = created or datetime(2026, 6, 3, tzinfo=timezone.utc)
        meta = UoDMetadata(
            uod_id=uod_id,
            uod_type=UoDType.HISTORICAL,
            name=name,
            description=description,
            category=category,
            created=when,
            last_modified=when,
        )
        uod = UniverseOfDiscourse(metadata=meta, current_egi=self._current)
        return self.to_chain(), uod


__all__ = ["ProofChain", "apply_rule", "replay_step"]
