# Troubleshooting — the refusal index

> **What this is.** When Arisbe refuses to do something, it refuses *for a reason stated in
> Existential-Graph vocabulary* — a refusal is a correctness feature, not a crash. This page
> catalogues every refusal a user or integrator meets, what it means, and what to do. It is
> the twin of the design docs: those say *why* the guarantees exist; this says *what you see
> when one bites*. (Disposed from the STORM documentation audit, G2, 2026-07-06.)

## The two kinds of "no"

Arisbe distinguishes **ill-formed** ("this cannot be read as a graph at all") from
**well-formed but refused** ("this is a graph, but the move you asked for is not licensed
here"). The first is a parse/validity error; the second is the calculus protecting a
guarantee. Knowing which you hit tells you whether to fix your *input* or your *move*.

## The refusal catalogue

| You see | What it means | What to do |
|---|---|---|
| **`CorrespondenceViolation`** (§3.3) — e.g. "vertex label box overlaps…", "line of identity strikes through a label it is not incident to" | The drawn picture and the linear form would denote *different* objects, or a mark is illegible — the central invariant refuses to serve a picture that lies about its logic. Raised at a render/save boundary (`correspondence_attestation.py`). | This is the system doing its job. In the web UI the pair is simply not served; try a different layout (regenerate), or a smaller graph. In an unattended run the segment is skipped-and-counted (see the operator note). If you are *authoring* a renderer, this is telling you your geometry doesn't match the EGI. |
| **`Regime3Violation`** — a presentation move (`move_vertex`/`reshape_cut`/…) that would cross a cut boundary | You tried a *pure-appearance* nudge that would change what the graph *means* (moving an element into or out of a cut). Regime-3 edits are meaning-preserving by construction; this one wasn't. | Keep the nudge inside the element's own area. To actually change containment, use a transformation *rule* (in Ergasterion/Agon), not a presentation move — meaning-changes must go through the calculus. |
| **`PHASE_REFUSED` (HTTP 409)** | A composition/workshop action was attempted in the wrong phase — e.g. applying a rule to a graph that has not been *fixed* yet, or changing the meaning of a graph that is already fixed. | Follow the phase contract: draw → **fix** (read the drawing into a sign) → then rules apply. The Graph↔Argument switch in Ergasterion makes the current phase visible; switch it before the move. |
| **drawing-validity findings** — `overlapping_cuts`, `dangling_line` (errors); `boundary_band`, `unwired_predicate`, `label_overlap` (warnings) | A freeform drawing cannot yet be read as a well-formed graph (errors) or is readable but risky (warnings). Raised by `drawing_validity.validate_drawing` before a fix. | Errors block the fix — resolve them (separate the cuts, connect the dangling line). Warnings don't block but flag likely mistakes. The report names each in EG terms, not internal ids. |
| **grading `DiffReport` findings** — `missing`, `extra`, `scope`, `incidence`, `order`, `structure` | Your freehand answer differs from the target: a predicate absent/extra, a line in the wrong area (scope), wrong argument order, etc. Not a refusal — *feedback* (`egi_diff.legible_diff`). | Each finding is a specific, plain-language correction. `same_graph` accepts *any* isomorphic rendering regardless of layout/label choices, so a diff means a genuine logical difference, not a cosmetic one. |
| **`NO_PROPOSAL`** (audit/modal routes) | You asked to peel a standing proposal against a UoD's history, but neither a `?proposal=` was given nor does the UoD declare an `audit-proposal` annotation. | Pass `?proposal=<EGIF>` explicitly, or add an `audit-proposal`-tagged annotation to the UoD. |
| **`MODAL_PROPOSAL_INVALID`** (modal route) | The `?proposal=` EGIF you passed to the modal lens's compound-meaning reader is not well-formed. | Fix the EGIF (the error carries the parser message); the modal lens's proposal box shows it inline. |
| **`CHAIN_NOT_FOUND`** (export/chain, history routes) | You asked for a transformation chain on a UoD that has none (a synchronic graph, not a worked derivation). | Synchronic UoDs have no chain to export/replay. Check `has_chain` on the detail route first; the modal/audit lenses report this cleanly. |
| **`UOD_NOT_FOUND`** | The UoD id doesn't exist in the corpus. | List ids via `GET /organon/uods`. |
| **import skip-report** — "cardinality restriction skipped", "union skipped", etc. | An OWL/CLIF construct outside the importable (Horn-shaped) fragment was **reported, not silently dropped**. | The construct isn't in M, on purpose. The report names each; decide whether to re-express it (e.g. a cardinality as a rule) or accept the honest gap. See `EXTERNAL_SOURCES_AND_IMPORT.md`. |
| **a layout that hangs on a very large graph** | Historically the ligature router and canonical-signature could go super-linear on hub-shaped graphs. | Largely fixed (2026-07: visibility-graph pruning, hash-consed signatures — see the run logs). If you still hit it, the graph is likely machine-scale (hundreds of atoms, one high-degree hub); reduce hub degree or file it with the fixture. |

## For unattended runs

A live run adds an operator's view of the same refusals. A checkpoint that fails §3.3 under
`checkpoint_refusal="skip"` is **counted and quarantined** (`refused_seg<n>.json` beside the
state file), and the run continues — never a silent skip, never an unattested write. A crash
is caught by the driver's supervisor and auto-resumed from the last checkpoint. Fetch errors
from a live source are counted (`fetch_errors`) and the poll retried next cycle. The
per-segment digest surfaces all of these; see `AUTOMATED_ENDOPOREUTIC_GAME.md` §10 and the
`runs/RUN_*_LOG.md` notebooks. (A consolidated operator runbook is queued — audit G5.)

## When it really is a bug

The refusals above are *designed*. If you hit an unhandled exception (a traceback, not a
structured refusal), that's a bug — see `CONTRIBUTING.md` for where it goes. The fastest
triage: does the message name an EG concept (a cut, a ligature, an area, a phase)? Then it's
a guarantee refusing. Is it a raw Python traceback? Then it's ours to fix.
