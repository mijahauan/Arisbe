# Sprotty / GLSP Evaluation for Arisbe

**Status:** research + analysis, June 2026.
**Question:** Is the Eclipse **Sprotty** diagramming framework (and its editing
successor **GLSP**) a good fit as the interactive editing/rendering shell for
Arisbe's web surface — given a Python backend, an existing ELK layout worker,
the `LayoutDTO` / `natural_layout` projection design, and the §3.3 / regime-3
correspondence invariant that is the crown jewel?

**Bottom line up front:** *Borrow concepts, do not adopt.* GLSP's
server-authoritative operation/handler architecture is a remarkably close
conceptual match to Arisbe's "the EGI lives in Python and the server decides
the truth of a drawing" stance — close enough to validate the design and to
steal vocabulary from. But neither Sprotty nor GLSP ships a Python server, and
both impose their own model (SModel / GModel) and their own ELK binding,
duplicating the `natural_layout` → ELK → `LayoutDTO` pipeline Arisbe already
owns and §3.3-attests. The integration cost is high and the strategic payoff is
low precisely *because* the hard part (the invariant) is the part no generic
framework knows about. A phased "borrow the protocol shape, keep the engine"
path is recommended instead. Details and the dissenting considerations below.

---

## 1. What Sprotty is

[Sprotty](https://sprotty.org/) is an open-source (Eclipse Public License 2.0)
web diagramming framework. The client is TypeScript, renders to **SVG**, styles
with CSS. Its architecture is explicitly *not* MVC; it is a Flux-style
**unidirectional, cyclic event flow**
([Architectural Overview](https://github.com/eclipse-sprotty/sprotty/wiki/Architectural-Overview)).

The moving parts:

- **SModel** — the diagram model. Every element is an `SModelElement` with a
  unique string `id` and a `type` used to look up its **View**. Elements form a
  tree via `parent`/`children`; the root is an `SModelRoot` holding an index for
  fast id lookup. The SModel is a *view model*, deliberately distinct from any
  domain ("source") model.
- **Views** — pure functions `SModelElement → VNode` (virtual DOM → SVG),
  re-rendered reactively.
- **Actions** — plain JSON objects describing operations on the model. They are
  the wire protocol; they serialize across a WebSocket. Examples: `SetModel`,
  `UpdateModel`, `SelectAction`, `RequestBounds` / `ComputedBounds`.
- **ActionDispatcher → ActionHandlers → CommandStack** — actions are turned into
  Commands (which can animate) and executed against the model.
- **ModelSource** — the seam to "where the model comes from." Two
  implementations: `LocalModelSource` (model lives in the browser, app code
  manipulates it directly) and `DiagramServer` (delegates to a remote source,
  typically over WebSocket).

Sprotty's original server glue (`sprotty-server`) was Xtext/LSP-oriented: it
enhanced the Language Server Protocol to carry Sprotty actions so a text
artifact and its diagram stay synchronized
([sprotty-server](https://github.com/eclipse/sprotty-server)). Sprotty by itself
is fundamentally a **renderer + view-model + reactive update cycle**. It has no
opinion about *editing operations* or domain-model validity — that is what GLSP
adds.

### Relationship to GLSP

[Eclipse GLSP](https://eclipse.dev/glsp/) (Graphical Language Server Platform,
EPL-2.0) is the editing-focused successor pattern. The **GLSP client is built on
top of Sprotty** (it reuses Sprotty's rendering/update cycle) and adds a
full client/server **editing** protocol modeled on LSP-for-diagrams. The key
design decision, quoting the project: GLSP "encapsulate[s] knowledge about the
graphical language on the **server** — including available node and edge types,
available operations, and validation — while the client-side editor is only
responsible for **rendering** the diagram and **providing editing tools**"
([Overview](https://eclipse.dev/glsp/documentation/overview/)).

The GLSP edit cycle
([Model Operations](https://eclipse.dev/glsp/documentation/modeloperations/)):

1. The user performs a gesture in the client (drag, create, delete).
2. The client sends an **Operation** (e.g. `ChangeBoundsOperation`,
   `CreateNodeOperation`, `ReconnectEdgeOperation`) to the server.
3. A single server-side `OperationActionHandler` dispatches to the registered
   `OperationHandler` for that operation type, which mutates the **source
   model**.
4. The server **regenerates the graphical model (GModel)** from the source model
   and sends an `UpdateModelAction` back.
5. The client re-renders from the authoritative model.

GModel is GLSP's analogue of SModel
([Graphical Model](https://eclipse.dev/glsp/documentation/gmodel/)). Each client
session gets a dedicated DI container holding session-specific handler instances;
a global container holds shared components. **This is the architecture that
matters to Arisbe** — see §4.

---

## 2. ELK integration

ELK is integrated through **`sprotty-elk`**
([introduction](https://sprotty.org/docs/sprotty-elk/introduction/)), a separate
module. The flow is five steps: transform SModel → ELK graph; optional
preprocess; `elk.layout()`; optional postprocess; copy positions/sizes back onto
the SModel.

Concrete facts relevant to EGs:

- **Nested / hierarchical layout is supported.** "Every transformation of an
  SModel element is accompanied by the transformation of its children," and ELK
  itself is a compound-graph layouter — exactly why Arisbe already chose ELK for
  nested cuts.
- **Ports are first-class.** SModel ports become `ElkPort`s; edges become
  `ElkEdge`s; labels become `ElkLabel`s. The basic-type mapping (`nodes →
  ElkNode`, `ports → ElkPort`, etc.) is documented.
- **Configuration** is via `ILayoutConfigurator` (default:
  `DefaultLayoutConfigurator`), overriding `graphOptions()`, `nodeOptions()`,
  `edgeOptions()`, `labelOptions()`, `portOptions()` to set the same ELK layout
  options Arisbe sets in `elk_layout_engine.py`.
- **Execution location is flexible.** `sprotty-elk` "can be used both on the
  frontend (with `LocalModelSource`) and on the backend (with `DiagramServer`)";
  client-side it runs inside Sprotty's DI container and *optionally* in a web
  worker. (Arisbe today runs ELK in a Node *subprocess* worker driven from
  Python — `src/elk_worker.js` → `src/elk_layout_engine.py`.)

**Maintenance caveat (verify before relying on it):** the original
`eclipse/sprotty-layout` repo that housed `sprotty-elk` is **archived**
(`eclipse-archived/sprotty-layout`), and the `sprotty.org` docs do not publish a
clear current version/maintenance statement. The package still exists on
[npm](https://www.npmjs.com/package/sprotty-elk) and GLSP continues to use ELK
layout, but the "use elkjs from Sprotty" story is less actively maintained than
Sprotty/GLSP core. Treat `sprotty-elk` as usable-but-stale rather than a
first-class supported surface.

---

## 3. The decisive point: Arisbe already owns this layer

Before the fit table, state plainly what Arisbe has, because it is most of what
Sprotty/GLSP would otherwise provide:

| Arisbe component | Sprotty/GLSP analogue |
|---|---|
| `RelationalGraphWithCuts` (immutable EGI, Python) | the *source model* (GLSP) — but GLSP keeps it server-side in Java/TS |
| `natural_layout.py` (coordinate-free containment tree, required crossing-sequence, ports) | *nothing equivalent* — Sprotty's SModel is geometric/view-level |
| `elk_layout_engine.py` + `elk_worker.js` | `sprotty-elk` |
| `layout_dto.py` (`LayoutDTO`: vertex/predicate positions, nested `cut_bounds`, `ligature_paths` w/ `port_index`, `viewport_bounds`) | the laid-out SModel / GModel |
| `simple_svg_renderer.py` | Sprotty Views (SVG) |
| `presentation_ops.py` (regime-3 algebra, refuses boundary crossings) | GLSP `OperationHandler`s + validation — *but GLSP has no notion of these rules* |
| `correspondence_attestation.py` (§3.3 runtime check) | GLSP live validation markers — *again, the rules are Arisbe-specific* |
| `POST /ergasterion/sessions/{id}/adjust` (`settle-adjust.js`) | GLSP `ChangeBoundsOperation` round trip |

The `natural_layout` row is the one with no analogue, and it is the row that
encodes the crown jewel. Sprotty's SModel is a *view* model; GLSP's GModel is a
*graphical* model regenerated from a source model. Neither has a place for
"projection-independent structure that any faithful drawing must realize." That
concept is Arisbe's own contribution and would sit *above* whatever framework is
chosen regardless.

---

## 4. Fit against the five requirements

### Req 1 — Nested containers, ports, perimeter/floating edge anchors

- **Nested containers:** **Strong.** SModel/GModel are trees; `parent`/`children`
  map directly onto cut containment, and `sprotty-elk` lays out compound nodes.
  A cut → `SCompartment`/`SNode` with children; a vertex/predicate → child node
  in the right cut. This is the requirement Sprotty handles best.
- **Ports:** **Strong.** First-class `SPort` / `ElkPort`. A predicate's argument
  positions (`port_index` in `LigaturePath`/`NaturalLigature`) map to ports.
- **Perimeter / floating anchor (the point on a predicate box facing the
  connected vertex):** **Adequate but not free.** Sprotty has *anchor computers*
  (`IAnchorComputer`, e.g. ellipse/rectangle anchors) that compute where an edge
  meets a shape's boundary — the right hook for "floating anchor facing the
  vertex." ELK's own edge routing also produces boundary attach points. So the
  capability exists, but EG ligatures are not ordinary directed edges: they are
  *lines of identity* with a **required crossing-sequence** through cuts.
  Sprotty/ELK route edges to minimize crossings; Arisbe needs routes that cross
  an *exact prescribed* set of cut boundaries (the `required_crossings` tuple).
  Expressing "cross these cuts, in this order, and no others" is **not** a
  built-in ELK/Sprotty concept — it is the topological invariant Arisbe added on
  top. You would be fighting the router's defaults, the same way the project
  memo notes buffers fight metric-vs-topological.

### Req 2 — Constraint-respecting interactive editing with external authority

This is the heart of the question, and it splits cleanly by framework:

- **Sprotty alone:** weak. With `LocalModelSource` the client mutates the model
  directly; there is no built-in "ask an authority, then accept/reject." You
  would hand-roll the validation round trip — i.e. rebuild what GLSP already is.
- **GLSP:** **conceptually excellent, mechanically constrained.** GLSP's whole
  premise is that **operations are validated and applied server-side**, and the
  client only renders the result. That is *exactly* the Arisbe stance: the EGI
  is the authority, the server decides the truth of a drawing. Two GLSP
  mechanisms map onto Arisbe's needs:
  - **Type hints** (`ShapeTypeHints`, `EdgeTypeHints`) let the server declare,
    at the type level, what is resizable/relocatable/reparentable and which
    source/target types an edge allows — pushed to the client so it can give
    *synchronous* feedback **without a round trip**
    ([Protocol](https://eclipse.dev/glsp/documentation/protocol/)). This is the
    "preview legality" affordance the requirement asks for, for the *static*
    rules.
  - **Live validation** (GLSP 2.x) runs validation on each model update and
    surfaces markers during editing
    ([GLSP 2 blog](https://eclipsesource.com/blogs/2024/01/31/eclipse-glsp-2-elevating-web-based-diagram-editors/),
    [issue #980](https://github.com/eclipse-glsp/glsp/issues/980)). This is where
    a §3.3 / regime-3 check would live.

  **The honest gap — "reject and snap back":** GLSP's normal model is *not*
  optimistic-with-rollback. A move is sent as a `ChangeBoundsOperation`; the
  server applies it (or doesn't) and returns the authoritative `UpdateModelAction`
  the client re-renders. The GLSP protocol docs do **not** describe a true
  optimistic-edit/server-veto/snap-back primitive
  ([Protocol](https://eclipse.dev/glsp/documentation/protocol/)). To get
  "drag freely, server refuses a boundary-crossing nudge, drawing snaps back,"
  you implement an `OperationHandler` that, on a `Regime3Violation`, **re-emits
  the unchanged model** (an `UpdateModelAction` identical to the prior state) —
  which the client renders as a snap-back. That is achievable and idiomatic, but
  it is *you* implementing the veto, not a feature you receive. Notably, Arisbe's
  current `POST /.../adjust` already does precisely this: it runs the regime-3 op,
  refuses on `Regime3Violation`, the server never mutated, and `settle-adjust.js`
  snaps the ghost back. **Arisbe has already built the exact pattern GLSP would
  ask you to build, minus GLSP's wire format.**

### Req 3 — ELK automatic layout

**Strong on paper, redundant in practice.** `sprotty-elk` gives nested + ports
ELK layout. But Arisbe already drives ELK with cut-aware pre/post-processing
(`_refit_oval_cuts`, empty-cut minimum sizing, authorized-crossing routing) that
encode EG-specific aesthetics and the topological invariant. Switching to
`sprotty-elk` means re-expressing all of that as an `ILayoutConfigurator` plus
pre/post hooks in TypeScript, *and* it relocates layout from a controlled Python
boundary (where §3.3 is attested in `layout_service.py`) into the client/Sprotty
DI container. You would either keep Python ELK and bypass `sprotty-elk` (then
Sprotty's main layout integration is unused), or move to `sprotty-elk` and
re-port the cut logic. Neither reuses the existing investment cleanly.

### Req 4 — Server-authoritative model

**Conceptually the best part; blocked by language.** GLSP's server-side
source-model + `OperationHandler` + regenerate-GModel pattern is the textbook
realization of "the model lives server-side and the server decides validity."
The architectural fit is genuinely high.

**But:** GLSP provides server *frameworks* only for **Java** and **Node/TS**
([Servers & Integrations](https://eclipse.dev/glsp/documentation/integrations/),
[glsp-server-node](https://github.com/eclipse-glsp/glsp-server-node)). There is
**no Python GLSP server framework.** The protocol is open (JSON-RPC) and the
project explicitly says a server "can be implemented in any language" — so a
Python GLSP server is *possible*, but you would be implementing the GLSP
protocol (RequestModel/SetModel/UpdateModel, the operation set, type-hint
negotiation, marker/validation actions, the action-message envelope, session DI
lifecycle) by hand in FastAPI. That is a substantial, ongoing protocol-tracking
burden against a moving 2.x spec, for a single-purpose tool. The realistic
alternatives are (a) stand up a Node GLSP server that calls into Python for the
EGI/§3.3 logic (a second backend + an RPC bridge), or (b) reimplement the
relevant slice of the protocol in Python. Both add a process boundary Arisbe does
not currently have.

### Req 5 — Coexist with / replace the vanilla-JS viewer; TS + build cost

- Today's viewer is vanilla JS + `svg-pan-zoom`, no framework, no build step
  (`src/web_viewer/js/*.js` are plain scripts; `simple_svg_renderer.py` renders
  server-side SVG).
- Sprotty/GLSP require **TypeScript + a bundler** (the ecosystem assumes
  webpack/vite, npm/yarn, often `inversify` DI). This is a real adoption cost:
  a new toolchain, a build pipeline in CI, and rewriting `diagram-viewer.js`,
  `selection-manager.js`, `settle-adjust.js`, `transformation-ui.js` as Sprotty
  Views/handlers. The current server-rendered-SVG model is abandoned in favor of
  client-side rendering from an SModel — meaning `simple_svg_renderer.py` (and
  its role as a §3.3 boundary) changes character: the client renders, so the
  attestation must guard the *model handed to the client*, not the SVG.
- Coexistence is awkward: Sprotty wants to own its mount point and update cycle.
  A gradual "one panel at a time" migration is possible but the two rendering
  philosophies (server SVG string vs. client view-model) don't share much.

---

## 5. Migration cost & risk for Arisbe specifically

**What could be reused:** the ELK *option set* and the conceptual graph→ELK
mapping (already proven in `elk_layout_engine.py`); the idea of operations as
serializable JSON (already true of `presentation_ops` requests); the
server-veto-then-resend pattern (already implemented in `/adjust`).

**What would be imposed / duplicated:**

- A second model representation (SModel/GModel) layered over the EGI +
  `LayoutDTO`, with conversions both directions — new surface for the very
  correspondence bugs §3.3 exists to catch.
- Either a re-port of cut-aware ELK logic into TS (`sprotty-elk`) or a permanent
  bypass of Sprotty's flagship layout integration.
- For GLSP: a non-Python server, i.e. a new Node process bridging to Python, or
  a hand-rolled Python implementation of an evolving protocol.
- A TS/bundler toolchain and a rewrite of the four+ viewer JS modules.

**Risk concentrated on the crown jewel:** the invariant is *not* something the
framework provides; it must be re-anchored at the new model boundary regardless.
Every new model-conversion seam (EGI↔GModel, GModel↔ELK, ELK↔SModel) is a place
where the linear↔graphical correspondence can silently drift, which is the exact
failure mode the project is built to prevent. Adopting a framework here **adds
seams to defend** rather than removing them.

**Net:** medium-to-high cost, concentrated risk, and the highest-value
component (the invariant + `natural_layout`) stays Arisbe's own work either way.

---

## 6. Alternatives (briefly), same requirements

| Library | License | Nested containers | Ports | Edge boundary anchors | Server-authoritative fit | Notes |
|---|---|---|---|---|---|---|
| **Sprotty** | EPL-2.0 (OSS) | Strong | Strong | Adequate (anchor computers) | Via GLSP only | SVG; reactive; no editing/validation by itself |
| **GLSP** | EPL-2.0 (OSS) | Strong | Strong | Adequate | **Best architectural fit** | No Python server; Java/Node only ([integrations](https://eclipse.dev/glsp/documentation/integrations/)) |
| **JointJS (core)** | MPL-2.0 (OSS); JointJS+ commercial | Via embedding/groups | Yes (free tier) | Yes (link anchors/connection points) | DIY round trip | SVG; mature; easiest "drop into existing JS" path ([libraries 2026](https://www.jointjs.com/blog/javascript-diagramming-libraries)) |
| **mxGraph / maxGraph** | Apache-2.0; **mxGraph EOL 2020**, maxGraph 0.x | Grouping/folding | Yes | Yes | DIY | maxGraph maintained but pre-1.0 / unstable API ([mxGraph→JointJS](https://www.jointjs.com/blog/mxgraph-to-jointjs-conversion)) |
| **yFiles** | Commercial (no free tier) | Strong (best-in-class layout) | Yes | Yes | DIY | Powerful, expensive; closed source |
| **GoJS** | Commercial (no free tier) | Yes (groups) | Yes | Yes | DIY | Canvas-based (accessibility/SVG tradeoffs); restrictive license ([JointJS vs GoJS](https://www.jointjs.com/blog/jointjs-vs-gojs)) |

Observations:

- **None** of these understand cuts, regime-3, or §3.3 — every option leaves the
  invariant as Arisbe's responsibility. The differentiator is therefore *how
  little the framework imposes* and *how well it accepts an external authority*.
- For a pure rendering/interaction upgrade with the **lowest imposition and no
  license cost**, **JointJS core (MPL-2.0)** is the pragmatic front-runner: SVG
  like the current viewer, real ports/anchors/grouping, and it does not demand a
  server framework — Arisbe keeps Python authoritative and JointJS just renders
  and emits gestures, mirroring today's `/adjust` flow.
- Commercial options (yFiles, GoJS) buy superior automatic layout — but Arisbe
  already has ELK *and* the layout work is constrained by the invariant, not by
  raw layout quality. Paying for layout solves a problem Arisbe doesn't have.

---

## 7. Recommendation

**Borrow concepts; do not adopt Sprotty, and do not adopt GLSP as infrastructure
— yet.**

Reasoning, tied to the two things that actually constrain the decision (the
crown-jewel invariant, and the existing ELK / `natural_layout` investment):

1. **The invariant is unframeworkable.** No diagram shell knows cuts, regime-3,
   or §3.3; that layer is and will remain Arisbe's. Adopting a framework does
   not retire it — it relocates it to a new, less-controlled model boundary and
   *adds* conversion seams where correspondence can drift. The framework would
   take over the easy 80% (render nested boxes, drag, ports) while the hard 20%
   (legality) stays yours and gets harder to defend.

2. **Arisbe already implements GLSP's best idea.** The server-authoritative
   operation→validate→(apply | refuse + resend unchanged)→re-render loop that
   makes GLSP attractive is **already running** in `presentation_ops` +
   `correspondence_attestation` + `POST /ergasterion/sessions/{id}/adjust` +
   `settle-adjust.js`. GLSP would mostly ask Arisbe to re-express this in a
   foreign wire format and a non-Python server. The conceptual win is real; the
   infrastructural swap is not.

3. **The ELK investment is already correct and Python-side.** ELK is the right
   engine (the project independently reached the same conclusion Sprotty/GLSP
   did). `sprotty-elk` would either be bypassed or force re-porting the cut-aware
   pre/post-processing into TS. Keep ELK where §3.3 can guard it
   (`layout_service.py`).

**What to actually do — a phased path:**

- **Phase 0 — Steal the vocabulary (now, zero infra change).** Adopt GLSP's
  protocol *shape* for the edit surface: model regime-3 gestures explicitly as
  named **Operations** (`MoveVertexOperation`, `ReshapeCutOperation`,
  `ReconnectLigatureOperation`), and adopt GLSP's **type-hint** idea — have the
  server publish, per element, what is movable/reshapeable/reparentable so the
  client can give *synchronous* preview feedback (grey out illegal targets)
  before posting. This directly addresses the existing friction of using Arisbe ourselves
  ("rule requirements not discoverable; §3.3 invisible until it fails") with no
  framework dependency. It also keeps the door open to GLSP later, because the
  edit API will already be operation-shaped.

- **Phase 1 — If the bespoke viewer's *rendering/interaction* becomes the
  bottleneck**, evaluate **JointJS core (MPL-2.0)** as a drop-in renderer behind
  the *same* server-authoritative flow: JointJS draws nested cuts/ports/anchors
  and emits gestures; Python stays the authority and answers with an
  attested layout, exactly as `/adjust` does today. This is the lowest-cost,
  lowest-risk way to get framework-grade interaction without surrendering the
  invariant or the ELK pipeline. (Sprotty client is a fallback option here if a
  reactive SVG view-model is wanted, but it pulls in TS/DI/bundler for less
  marginal benefit than its GLSP server story — which is the part Arisbe can't
  use.)

- **Phase 2 — Reconsider full GLSP adoption only if** Arisbe needs to integrate
  into the broader Eclipse/Theia/VS Code modeling ecosystem (e.g. shipping the EG
  editor as a Theia/VS Code extension alongside other GLSP tools). *That* is the
  scenario where GLSP's protocol and tooling pay for themselves. Absent that
  ecosystem goal, the cost/benefit does not justify a Node GLSP server bridging
  to Python, or hand-implementing the protocol.

In short: **stay bespoke on infrastructure, converge on GLSP's *interaction
contract*.** Arisbe has, somewhat by accident, already arrived at GLSP's central
architecture in Python; the right move is to sharpen that contract (named
operations + type hints + legality preview), keep ELK and `natural_layout` and
§3.3 exactly where they are, and reach for a *rendering* library (JointJS first,
Sprotty second) only when the hand-rolled SVG viewer's ergonomics — not its
correctness — become the limiting factor.

---

## 8. Uncertainty / things to verify before any commitment

- **`sprotty-elk` maintenance status** — the housing repo is archived; confirm
  the current supported way to use ELK with Sprotty/GLSP and which versions are
  live before betting on it.
- **Exact GLSP snap-back ergonomics** — confirm by prototype that re-emitting an
  unchanged `UpdateModelAction` on a rejected `ChangeBoundsOperation` yields a
  clean visual snap-back without fl/animation glitches; the protocol docs don't
  spell this out as a first-class affordance.
- **GLSP type-hint expressiveness for "exact required crossing-sequence."** Type
  hints cover containment/reconnect at the *type* level; the per-instance
  topological crossing constraint almost certainly exceeds them and remains a
  custom validation/marker concern. Confirm before assuming hints give free
  ligature-legality preview.
- **License confirmation** for any commercial option (yFiles, GoJS) and the
  precise JointJS core vs. JointJS+ feature split, if Phase 1 is pursued.

### Sources

- Sprotty: <https://sprotty.org/> · architecture <https://github.com/eclipse-sprotty/sprotty/wiki/Architectural-Overview> · server glue <https://github.com/eclipse/sprotty-server>
- sprotty-elk: <https://sprotty.org/docs/sprotty-elk/introduction/> · npm <https://www.npmjs.com/package/sprotty-elk> · archived repo <https://github.com/eclipse-archived/sprotty-layout>
- GLSP: <https://eclipse.dev/glsp/> · overview <https://eclipse.dev/glsp/documentation/overview/> · protocol <https://eclipse.dev/glsp/documentation/protocol/> · model operations <https://eclipse.dev/glsp/documentation/modeloperations/> · graphical model <https://eclipse.dev/glsp/documentation/gmodel/> · servers & integrations <https://eclipse.dev/glsp/documentation/integrations/> · node server <https://github.com/eclipse-glsp/glsp-server-node>
- GLSP 2 / live validation: <https://eclipsesource.com/blogs/2024/01/31/eclipse-glsp-2-elevating-web-based-diagram-editors/> · <https://github.com/eclipse-glsp/glsp/issues/980>
- Alternatives & licensing: JointJS comparison <https://www.jointjs.com/blog/javascript-diagramming-libraries> · JointJS vs GoJS <https://www.jointjs.com/blog/jointjs-vs-gojs> · mxGraph→JointJS (EOL note) <https://www.jointjs.com/blog/mxgraph-to-jointjs-conversion>
