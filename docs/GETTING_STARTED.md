# Getting Started with Arisbe — a layered, role-aware on-ramp

> **What this is.** The written front door for a new user. It starts assuming
> **no logic or mathematics background at all**, gets you to a running system and
> your first graph, and then **branches** to what each kind of reader needs next —
> a curious newcomer, an **ontologist**, a **logician**, a **mathematician**, or a
> **Peirce scholar**. It is deliberately a *map of doors*, not a manual: each
> section is short and **links out** to the deep doc, the in-app surface, or the
> module that does the real work.
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) (what/why/scope) ·
> [GLOSSARY.md](GLOSSARY.md) (terms + a contributor reading order) ·
> [FIELD_GUIDE_AND_DRAGONS.md](FIELD_GUIDE_AND_DRAGONS.md) (the visual alphabet +
> the pitfalls) · [FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md) (the
> ideas, in plain language). This doc complements the **in-app primer** (the "New
> here?" door inside the web app) with a written, role-aware orientation.
>
> *Created 2026-06-29.*

---

## 0. What Arisbe is, in three sentences

Arisbe is an environment for **doing logic in pictures, not pictures of logic** —
Charles Sanders Peirce's "moving pictures of thought" made operational. You draw,
transform, and contest **Existential Graphs** ([EGs](GLOSSARY.md#eg)) directly; the picture *is* the
reasoning, not an illustration of reasoning done elsewhere. Peirce is the **aim**;
Frithjof Dau's formalization is the **guarantor of correctness** underneath.

If you read nothing else first, read the one-page
[FIELD_GUIDE_AND_DRAGONS.md](FIELD_GUIDE_AND_DRAGONS.md): there are only **four
marks** (a sheet, a loop, nested loops, a line), and you can draw all of logic that
matters here with a pen.

---

## 1. The shared five minutes (everyone starts here)

**You do not need any logic or mathematics to begin.** You need a terminal and a
browser.

### Run it

Dependencies are managed by **uv** (Python 3.12):

```bash
uv sync --extra dev --extra web         # one-time setup (the web extra carries FastAPI/uvicorn)
uv run uvicorn --app-dir src web_api.main:app --reload --port 8000
```

Then open <http://localhost:8000/> and click **"New here?"** — the in-app **primer**
draws a handful of first graphs with the real engine (a scroll, an empty cut) and
deep-links you into practice.

### The three modes, in one breath

Arisbe surfaces three *conceptual modes* (after their Greek names) as routes in the
web app:

| Mode | Greek | What you do there | Open |
|------|-------|-------------------|------|
| **Organon** | "instrument" | Browse the corpus, read worked proofs, step a chain — **read-only** | `/organon` |
| **Ergasterion** | "workshop" | Draw a graph freehand, have Arisbe *read it back*, practise the rules, take a **challenge** | `/ergasterion` |
| **Agon** | "contest" | Play a proposition against a world (a model **M**): get a verdict + witness, or ask "where does this hold?" | `/agon` |

### Your first graph, two ways

- **Read one.** Open `/organon`, pick `peirce_cp_4_394_man_mortal`, and watch
  "every man is mortal" drawn as a *scroll* (nested loops). Toggle its linear forms
  (Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif)) / Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif)) / Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif)) / First-Order Predicate Logic ([FOPL](GLOSSARY.md#fopl))) and watch the same proposition stay recognizable.
- **Draw one.** Open `/ergasterion`, switch to **challenge mode**, pick the dragon
  `🐉1` "every man is mortal," and draw it freehand. Arisbe grades your attempt with
  a **plain-language diff** of how it differs — and hands back the antidote when you
  trip. (The five drawable [dragons](FIELD_GUIDE_AND_DRAGONS.md) are each a
  challenge.)

### The one discipline to internalize early

Arisbe **attests correspondence, never truth.** It guarantees your *picture and
your sentence say the same thing*; it never claims either is *true of the world*.
Truth is earned elsewhere — by surviving challenge, in the Agon — and can be lost
again. Hold that and you will not misread anything below. (The deep version:
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md).)

---

## 2. Pick your door

Now branch. Each door below says: **what you already care about**, **the shortest
path in**, **what to read**, and **the honest frontier** for your kind of work.
The doors overlap on purpose — read more than one.

---

### 2a. The newcomer — "I've never done formal logic"

**Start here and stay a while.** You don't need symbols; you need the four marks and
a feel for the handful of places the picture fools people.

1. [FIELD_GUIDE_AND_DRAGONS.md](FIELD_GUIDE_AND_DRAGONS.md) — the visual alphabet,
   then the eight **dragons** ("here be dragons" — spots where a natural-seeming
   move is illegal, or the picture means the opposite of what it looks like). Every
   example is typeable into the viewer.
2. In the app: the **primer** ("New here?"), then **challenge mode** in Ergasterion.
   Draw the dragons; let the grader teach you by correcting your hand.
3. When you want the *ideas* behind it — what counts as a fact, why a name buys
   nothing — read [FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md) (no
   logic required) and the lived scenarios in
   [ARISBE_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md).

**The two reflexes worth keeping for life** (both from the Field Guide): *posited
vs. derived* (did someone **assert** this premise, or did the **rules hand it to
you**? — the picture won't tell you), and *a fragment is a building block* (a lone
graph is usually an **extract**; ask what whole it was cut from and what universe it
stands in).

**Your frontier:** none — this door has no prerequisites. The only trap is rushing
past the dragons; they catch experts too (and caught the author writing the guide).

---

### 2b. The ontologist — "I have vocabularies, OWL/RDF, a T-box"

Arisbe treats an **ontology as a theory you can draw and reason in** — every terminological box ([T-box](GLOSSARY.md#t-box))
axiom is already an EG shape (subsumption is a *scroll*, disjointness is a denial,
domain/range are typing scrolls). You bring a file in; it becomes a `kind=ontology`
Universe of Discourse you can browse in Organon and play as a **model M** in Agon.

**Shortest path in:**
1. Read [EXTERNAL_SOURCES_AND_IMPORT.md](EXTERNAL_SOURCES_AND_IMPORT.md) — the
   consolidating import doc: what enters, at what warrant, attributed how, attested
   how. This is your main door.
2. Bring a file: **Web Ontology Language ([OWL](GLOSSARY.md#owl))** (Functional-Style `.ofn`) and **Resource Description Framework ([RDF](GLOSSARY.md#rdf))** (Turtle/RDF-XML/…)
   travel **OWL → CLIF → Existential Graph Instance ([EGI](GLOSSARY.md#egi))**; **Standard Upper Ontology Knowledge Interchange Format ([SUO-KIF](GLOSSARY.md#suo-kif))** and raw **CLIF/Common Logic Ontology Repository ([COLORE](GLOSSARY.md#colore))** import directly
   (the back half is `clif_parser_dau`). See the tool/module table in that doc.
3. Ask a question of it. In `/agon`, pick your imported ontology as M and let
   `theory_query.entails` decide a **subsumption / intersection / transitivity**
   theorem — the "is G a theorem of this theory?" inning. The conceptual account is
   [DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md) §6.2.

**What you most want to know, stated honestly:**
- **Honest partial translation.** Constructs Arisbe can't express as ground EG
  (cardinality, union, `AllValuesFrom`, datatypes, modal/higher-order SUO-KIF) are
  **reported by construct, never silently dropped.** Bring across the expressible
  ground, at low warrant, and be explicit about the rest. (Same floor as everything
  else: *attest correspondence, not truth*.)
- **The upper ontology is Peircean.** SUMO's top division
  (`Independent / Relative / Mediating` under `Entity`) *is* Peirce's
  Firstness / Secondness / Thirdness — the root of a modern merged ontology is the
  triad the rest of the corpus rests on.
- **Frontier:** Manchester OWL syntax (no maintained Python parser — deferred); a
  **web import-doorway notation** for multi-axiom ontologies (would flatten the
  skip-report — not yet surfaced); and **layout performance** for very large
  theories (a 100+-axiom ontology is correct but super-linear to *draw* — large
  taxonomies live as spines + translators today). All three are in
  [EXTERNAL_SOURCES_AND_IMPORT.md](EXTERNAL_SOURCES_AND_IMPORT.md) §6.

---

### 2c. The logician — "I want a sound calculus and round-tripped notations"

Arisbe implements **Dau's formalization** of Alpha (cut, sheet, juxtaposition) and
Beta (the line of identity) faithfully, with all **six transformation rules** (ERA,
INS, IT+, IT−, DC+, DC−), Beta-aware. A graph round-trips across **four linear
notations** and stays the same proposition everywhere.

**Shortest path in:**
1. [GLOSSARY.md](GLOSSARY.md) for the Peirce/Dau/Arisbe vocabulary, then
   [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) — **the
   central contract**: picture and proposition denote the *same* object, stated,
   tested, and runtime-attested (§3.3).
2. Round-trip a form yourself: in any mode, toggle **EGIF / CGIF / CLIF / FOPL** on
   one graph. FOPL is **Dau's Φ/Ψ translation** (Chapter 18), not a naïve
   conversion. Formats and their modules: [IMPORT_EXPORT_FORMATS.md](IMPORT_EXPORT_FORMATS.md).
3. Build a proof. The headless **RuleInteraction** protocol
   (`begin → advance → apply`) and the fluent **`ProofChain`** builder
   (`proof_authoring.py`, authoring by *locator* not ephemeral id) construct and
   replay derivations; the worked corpus proofs (Peirce's Law, Barbara, Leibniz's
   *Praeclarum Theorema*) are real chains you can step in Organon.

**What you most want to know:**
- **A step and its warrant are the same act.** You cannot make a change and *then*
  check it: a rule won't apply unless its preconditions hold, so the move *is* its
  proof of soundness. ([CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md).)
- **Two games, not one.** The Endoporeutic **contest** (Dau's six-rule proof game)
  and the inner **semantic** evaluation game (peel G against a model M → a
  three-valued Kleene verdict + witness/counterexample) are kept distinct and
  bridged by deiteration. [GENERATION_AND_TESTING.md](GENERATION_AND_TESTING.md),
  [AUTOMATED_GRAPHEUS.md](AUTOMATED_GRAPHEUS.md).
- **Modality needs no new mark.** □/◇ go to ordinary Beta quantifiers over an
  accessibility relation, and the diachronic directed acyclic graph ([DAG](GLOSSARY.md#dag)) *is* that frame. *Gamma-as-modality
  is out of scope* on purpose. [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md).
- **Frontier:** the automated **Grapheus** opponent and a learned dynamic M for the
  contest register; the universal-generalization rule's Dau-native scaffold
  ([UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md](UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md)).

---

### 2d. The mathematician — "I want the formal object and the invariants"

The fundamental object is **not a diagram** but the **Universe of Discourse** — a
*diachronic* (evolving) reasoning process; a single EG is a *synchronic* snapshot.
The data model is **immutable**: state advances only by constructing a new graph,
so provenance is append-only and history is a branching **DAG**.

**Shortest path in:**
1. [../CLAUDE.md](../CLAUDE.md) — the annotated module map, the data-model
   invariants, and the mathematical-foundation chapter mapping (code chapters track
   Dau's textbook: Ch. 14/15 rules, Ch. 16–17 ligatures/soundness, Ch. 18 Φ/Ψ,
   Ch. 20 syntactic equivalence).
2. The formal structure: **EGI** = `RelationalGraphWithCuts` `(V, E, ν, ⊤, Cut,
   area, ρ)` (`egi_core_dau.py`), carrying **two co-resident structures** over one
   element population — cut-containment (a tree) and ligatures (the W-partition,
   cutting across the hierarchy). [UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md),
   [DAG_HISTORY_ARCHITECTURE.md](DAG_HISTORY_ARCHITECTURE.md).
3. The **correspondence machinery** — your likely interest. Layout is a
   *coordinate-free projection*: `natural_layout` (containment tree + per-ligature
   required **crossing-sequence** + incidence + ports) imports no geometry, so a
   future 3-D projection is additive; renderers (Eclipse Layout Kernel ([ELK](GLOSSARY.md#elk)), the experimental *tension*
   engine) are pluggable optimizers within those constraints; `attest_correspondence`
   enforces §3.3 at runtime. [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md)
   §3.1–3.3, [TENSION_LAYOUT.md](TENSION_LAYOUT.md).

**What you most want to know:**
- **The ligature-crossing invariant is topological, not metric** — a per-ligature
  crossing-sequence derived from the containment tree, checked as an actual-vs-
  required multiset (buffers fail; topology holds).
- **Three regimes scope the invariant** — composition (suspended), asserted
  (mandatory, attested), presentation-only (free, preserved by construction via
  `presentation_ops`, boundary crossings raise `Regime3Violation`).
- **The math core test suite must always pass** — a failing core test is a real
  correctness defect, not noise. The genuine calculus core is 14 protected modules.
- **Frontier:** the named research direction is **second-order logic about the
  graphs themselves** (graphs of graphs, abstraction, predication of qualities) —
  toe-in-water already exists (`schema.py`, the math-fixtures track). Not modality.
  [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md), [ROADMAP.md](ROADMAP.md) #13.

---

### 2e. The Peirce scholar — "I care about fidelity, history, and provenance"

Arisbe does not try to improve Peirce's calculus — it implements Dau's rigorous
formalization faithfully and is honest about the **three places it consciously
departs**, each examined adversarially and surviving *with amendment*. The corpus
is a **library of universes**, faithful to a community across history rather than
cured into one consistent whole.

**Shortest path in:**
1. [ARISBE_FOR_SCHOLARS.md](ARISBE_FOR_SCHOLARS.md) — the scholar's introduction
   (and the specific questions it puts to readers in the Pietarinen tradition: the
   *Agonothetes* construct, and the correspondence invariant as **mechanized
   iconicity** — the claim that the graph *is* the proposition, not a notation for
   it).
2. The departures, plain then precise:
   [FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md) → then
   [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) +
   [ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md) (the doubts written as
   charges, attacked by hired prosecutors, kept only where they survived).
3. **Transcription with provenance.** Every corpus item carries a typed provenance
   bundle: its **import kind** (exemplar / proof / pattern / domain_model /
   ontology), *transcribed-vs-authored*, and *cited-vs-synthetic* — three different
   facts that must not be collapsed. A synthetic test graph may **never** carry a
   fabricated citation (enforced). [CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md),
   [ORGANON_IMPORT_WALKTHROUGH.md](ORGANON_IMPORT_WALKTHROUGH.md).

**What you most want to know:**
- **No mark bears actuality.** A mark may carry *form* (negation, conditionality,
  even modality-as-form) but never *actuality* — no solid line for "fact," no
  dotted line for "the real world." Polarity is named **in words, never by colour**.
  [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md).
- **To assert is to take responsibility** (Peirce's 1906 Phemic Sheet) — an *act*,
  not a feature of the drawing. Arisbe marks the seam the everyday presentations
  leave flush: posited premise (low warrant) vs. derived theorem (end of a sound
  chain). [LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md).
- **For publication:** the authentic-Peirce **LaTeX/TikZ export** reimplements the
  *function* of Jukka Nikulainen's `egpeirce.sty` (oval cuts, scrolls, heavy lines
  of identity, hooks) in pure pdflatex — wedded to the §3.3-attested graph and
  delta-faithful (export what you *adjusted* to see). The `peirce-tikz` format and a
  worked-chain → multi-figure document. [FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md](FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md).
- **Frontier:** the by-hand **reading desk** (interactive transcription of a graph +
  provenance through the UI) is wanted but not yet a single surface; the building
  blocks exist. [CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md) §6.

---

## 3. If you are about to change code

This doc is for *using* and *orienting*. If you are about to **contribute**, the
reading order is different — start with [../CLAUDE.md](../CLAUDE.md) (module map,
commands, invariants, test inventory) and the contributor track in
[GLOSSARY.md](GLOSSARY.md), and read
[LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) before
touching anything that produces or consumes an `(EGI, drawing)` pair. The
capability/test home of everything is [CAPABILITY_MAP.md](CAPABILITY_MAP.md).

---

## 4. One-screen map of the doors

| You are… | Read first | Do first | Your frontier |
|----------|-----------|----------|---------------|
| **Newcomer** | [Field Guide](FIELD_GUIDE_AND_DRAGONS.md) | In-app primer → challenge mode | (none — just don't skip the dragons) |
| **Ontologist** | [External sources & import](EXTERNAL_SOURCES_AND_IMPORT.md) | Import a file → ask a theorem in Agon | Manchester OWL; web import notation; layout at scale |
| **Logician** | [The central contract](LINEAR_GRAPHICAL_CORRESPONDENCE.md) | Round-trip a form → build a chain | automated Grapheus; ∀-generalization scaffold |
| **Mathematician** | [CLAUDE.md](../CLAUDE.md) module map | Read `egi_core_dau` + the correspondence layer | second-order logic about the graphs |
| **Peirce scholar** | [For Scholars](ARISBE_FOR_SCHOLARS.md) | Step a worked proof in Organon → read the departures | the by-hand reading desk |

The blank sheet is the only unconditioned thing, and it asserts nothing. Everything
above it you build by legal nesting — and everything is surrenderable. Welcome.
