# Web Viewer Design System

The single source of truth for the look, motion, and vocabulary of Arisbe's
three web-viewer modes — **Organon** (archive, read-only), **Ergasterion**
(workshop, composition), **Agon** (arena, contest). It exists so the three
surfaces read as *one application*, and so a returning author (or agent) does
not re-derive the conventions each session.

> Scope note. This is the *chrome* contract — colours, spacing, type, camera,
> vocabulary. It is deliberately **not** an architecture doc (that is
> [CLAUDE.md](../CLAUDE.md)) nor the correspondence contract (that is
> [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md)). The
> guardrail those docs impose still binds here: **no mark bears actuality**
> (see [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md)). Every colour and
> line-style below is interface chrome; polarity is rendered value-only, and
> hue/texture as a *logical* mark is reserved for Gamma.

---

## 1. Tokens — `src/web_viewer/css/design-system.css`

All shared visual constants live in `:root` in
[`css/design-system.css`](../src/web_viewer/css/design-system.css), loaded by
each mode **after** `css/styles.css` (the original index viewer's layout + the
partial `--sidebar-*` palette). Mode `<style>` blocks reference `var(--…)`
tokens; they no longer declare colour literals (verified: zero `#rrggbb` in any
of the three shells).

**Palette provenance.** The dark chrome is **Catppuccin Mocha** (`--ctp-*`); the
one light surface — Organon's read-only *detail header* — is **Catppuccin
Latte** (`--ltt-*`). A small custom set covers on-canvas selection
(`--select-*`), the regime-3 settle handles (`--settle`), the Ergasterion phase
banner (`--phase-*`), the corpus **kind taxonomy** badges (`--kind-*`), and the
Organon adaptive-scope **lens** accents (`--lens-*`). Names carry the origin so
drift is legible.

**Layers (use the semantic aliases in mode CSS, not raw `--ctp-*`):**

| Concern | Token |
|---|---|
| Panel / canvas-chrome bg | `--panel-bg` (`--ctp-base`) |
| Header / sub-bar bg | `--header-bg` (`--ctp-mantle`) |
| Primary / secondary / muted text | `--text` · `--text-secondary` · `--text-muted` |
| Border | `--border` (`--ctp-surface0`) |
| Accent (the through-line blue) | `--accent` (`--ctp-blue`) |
| Status success / warning / error | `--status-success` · `--status-warning` · `--status-error` |
| Agon roles (by polarity) | `--role-graphist` (blue) · `--role-grapheus` (maroon) |
| On-canvas selection | `--select-subgraph` · `--select-area` · `--select-justify` |

**Scale, radii, type, rhythm.** Spacing is an 8-step scale `--space-1…9`
(2–18px) replacing the scattered magic numbers; radii are
`--radius-sm/md/lg/pill`; type is `--font-sans` / `--font-mono`; the shared
shell rhythm is `--panel-width` (320px), `--header-pad`, `--statusbar-pad`.

---

## 2. Camera convention — `DiagramViewer.render(svg, {camera, dolly, transition})`

All three modes render through the one shared component
([`js/diagram-viewer.js`](../src/web_viewer/js/diagram-viewer.js)). The
**canonical default is `camera: 'fit'`** on first load of a new graph. The
*preservation* behaviour legitimately differs by mode intent — this is
deliberate, not drift:

| Mode | On load | On step/move/lens | Why it differs |
|---|---|---|---|
| **Organon** | `fit` | `fit` + `dolly` per chain frame; overview lens `fit` on entry / `keep` on expand | Chain frames are *independent* drawings — re-fit each; the overview keeps the camera so detail appears *in place* (the map-app feel). |
| **Ergasterion** | `fit` | `keep` + `transition` while preserving | A workshop edit should hold the view but **re-fit if content overflows** — the graph is mutating under you. |
| **Agon** | `fit` | `hold` + `transition` while preserving | A game move must **not move the board under the player** — strict absolute preservation. |

Rule of thumb: `fit` = frame a *new* object; `keep` = hold but yield to overflow
(mutable content); `hold` = never re-frame (the board is fixed under the player).

---

## 3. Vocabulary

One word per concept across all three modes (visible strings; internal
identifiers may lag and are aligned opportunistically):

| Concept | Canonical word | Not |
|---|---|---|
| A rule application (the transition) | **move** | step, transformation |
| A position within a recorded derivation | **state** | frame |
| Count label | "*N* move(s)" | — |
| Position label | "state *N* / total" ("base state · 0") | "step N", "frame N" |
| The three modes | **Organon · Ergasterion · Agon** | — |

(Agon's "Frame `~[ M ~[ G ] ]`" is a *different* sense — the framing of the
proposition — and is left as is.)

---

## 4. Nav + chrome

