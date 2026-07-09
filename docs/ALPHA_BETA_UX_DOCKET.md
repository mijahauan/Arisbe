# Alpha/Beta UX Docket — persona audit (2026-07-09)

> **What this is.** A cross-persona audit of the **alpha + beta** Existential-Graph
> user experience in the web app (`/organon`, `/ergasterion`, `/agon`, `/import`),
> before any 2nd-order/frontier work. One agent traced each of the five
> [GETTING_STARTED.md](GETTING_STARTED.md) personas through their *typical tasks*
> against the actual route handlers + templates + JS; every finding is grounded in
> `file:line`. **Gamma / second-order / modality-frontier was out of scope by
> deliberate steer** — the goal is to get alpha/beta *squared away* first.
>
> IDs are `U1…U25` (this docket's namespace, cf. the `Gx`/`Rx` dev-tracking
> convention in [GLOSSARY.md](GLOSSARY.md#notation--reference-numbers)). Nothing
> here is fixed yet; this is the pre-work docket for prioritization.

## The headline pattern — *backend built, UI not wired*

The single most common finding, and it recurs across **all five personas**: a
capability is fully implemented and tested at the route/service layer, but the web
viewer never surfaces it. The calculus is not the gap — the last mile is. The
clearest instances: FOPL export (U4), worked-chain LaTeX (U5), citation/BibTeX
(U6), the readable formal-object view (U7), the construct-level skip-report (U17),
and the whole ontology file-import path (U1). Most are **additive, low-risk**
surface work over already-attested endpoints.

## Per-persona task completion — can they do it in the browser today?

| Persona | Typical task | In browser today? | Blocking finding |
|---|---|---|---|
| **Newcomer** | primer → challenge → draw a dragon, get graded | ⚠️ marquee deep-link lands on a **disabled canvas** | U2 |
| **Ontologist** | import a file → browse → ask a theorem of it | ❌ **no web import at all**; theorem silently no-ops | U1, U3 |
| **Logician** | 4-way form round-trip → apply six rules → step a proof | ⚠️ only **3** notations (no FOPL); proof loop itself works | U4 |
| **Mathematician** | read the formal object; §3.3; DAG history | ⚠️ sees only the **rendered picture**; formal object hidden | U7, U8 |
| **Peirce scholar** | step a proof → provenance/cite → LaTeX export | ⚠️ single-graph export works; **no chain export / no BibTeX** | U5, U6 |

The logician and mathematician have *degraded-but-functional* paths; the
**ontologist, scholar, and newcomer each have a broken primary path**.

---

## Findings

### Blocker

- **U1 · [BLOCKER] · Ontologist · Import** — No web file-import exists. `/import`
  accepts only *pasted linear-form text* (EGIF/CGIF/CLIF); there is no file upload
  and no OWL/`.ofn`/RDF/Turtle/SUO-KIF option. Every OWL/RDF path is CLI-only
  (`tools/owl_to_clif.py`, `domain_model_importer.from_owl_*`); the shipped
  `kind=ontology` UoDs were all pre-built by scripts. An ontologist working in the
  browser cannot get their file in.
  *Evidence:* `import.html:71`, `imports.py:56-127`, `import_service.py:58`
  (`_PARSERS = {egif,cgif,clif}`). *Direction:* file-upload affordance on `/import`
  wiring the existing translators → `kind=ontology` UoD.

### Real bugs (a core task fails silently or functionally)

- **U2 · [MAJOR] · Newcomer · Ergasterion** — The primer's dragon deep-link
  (`/ergasterion?challenge=🐉1`, the marquee newcomer path) has a load-time race:
  `openSession('empty_sheet')` (un-awaited) and `loadChallenges().then(...)` run
  concurrently; the challenge callback arms the freeform canvas, but session-open
  resolves later and unconditionally *clears + disables* freeform — so the newcomer
  typically lands with the challenge prompt, an enabled "Grade" button, and **no
  draw tools**. *Evidence:* `ergasterion.html:3039-3052, 2317-2346 (2332-2337),
  2875-2896`. *Direction:* `await openSession` before engaging the challenge, or
  guard the freeform reset for a pending challenge.
- **U3 · [MAJOR] · Ontologist · Agon** — Materialize-off trap. The theorem block
  (`theory_query.entails`) renders only when `materialize` is set, but picking a
  *corpus* ontology as M does **not** turn it on (only the curated examples do), so
  a pure T-box peels vacuously (TRUE/UNKNOWN) with no theorem block — the
  ontologist's core task silently produces a non-answer. *Evidence:*
  `agon.py:540-561`, `agon.html:456-462`. *Direction:* default materialize on when
  a `kind=ontology` UoD is chosen as M.
- **U22 · [MAJOR] · Ontologist · Import** — The one working web path (pasting raw
  CLIF) mis-shelves the result: `admit` hardcodes `UoDCategory.LITERATURE_EXAMPLE`
  and `source:` tags, so a pasted T-box never becomes a `kind=ontology` UoD (won't
  appear under Organon's "Ontologies" facet or read as an ontology in the
  M-picker). *Evidence:* `import_service.py:220, 209-213`. *Direction:* let the
  doorway declare/shelve a paste as `kind=ontology`.

### Backend built, UI not wired (surface existing tested endpoints)

- **U4 · [MAJOR] · Logician · all modes** — FOPL missing from the linear-form
  toggle. GETTING_STARTED §2c promises "EGIF / CGIF / CLIF / **FOPL**," and a
  module-level `egi_to_fopl(egi)→str` exists, but the data-driven `_FORMATS`
  registry has only three rows, so the fourth notation never appears. *Evidence:*
  `linear_forms.py:39-43`; generator at `chapter18_fopl_translation.py:741`.
  *Direction (verified trivial):* add `{"key":"fopl","label":"FOPL","generator":
  egi_to_fopl}` to the registry — the panel/selector are data-driven and need no
  change.
- **U5 · [MAJOR] · Scholar · Organon** — No worked-chain LaTeX export from the
  browser. `/export/chain` (one captioned figure per step) and `/export/document`
  (appendix of several UoDs) are fully wired server-side, but the export panel only
  ever POSTs single-graph `/export`. *Evidence:* `export.py:151, 201`; zero
  `export/chain|document` refs in `web_viewer/` (verified). *Direction:* an "Export
  worked chain (LaTeX)" button shown when the UoD has a chain.
- **U6 · [MAJOR] · Scholar · Organon** — No citation/BibTeX view. `/export/citation`
  returns an author-date line + BibTeX entry (and its docstring says it feeds the
  Cite affordance), but nothing calls it; the only cite surface is a checkbox that
  bakes a caption into LaTeX. *Evidence:* `export.py:182`; zero `export/citation`
  refs in `web_viewer/` (verified). *Direction:* fetch on UoD open, render the
  author-date line + a copyable BibTeX block.
- **U7 · [MAJOR] · Mathematician · Organon** — No readable formal-object view. The
  coordinate-free `/structure` payload (containment tree + polarity + per-ligature
  crossing-sequence) is consumed only by the WebGL well + the accessible lens; the
  accessible lens literally *is* the coordinate-free object but is labeled
  "Accessible reading — non-visual (screen-reader)," so the mathematician never
  opens the one view that shows their crown jewels. *Evidence:*
  `accessible-lens.js:86-108`, `organon.py:332-363`, menu at `organon.html:366-377`.
  *Direction:* add/relabel a "Structure (coordinate-free)" lens reading the existing
  `/structure` endpoint.
- **U17 · [MAJOR] · Ontologist · Import/Organon** — The "reported by construct,
  never silently dropped" promise is honored only at the CLI (stdout warnings at
  build time). The ontology UoD's provenance carries only a free-text `note`, not
  the structured skipped-construct list, and Organon surfaces no skipped block.
  *Evidence:* `porphyry_tree/provenance.json` (note-only); no import skip-report in
  `organon.{html,py}`. *Direction:* persist the importer's construct-level
  skip-report into provenance and render it in Organon detail.

### Navigation & legibility of results

- **U8 · [MAJOR] · Mathematician · Organon** — The derivation-DAG lens is
  display-only: nodes are non-interactive `div`s, so you can see branch topology but
  cannot click a state to inspect its formal object / linear form. *Evidence:*
  `derivation-dag-lens.js:139-150`. *Direction:* make nodes selectable → load that
  state into the drawing + form + reflex panels.
- **U9 · [MINOR] · Newcomer · Ergasterion** — On a wrong challenge answer the
  learner gets the word-diff + antidote but never sees the **correct target
  picture**; the route already returns `target_linear_forms` but the UI ignores it,
  and the prompt omits the challenge's plain-English title. *Evidence:*
  `ergasterion.html:2886-2892, 2898-2934`; `ergasterion.py:1218-1227`. *Direction:*
  draw the target beside the diff on an incorrect grade.
- **U10 · [MINOR] · Logician · Organon** — The chain player shows rule name +
  annotation per frame but not *what the step changed* (the per-step `legible_diff`
  that `/history-structure` already computes). *Evidence:* `organon.html:1299-1303`
  vs `organon.py:441-464`. *Direction:* carry `legible_diff` into `/chain` frames,
  render a one-line "+… / −…".
- **U11 · [MINOR] · Mathematician · Organon** — The per-ligature crossing-sequence
  (the central correspondence invariant) is never shown as *data* — only as a hue in
  the well lens and a phrase in the accessible lens. *Evidence:*
  `negation-well-lens.js:62-63,111`; `accessible-lens.js:99`. *Direction:* surface
  each ligature's required crossing-sequence in the structure lens (and on
  context-reflex when a line is selected).

