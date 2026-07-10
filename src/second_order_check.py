"""De-risking harness for the **second-order frontier** — ROADMAP #13.

Read-only. **Nothing here mutates the protected core or imports a layout engine.**
It is the second-order analogue of ``reference_resolution_check`` (increment 1's
harness), built the same way and for the same reason: *prove the law the device
would have to satisfy — on real candidates, before opening the core.*

The frontier ([docs/SECOND_ORDER_FRONTIER.md](../docs/SECOND_ORDER_FRONTIER.md))
is "second-order logic **as a picture**": graphs about graphs, quantification over
predicates, hypostatic abstraction — drawn, not annotated. Its sharp design test is
**the correspondence check (§3.3) raised one order**: *can the second-order device
be drawn, and read back off the drawing, so the picture* is *the second-order
proposition?* Peirce supplies the *device* (a line attached to a dotted oval
containing a whole proposition — the "graph of a graph") and the *ascent operator*
(hypostatic abstraction), but **not comprehension control** — which such marks may
be formed without paradox (Russell / Grelling / Liar). That missing floor is the
one thing a modern guide must supply, drawn as a well-formedness rule on **sorts**
rather than a symbolic type annotation.

**A quotation candidate** (this harness's unit) is that device modelled as an
*overlay beside* the EGI (exactly as ``reference_node``'s mark sits beside
``egi_core_dau`` — the core is untouched): a **proposition-sorted line** in a host
graph that *names* a whole graph ``quoted`` (the dotted oval's contents), carrying
its drawn position and whether the quote reaches back to the host's own level.

The law — the second-order restatement of ``RESOLVE ≡ INLINED-AND-ATTESTED``:

  S1  **Well-sorted / stratified** (the borrowed floor — comprehension control).
      An *impredicative* quote — one that names the host itself, or a graph at the
      host's own level or above (the self-referential / Liar case) — is well-formed
      **only when drawn *enclosed*** (under ≥ 1 cut), never flat on the sheet. This
      is the paradox floor drawn as a rule on the picture: it is exactly field-guide
      **dragon 9** (docs/MEANING_BY_HISTORY.md) — a self-assessment read off *one*
      history is at most ◇ (*some* trajectory), and asserting it flat misreads ◇ as
      □; it is legitimate only enclosed (under a cut, as an antecedent one
      conditions on). A *predicative* quote (a strictly-lower graph, no reach-back)
      is always well-formed. **This is one chosen, defensible floor** — the most
      Peirce-continuous (his "vary the sort, not the rules" method) — not the only
      one; the choice is the author's (SECOND_ORDER_FRONTIER §"The design rule").

  S2  **Quote-equals-quoted-and-attested** (the object recovers; §3.3 recurses).
      Resolving the quotation yields *exactly* the independently-obtained quoted
      graph (``same_graph(resolve(), quoted_ground)``), and that graph itself draws
      in full §3.3 correspondence (``attest_fn(resolve(), layout_fn(resolve()))``).
      So a quotation never launders an ill-formed graph past the invariant — the
      first-order contract holds one level down, recursively. (The analogue of R1+R2.)

  S3  **Read-back one order up** (§3.3 raised — the frontier's promise). The
      sort-marked drawing reads back to the *same* second-order proposition: the
      injected ``read_back`` recovers the ``(sort, quoted)`` device, and it matches.
      The second-order *reader* is the unbuilt frontier itself, so ``read_back`` is
      **injected** (like ``layout_fn`` drives S2); with none supplied S3 is *skipped
      and named*, never silently passed — the harness proves the law's shape without
      fabricating the reader.

  S4  **Honest horizon.** Whatever the floor *forbids* (an impredicative quote drawn
      flat) or a resolver could not locate is **named**, never silently dropped. The
      marked departure: Peirce leads to *drawing* a second-order claim; the borrowed
      floor says *which* claims are well-formed — S1 is exactly that line.

Falsifiability (``tests/test_second_order_check.py`` pins these, so a pass is
earned): draw an impredicative quote *flat* and S1 must fail; doctor a candidate's
``quoted_ground`` and S2 must fail; a ``read_back`` that drops the sort/quote must
fail S3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence

from egi_core_dau import RelationalGraphWithCuts
from eg_navigation import same_graph

# Injected so this module imports no geometry / no unbuilt reader and stays
# unit-testable — the runner wires in the real ELK engine + (eventually) the
# second-order reader.  A layout function maps an EGI to whatever attest consumes.
LayoutFn = Callable[[RelationalGraphWithCuts], object]
AttestFn = Callable[[RelationalGraphWithCuts, object], None]

# The second-order sorts (Peirce's device + hypostatic abstraction). "individual"
# is ordinary first-order EG (a plain line); the harness's candidates carry a
# higher sort on the quoting line.
SORT_PROPOSITION = "proposition"
SORT_ABSTRACTION = "abstraction"
_SECOND_ORDER_SORTS = (SORT_PROPOSITION, SORT_ABSTRACTION)


@dataclass(frozen=True)
class QuotationReading:
    """What the (future) second-order reader recovers from a sort-marked drawing:
    the ``sort`` of the quoting line and the ``quoted`` graph the dotted oval holds."""

    sort: str
    quoted: RelationalGraphWithCuts


@dataclass(frozen=True)
class Quotation:
    """One second-order device to validate — a *quotation* (graph-of-a-graph),
    modelled as an overlay beside the core.

    ``sort`` is the second-order sort the quoting line carries. ``host`` is the
    graph the quotation is drawn in. ``resolve`` produces the quoted graph on
    demand (the dotted oval's contents); ``quoted_ground`` is the *independently
    obtained* ground truth it is checked against (a different path than ``resolve``
    or S2 is vacuous). ``enclosed`` is whether the quoting line is drawn under ≥ 1
    cut. ``impredicative`` is whether the quote reaches the host's own level or
    itself (defaults to ``same_graph(quoted_ground, host)`` — the direct self-quote
    — with an explicit override for the transitive case). ``read_back`` is the
    injected second-order reader (S3); ``unresolved`` names anything a resolver
    could not locate, for the honest horizon.
    """

    name: str
    sort: str
    host: RelationalGraphWithCuts
    resolve: Callable[[], RelationalGraphWithCuts]
    quoted_ground: RelationalGraphWithCuts
    enclosed: bool = False
    impredicative: Optional[bool] = None
    read_back: Optional[Callable[[], QuotationReading]] = None
    unresolved: Sequence[str] = ()

    def is_impredicative(self) -> bool:
        """Whether the quote reaches the host's own level / names the host itself.
        Explicit override wins; otherwise the direct self-quote is detected
        structurally (``quoted_ground`` is the host)."""
        if self.impredicative is not None:
            return self.impredicative
        try:
            return same_graph(self.quoted_ground, self.host)
        except Exception:
            return False


@dataclass
class QuotationReport:
    """The per-candidate verdict — booleans plus the failures that explain them,
    with what the harness did *not* test kept beside every result (``honest_limits``)."""

    name: str
    sort: str
    well_sorted: bool            # S1
    quote_equals_quoted: bool    # S2 (structural half)
    quoted_attested: bool        # S2 (§3.3 half)
    read_back_faithful: Optional[bool]  # S3 (None = skipped, no reader)
    unresolved: List[str]
    forbidden_if_flat: bool      # S4: is this an impredicative quote (enclosure-gated)?
    failures: List[str] = field(default_factory=list)
    honest_limits: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            self.well_sorted
            and self.quote_equals_quoted
            and self.quoted_attested
            and self.read_back_faithful is not False
        )


class SecondOrderViolation(AssertionError):
    """Raised when a quotation candidate breaks the law. Mirrors
    ``ReferenceViolation`` / ``CorrespondenceViolation``: carries the formatted
    failures + a context label for post-mortems."""

    def __init__(self, failures: Sequence[str], context: Optional[str] = None):
        self.failures: List[str] = list(failures)
        self.context = context
        head = (f"Second-order law violated at {context} "
                if context else "Second-order law violated ")
        super().__init__(head + f"({len(self.failures)} failure(s)):\n"
                         + "\n".join(self.failures))


def check_quotation(
    q: Quotation,
    *,
    layout_fn: Optional[LayoutFn] = None,
    attest_fn: Optional[AttestFn] = None,
) -> List[str]:
    """Run the second-order-law checks on one candidate. Returns failures ([] = ok).

    ``layout_fn`` (+ optional ``attest_fn``) drive S2's §3.3 half; pass both, or
    neither to run the structural law only. S3 runs iff ``q.read_back`` is supplied.
    """
    failures: List[str] = []

    # S1 — well-sorted / stratified (the borrowed comprehension floor, drawn).
    if q.sort not in _SECOND_ORDER_SORTS:
        failures.append(
            f"  S1 well-sorted: '{q.name}' carries sort {q.sort!r}, not a "
            f"second-order sort {list(_SECOND_ORDER_SORTS)}")
    if q.is_impredicative() and not q.enclosed:
        failures.append(
            f"  S1 stratified: '{q.name}' is an impredicative quote (it names the "
            f"host's own level / itself) drawn FLAT on the sheet — the comprehension "
            f"floor admits it only ENCLOSED (under a cut; dragon 9: ◇, not □)")

    # S2 — quote-equals-quoted-and-attested (the object recovers; §3.3 recurses).
    try:
        resolved = q.resolve()
    except Exception as exc:
        failures.append(f"  S2 resolve: '{q.name}' did not resolve its quote: {exc}")
        return failures  # nothing downstream is meaningful without a quoted graph
    if not same_graph(resolved, q.quoted_ground):
        failures.append(
            f"  S2 quote-equals-quoted: resolving '{q.name}' does not match the "
            f"independent quoted graph (resolve ≢ quoted_ground)")
    if layout_fn is not None:
        attest = attest_fn or _default_attest()
        try:
            attest(resolved, layout_fn(resolved))
        except Exception as exc:
            failures.append(
                f"  S2 quoted-attested: the quoted graph of '{q.name}' is not in "
                f"§3.3 correspondence one level down: {exc}")

    # S3 — read-back one order up (§3.3 raised); only when a reader is supplied.
    if q.read_back is not None:
        try:
            reading = q.read_back()
        except Exception as exc:
            failures.append(f"  S3 read-back: reader for '{q.name}' raised: {exc}")
        else:
            if reading.sort != q.sort:
                failures.append(
                    f"  S3 read-back: the drawing of '{q.name}' reads back sort "
                    f"{reading.sort!r}, not the marked {q.sort!r}")
            if not same_graph(reading.quoted, q.quoted_ground):
                failures.append(
                    f"  S3 read-back: the drawing of '{q.name}' reads back a "
                    f"different quoted graph (the second-order device was not "
                    f"recovered faithfully)")

    # S4 — honest horizon is informational (named, not failed).
    return failures


def attest_quotation(
    q: Quotation,
    *,
    layout_fn: Optional[LayoutFn] = None,
    attest_fn: Optional[AttestFn] = None,
    context: Optional[str] = None,
) -> None:
    """Raise ``SecondOrderViolation`` if the candidate breaks the law; else None.
    The production-shaped hook a first-class second-order node would call at its
    boundary, exactly as ``attest_correspondence`` / ``attest_reference`` are."""
    failures = check_quotation(q, layout_fn=layout_fn, attest_fn=attest_fn)
    if failures:
        raise SecondOrderViolation(failures, context=context or q.name)


def run_quotation(
    q: Quotation,
    *,
    layout_fn: Optional[LayoutFn] = None,
    attest_fn: Optional[AttestFn] = None,
) -> QuotationReport:
    """Validate one candidate → a structured ``QuotationReport`` (the measurement
    form — never raises on a law failure, it records it)."""
    failures = check_quotation(q, layout_fn=layout_fn, attest_fn=attest_fn)

    def failed(tag: str) -> bool:
        return any(tag in f for f in failures)

    limits: List[str] = []
    if layout_fn is None:
        limits.append(
            "S2 §3.3 half (quoted-attested) skipped: no layout_fn supplied — "
            "structural law only, §3.3 not exercised one level down")
    if q.read_back is None:
        limits.append(
            "S3 (read-back one order up) skipped: no second-order reader supplied "
            "— the reader IS the frontier; the law's shape is proven, its drawn "
            "recovery is not yet exercised")

    return QuotationReport(
        name=q.name,
        sort=q.sort,
        well_sorted=not failed("S1"),
        quote_equals_quoted=not failed("S2 quote-equals-quoted") and not failed("S2 resolve"),
        quoted_attested=(layout_fn is None) or not failed("S2 quoted-attested"),
        read_back_faithful=None if q.read_back is None else not failed("S3"),
        unresolved=list(q.unresolved),
        forbidden_if_flat=q.is_impredicative(),
        failures=failures,
        honest_limits=limits,
    )


def _default_attest() -> AttestFn:
    from correspondence_attestation import attest_correspondence
    return attest_correspondence


__all__ = [
    "Quotation",
    "QuotationReading",
    "QuotationReport",
    "SecondOrderViolation",
    "check_quotation",
    "attest_quotation",
    "run_quotation",
    "SORT_PROPOSITION",
    "SORT_ABSTRACTION",
]
