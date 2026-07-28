# Arisbe Triad Architecture

> **Updated 2026-06-08.** This doc's *conceptual* triad (Organon / Ergasterion
> / Agon as Peirce's sign-triad) still holds, and it carries weight. Its
> implementation pointers date from the Qt GUI. That GUI went to
> `archive/qt-gui-2025/` in May 2026, and all three modes now live as **web
> routes** (`src/web_api/routes/{organon,ergasterion,agon}.py` +
> `src/web_viewer/{organon,ergasterion,agon}.html`). The location and status
> lines below follow that move.

## Overview

Arisbe runs a complete cycle of inquiry through three connected modes, modelling Peirce's vision of logic as a living, diagrammatic practice. The three modes answer to the three phases of reasoning: *knowing* (Organon), *making* (Ergasterion), and *contesting* (Agon).

The graphical interface does more than render logical structures. Following Peirce's conception of "moving pictures of thought," it facilitates aesthetic, expressive, and interpretive engagement with diagrams.

### Semiotic Architecture

The triad did not arrive by accident. It reflects Peirce's irreducibly triadic conception of the sign:

| Sign element | Arisbe mode | Function |
|---|---|---|
| **Object** | **Organon** | The domain — what is known, the world that signs refer to |
| **Representamen** | **Ergasterion** | The sign-making workshop — where new representations are crafted |
| **Interpretant** | **Agon** | The understanding produced — what the sign means when tested against the domain |

No pair suffices. The Organon without the Ergasterion stands as a library no one writes for. The Ergasterion without the Agon produces signs that nothing ever tests. The Agon without the Organon has nothing to test against. The three together form the minimal structure for the growth of understanding.