### Discoverability & surfacing of existing UI

- **U12 · [MINOR] · Newcomer · Ergasterion** — Docs say "switch to challenge mode,"
  but challenge is a `<details>` disclosure nested inside the freeform block,
  reachable only after first picking a base context; a newcomer landing at
  `/ergasterion` meets a jargon-dense workshop with no signpost. *Evidence:*
  `ergasterion.html:694-706, 514-546`. *Direction:* a first-class
  "Challenge / practice" door on an empty session.
- **U13 · [MINOR] · Mathematician · Organon** — §3.3 attestation is stated
  positively but easy to miss: the status line is transient and the "≡ picture ↔
  proposition · correspondence, not truth" chord lives inside a `<details>` that
  renders **collapsed by default**. *Evidence:* `organon.html:725-735`,
  `linear-form-panel.js:91, 119-127`. *Direction:* a persistent "§3.3 attested"
  badge in the detail header, twinned with the standing badge.
- **U14 · [MINOR] · Ontologist · Agon** — The M-picker lists every corpus UoD flat
  under one optgroup by title, with no kind grouping (unlike Organon's "Ontologies"
  facet), so the ontologist hunts their ontology among proofs and boards.
  *Evidence:* `agon.py:453-462`, `agon.html:438-439`. *Direction:* carry `kind` into
  `/agon/models`, group ontologies.
