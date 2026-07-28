# Letter draft — Frithjof Dau

**Status: internal draft in the author's voice (2026-07-28), built from
[LETTER_DAU_SKELETON](LETTER_DAU_SKELETON.md). Not for sending until the
author revises and signs.**

---

Dear Dr. Dau,

I have spent several years building an environment for Peirce's existential
graphs, and your *Mathematical Logic with Diagrams* serves as its bedrock —
not as an influence among others, but as the mathematics the whole system
stands on. That makes you the one reader best placed to refute it, which
gives me two reasons to write: to acknowledge the debt, and to ask for the
refutation.

The calculus in the engine remains yours, deliberately unimproved: erasure,
insertion, iteration and de-iteration, the double cut, Beta-aware, over your
graph-with-cuts structure. Where the system says "the picture never lies," it
can say so only because your formalization makes that a theorem rather than a
hope. A protected core of tests — the rules, closure, isomorphism, the Beta
proof exercises — must pass on every change, and a failure there counts as a
mathematical defect, never as noise. As far as we could find, no
machine-checked formalization of your calculus exists in Coq, Lean, or
Isabelle; our executable suite comes closest among what we located, and we
offer it for your inspection as exactly that — an operational guarantor, not
a proof. A true mechanization would serve the field, and we would welcome
your involvement in one.

Three claims stand where your judgment would weigh most.

First, the correspondence invariant. Your Chapter 18 translations anchor the
linear side; we claim the drawn side now carries equal standing. Every pair
the system serves — the graph as drawn, the graph as written — passes a
runtime check that reads containment, incidence, and each ligature's
crossings off the drawn shape, and refuses any pair whose forms fail to
denote one object. Not proved once; attested at every request.

Second, the examined departures. In three places we depart from Peirce as
you and the tradition read him, and each departure has survived an
adversarial examination only with amendment: the treatment of convergence
and "the real"; the rule that nothing contingent stands derived at the sheet
level; and the choice to draw no modal mark at all, letting the branching
history serve as the frame — adequacy claimed, completeness not. We also
concede a loss outright: identity as a spot where Peirce had the line. You
may judge any of these wrongly taken. The record of the examinations exists
so that you can.

Third, the one opening of the core. In July we added a second-order device —
a sort on the incidence and a quotation area, mention never use — and made
all six rules preserve it while refusing to operate inside it. The standing
invariant we claim: conservativity over your calculus. A three-tier gate
tests it — corpus-wide invisibility, an erasure projection under which a
quoted law licenses nothing, restraint of every rule at the boundary.
"Dau remains the guarantor" names a testable claim in this system, not a
posture, and we would rather you test it than take our word.

So, the questions:

1. Does the implementation read to you as your calculus? Any divergence you
   find counts as our defect by definition — the bedrock stays
   non-negotiable.
2. Does conservativity state the right invariant for the second-order
   opening — or can you construct a leak?
3. On identity-as-spot: does our concession state the loss honestly, or did
   we miss a line-of-identity treatment we should have found?
4. Would a machine-checked mechanization of your calculus interest you, as a
   joint or supervised effort?

Behind this letter stand the documents and suites you would need: the
correspondence contract, the fidelity examinations with the departures
argued, the conservativity briefs, and a short page of exact commands — the
core suite, the conservativity gate, a worked chain replayed end to end — so
that breaking it costs you an afternoon, not a month. If it breaks, we want
to know more than anyone.

With respect and gratitude,

Michael Hauan
