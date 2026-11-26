"""The one door to the rule engine (calculus-conformance specification §3.3).

Every path by which a graph changes by inference comes through this module.
It performs the move by the way in the caller names, and then asks the kernel
(``dau_kernel``, which imports no engine code) whether the graph that came
back is what Dau's rule makes of the graph that went in. The answer is a
``Certificate``.

**Observe mode (Phase 2 of the conformance arc).** A certificate is computed
and checked for every applied move, and a failure is *counted, not raised*: no
caller sees any difference in what the engine does. ``OBSERVED`` holds the
tally. Phase 4 turns ``MODE`` to ``"enforce"``, and a rejected step then raises
``CalculusViolation``.

There are several doors because the engine has several ways in, and they do
not agree with one another (specification §3.3a, finding 1): the interaction
protocol, the engine called directly, a rule object handed a context, the
ligature engine, and the split and merge operations. ``certify`` is the general
door; the others exist for callers that need the engine's own result object or
drive the protocol a step at a time. All of them end in ``_observe``.

**Naming.** A certificate names Dau's rule, not the engine's (§3.2). Where a
caller does not say which Dau rule it means, ``name_move`` decides from the
request — never from what the engine did with it:

- ``HEAVY_DOT`` is Dau's inserting a vertex, ``VERTEX_INS``;
- ``ERA`` of a single vertex with no edge on it is erasing a vertex:
  ``VERTEX_ERA`` for a generic one, ``CONSTANT_EXISTENCE`` for one carrying a
  constant (Def 24.10, p.271). Every other erasure is ``ERA``;
- ``DC+`` with no spot is read as the engine reads it — around the selection in
  the selection's own context, or around the whole sheet when nothing is
  selected (ruling R4: kept, and recorded);
- ``DC+`` with a spot and nothing selected means two different things by two
  ways in, and is named as each means it: through the protocol, an empty double
  cut at the spot; through the engine or a rule object, a double cut around
  everything in that area (unless the context says ``enclose_empty``);
- ``ERA``, ``DC-``, ``IT-`` and ``VERTEX_ERA`` take no target in Dau, so none
  is recorded; nor does the erasing direction of ``CONSTANT_EXISTENCE`` (a
  vertex selected) or of ``CONSTANT_IDENTITY`` (an identity link selected).
"""
from __future__ import annotations

import atexit
import json
import os
import sys
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

import dau_kernel
import rule_interaction
from dau_kernel import ACCEPTED, REJECTED, UNJUDGED, Move
from egi_core_dau import RelationalGraphWithCuts
from formal_transformation_rules import FormalTransformationEngine
from ligature_manipulation_rules import LigatureManipulationEngine
from vertex_splitting_merging_rules import (
    VertexMergingRule, VertexSplitSpec, VertexSplittingRule,
)

G = RelationalGraphWithCuts

MODE = os.environ.get("ARISBE_CERTIFY", "observe")      # "observe" | "enforce"
KERNEL_CRASHED = "kernel-crashed"


class CalculusViolation(Exception):
    """The kernel rejected a step: the engine produced a graph Dau's rule does
    not license. Raised only in enforce mode."""

    def __init__(self, certificate: "Certificate"):
        self.certificate = certificate
        super().__init__(f"{certificate.way} {certificate.engine_rule}: {certificate.why}")


class EngineRefusal(AssertionError):
    """The engine declined the move. An ``AssertionError``, which is what the
    protocol path has always raised, so one ``except`` serves every way in."""


@dataclass(frozen=True)
class Act:
    """One request to the engine, as its caller makes it."""
    way: str                 # see WAYS
    rule: str                # the rule's name on that way ("ERA", "HEAVY_DOT", ...)
    selection: Tuple[str, ...] = ()
    target: Optional[str] = None
    content: Optional[str] = None
    hooks: Tuple[Tuple[str, int], ...] = ()
    dau_rule: Optional[str] = None    # the Dau rule the caller means; None = named here


@dataclass(frozen=True)
class Certificate:
    way: str
    engine_rule: str
    steps: Tuple[Move, ...]           # one step for a primitive move
    status: str                       # ACCEPTED | REJECTED | UNJUDGED | KERNEL_CRASHED
    why: str

    @property
    def accepted(self) -> bool:
        return self.status == ACCEPTED


WAYS = ("protocol", "engine", "rule", "ligature", "split-unchecked", "merge-checked",
        "merge-unchecked")


# -- the tally ---------------------------------------------------------------

