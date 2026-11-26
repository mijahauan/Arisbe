# Directive: calculus conformance and certified soundness

**For:** Claude Code, working in this checkout. **From:** the author, 2026-11-25.
**The specification is** [../specs/2026-11-25-calculus-conformance.md](../specs/2026-11-25-calculus-conformance.md).
**Background:** [../specs/2026-11-11-reassessment.md](../specs/2026-11-11-reassessment.md).

This directive supersedes the `▶ START HERE` block in `CURRENT_PLAN.md` (docket item 10, the
UoD alphabet, waits behind this arc). Read the specification in full before touching code. Where
this directive and the specification disagree, stop and ask.

## The goal, in one sentence

Every inferential move Arisbe makes is either exactly one of Dau's rules or a recorded sequence of
them, checked at runtime by a kernel that imports no engine code — so that the soundness of every
recorded history follows from Dau's theorem and the kernel's correctness.

## Rules for this arc

- **Rulings come from the author.** R1 and R3–R8 are ruled (the specification's §7). R2 — the
  seven PROVISIONAL readings of Dau, checked against the book — is open and **blocks Phase 3
  only**: Phases 0–2 change no behaviour and may proceed. If the code suggests a PROVISIONAL
  reading of Dau is wrong, stop and say so; do not resolve it.
- **The standing cautions in `CLAUDE.md` all apply,** and four bite here: never change the tree
  under a running measurement (1); a fix that changes which moves apply re-pins refusal, structure
  *and* soundness (2); when a fix breaks a test, ask first whether the test passed because of a
  second defect (3); stage deliberately — one ledger family per commit, message true to the diff (7).
- **Prove a ledger fix by its extent key disappearing,** read from the pinned diff, and reproduce
  one instance by hand before shrinking an entry (CURRENT_PLAN's 2026-09-25 caution).
- **Numbers are generated, not narrated.** Every count in a commit message or document comes from
  a command run in that session.
- **No outreach.** Do not edit or send any letter, except marking `docs/share/LETTER_DAU_DRAFT.md`
  HELD in Phase 0 and correcting claims in Phase 5.
- **End every session** with a `CURRENT_PLAN.md` handoff that says which phase and entry are next.

## Phase 0 — orient (one short session)

1. Confirm HEAD and that `main` is level with origin (the author is pushing `655a88c` by hand; this
   environment's earlier attempt to push was blocked). If it is still ahead, say so before committing.
2. Commit the two specification documents and this directive, as the author's own commit if he
   prefers — ask.
3. Mark the Dau letter HELD at its top, with one line pointing to the specification.
4. Map every path by which a graph changes by inference (the specification's §3.3 lists the known
   ones): `graphify query`/`path` first, then grep. Write the map into the specification as §3.3a.

## Phase 1 — extract the kernel, changing no behaviour

Move `legal()` and its helpers, the licensed-result constructors and `postconditions` into
`src/dau_kernel.py`, per §3.1. The tests import the kernel. Add a test that fails if the kernel
imports any module outside the trusted base. **Gate:** the default calculus suite passes with
`tests/calculus_extent.json` byte-identical — a pure move changes no count.

## Phase 2 — certify, observing only

Build `certify()` and the certificate (§3.2) and route every path from the Phase 0 map through it,
in **observe mode**: certificates are computed and checked, and failures are counted, not raised.
Type every recorded act by the §3.4 classes. **Gate:** the kernel rejects exactly the moves the
ledger's SEVERE, DIFFERS and NOT-AN-EQUIVALENCE entries describe, and nothing else. Any other
rejection is a finding: stop and report it.

## Phase 3 — conform, one family per commit

In this order, which builds what later fixes need first:

1. VERTEX_ERA as its own entry point; CONSTANT_EXISTENCE and CONSTANT_IDENTITY (a kernel judgement
   and an entry point each); the constant normalisation at discharge becomes a recorded expansion
   (the specification's §4.4 — CONSTANT_IDENTITY added by the author's amendment of R7, 2026-11-25).
2. ERA of an edge removes the edge only (§4.1); the isolated vertex stays.
3. IT+ copies every vertex; the deeper-context join becomes copy, extend, merge as discrete steps
   (ruled 2026-11-25, R2 option A: the second iteration clause is a rule of its own, and the
   expansion to reproduce is the specification's §7a — extend, iterate with the link, merge, merge);
   the isolated-vertex defect is fixed; `derived_rules.universal_instantiation` is checked for a
   double join.
4. Enlarged selections (ERA, IT+) refused, with the closure offered per R3.
5. DC+ refuses a spot that is not the subject's area; the no-argument default per R4.
6. The named-with-contents normaliser for DC+, ERA, IT+, IT− — and the tier-A IT− residue
   investigated, not assumed.
7. IT− finds originals in the candidate's own context.
8. Vertex insertion in any context.
9. INS_EDGE as its own entry point.
10. MOVE_BRANCHES tries both orientations.

**Gate for each:** the entry's extent key is gone from the pinned diff; refusal, structure and
soundness are re-pinned together; the observe-mode certificate failures for that family fall to
zero; the correspondence suite is green on the affected rules (an isolated vertex left by edge
erasure must draw and re-read).

## Phase 4 — enforce

`certify` raises `CalculusViolation`; the UoD history stores each certificate; certificates are
re-checked on load. Add `rule_version` to chain steps and the legacy expansion (§5, per R5). Then
regenerate the corpus exemplars, asserting `same_graph` per file before each rewrite, and confirm
the `runs/` archive still loads. **Stop and ask the author before regenerating the corpus.**

## Phase 5 — measure and say so

With the tree frozen, run the exhaustive calculus suite and the full suite. Write the trusted-base
document (modules, line counts, what each is trusted for). Correct README, VISION_AND_SCOPE,
SOUNDNESS_BOUNDARY, CAPABILITY_MAP and CONTRIBUTION_AND_PRIOR_ART to say only what the certificates
support, and list what is still incomplete. Check the result against the specification's §8,
criterion by criterion, and report each as met or not.
