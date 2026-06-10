# Composition Workflow Specification

**Status:** reviewed design (2026-06-09), not yet implemented.
**Scope:** how Ergasterion lets a user *create* a graph from nothing — figure
out what she wants to say by direct manipulation — and carry the result
through derivation to a disposition (vault, Organon, Agon). Companion to
[TRANSFORMATION_WORKFLOW_SPEC.md](TRANSFORMATION_WORKFLOW_SPEC.md) (the
four-beat rule grammar, which governs the *middle* of this workflow) and
[LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md)
(the regimes; composition is regime 1 *by design*, §4).

---

## 0. The finding this spec answers

The current Ergasterion is a **derivation** UI that was never given its
**composition** half. The blank-sheet experience is a dead end:

- The only authoring input in the whole workshop is a raw EGIF textarea
  inside the INS rule form — and INS (correctly, as Dau's sound insertion)
  refuses positive areas, so **on a fresh sheet it can never fire**. The
  only sound way to get `(Human *x)` onto an empty sheet is the
  theorem-proving dance (DC+ → INS into the outer cut → DC−). That is
  *derivation*; a person drafting what she wants to *say* should never
  meet it.
- ERA (sound erasure) refuses negative areas — but a composer must be able
  to erase anything she just drew.
- Settle (regime 3) can move and resize elements — but only elements that
  already exist; nothing creates them.
- The architecture already licenses the missing workflow: regime 1 is
  defined as "drawn but not asserted, **invariant suspended on purpose**"
  — but no API or UI ever implemented a regime-1 mutation. Every mutation
  route is `/apply` with the six sound rules.

The repair is not to weaken the rules. It is to give the workshop the
composition phase the regime model always promised, with **explicit gates**
between the regimes so the user always knows which act she is performing.

---

## 1. The shape: three phases, two fixings

```
   COMPOSE  ──[ ① fix the graph ]──▶  DERIVE  ──[ ② fix the chain ]──▶  DISPOSE
  (regime 1,                        (the six rules,                  (vault ·
   palette,                          four-beat grammar,               Organon ·
   anything goes)                    recorded · undoable ·            Agon)
                                     replayable)
```

Two *fixings*, two different objects, both inside the workshop:

- **① Fix the graph** — the drafted drawing stops being clay and becomes a
  determinate proposition: the chain's **base state**. From then on it can
  change only by rule. (Peirce: the first fixing determines a *sign*.)
- **② Fix the chain** — the worked sequence of transformations stops being
  exploratory and becomes a determinate **reasoning episode**: sealed,
  replayable, citable. Only a fixed chain is eligible to leave the
  workshop. (The second fixing determines an *argument*.)

A session therefore carries a `phase` — `composing | deriving | sealed` —
and the UI signals it unmistakably (§5.1). Both fixings are themselves
recorded steps in the chain, so the whole episode — including its own
gate-crossings — replays.

### What each phase suspends and preserves

| | composing (regime 1) | deriving (regime 2) | sealed |
|---|---|---|---|
| soundness | **suspended** — add/erase anything | enforced (the six rules) | n/a (read-only) |
| well-formedness | **enforced** — the draft is always a real EGI (§3) | enforced | enforced |
| §3.3 attestation | not fired (regime-1 contract, existing tests) | not fired in-workshop; fired at save/serve boundaries as today | fired on export paths as today |
| linear forms | live after every action | live after every move | live |
| presentation (regime 3) | always available | always available | always available — *style within the fixed meaning* |

The last cell is the user's "finally fix the local meaning and then adjust
the appearance or style as desired **within that meaning**": settle and
style reprojection remain free at every phase because they never touch the
proposition.

---

## 2. Phase A — composing (the palette)

### 2.1 The palette

Four tools, matching the four kinds of ink Beta allows. Nothing else —
the palette *is* the ontology, which is itself the pedagogy:

| Tool | Places | EGI effect |
|---|---|---|
| **Cut** | an oval in a region | `with_cut` (new cut in that area) |
| **Line of identity** | a heavy spot/line in a region | `with_vertex_in_context` (generic vertex) |
| **Relation** (name + arity) | a named spot with n hooks | `with_edge` (edge, `rel`, `nu` over chosen lines) |
| **Constant** | a labelled spot | `with_vertex_in_context` (vertex with label, `rho`) |

Plus two non-placing actions: **Attach/Detach** (wire a relation hook to a
line of identity — drag from hook to line) and **Erase** (anything,
cascading; §3) and **Rename** (relation name, constant label).

A power-user fifth tool, **Fragment**, accepts EGIF text and grafts it into
the clicked region (`eg_splice.graft`) — the existing INS textarea
generalized to composition, where it belongs.

### 2.2 Placement = region + position

A click while a tool is armed determines two things:

- the **area** — by the same hit-testing the selection layer already does
  (the innermost cut interior under the cursor, else the sheet). This is
  the *logical* placement and the only part the EGI records.
- the **position** — recorded as a presentation delta (the regime-3
  machinery the session already carries, `presentation_deltas` /
  `effective_deltas`), so the user's spatial intent survives re-layout.

Drag-to-move and cut-corner-resize are Settle's existing interactions,
enabled permanently during composing (no toggle needed — in regime 1 the
canvas is *always* clay). Dragging an element across a cut boundary in
composing phase is a **logical move** (`with_vertex_moved_to_context` /
area reassignment), not a regime-3 violation — this is the one phase where
crossing a boundary is exactly what the user means.

### 2.3 The recorded step is a *rule application on a fixed graph* — composition is freeform

**Revised 2026-06-09 (supersedes the earlier "every action is a recorded
step").** The principle:

> **Every application of a transformation rule on a fixed graph is a recorded
> step. Composition of the base graph is freeform and records nothing.**

This tracks the seam between a *synchronic* sign and a *diachronic* argument. A
single graph is a proposition: its meaning is its **final configuration**, so the
*order* in which its elements were placed or erased carries no logical or semiotic
content — an element is a letter in a word, placed and erased freely until the
word is right. The view holds only the **presence, position, and removal** of
elements, never a history of how they got there. Composition is therefore
**freeform**: each palette action (§4) `POST /compose` **mutates the live
synchronic graph in place** (`update_composing_state`; the composing branch stays
`steps == []`) and **records no step**. Correcting a mistake is a direct edit —
erase the element — not a step-back through a sequence.

The *recorded* unit appears only in the next phase. Once the graph is **fixed**
(gate ①) the user explores the **paths of an argument** that is not yet fixed:
each transformation-rule application *is* a recorded, navigable, undo/redo-able
step (§3 of the transformation spec) — this is where the learning is. When the
argument is itself fixed (gate ②), the **fixed base graph + the worked path** can
be saved in Ergasterion as a possible graph/argument, or sent to Organon or Agon.
The recorded chain's **base state is the fixed graph**; it contains no
`compose.*` steps.

Three categories, kept distinct: **(a) composition** — freeform structure-building
of one synchronic graph, unrecorded; **(b) transformation** — recorded inference
on the fixed graph, diachronic; **(c) presentation** (Settle / regime-3) — free
repositioning in *any* phase, §3.3-attested, **never** a recorded step. (a)↔(b) is
the fixing boundary; (c) is orthogonal to both.

(Re-opening the clay: composing from the pre-gate synchronic base of a branch
that has since been fixed forks a *fresh* composing draft — a new single-graph
clay — leaving the fixed line intact.)

### 2.4 The live linear mirror

The `LinearFormPanel` (EGIF / CGIF / CLIF) already re-renders per state;
in composing phase it updates after **every palette action**. Watching the
linear form assemble while drawing — and conversely seeing the Fragment
tool's EGIF appear as ink — is the core teaching loop the user asked for:
*"see the linear translation of what she was drawing."*

---

## 3. Well-formedness: the invariant composing keeps

Regime 1 suspends *soundness and assertion*, *not* coherence. Every state
the palette can reach is a genuine `RelationalGraphWithCuts`:

- An edge's hooks may reference only lines in its own or **enclosing**
  areas (Dau's context condition) — the Attach tool simply refuses a hook
  to a line buried in a sibling/deeper cut, with a one-line explanation.
- Erase **cascades** to dependents: erasing a line takes the hooks wired
  to it (the edges are re-arched or refused per a confirm hint); erasing a
  cut takes its whole subtree. No dangling `nu`, no orphan areas.
- Rename/arity edits keep `rel`/`nu` consistent.

So "anything goes" means *any well-formed graph is reachable*, not *any
ink is storable* — which is exactly why the moment of fixing (gate ①) needs
no validation pass: the draft is an EGI by construction.

---

## 4. The server: composition ops + session phases

### 4.1 `src/composition_ops.py` (new, unprotected)

Pure functions `egi → egi` over the public immutable constructors
(`with_vertex_in_context`, `with_edge`, `with_cut`, …), one per palette
action, each enforcing §3 and raising `ValueError` with a readable message
on refusal. No protected-module change. (The archived
`drawing_to_egi_adapter.py` is superseded by this: ops over a live session
rather than a bulk import of a parallel drawing schema — one source of
truth, one render path.)

### 4.2 Session model deltas

- `WorkshopSession.phase: composing | deriving | sealed`.
  - `empty_sheet` and reopened *unfixed* scratch drafts open `composing`;
  - corpus-UoD bases open `deriving` (an asserted graph is already fixed);
  - reopening a draft past gate ① opens at its recorded phase.
- Gate crossings are recorded steps: `compose.fix_graph` (①) and
  `chain.fix` (②), so phase is derivable from the chain itself.
- Branch semantics: applying from a state *before* gate ① forks a
  composing branch (existing fork machinery); the gates belong to a branch,
  not the session, so an exploratory fork can re-open the clay while the
  fixed line stays fixed.

### 4.3 Routes

| Route | Phase guard | Effect |
|---|---|---|
| `POST /ergasterion/sessions/{id}/compose` | composing only | one palette op; body `{action, parameters, from_state_id}`; returns the standard session payload (svg, linear forms, chain, introspection) |
| `POST …/fix-graph` | composing → deriving | records `compose.fix_graph`; locks the palette; opens the six rules |
| `POST …/apply` (existing) | deriving only | unchanged |
| `POST …/fix-chain` | deriving → sealed | records `chain.fix`; the chain becomes read-only (navigation/replay/regime-3 only) |
| `POST …/adjust` (existing) | any phase | regime-3, unchanged |

Refusals are explicit (`409` + message): rules during composing ("the graph
isn't fixed yet — finish composing first"), palette during deriving ("the
graph is fixed — step back before the fixing to fork a new draft, or reopen
composition"), any mutation after sealing.

---

## 5. The UI

### 5.1 Unmistakable phase signal

The user must always know which act she is performing (her first ask: *"to
know, by some clear indication, that one had initiated the creation of a
new graph"*):

- a **phase banner** across the canvas top: `COMPOSING — nothing asserted;
  draw freely` (regime-1 amber) → `DERIVING — graph fixed; change by rule
  only` (regime-2 green) → `FIXED CHAIN — read-only; style and replay`
  (neutral);
- the right panel swaps wholesale: **palette** while composing, **rule
  grid** while deriving, **disposition panel** when sealed;
- the gate buttons are the panel's primary action: `① Fix this graph`
  (composing) and `② Fix this chain` (deriving), each with a one-sentence
  consequence line under it.

### 5.2 Canvas affordances (composing)

- armed tool → crosshair cursor + **ghost preview** under the pointer
  (the oval / spot / named spot that *would* land, in the region that
  would receive it — the region softly highlighted);
- click places; `Esc` disarms; `Delete`/`Backspace` erases the selection;
  double-click a relation/constant renames inline;
- drag = move (boundary-crossing allowed, §2.2); cut corners = resize;
  drag hook→line = attach;
- the linear panel pulses on each change so the eye is drawn to the
  sentence forming.

### 5.3 Disposition panel (sealed)

Replaces today's always-visible "Keep this work" section — disposition is
only offered for a **fixed chain** (an unfixed draft can still be parked in
the vault as a draft):

| Action | Meaning | Mechanism |
|---|---|---|
| **Save to vault** | keep the fixed episode in the workshop | scratch store, renamed **vault** in the UI; stores the full chain incl. compose steps and both fixings |
| **Send to Agon** | submit the result as proposal G to be tested | existing handoff, unchanged — *the only road to attested status* |
| **Publish to Organon (unattested)** | make the episode browsable in the archive as a **workshop record** | new: persists via `save_uod_with_chain` into a `workshop/` facet, **badged unattested** in every Organon view |

**Mode-contract note (flagged for the author).** The existing contract says
*no direct workshop→corpus route* — the corpus is earned through Agon, and
direct promotion was deliberately retired. "Publish to Organon" is
reconciled with that contract by **facet, not exception**: what reaches
Organon this way is an *unattested workshop record*, visibly badged, never
mingled with the attested corpus; §3.3 still runs at its save/serve
boundaries (it attests correspondence, not truth — same doctrine as today).
If even a badged presence is unwanted, this row drops without affecting the
rest of the spec.

---

## 6. Implementation order

1. **`composition_ops.py` + `tests/test_composition_ops.py`** — the pure
   layer: each op's happy path, §3 refusals (sibling-cut attach, dangling
   erase), cascade semantics, and `compose-op ∘ undo = identity` shapes.
2. **Session phases + routes + `tests/test_ergasterion_compose_routes.py`**
   — empty sheet opens composing; palette actions mutate the synchronic graph
   and record **no** step (the chain begins at gate ①); gate ① flips phase and
   refuses out-of-phase actions both ways; gate ② seals; scratch/vault
   round-trip preserves the fixed-graph base + the recorded chain (gates + rule
   moves, no `compose.*`); replay verifies the loaded chain end-to-end.
3. **UI: palette + phase banner + gates** — tool arming, ghost previews,
   placement (area + position delta), drag/resize/attach/erase, inline
   rename, live linear panel; disposition panel.
4. **Polish** — bidirectional linear↔canvas (edit EGIF in the panel while
   composing → re-parse and redraw), keyboard map, onboarding hint text on
   the empty sheet ("pick a tool and click the page").

Phases 1–2 are pure logic + routes (no protected modules, testable
headless); phase 3 is where the user's experience changes.

---

## 7. Test fixtures worth writing first

- *the user's own scenario*: blank sheet → place `Human` spot → line →
  attach → cut around it → place `Mortal` inside → fix graph → DC+/IT+ a
  derivation → fix chain → vault. Assert the linear mirror at each step.
- erase-cascade: erase a line wired to two relations; erase a cut holding
  a sub-draft.
- gate refusals both directions; fork-before-gate re-opens clay.
- replay a vaulted chain containing compose steps, both fixings, and rule
  steps — byte-stable states throughout.