class Observations:
    def __init__(self) -> None:
        self.counts: Counter = Counter()      # (way, engine rule, Dau rule, status) -> n
        self.seconds = 0.0
        self.slowest = (0.0, "")

    def reset(self) -> None:
        self.__init__()

    def record(self, cert: Certificate, elapsed: float, size: int) -> None:
        self.counts[(cert.way, cert.engine_rule, cert.steps[0].rule, cert.status)] += 1
        self.seconds += elapsed
        if elapsed > self.slowest[0]:
            self.slowest = (elapsed, f"{cert.way} {cert.engine_rule}, {size} elements")

    def by_status(self) -> Counter:
        out: Counter = Counter()
        for (_way, _rule, _dau, status), n in self.counts.items():
            out[status] += n
        return out


OBSERVED = Observations()
_LOG = os.environ.get("ARISBE_CERTIFY_LOG")


def _log(record: dict) -> None:
    if _LOG:
        with open(_LOG, "a") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")


_DOOR_FILES = ("calculus_certify.py", "proof_authoring.py")


def _caller() -> str:
    """Who asked for the move: the nearest frame outside the door and the
    protocol wrapper, as ``file:function``. Read only when a log is being
    written, so the observation costs nothing otherwise."""
    frame = sys._getframe(1)
    while frame is not None:
        name = os.path.basename(frame.f_code.co_filename)
        if name not in _DOOR_FILES:
            return f"{name}:{frame.f_code.co_name}"
        frame = frame.f_back
    return "?"


if _LOG:
    @atexit.register
    def _write_summary() -> None:
        _log({"summary": [[*k, n] for k, n in sorted(OBSERVED.counts.items())],
              "seconds": round(OBSERVED.seconds, 3), "slowest": list(OBSERVED.slowest)})


# -- naming ------------------------------------------------------------------

_NO_TARGET = frozenset({"ERA", "DC-", "IT-", "VERTEX_ERA", "MERGE_VERTICES"})


def name_move(g: G, rule: str, selection=(), target: Optional[str] = None,
              content: Optional[str] = None, hooks=(), *,
              empty_means_whole_area: bool = False) -> Move:
    """The Dau move a request amounts to, read from the request alone.

    ``empty_means_whole_area`` is the convention of the ways in that take no
    protocol step: there a ``DC+`` with nothing selected encloses everything
    in the target area."""
    sel = tuple(selection or ())
    hooks = tuple(tuple(h) for h in (hooks or ()))
    if rule == "HEAVY_DOT":
        return Move("VERTEX_INS", (), target)
    if rule == "INS":
        return Move("INS", (), target, content)
    if rule == "ERA" and len(sel) == 1 and sel[0] in {v.id for v in g.V} \
            and not dau_kernel.edges_on(g, sel[0]):
        generic = next(v for v in g.V if v.id == sel[0]).is_generic
        return Move("VERTEX_ERA" if generic else "CONSTANT_EXISTENCE", sel)
    if rule == "CONSTANT_EXISTENCE":
        return Move(rule, sel) if sel else Move(rule, (), target, content)
    if rule == "CONSTANT_IDENTITY":
        return Move(rule, sel) if len(sel) == 1 else Move(rule, sel, target)
    if rule == "DC+" and target is not None and not sel and empty_means_whole_area:
        sel = tuple(sorted(g.area.get(target, ())))
    if rule == "DC+" and target is None:
        known = set(dau_kernel.elements(g))
        if not sel:
            sel, target = tuple(sorted(g.area.get(g.sheet, ()))), g.sheet
        elif all(x in known for x in sel):
            contexts = {g.get_context(x) for x in dau_kernel.tops(g, dau_kernel.expand(g, sel))}
            target = next(iter(contexts)) if len(contexts) == 1 else None
    if rule in _NO_TARGET:
        target = None
    return Move(rule, sel, target, content, hooks)


# -- the check ---------------------------------------------------------------

def _observe(way: str, rule: str, g: G, h: G, move: Move, may_raise: bool = True) -> Certificate:
    started = time.perf_counter()
    try:
        check = dau_kernel.check_step(g, move, h)
        status, why = check.status, check.why
    except Exception as exc:           # the judge must never take the engine down with it
        status, why = KERNEL_CRASHED, f"{type(exc).__name__}: {exc}"
    cert = Certificate(way, rule, (move,), status, why)
    size = len(g.V) + len(g.E) + len(g.Cut)
    OBSERVED.record(cert, time.perf_counter() - started, size)
    if status != ACCEPTED and _LOG:
        _log({"way": way, "engine_rule": rule, "dau_rule": move.rule, "status": status,
              "why": why, "elements": size, "selection": len(move.selection),
              "caller": _caller(), "test": os.environ.get("PYTEST_CURRENT_TEST", "")})
    if MODE == "enforce" and may_raise and status == REJECTED:
        raise CalculusViolation(cert)
    return cert


