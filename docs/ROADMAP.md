# Arisbe — Roadmap

> **What this is.** The program lever, not a contract — one place naming what's live and who
> decides what's next. *Re-consolidated 2026-07-20; superseding the 2026-06-27 consolidation*
> (that text is preserved in git history; every existing link to this file keeps working).
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) · [CAPABILITY_MAP.md](CAPABILITY_MAP.md) ·
> [GLOSSARY.md](GLOSSARY.md) · [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md).
>
> Items marked **(author decision)** need a call only the author can make; the rest are buildable
> once sequenced. **Maturity** mirrors [CAPABILITY_MAP.md](CAPABILITY_MAP.md): DESIGNED = specced
> not built; FRONTIER = built but an edge remains; DECISION = a choice precedes any build.

---

## Preamble

The organizing principle changed on 2026-07-20. Instead of a flat backlog, the program is now
four workstreams, named by verb: **Share · Use · Run · Understand.** The frame is
[THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) — the doctrine doc that
worked out the UoD/commens pair, why institutionalization cannot occur in an individual, and the
entailment that follows (§10): the solitary ceiling on what one kytos can attest sits below the
community's **by kind, not effort**, and because the commens is a social construct sustained only
by participation, connecting outward does not merely reach a standing resource — it **keeps that
resource in being**. That entailment is stated up front because it is the reason this rewrite
exists: the four workstreams below are its concrete forms, not four independent priorities.

- **Understand** (Workstream A) — keep the doctrine that grounds everything else legible and
  ratified, so the other three workstreams build on a conforming foundation.
- **Share** (Workstream B) — push the project's own membrane outward: the documentation sweep
  and the first publication, the acts of *export* the doctrine doc names in §1 and §10.
- **Run** (Workstream C) — strengthen the membrane mechanism itself: the UoD-per-instance
  discipline made code-real, import/export unified, the interaction capability (**A** in the S/A
  pair, doctrine doc §4) instrumented to match the interior (**S**).
- **Use** (Workstream D) — the people-facing edge: the issue inventory and the Charter-gated UX
  fixes that make the other three workstreams reachable by someone who wasn't here while they
  were built.

**Two rules hold across every item below:** every item carries either an **(author decision)**
tag or a concrete next action — nothing is left to float without an owner; and the doctrine doc's
vocabulary is used exactly (UoD = the internalized, attested model inside a membrane; commens =
the un-possessed outside, never a data structure) with the ban-list from doctrine §7 respected
throughout — the register here is "tends," "the current best-attested," "open," never a terminus
word.

---

## Workstream A — Understand

The foundation sub-project itself: [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md)
(the doctrine doc), the minimal ripple set into [GLOSSARY.md](GLOSSARY.md),
[THE_KYTOS.md](THE_KYTOS.md), [THE_MEASURE_OF_KNOWLEDGE.md](THE_MEASURE_OF_KNOWLEDGE.md), and
[CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md), and this rewritten ROADMAP.
**Shipped when this commit lands.**

