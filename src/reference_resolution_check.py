"""Validation harness for the reference / transclusion node — ROADMAP #3, option (b).

Read-only. **Nothing here mutates the protected core or imports a layout engine.**

A *reference / transclusion node* (Nelson's "the same content, knowably, in more
than one place") is the open architectural fork in
``docs/THE_MINIMAL_IN_VIEW_SET.md`` §12: a spot that points at material defined
elsewhere — a definition body, another corpus UoD, an imported module — *by name
+ provenance* instead of inlining it.  Making it a first-class element touches
``egi_core_dau`` and the §3.3 correspondence contract, so it is an author
decision, not a safe additive build.

Before opening the core we want the **law** the node would have to satisfy to be
already tested on real graphs.  §12 decision 3 names it: an ``attest_reference``
analogous to ``attest_overview`` (``correspondence_attestation.py``), with the law

    RESOLVE ≡ INLINED-AND-ATTESTED.

This module is that analogue, prototyped as a *checker over candidates* rather
than a production hook.  Like ``attest_overview`` (whose overview is a
deliberately incomplete drawing tied to the full §3.3 picture by an expansion
law), a reference is a deliberately incomplete drawing — it abbreviates by
reference — and this is the honest weaker contract it can make:

  R1  **Resolve-equals-inline.**  Resolving the reference yields *exactly* the
      independently-inlined target: ``same_graph(resolve(), inlined)``.  This is
      the heart of the law — the abbreviation denotes the same mathematical
      object as writing the material out in full.

  R2  **Resolved-is-attested.**  The resolved graph draws in full §3.3
      correspondence: ``attest_fn(resolve(), layout_fn(resolve()))`` does not
      raise.  "...-and-attested": the thing the reference stands for is itself a
      licit (EGI, drawing) pair, so the abbreviation never launders an
      ill-formed graph past the invariant.

  R3  **Recoverable** (when an inverse exists — e.g. ``definitions.fold``).  The
      abbreviation is lossless: ``same_graph(refold(resolve()), host)``.  No
      information is created or destroyed by going reference → inlined → reference,
      so the reference is an *honest* abbreviation, not a lossy summary (contrast
      ``attest_overview``'s P2, which *is* lossy and must instead declare what it
      hides).

  R4  **Honest horizon.**  Whatever a resolver could not locate is *named*, never
      silently dropped (``unresolved``).  The Borges floor: the map never claims
      to be the territory.

The expansion law ties R1+R2 to the strong §3.3 contract exactly as
``attest_overview``'s does: a reference with nothing left to resolve *is* the
inlined graph, fully attested.

Falsifiability: doctor a candidate's ``inlined`` ground truth and R1 must fail;
doctor its ``refold`` and R3 must fail.  ``tests/test_reference_resolution_check.py``
pins both so a passing report is earned, not vacuous.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence

from egi_core_dau import RelationalGraphWithCuts
from eg_navigation import same_graph

# A layout function maps an EGI to whatever the attest function consumes (a
# LayoutDTO in production).  Injected so this module imports no geometry and
# stays unit-testable; the runner wires in the real ELK engine.
LayoutFn = Callable[[RelationalGraphWithCuts], object]
AttestFn = Callable[[RelationalGraphWithCuts, object], None]


@dataclass(frozen=True)
class Reference:
    """One reference / transclusion candidate to validate.

    ``name`` / ``origin`` are the provenance the node would carry (what it points
    at, and where that lives — ``definition:subset``, ``transclusion:tomos/<uod>``).
    ``resolve`` produces the inlined EGI on demand (the node's expand-on-resolve
    semantics).  ``inlined`` is the *independently obtained* ground-truth inlining
    the law is checked against — it must come from a different path than
    ``resolve`` (e.g. the raw hand-authored fixture vs. expanding the defined
    form) or R1 is vacuous.  ``host`` + ``refold`` are the abbreviated form and
    its inverse, supplied only when one exists (definitions: ``fold``).
    ``unresolved`` names anything no resolver located, for the honest horizon.
    """

    name: str
    origin: str
    resolve: Callable[[], RelationalGraphWithCuts]
    inlined: RelationalGraphWithCuts
    host: Optional[RelationalGraphWithCuts] = None
    refold: Optional[Callable[[RelationalGraphWithCuts], RelationalGraphWithCuts]] = None
    unresolved: Sequence[str] = ()


@dataclass
class ReferenceReport:
    """The per-candidate verdict — booleans plus the failures that explain them.

    ``ok`` is the conjunction of every check that applied (R3 is skipped, not
    failed, when no inverse is supplied; R4 is informational).  ``honest_limits``
    surfaces what the harness did *not* test, kept beside every result the way
    the diagram↔narration harness does.
    """

    name: str
    origin: str
    resolve_equals_inline: bool
    resolved_attested: bool
    recoverable: Optional[bool]
    unresolved: List[str]
    failures: List[str] = field(default_factory=list)
    honest_limits: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            self.resolve_equals_inline
            and self.resolved_attested
            and self.recoverable is not False
        )


class ReferenceViolation(AssertionError):
    """Raised when a reference candidate does not satisfy the law.

    Mirrors ``CorrespondenceViolation`` / ``OverviewViolation``: inherits
    ``AssertionError`` and carries the formatted failures; ``failures`` /
    ``context`` are exposed for post-mortem reports.
    """

    def __init__(self, failures: Sequence[str], context: Optional[str] = None):
        self.failures: List[str] = list(failures)
        self.context = context
        if context:
            header = (
                f"Reference law violated at {context} "
                f"({len(self.failures)} failure(s)):"
            )
        else:
            header = f"Reference law violated ({len(self.failures)} failure(s)):"
        super().__init__(header + "\n" + "\n".join(self.failures))


def check_reference(
    ref: Reference,
    *,
    layout_fn: Optional[LayoutFn] = None,
    attest_fn: Optional[AttestFn] = None,
) -> List[str]:
    """Run the reference-law checks on one candidate.  Returns failures ([] = ok).

    ``layout_fn`` + ``attest_fn`` drive R2 (resolved-is-attested); pass both, or
    neither to skip R2 (a structural-only run for environments without a layout
    engine — the skip is recorded in ``honest_limits`` by ``run_reference``, not
    here).  ``attest_fn`` defaults to ``attest_correspondence`` when a
    ``layout_fn`` is given.
    """
    failures: List[str] = []

    # R1 — resolve-equals-inline (the heart of the law).
    try:
        resolved = ref.resolve()
    except Exception as exc:  # a reference that cannot resolve fails the law
        failures.append(f"  R1 resolve: '{ref.name}' did not resolve: {exc}")
        return failures  # nothing downstream is meaningful without a resolved graph

    if not same_graph(resolved, ref.inlined):
        failures.append(
            f"  R1 resolve-equals-inline: resolving '{ref.name}' does not match "
            f"the independent inlining (resolve ≢ inlined)"
        )

    # R2 — resolved-is-attested ("...-and-attested").
    if layout_fn is not None:
        attest = attest_fn or _default_attest()
        try:
            attest(resolved, layout_fn(resolved))
        except Exception as exc:
            failures.append(
                f"  R2 resolved-attested: the resolved form of '{ref.name}' "
                f"is not in §3.3 correspondence: {exc}"
            )

    # R3 — recoverable (lossless abbreviation), only when an inverse is supplied.
    if ref.refold is not None and ref.host is not None:
        try:
            refolded = ref.refold(resolved)
        except Exception as exc:
            failures.append(
                f"  R3 recoverable: refolding '{ref.name}' raised: {exc}"
            )
        else:
            if not same_graph(refolded, ref.host):
                failures.append(
                    f"  R3 recoverable: reference→inlined→reference does not "
                    f"recover the host for '{ref.name}' (lossy abbreviation)"
                )

    # R4 — honest horizon is informational: unresolved names are reported, not a
    # failure (an incomplete reference is licit as long as the gap is named).
    return failures


def attest_reference(
    ref: Reference,
    *,
    layout_fn: Optional[LayoutFn] = None,
    attest_fn: Optional[AttestFn] = None,
    context: Optional[str] = None,
) -> None:
    """Raise ``ReferenceViolation`` if the candidate breaks the law; else None.

    The production-shaped hook a first-class reference node would call, exactly as
    ``attest_correspondence`` / ``attest_overview`` are hooked at their boundaries.
    """
    failures = check_reference(ref, layout_fn=layout_fn, attest_fn=attest_fn)
    if failures:
        raise ReferenceViolation(failures, context=context or ref.name)


def run_reference(
    ref: Reference,
    *,
    layout_fn: Optional[LayoutFn] = None,
    attest_fn: Optional[AttestFn] = None,
) -> ReferenceReport:
    """Validate one candidate and return a structured ``ReferenceReport`` (the
    measurement form — never raises on a law failure, it records it)."""
    failures = check_reference(ref, layout_fn=layout_fn, attest_fn=attest_fn)

    def failed(tag: str) -> bool:
        return any(tag in f for f in failures)

    limits: List[str] = []
    if layout_fn is None:
        limits.append(
            "R2 (resolved-is-attested) skipped: no layout_fn supplied — "
            "structural law only, §3.3 not exercised"
        )
    if ref.refold is None:
        limits.append(
            "R3 (recoverable) not applicable: no inverse supplied for this "
            "reference kind (e.g. transclusion has no local fold)"
        )

    return ReferenceReport(
        name=ref.name,
        origin=ref.origin,
        resolve_equals_inline=not failed("R1"),
        resolved_attested=(layout_fn is None) or not failed("R2"),
        recoverable=None if ref.refold is None else not failed("R3"),
        unresolved=list(ref.unresolved),
        failures=failures,
        honest_limits=limits,
    )


def _default_attest() -> AttestFn:
    from correspondence_attestation import attest_correspondence

    return attest_correspondence


__all__ = [
    "Reference",
    "ReferenceReport",
    "ReferenceViolation",
    "check_reference",
    "attest_reference",
    "run_reference",
]