def _move_for(g: G, act: Act) -> Move:
    if act.dau_rule is not None:
        return Move(act.dau_rule, tuple(act.selection), act.target, act.content, tuple(act.hooks))
    return name_move(g, act.rule, act.selection, act.target, act.content, act.hooks)


# -- the doors ---------------------------------------------------------------

def certify(g: G, act: Act) -> Tuple[G, Certificate]:
    """Perform ``act`` on ``g`` by the way it names, and certify the result.

    Returns the new graph and its certificate. Raises ``EngineRefusal`` (an
    ``AssertionError``) with the engine's own message when the engine declines;
    any other exception is the engine's crash and is not caught."""
    h = _perform(g, act)
    return h, _observe(act.way, act.rule, g, h, _move_for(g, act))


def _perform(g: G, act: Act) -> G:
    sel = list(act.selection)
    if act.way == "protocol":
        return _drive_protocol(act.rule, g, sel, act.content, act.target)
    if act.way == "engine":
        return _unwrap(FormalTransformationEngine().apply_rule(
            act.rule, g, act.target, frozenset(sel), insertion_egif=act.content))
    if act.way == "ligature":
        # A plain frozenset: the engine's choice of vertex within the selection
        # is a function of the graph (its canonical signature), not of an order.
        return _unwrap(LigatureManipulationEngine().apply_rule(
            act.rule, g, act.target, frozenset(sel)))
    if act.way == "split-unchecked":
        spec = VertexSplitSpec(source_vertex=sel[0], target_context=act.target,
                               hooks_to_move=list(act.hooks), new_vertex_id="split_new_v")
        return VertexSplittingRule()._apply_vertex_split(g, spec)
    if act.way == "merge-checked":
        # Def 16.6 merging names v1 and v2 in order (v2 into v1), which a
        # frozenset selection cannot carry, so this is the rule's ordered entry
        # point. It checks the rule's own preconditions; ``merge-unchecked``
        # performs the merge and checks nothing.
        v1, v2, e = sel
        return _unwrap(VertexMergingRule().merge_vertices(
            g, v1_id=v1, v2_id=v2, identity_edge_id=e))
    if act.way == "merge-unchecked":
        v1, v2, e = sel
        return VertexMergingRule()._apply_vertex_merge(
            g, v1_id=v1, v2_id=v2, identity_edge_id=e)
    raise KeyError(f"no way into the engine is called {act.way!r}")


def _unwrap(result: Any) -> G:
    if not result.success:
        raise EngineRefusal(result.error_message or "")
    return result.result_egi


def _drive_protocol(rule_name: str, egi: G, selection, egif, target) -> G:
    """One rule through the ``RuleInteraction`` protocol. This was the body of
    ``proof_authoring.apply_rule`` and is unchanged; that function now calls
    ``certify``.

    Calling conventions (mirroring the protocol):
      * ``INS`` — ``egif`` (content) + ``target`` (a negative area)
      * ``IT+`` — ``selection`` (source) + ``target`` (a nested area)
      * ``DC+`` — ``selection`` (elements to enclose) and/or ``target`` (the
        spot area); empty ``selection`` + a ``target`` inserts a truly empty
        double cut there; no ``target`` falls back to the whole/common-area wrap
      * ``DC-`` / ``ERA`` / ``IT-`` — ``selection`` only
    """
    state = rule_interaction.begin_interaction(rule_name, egi)
    advance = rule_interaction.advance_interaction
    if rule_name == "INS":
        r1 = advance(state, egif)
        assert r1.valid, f"INS content rejected: {r1.message}"
        r2 = advance(state, target)
        assert r2.valid, f"INS target rejected: {r2.message}"
    elif rule_name == "IT+":
        r1 = advance(state, selection)
        assert r1.valid, f"IT+ source rejected: {r1.message}"
        r2 = advance(state, target)
        assert r2.valid, f"IT+ destination rejected: {r2.message}"
    elif rule_name == "DC+" and target is not None:
        # DC+ with an explicit spot (the SELECT_AREA step): an empty subject +
        # a target area inserts a truly empty double cut there (``enclose_empty``);
        # a non-empty selection encloses it in that area. Without a target this
        # falls through to the single-step path (legacy whole-area / common-area
        # wrap), so existing callers are unaffected.
        r1 = advance(state, selection or [])
        assert r1.valid, f"DC+ subject rejected: {r1.message}"
        r2 = advance(state, target)
        assert r2.valid, f"DC+ spot rejected: {r2.message}"
    else:  # DC+, DC-, IT-, ERA — single selection step
        r = advance(state, selection or [])
        assert r.valid, f"{rule_name} rejected: {r.message}"
    result = rule_interaction.apply_interaction(state)
    assert result.success, f"{rule_name} apply failed: {result.message}"
    return result.result_egi