- **Left nav** is shared and identical across modes
  ([`js/mode-nav.js`](../src/web_viewer/js/mode-nav.js)): "Arisbe" home, the
  three-mode row with the active mode highlighted, and the one-line descriptions
  ("archive · read-only" / "workshop · composition" / "arena · contest").
- **Panel width** is `--panel-width` (320px). *Known exception:* Agon's columns
  are 340px — its setup form + disposition taxonomy are denser. Flagged here so
  it reads as a choice, not drift; revisit if it ever feels off.
- **Header / status padding** are tokenized (`--header-pad`, `--statusbar-pad`)
  and identical across modes (this pass fixed Organon's status bar, which had
  drifted to `6px 18px`).
- **Legitimate per-mode chrome** (keep): Organon's bright Latte detail header
  (read-only register), Ergasterion's phase banner (composing/deriving/sealed),
  Agon's turn banner (current role + territory).

---

## 5. The context reflex — `js/context-reflex.js`

A shared, framework-free panel (`window.ContextReflex`, the twin of
[`LinearFormPanel`](../src/web_viewer/js/linear-form-panel.js)) that floats over
the diagram host in **all three modes** and answers the field guide's first
reflex — *"what context lets you read this?"*
([FIELD_GUIDE_AND_DRAGONS.md](FIELD_GUIDE_AND_DRAGONS.md) point 4;
[LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md) — contextual
honesty made visible). It renders two sections:

- **The ground** — the universe the graph is asserted in (name + standing badge),
  the regime, and the derivation position. Each mode supplies a `ground` object
  with what it knows; missing fields are omitted, so the same component reads
  correctly as a corpus item (Organon: standing + "state N of M"), a regime-1
  draft (Ergasterion: "regime 1 · workshop", with a *correspondence-suspended*
  claim), or a contest board (Agon: move position, *nothing-asserted* claim).
- **The structure** — on element click, the enclosing-cut breadcrumb
  (`⊙ sheet › ¬ › ¬ ▸ here`) plus the element's polarity/depth in words and the
  lines through it. Computed by walking the area tree in the **introspection**
  block (`{ areas, elements }`).

**The id-matching contract (important):** the enclosure walk only works if the
clicked SVG `data-element-id` matches an introspection key. That holds **only**
when the introspection comes from the *same egi* as the rendered svg — so each
mode passes the introspection **bundled with the render**, never a fresh
`/introspect {text}` (re-parsing regenerates ids). Ergasterion and Agon already
carry an `introspection` block in their state/game payloads; Organon's detail and
chain-frame payloads now do too. Polarity is shown in **words, never hue** (floor
#6: hue/line-style stay reserved for Gamma; this is a meta-affordance, not a mark).

**Docking — auto-dim-on-overlap.** The panel floats absolute top-left, so a
left-heavy or frame-filling drawing can sit beneath it. Rather than dock it into a
per-mode column, the panel watches the drawn extent — the `.svg-pan-zoom_viewport`
group's screen rect, the same measure `DiagramViewer._contentFitsViewport` uses —
and toggles `cx-occluding` when the open panel overlaps it: the panel recedes to a
faint "Context" chip, and the body becomes **click-through** (`pointer-events:none`)
so nothing under it is unreachable. Hover or focus (`cx-peek`) restores it in full.
Because `fit`+`centre` leaves margins, the picture only reaches the top-left corner
when it is genuinely large — so a small/centred drawing leaves the panel untouched
(zero regression). The test is re-run on render, on camera changes (wheel-zoom /
pan-drag end, rAF-coalesced), and on resize. Opacity/background only — no layout
change, so the overlap test never oscillates.

API: `ContextReflex.render(host, {ground, introspection})` (re-attaches after the
host's innerHTML is swapped) · `.select(host, id)` / `.clearSelect(host)` (the
breadcrumb) · pure `.enclosureChain(intro, id)` / `.describeElement(intro, id)` ·
`.recomputeOcclusion(host)` / `._rectsOverlap(a, b)` (the docking helpers).
Open/closed state + last selection persist on the host dataset. Tests:
[`test_context_reflex_e2e.py`](../tests/test_context_reflex_e2e.py) (Organon
integration + the cross-mode module contract on all three pages + the
auto-dim/peek docking behaviour on a synthetic deterministic host).

---

## 6. Known follow-ups (documented, not silently dropped)

- **`rgba(...)` alpha variants** (phase-banner tints, hint backgrounds) are not
  yet tokenized — they're contextual one-offs; tokenize if a second use appears.
- **Lens three.js colours** are set as numeric (`0x…` / `THREE.Color`) constants
  in the WebGL lenses (`negation-well-lens.js`, `time-stack-lens.js`) and cannot
  reference CSS vars. `--lens-*` in `design-system.css` is their documented
  mirror / source of truth; keep the two in sync by hand.
- **Agon 340px panel width** — left intentional (see §4); unify to 320px only if
  the denser layout proves unnecessary.