- **U15 · [MINOR] · Logician · Ergasterion** — A rule refusal shows only as one
  transient line in the page-wide bottom status bar, disconnected from the rule grid
  where the logician acted, and gone on the next status write. *Evidence:*
  `ergasterion.html:2367-2372, 465-473`. *Direction:* surface the refusal inline near
  the rule-steps guidance, highlighting the failed step.
- **U16 · [MINOR] · Logician · Ergasterion** — "Apply rule" enables the moment a
  rule is selected, regardless of whether its declared steps are filled, so a
  premature click bounces off a server refusal. *Evidence:* `ergasterion.html:1985`
  (`btnApply.disabled = !currentRule`); `stepFilled` exists at `1115-1123` but isn't
  gated. *Direction:* gate the button on non-optional steps being filled.

### Honesty signals

- **U18 · [MINOR] · Scholar · Organon** — The cite checkbox is always enabled for
  peirce-tikz regardless of whether the graph has a source; the honesty guarantee is
  real but lives only at the data layer (`has_source:false` → an honest "reproduced
  with Arisbe" line), so the scholar gets no *pre-export* signal. *Evidence:*
  `organon.html:1385-1390`; `export.py:49-62`. *Direction:* disable/annotate the
  checkbox from the citation payload's `has_source`.
- **U19 · [MINOR] · Scholar · Organon** — The transcribed-vs-authored distinction is
  shown only implicitly, as the phrasing of the "proof:" line; no explicit labeled
  flag. *Evidence:* `provenance.py:140-152`, `organon.html:767`. *Direction:* a small
  "transcribed | authored" label beside the proof line.
- **U20 · [MINOR] · Scholar · Organon** — GETTING_STARTED §2e advertises ○/⛓/**⚔**,
  but ⚔ (withstood) requires an Agon signal and can never appear on corpus items, so
  a scholar reading Organon only ever sees ○ and ⛓ with no explanation. *Evidence:*
  `provenance.py:281-288`. *Direction:* note in the badge legend that ⚔ is earned
  only through Agon (docs, not a bug).
- **U21 · [MINOR] · Mathematician · Organon** — Nothing tells the mathematician the
  DAG states are immutable / append-only / content-addressed; node ids print raw.
  *Evidence:* `derivation-dag-lens.js:146-148`. *Direction:* a one-line note or
  tooltip on the node id.

### Copy / expectation mismatches

- **U23 · [MINOR] · Newcomer · Home** — The home Ergasterion card promises "promote a
  result into the corpus," but the mode contract has no direct workshop→corpus route
  (output goes to scratch or Agon), which the workshop UI then contradicts.
  *Evidence:* `index.html:83-88` vs `ergasterion.html:841-864`, `ergasterion.py:13-21`.
  *Direction:* reword to "…send a result to Agon to be tested."
- **U24 · [MINOR] · Newcomer · Home/Ergasterion** — The two reflexes GETTING_STARTED
  calls "worth keeping for life" (posited-vs-derived; a fragment is a building block)
  are never surfaced in the in-app path. *Evidence:* `primer.js:78-106`. *Direction:*
  a one-line "two reflexes" note in the primer's "where to go next," echoed on a
  correct grade.

### Scale

- **U25 · [MINOR] · Ontologist · Organon/Import** — Nothing warns before rendering a
  100+-axiom ontology (acknowledged super-linear to draw); the ontologist hits the
  slowness blind. *Evidence:* `GETTING_STARTED.md:153-155`; no size guard in
  `import_service.check` or the Organon render path. *Direction:* an axiom-count
  threshold warning and/or spine-only preview.

---

## Proposed fix ladder (priority × effort)

**Tier 1 — quick wins** — ✅ **SHIPPED 2026-07-09** (all nine; low-risk, additive,
mostly surface-existing endpoints; several *un-break a broken primary path*):

| ID | Persona | Fix | Status |
|---|---|---|---|
| U4 | Logician | FOPL registry row (`egi_to_fopl`) | ✅ live-verified: `fopl` in served forms |
| U2 | Newcomer | order deep-link: open session before arming challenge | ✅ E2E regression guard added |
| U3 | Ontologist | default materialize for `kind=ontology` M (+ `kind` in `/agon/models`) | ✅ ontologies labeled in picker |
| U5 | Scholar | worked-chain LaTeX export button (`/export/chain`) | ✅ live-verified: 13.8 KB `.tex` |
| U6 | Scholar | citation/BibTeX panel (`/export/citation`) | ✅ live-verified: citation + BibTeX |
| U13 | Mathematician | persistent "§3.3 ✓ attested" chip in detail header | ✅ |
| U18 | Scholar | cite checkbox `has_source` gate | ✅ (8/25 corpus items sourceless) |
| U23 | Newcomer | home card copy → "send a result to Agon" | ✅ |
| U20 | Scholar | standing-ladder note (⚔ earned only in Agon) in badge tooltip | ✅ |

*Verification: 145 tests green across the touched routes (export/organon/agon/primer/
ergasterion) + E2E page-load of all three modes + a live-server smoke of every wired
route + a new U2 regression assertion. No calculus/core module touched.*

**Tier 2 — medium** (a real lens/feature, still additive): U7 structure lens ·
U8 DAG click-through · U9 challenge target picture · U10 chain per-step diff ·
U11 crossing-sequence as data · U14 M-picker kind grouping · U15/U16 rule refusal
inline + apply-gating · U12 challenge-mode door · U17 skip-report persist+render ·
U19 transcribed/authored label · U24 two reflexes · U21 immutability note.

**Tier 3 — structural** (bigger; U1 is a *blocker* but a larger build): U1 web
file-import (upload + wire translators) · U22 import shelving as `kind=ontology`
(goes with U1) · U25 layout-at-scale guard.

*Note: priority ≠ effort. U1 is the audit's only blocker but is Tier-3 by size; the
Tier-1 quick wins collectively un-break the newcomer, ontologist-theorem, and
scholar-export paths for a fraction of the cost.*