def protocol_apply(state, *, selection=(), target: Optional[str] = None,
                   content: Optional[str] = None, dry_run: bool = False):
    """``apply_interaction`` for a caller that walks the protocol's steps itself
    (the workshop route, which reports each step's refusal to the user). The
    request is passed beside the state because the certificate names what was
    asked for, and the state holds what the protocol made of it.

    ``dry_run`` marks an application whose result is thrown away (the route's
    rule check); it is tallied under its own way so it is never mistaken for a
    change to a graph. Returns ``(ApplyResult, Certificate or None)``."""
    result = rule_interaction.apply_interaction(state)
    if not result.success:
        return result, None
    way = "protocol:dry-run" if dry_run else "protocol"
    move = name_move(state.egi, state.rule_name, selection, target, content)
    # A dry run changed nothing, so there is nothing to refuse: it never raises.
    return result, _observe(way, state.rule_name, state.egi, result.result_egi, move,
                            may_raise=not dry_run)


def engine_apply(rule: str, egi: G, target_area, selected, insertion_egif: Optional[str] = None,
                 engine: Optional[FormalTransformationEngine] = None):
    """``FormalTransformationEngine.apply_rule``, certified. Returns
    ``(TransformationResult, Certificate or None)``."""
    result = (engine or FormalTransformationEngine()).apply_rule(
        rule, egi, target_area, selected, insertion_egif=insertion_egif)
    if not result.success:
        return result, None
    move = name_move(egi, rule, sorted(selected), target_area, insertion_egif,
                     empty_means_whole_area=True)
    return result, _observe("engine", rule, egi, result.result_egi, move)


def rule_apply(rule_name: str, rule: Any, context: Any):
    """A rule object applied to a context it is handed, with no protocol step
    and no engine in between (the game engine's way in). Returns
    ``(TransformationResult, Certificate or None)``."""
    result = rule.apply_transformation(context)
    if not result.success:
        return result, None
    move = name_move(context.source_egi, rule_name, sorted(context.selected_subgraph),
                     context.target_area, getattr(context, "insertion_egif", None),
                     empty_means_whole_area=not getattr(context, "enclose_empty", False))
    return result, _observe("rule", rule_name, context.source_egi, result.result_egi, move)


def insert_apply(egi: G, target_area, egif: str):
    """``rule_interaction.insert_from_egif`` called directly (the game engine's
    INS). Returns ``(result, Certificate or None)``."""
    result = rule_interaction.insert_from_egif(egi, target_area, egif)
    if not result.success:
        return result, None
    move = name_move(egi, "INS", (), target_area, egif)
    return result, _observe("rule", "INS", egi, result.result_egi, move)


def merge_unchecked(egi: G, *, v1_id, v2_id, identity_edge_id) -> Tuple[G, Certificate]:
    """The merge that performs the change and checks nothing
    (``VertexMergingRule._apply_vertex_merge``), certified as Def 16.6 merging."""
    return certify(egi, Act("merge-unchecked", "MERGE_VERTICES", (v1_id, v2_id, identity_edge_id),
                            dau_rule="MERGE_VERTICES"))


def split_unchecked(egi: G, spec: VertexSplitSpec) -> Tuple[G, Certificate]:
    """The split that performs the change and checks nothing
    (``VertexSplittingRule._apply_vertex_split``), certified as Def 16.6 splitting."""
    h = VertexSplittingRule()._apply_vertex_split(egi, spec)
    move = Move("SPLIT_VERTEX", (spec.source_vertex,), spec.target_context,
                hooks=tuple(tuple(hk) for hk in spec.hooks_to_move))
    return h, _observe("split-unchecked", "SPLIT_VERTEX", egi, h, move)


def observations() -> List[Tuple[str, str, str, str, int]]:
    """The tally as rows, for a report: (way, engine rule, Dau rule, status, n)."""
    return [(*key, n) for key, n in sorted(OBSERVED.counts.items())]