This triadic structure recurs *within* the Agon itself, where the Graphist (representamen — produces the proposed sign), the Grapheus (object — the domain model that tests the sign), and the [Agonothetes](GLOSSARY.md#agonothetes) (interpretant — the understanding the contest produces) form a sign-triad at the level of the individual game. See `docs/ENDOPOREUTIC_GAME_GUIDE.md` for the full account.

---

## The Three Modes

### Organon — Corpus and Exploration

**Purpose**: Knowledge corpus management, graph browsing, linear form import, read-only visualization.

**Location**: `src/web_api/routes/organon.py` + `src/web_viewer/organon.html`

**Core functions**:

- Browse the [tomos](GLOSSARY.md#tomos) (corpus) of Existential Graph Instance ([EGI](GLOSSARY.md#egi)) graphs by category and metadata
- Import EGIs from linear forms (Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif)), Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif)), Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif)), First-Order Predicate Logic ([FOPL](GLOSSARY.md#fopl)))
- View diagrams in multiple styles (Dau, Peirce, Sowa)
- Inspect transformation history (diachronic view of a reasoning session)
- Export to SVG, PNG, LaTeX/TikZ

**Data flow**:
```
Linear form (EGIF/CGIF/CLIF) → parser → EGI → TomosService storage
EGI corpus → OrganonMode → DiagramController → layout → display
```

**API surface**:
```python
from tomos_service import TomosService
corpus = TomosService(Path("corpus"))
uods = corpus.list_uods(is_static=True)
uod = corpus.load_uod(uod_id, load_history=True)
```

**Current status**: Live. Read-only corpus browsing, UoD detail, and chain/timeline navigation; §3.3 attests both the load boundary and the render boundary.

---

### Ergasterion — Workshop and Practice

**Purpose**: Interactive graph construction, transformation practice, derivation sequences.

**Location**: `src/web_api/routes/ergasterion.py` + `src/web_viewer/ergasterion.html`

**Core functions**:

- Build EGI graphs from scratch using DC+ as the primary composition rule
- Apply any of the six transformation rules to a working graph
- Practice derivations with step-by-step undo/redo
- Work within a composition context (a negatively-enclosed area on the sheet)
- Save completed graphs to the Organon corpus

**Composition principle**: Every graph utterance begins from an empty sheet (or a double-cut context) and grows through rule-governed transformations. The sheet of assertion serves as the axiomatic ground; DC+ provides the first negation context; INS places content; IT+ and ERA develop and simplify.

**Data flow**:
```
Empty sheet → DC+ → composition context → INS sequence → EGI
EGI → transformation rules → new EGI → history tracking → corpus save
```

**API surface**:
```python
from diagram_controller import DiagramController
from formal_transformation_rules import TransformationContext, AreaPolarity

controller = DiagramController()
controller.load_egi(egi)
# Apply rule
context = TransformationContext(
    source_egi=egi,
    target_area=area_id,
    selected_subgraph=frozenset(element_ids),
    area_polarity=AreaPolarity.NEGATIVE,
    nesting_depth=1,
)
result = InsertionRule().apply_transformation(context)
```

**Current status**: Live. A session-based workshop over the headless `RuleInteraction` protocol, carrying all six rules via the four-beat grammar, regime-1 drafts, branch-on-edit, move-by-move navigation, and a scratch store. Output goes to scratch, or on to Agon, never straight to the corpus.

---

### Agon — Formal Game and Reasoning

**Purpose**: Formal dialogical reasoning via the [Endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in) Game, proof construction, semantic validation.

**Location**: `src/web_api/routes/agon.py` + `src/web_viewer/agon.html` (arena), `src/endoporeutic_game.py` (engine)

**Core functions**:

- Load a domain model (Universe of Discourse ([UoD](GLOSSARY.md#uod))) as an EGIF
- Propose an assertion (another EGIF) for testing against the domain
- Play the Endoporeutic Game: Proposer (Graphist) and Skeptic (Grapheus) alternate moves
- Validate proofs: a sequence of rule applications from premises to conclusion
- Classify outcomes: tautology, contradiction, or contingent (hypothesis)
- **Interpretation register**: choose a reference model M, [peel](GLOSSARY.md#peel) an
  assertion against it to a three-valued verdict with witness/counterexample,
  materialize M (Horn rules → least Herbrand model), and run the inverse pivot
  ("in what domain does G hold?") — see `docs/DOMAIN_ORACLE_AND_M.md`

**Game structure** (a sign-triad within the Agon):

- **Graphist** (Representamen) — proposes a sign, defends it by operating in negative areas
- **Grapheus** (Object) — the domain model; challenges the sign by operating in positive areas
- **Agonothetes** (Interpretant) — the meaning-making function, which validates moves, tracks
  the traversal, and interprets the outcome into understanding that flows back into the UoD
- The user straddles both player roles. The Agonothetes joins as no third player; it serves as
  the telic function of the game. See `docs/ENDOPOREUTIC_GAME_GUIDE.md` §Agonothetes

**Domain model as EGIF**: An EGIF graph carries all domain knowledge, not external data and not a separate knowledge base. The domain model remains an EGI itself, so the same tools browse it, transform it, and reason about it.

**Data flow**:
```
Domain EGIF → parse → EGI (universe of discourse)
Assertion EGIF → parse → EGI (hypothesis)
GameEngine.play() → alternating moves → GameOutcome
```

**Current status**: Live, well past the original thin V1 arena (shipped 2026-06-01). The game engine (`src/endoporeutic_game.py`) sits wired in. Play runs hot-seat, one user driving both roles; nothing auto-asserts; the outcome takes the form of an open disposition taxonomy. The semantic layer, an automated Grapheus opponent (`src/grapheus.py`), and dynamic-M development (`src/agon_evolution.py`/`src/model_revision.py`) have since shipped. The frontier now lies with the 3-LLM-role automated Endoporeutic Game (`src/agon_llm.py`) and the meta-learning layer that studies the game's own resolution principles (`src/agon_metalearning.py`). See [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md) and `docs/AUTOMATED_ENDOPOREUTIC_GAME.md`.

---

## Shared Infrastructure

### EGI Core (`egi_core_dau.py`)

The single source of truth for all logical content. All three modes read from and write to immutable EGI structures. The mode boundaries follow from which operations each mode permits, not from separate data models.

### DiagramController (`diagram_controller.py`)

Central coordinator shared across all three modes. Manages:

- Current EGI and layout DTO
- Transformation history (diachronic workflow)
- User-defined layout deltas (aesthetic overrides)
- Rule application and validation

### TomosService (`tomos_service.py`)

Corpus management shared across Organon and Agon. Provides fast index-based browsing, UoD loading with history, and persistence.

### Style System (`style_loader.py`, `style_specification.py`)

Three styles selectable across all modes:

- **Dau**: Mathematical — vertex dots, precise labeling
- **Peirce**: Authentic — lines of identity, minimal decoration
- **Sowa**: Conceptual graph — CG-style boxes and ovals

---

## Integration Workflows

### Workflow 1: Import and Browse

```
1. Organon: paste EGIF text or open file
2. parser → EGI → TomosService.save_uod()
3. Organon: corpus browser reflects new entry
4. User selects → DiagramController.load_egi() → display
```

### Workflow 2: Practice a Derivation

```
1. Organon: select starting graph → "Edit in Ergasterion"
2. Ergasterion: DiagramController loads EGI
3. User selects elements → picks rule → TransformationContext built
4. Rule.apply_transformation() → new EGI
5. DiagramController records history step
6. Repeat until goal reached
7. "Save to Corpus" → TomosService persists full UoD with history
```

### Workflow 3: Play the Endoporeutic Game

```
1. Agon: load domain model (EGIF)
2. Agon: enter assertion (EGIF)
3. GameEngine.start_game(domain, assertion)
4. REPL/GUI loop:
   - Proposer: apply rule in negative context
   - Skeptic: challenge or apply rule in positive context
   - Agonothetes: validate each move
5. GameEngine.evaluate() → WIN | LOSE | DRAW
6. Full game transcript saved as proof notation (EGIF sequence)
```

---

## Architecture Principles

**Immutability**: Nothing modifies an EGI in place. Every transformation produces a new EGI. The history forms a directed acyclic graph ([DAG](GLOSSARY.md#dag)) of EGI states with rule applications as edges.

**EGIF as the universal language**: EGIF can represent every domain model, assertion, proof step, and corpus entry. The domain gets no separate "data model". It stands as an EGI.

**Rule-governed construction**: Formal transformation rules produce every graph utterance in Ergasterion and Agon. Logical reasoning permits no arbitrary graph editing; only initial composition, in Ergasterion's composition mode, allows it.

**Mode separation by permission, not by data**: All three modes operate on the same EGI structures via the same `DiagramController`. The difference lies in which operations each mode offers. Organon reads only; Ergasterion permits composition and practice transformations; Agon enforces the game protocol.

**GUI as facilitator, not renderer**: The graphical interface aims to develop aesthetic, expressive, and interpretive skills. It exposes the structure of EGI in ways that reward careful attention. It does not merely display a computed picture; it lets the user see and think with the diagram.