What remains in this workstream is not a build — it is a set of rulings only the author can make.
The doctrine doc carries eleven `[flagged]` assistant elaborations, gathered as a numbered list in
its own [§11 — Open verdicts](THE_COMMENS_AND_THE_COMMUNITY.md#11--open-verdicts)
**(author decision — ruled later, per the doctrine doc's own OQ3)**. Two carried backlog items
belong here too (see Carried-forward → Understand, below): B-full (#13) and the Departure-I
reflexive-diagonal thread (#12).

## Workstream B — Share

The documentation sweep plus the first publication choice — the project's membrane pushed
outward, per doctrine §10.

**The sweep (next action, no single owner-decision blocks starting):**
- One canonical phrasing per concept across the docs the doctrine arc touched only glancingly —
  README, [CAPABILITY_MAP.md](CAPABILITY_MAP.md), [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md), the
  membrane docs ([AUTOMATED_MODEL_DEVELOPMENT.md](AUTOMATED_MODEL_DEVELOPMENT.md),
  [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md)) — none of which were
  harmonized to UoD/commens vocabulary by workstream A (that harmonization was explicitly routed
  here, not done in A).
- The overclaim hunt, including the "final"-family ban (doctrine §7) applied corpus-wide, not
  only in the doctrine doc itself.
- Quarto-book (`_quarto.yml`) membership decisions, including whether/where
  [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) joins the book (deferred by
  workstream A on purpose).
- A readability pass over the whole spine with an outside reader's eye — the sweep's purpose is
  **legibility** (takeable-up by someone who wasn't in the room), not tidiness for its own sake.

**The publication choice.** Five candidate theses, carried as candidates only — **which one is
first is (author decision)**, not made here:

| # | Candidate | What it argues | Venue note |
|---|---|---|---|
| i | §3.3 correspondence | The inerrant linear↔graphical correspondence discipline (totality/injectivity, containment, incidence, transformation invariance) as a general contract for diagram calculi, not only for EGs | A diagrammatic-reasoning or formal-methods venue (e.g. *Diagrams*, or a proof-theory/logic journal covering diagrammatic calculi) |
| ii | Modality without Gamma | The diachronic branching DAG read as a Kripke frame with no modal mark in the ink — [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) | A modal-logic or philosophy-of-logic journal, or a Peirce-studies venue (e.g. *Transactions of the Charles S. Peirce Society*) |
| iii | Conservative mention-ascent ("thirdness kept") | The B-min quotation crossing as a scoped, conservative slice of Gamma — expressive power unchanged (Dau Ch. 26's reduction), iconicity the only honest motive to cross at all | The same Peirce-studies venue as (ii), or a higher-order-logic venue interested in conservative extensions |
| iv | The EPG as live model-development architecture | `agon_evolution.py` → `agon_llm.py` → `agon_metalearning.py` → the membranes → `live_runner.py` as a working automated-theory-revision loop over live sources | A knowledge-representation or multi-agent-systems venue (e.g. KR), or the belief-revision (AGM) community directly |
| v | The measure and the kytos | [THE_MEASURE_OF_KNOWLEDGE.md](THE_MEASURE_OF_KNOWLEDGE.md) + [THE_KYTOS.md](THE_KYTOS.md) as a fractal, vector-valued (never scalar-over-agents) knowledge measure, with the West correspondence as the named quantitative frontier | A cognitive-science or complexity-science venue interested in scaling laws applied to knowledge/institution measures |

**Next action:** hold the sweep as a standing docket; surface the five candidates to the author
for the first-paper ruling once the sweep has stabilized the vocabulary each draft would need.

## Workstream C — Run

Strengthening the membrane mechanism itself — the mechanism the doctrine doc's §1 defines and §4
splits into S (interior) and A (interaction).

- **Settle UoD-per-instance operationally.** The doctrine doc's per-kytos UoD definition (§1) is
  currently a doctrinal statement more than a code-level guarantee everywhere it should hold;
  make it code-real across the loops and membranes that currently carry M more loosely.
  **Next action:** an audit of every place a "model" is carried (`world_scroll.py`'s residence,
  the live membranes, the corpus UoDs) against the doctrine's per-instance/internalized/attested
  definition, flagging any gap.
- **Unify import/export into one membrane seam.** The codebase already gestures at this —
  `ImportExportManager` is sketched but not implemented
  ([IMPORT_EXPORT_FORMATS.md](IMPORT_EXPORT_FORMATS.md) §36.6, marked PLANNED API), and the
  2026-07-20 graphify run over the codebase surfaced it again as the natural single seam for what
  is currently split across `/import`, `export_service`, and the individual format
  parsers/generators. **Next action:** design the real seam (author decision on scope — whether it
  subsumes the live-source membranes too, or stays a linear-format doorway).
- **S/A instrumentation symmetry.** S (the interior) is already well-instrumented (|M|, the K3
  materialization ratio, the peel's cost curve, decay TTL, admission/retraction rates). A (the
  membrane) is the "missing fifth," younger and thinner-instrumented — import/export throughput,
  proposal/doubt rate, horizon size, severity-weighted yield exist individually but are not read
  together the way S's numbers are. **Next action:** an A-side dashboard/digest parallel to the
  existing S-side digests, so poise (doctrine §4) can be read from data rather than inferred.
- **Payoff.** Once S and A are both legible per-instance, the Q-B apportionment / West experiment
  (one big Arisbe vs. distributed kytē + a coordinator, doctrine §5) becomes actually runnable —
  it needs measurable S, measurable A, and a measurable allocation between them on *multiple*
  instances at once, which this workstream is what supplies.
- **Gate:** any push-back-on-source behavior (directed engagement rung 2, #17 below) needs its own
  outward-facing ethics pass **before** it ships, independent of the rest of this workstream.

## Workstream D — Use

The people-facing edge. **First deliverable: the issue inventory** — the author's own list and/or
a fresh persona / [UI_TRANSPARENCY_CHARTER.md](UI_TRANSPARENCY_CHARTER.md) audit, both feeding one
docket rather than two competing ones. **Next action:** run that audit (a subagent task, not a
design decision) and produce the docket.

Once the docket exists, fixes are tiered under the Charter's seven testable principles
(orientation · one-word-one-way · recognition-never-recall · the-picture-never-lies ·
prevent-don't-punish · error language · help ≤1 hover/2 clicks) — the same discipline every prior
UI docket in this project has used. Several carried items below (#6, #7, #8, #10, #11) are UX
frontiers that the issue inventory should re-triage rather than resequence blind.

---

## Carried-forward items

Every still-live item from the pre-2026-07-20 backlog, kept under its **old number** for
traceability, slotted under the workstream it now belongs to.

### Understand

- **#12 — Doctrine: Departure I reflexive-diagonal argument.** The one open joint held "at parity"
  in [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md). A standing intellectual thread, not
  a build. **(author decision — open, no forcing function)**.
- **#13 — B-full, the second-order core opening's next rung.** Stage ⓪ (the quotation overlay)
  and stage ① (B-min, the authorized core opening) both shipped 2026-07-15/16; B-full — a native
  graph-valued element kind, widening ν across ~52 modules/252 sites, not additive the way B-min
  was — needs a **freshly stated marginal value** before it is authorized at all (the memo's
  original stated hinge, S3, was discharged at B-min). Four open questions (B-full-1…4) are
  carried in `CURRENT_PLAN.md`. **(author decision, held — awaiting a fresh marginal value)**.

### Share

*(No carried numbered items — workstream B's own docket, above, is the live work here.)*

### Run

- **#3 — Cross-UoD reference/transclusion, increment 2 (the use/mention fork).** Increment 1
  (intra-UoD) shipped 2026-06-29. Increment 2 is not "more reference" but a fork per
  [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) — **use** (governed import via the
  scroll `~[ B ~[ G ] ]`, low/attributed warrant, never a transparent merge of universes) vs.
  **mention** (second-order naming — the B-min quotation-overlay path already discharged this
  half, see Discharged tail). **The *use* half is (author decision, held)** on the second-order
  frontier; it belongs to Run because a governed cross-UoD import is exactly the membrane-seam
  work this workstream is doing anyway.
- **#9 — Layout-perf frontier.** Super-linear layout cost beyond ~127 axioms; the 130-cut COLORE
  density closure imports as data but stays undrawn. Belongs to Run because it is an S-side
  (interior) scaling limit directly relevant to the Q-B/West experiment's cost curves. The
  display-side mitigation (adaptive-scope / semantic-zoom) is tracked separately in
  [ADAPTIVE_SCOPE_VIEWER.md](ADAPTIVE_SCOPE_VIEWER.md). **Next action:** none scheduled; re-triage
  alongside the Q-B experiment design.
- **#17 — Directed engagement, rung 2 (mutual co-evolution / pushing back on the source).**
  Staged in [BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md](BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md) §3: rung
  0 (tropism + docket) is built; rung 1 (the economy-of-research ordering of reaches) shipped
  2026-07-17 (`attention_economy.py` + `arithmetic_world.py`, S1–S5 held). Rung 2 needs its own
  outward-facing ethics pass before any push-back-on-source behavior ships — **the Run workstream's
  own gate, above.** **(author decision — the ethics pass itself, not yet scheduled)**.
- **Vault V2a.2, items 1 and 3.** Item 2 (banking an answer via quotation) shipped 2026-07-18/19.
  Items 1 (multi-paragraph answers) and 3 (real NL interpretation of an answer's content) are
  deferred on a **timing rider: RUN 13's first answered note** — they need a real answered note to
  design against, not a fixture. **Next action:** wait on RUN 13 (Standing runs, below), then
  design items 1+3 against what the author actually wrote back.

### Use

- **#6 — NL→logic fast-follows.** (a) Multi-candidate disambiguation (G1/G2/G3 ranked *by
  verdict*, not parser confidence — the distinctively-Peircean move) is a UX design task; (b)
  LOW-warrant `/import/admit` persistence of a tested proposal carrying its NL+LLM provenance
  touches the Run workstream's import/export seam and should be sequenced after that seam exists
  rather than against today's split doorway. **Next action:** (a) is buildable now; (b) waits on
  Run's unified seam.
- **#7 — Endoporeutic Game contest-UX frontier.** Fuller semantic-layer integration into the
  contest UX, and a dynamically-learned model M in the hot-seat arena (today's V1 arena is
  hot-seat only). See [AUTOMATED_GRAPHEUS.md](AUTOMATED_GRAPHEUS.md). The UX half sits in Use; the
  "dynamically-learned M" half is really Run's automated-EPG arc reaching into the contest board —
  **re-triage once the issue inventory exists.**
- **#8 — Tension layout frontier.** Branch points, multiple threads, non-monotone ligatures
  (single collinear threads done, 10/11). See [TENSION_LAYOUT.md](TENSION_LAYOUT.md) §9–§10.
  **Next action:** none scheduled; a Charter-relevant ("the picture never lies") re-triage
  candidate for the issue inventory.
- **#10 — Diagram↔narration, next falsifications.** The scorer is a prototype (8 chains/35 steps).
  Next: a narration corpus (inter-narrator agreement), an LLM bridge (free narration), macro
  sub-step expansion, metric-3 chapter-boundary on a branching DAG. See
  [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) §10. **Next action:** none scheduled;
  candidate for the issue inventory's docket.
- **#11 — Schema-drawing / §3.3 for the schema node.** The graph-with-holes schema layer is built;
  drawing it and attesting its correspondence is the open edge (the math track is otherwise
  complete). **Next action:** none scheduled; candidate for the issue inventory's docket.
- **Tutor loop (its own note, cross-cutting Use).** Designed 2026-07-17
  ([TUTOR_LOOP.md](TUTOR_LOOP.md)): the attention socket pointed at a human learner, a
  learner-ledger (K1–K4 per skill atom, never a scalar rank or access gate), the EPG as tutorial
  protocol, staged T0 scripted-learner → T1 author → T2 neophyte with TS1–TS5 pre-registered.
  **Design complete; build unauthorized. (author decision — placement/authorization, held per the
  design doc's own open decisions in its §7.)**

---

## Discharged tail

Done items, one line each. Full build history lives in `CURRENT_PLAN.md` and the project memory.

- **#1 — Protected-core question.** Decision taken & executed 2026-06-27 (17 → 14 modules; the
  three §3.3 enforcers added, the linear parsers/generators trimmed).
- **#2 — Render-M UI.** Ground/legend + relevant-neighborhood M-render shipped 2026-06-28.
- **#4 — Newcomer/EGIF on-ramp.** Stages 1 + 2(a) + 2(b) all shipped 2026-06-28 (propose-vs-model
  split, the plain-English NL door, the guided primer).
- **#5 — Context-reflex overlay docking.** Shipped 2026-06-28 (auto-dim-on-overlap).
- **#14 — LaTeX export path.** Complete 2026-06-29 (the authentic-Peirce TikZ exporter, the
  iconic scroll glyph, the worked-chain document, the drawing→EGI learning loop).
- **#15 — Start-up guidance for new users.** [GETTING_STARTED.md](GETTING_STARTED.md) done
  2026-06-29.
- **#16 — External-sources & import documentation.**
  [EXTERNAL_SOURCES_AND_IMPORT.md](EXTERNAL_SOURCES_AND_IMPORT.md) done 2026-06-29.
- **Mention-ascent, stages ⓪+①.** The quotation overlay (stage ⓪) and B-min (stage ①, the
  authorized core opening: sort/quotation maps, all six rules sort-preserving, the committed
  drawn convention, S3 checked off the drawing) both shipped 2026-07-15/16
  ([CROSSING_DECISION_BRIEFS.md](CROSSING_DECISION_BRIEFS.md)). B-full carried forward as #13,
  above.
- **The automated-EPG arc.** `agon_evolution.py` (the Agon as engine of change) →
  `agon_llm.py` (the three LLM roles under an incorruptible mechanical referee) →
  `agon_metalearning.py` (the game studying its own resolution principles) → the membranes
  (`discourse_membrane.py`, `resolving_membrane.py`, `wiki_dispute_membrane.py`) →
  `live_runner.py` (bounded, paced, checkpointed live play) → the live sources
  (`wikidata_source.py`, the weather trilogy runs 7–11, `sports_source.py` / RUN 12). See
  [AUTOMATED_MODEL_DEVELOPMENT.md](AUTOMATED_MODEL_DEVELOPMENT.md) and
  [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md).
- **The vault arc, V0 → V2a.2 item 2.** V0 (the metadata membrane, `vault_world.py` +
  `probe_feed.py`) built + pushed 2026-07-18; V2a.1 (the oracle-notes loop, `oracle_notes.py`)
  built 2026-07-18; V2a.2 item 2 (banking an answer via quotation) built 2026-07-18/19. Items 1+3
  carried forward under Run, above. RUN 13 (Standing runs, below) is this arc live against the
  real vault.
- **The measure/kytos/tutor-design pass.** [THE_MEASURE_OF_KNOWLEDGE.md](THE_MEASURE_OF_KNOWLEDGE.md)
  ratified + K3 (materialization ratio) built 2026-07-17; [THE_KYTOS.md](THE_KYTOS.md) ratified
  2026-07-19; [TUTOR_LOOP.md](TUTOR_LOOP.md) designed (carried forward, unauthorized, under Use
  above).
- **Pre-existing discharged tracks** (carried forward unchanged from the 2026-06-27
  consolidation, for the record): the freeform composition arc (steps 1–4); fold-to-define; the
  warrant-gradient / context-reflex / correspondence-chord / dragons UX threads; the FOLIO/DLCore
  coverage levers; the OWL/RDF import breadth; the modality-without-Gamma and level-zero doctrine
  passes; the web-presentation fidelity audit (2026-06-26).

---

## Standing runs

A section the pre-2026-07-20 ROADMAP lacked — the live/recently-closed automated runs, tracked
here rather than only in `runs/`.

- **RUN 13 — in flight.** The vault cycle, World #2 (the author according to Arisbe): the P2¹³
  vault oracle loop is running against the real vault, its legible-questions comparator instrument
  (docket-selected vs. template-random, author-rated) **on by default**. See
  [runs/RUN_13_LOG.md](../runs/RUN_13_LOG.md) for the pre-registered priors (P1¹³–P5¹³) and the
  findings recorded so far (F1¹³/F2¹³/F3¹³, all fixed same-day). Disposal against the priors is
  the author's, in due course.
- **RUN 12 — disposed 2026-07-20.** The sports (MLB) resolving membrane, closed by author STOP
  after 359 rounds (300 picks raised, 215 resolved). `select_best` **did discriminate** among the
  five rival arms — closing standings: odds +8 net / 0.633 acc, home +6 / 0.607, naive +1 / 0.667,
  cal −1 / 0.484, strong −3 / 0.448, with the leader flipping home↔odds across the run rather than
  being fixed from the start. See [runs/RUN_12_LOG.md](../runs/RUN_12_LOG.md) for the full
  per-prior evidence (P1¹²–P5¹²) including the two mid-run operational findings (the All-Star-break
  thin-data leg, the decay-refusal crash-loop already fixed on `main` ahead of the live evidence).
  **The disposal ruling against the pre-registered priors is the author's** — this ROADMAP records
  the run as closed and the data as landed, not any particular disposition of the priors.
