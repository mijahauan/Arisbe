# The Minimal In-View Set

*Design-of-record. Scale, attention, and scoping in EG visualization — and the diagram↔narration
correspondence that checks them.*

> **New here? Read §1–§2 first.** This is a doctrine document, not an implementation report. It states a
> normative theory (which subset of a reasoning process to keep visible) and gives that theory a falsifiable
> test. No code is proposed for immediate build; §11–§12 lay out options and the two decisions that remain the
> author's.

**Status:** design-of-record, 2026-06-25. **Companion to** [`LINEAR_GRAPHICAL_CORRESPONDENCE.md`](LINEAR_GRAPHICAL_CORRESPONDENCE.md)
(the bedrock correspondence), [`ADAPTIVE_SCOPE_VIEWER.md`](ADAPTIVE_SCOPE_VIEWER.md) (the overview machinery
this generalizes), [`DOMAIN_ORACLE_AND_M.md`](DOMAIN_ORACLE_AND_M.md) (how M is held), and
[`MODALITY_WITHOUT_GAMMA.md`](MODALITY_WITHOUT_GAMMA.md) §5 (the map-symbol gate every abbreviation passes).

---

## 1. The problem, in Peirce's own terms

Peirce built Existential Graphs to *leverage the human capacity to think visually* — the diagram is not a
picture *of* a thought but the moving picture that *is* the thought, an external surface one experiments on.
The whole bet is cognitive: a drawn structure offloads work the mind cannot hold internally.

But that same bet sets a limit. We cannot have everything "in view," which is to say everything "in mind," at
once. A Universe of Discourse (UoD) — a whole diachronic reasoning process — vastly exceeds a screen, and
(more importantly) a working attention. So the practical question that surfaced as "how do we render M?" is
really the founding question turned on the corpus itself: **what subset of the UoD do we keep in view to stay
cognizant of the context that makes the immediate issue interpretable, without that context drowning the
issue?**

The answer lives between two failure modes, both of which the project already names:

- **Failure A — draw-on-a-sheet.** Scribe the graph "as if that made sense," ignoring that the *interpretive
  context* is invisible. Per [`LEVEL_ZERO_AND_THE_REGISTERS.md`](LEVEL_ZERO_AND_THE_REGISTERS.md), the
  invisible thing is **context-as-ground** (*whose* universe, *what* commitments), not context-as-enclosure
  (the bounding cut, which Dau's formalism already handles). "No context at level 0" is true of enclosure and
  *quietly false of ground*. Failure A renders the figure while leaving the ground mute.
- **Failure B — render-the-whole-UoD.** Drawing it all fails twice over: on **scale** (the SUMO ground
  taxonomy is ~289 s of full layout vs ~0.8 s as an overview — [`ADAPTIVE_SCOPE_VIEWER.md`](ADAPTIVE_SCOPE_VIEWER.md)
  §9) and on **category** (a UoD is a *process* — a branching transformation history — not a diagram; drawing
  it whole is Borges's 1:1 map).

The third thing — neither mute nor total — is to **render a focus at full fidelity, make the ground legible by
reference and indication rather than drawn in full, and make every abbreviation honest by an expansion law.**
Recast cognitively: keep the *minimum-necessary set* that sustains situation awareness — enough to *perceive*
the focal graph, *comprehend* it (its ground), and *project* it (its next legal moves), in Endsley's terms
(§4) — within the attention budget. This document states the rules for that set (§9), grounds them in the
study of bounded attention and discourse (§4–§8), and — the keystone — gives them a falsifiable test (§10).

## 2. Three correspondences

Arisbe is organized around correspondence. Two are already in the doctrine; this document adds a third.

1. **Linear ↔ graphical** — the bedrock. A picture and a proposition denote the same mathematical object
   across every transformation ([`LINEAR_GRAPHICAL_CORRESPONDENCE.md`](LINEAR_GRAPHICAL_CORRESPONDENCE.md),
   attested at §3.3). Scoped to three regimes (composition / asserted / presentation-only).
2. **Presentation regimes** — the same EGI may be reprojected freely (regime 3) without changing what it
   denotes; an overview is a *fourth thing*, a viewing operation, never a promotion source.
3. **Diagram ↔ natural-language narration** *(new, this document)* — a line of thought narrated in speech is
   the naturally serialized, naturally chunked trace of the same reasoning a diagram-chain records. The
   correspondence between the two is the **empirical check** on whether our *cognitive* scoping rules match
   how people actually hold an argument together.

Note the third is a **validation correspondence, not a new assertion regime.** It does not let anything new
enter the corpus; it tests a theory. It earns its place because Arisbe already round-trips EGIF↔CLIF↔NL and
already stores a narration on every node and edge of a proof chain (§10, §F-evidence).

## 3. Three scale axes that "too big" conflates

"Too big for a screen" hides three different problems, each needing a different abbreviation strategy:

| Axis | What is too big | Diachronic? | Existing handle | "Abbreviate" means |
|---|---|---|---|---|
| **(i) Synchronic EGI** | breadth/depth of one drawn graph | no | [`overview_projection.py`](../src/overview_projection.py) | collapse cuts to form-only placeholders |
| **(ii) Diachronic process** | the transformation-history DAG | **yes** | the derivation-DAG lens | chapter/checkpoint the DAG |
| **(iii) Ambient ground M** | the model behind an assertion | partly | [`domain_oracle.py`](../src/domain_oracle.py) — *M queried, not held* | draw only the neighborhood G touches; reference the rest |

**"Render M" is axis (iii).** The oracle gives axis (iii) its *semantics* but no *rendering*; the overview
machinery is built for axis (i). The near-term engineering (§11) gives axis (iii) a rendering that obeys the
same expansion-law discipline as axis (i), and makes the ground (Failure A) legible alongside it.

## 4. The cognitive constraint and external cognition (precedent register 1 — the *study*)

The rules in §9 are not stipulations; they discharge findings from the study of bounded attention and the use
of external representations to escape it. Each entry: the finding, then its implication for the in-view set.

- **Chunk capacity.** Miller's "magical number seven" was always a rough regularity counted in *chunks*, not
  items ([Miller 1956](https://psychclassics.yorku.ca/Miller/)); when rehearsal and long-term recoding are
  controlled out, the pure focus-of-attention capacity is about **four** chunks ([Cowan 2001](https://www.cambridge.org/core/journals/behavioral-and-brain-sciences/article/magical-number-4-in-shortterm-memory-a-reconsideration-of-mental-storage-capacity/44023F1147D4A1D44BDC0AD226838496)).
  *Implication:* the default simultaneously-attended budget should be small (~4; ≤7 for browsing), and counted
  in **chunks, not nodes** — so folding is the primary lever (S1, S2). *(Caveat: "~4" is the focus-of-
  attention figure; the language-side results in §6 support "small and bounded," not a universal integer.)*
- **A managed, multi-channel store.** Working memory is not one buffer but a central executive allocating a
  separate **visuospatial sketchpad** and a verbal store ([Baddeley & Hitch 1974; Baddeley 2000 episodic
  buffer](https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613(00)01538-2)). *Implication:* put
  the diagram in the sketchpad and the *ground* (universe, commitments) in the verbal channel — keep textual
  ground off the canvas so it does not consume visual budget (S4).
- **Cognitive load.** Total load = intrinsic (the problem's irreducible element-interactivity) + extraneous
  (imposed by presentation) + germane ([Sweller; cognitive load theory](https://en.wikipedia.org/wiki/Cognitive_load)).
  *Implication:* everything in view that is neither the focus nor its required ground is *extraneous* load and
  must be collapsible. The overview's form-only placeholders are an extraneous-load reduction.
- **Change blindness / inattentional blindness.** People miss large, salient changes when attention is
  elsewhere ([Simons & Chabris 1999](https://doi.org/10.1068/p281059); [Rensink, O'Regan & Clark 1997, "To
  See or Not to See"](https://doi.org/10.1111/j.1467-9280.1997.tb00427.x)).
  *Implication:* a transformation's delta must be made *attention-grabbing*, not merely present — passively
  keeping history around does not keep it in mind (D2).
- **Situation awareness.** Staying oriented in a dynamic task is a three-level achievement: *perceive* →
  *comprehend* → *project* ([Endsley 1995](https://journals.sagepub.com/doi/10.1518/001872095779049543)).
  *Implication:* the in-view set must serve all three — not just show the focal graph but its ground
  (comprehend) and its next legal moves (project). A view that supports perception alone has *too little*
  context — the floor below which the set must not shrink (S3, S5).
- **The diagram as offloaded mind.** A diagram and a sentence can be informationally equal yet not
  computationally equal — spatial indexing collapses search and working-memory matching ([Larkin & Simon
  1987](https://mechanism.ucsd.edu/bill/teaching/F12/cs200/Readings/larkin.whyadiagramissometimesworth.1987.pdf)).
  *Implication:* spatial adjacency is *free* working memory; keep things that must be compared together
  physically adjacent — the warrant for synchronic juxtaposition.
- **Distributed cognition.** Real cognition is spread across people, artifacts, and *time*; earlier results
  are propagated forward as state in the environment ([Hutchins 1995, *Cognition in the Wild*](https://arl.human.cornell.edu/linked%20docs/Hutchins_Distributed_Cognition.pdf)).
  *Implication:* let the *system* hold the trajectory; keep in view only the propagated state needed now (D1).
- **Epistemic action / the intelligent use of space.** People rearrange the world to make information cheaper
  to read off ([Kirsh & Maglio 1994, the Tetris study](https://adrenaline.ucsd.edu/kirsh/Articles/CogsciJournal/DistinguishingEpi_prag.pdf);
  [Kirsh 1995](https://adrenaline.ucsd.edu/kirsh/Articles/Space/intelligent_useof_space.pdf)). *Implication:*
  view-changes (fold/unfold, zoom, pin) are *epistemic actions* and must be cheap, reversible, and
  non-destructive — never confused with logical transformations of the EGI; layout is a cognitive resource.
- **The extended mind.** When an external store plays memory's functional role (reliable, accessible,
  endorsed), it *is* part of the cognitive system ([Clark & Chalmers 1998](https://en.wikipedia.org/wiki/Extended_mind_thesis)).
  *Implication:* M behind the oracle is legitimately part of the reasoner's mind — keep it *queryable*, not
  *displayed* (S4). The Parity Principle is the license for "M queried, not held."
- **External cognition mechanisms.** Graphical representations help by computational offloading,
  re-representation, and *graphical constraining* ([Scaife & Rogers 1996](https://www.sciencedirect.com/science/article/abs/pii/S1071581996900488)).
  *Implication:* because cuts iconically constrain scope, collapsing a cut to a placeholder *preserves the
  constraint structure* — the warrant that semantic zoom is a legitimate inference aid, not mere shrinkage.

## 5. Peirce-specific: diagrammatic reasoning and what must stay co-present

- **Theorematic vs. corollarial.** Corollarial deduction reads the conclusion off the diagram as given;
  *theorematic* deduction requires **introducing a new element** — experimenting on the diagram — before the
  conclusion appears ([Stjernfelt, "Corollarial and Theorematic Diagram Experiments"](http://frederikstjernfelt.dk/Peirce/Corollarial%20and%20Theorematic%20Diagram%20Experiments.2011:2014.pdf)).
  *Two consequences:* the **focus must stay manipulable**, never frozen into a read-only summary, because
  that is where new elements get introduced (S5); and **corollarial runs are exactly what is safe to squash**
  diachronically, while theorematic moves stay visible (D4).
- **Moving pictures of thought.** A Peircean diagram is an icon one *watches move*; knowledge comes from the
  transformation, not the static frame (Stjernfelt, *Diagrammatology*, 2007). *Implication:* the diachronic
  dimension is not bookkeeping — it is where the inference lives, so the in-view set must make the *movement*
  legible (before→after juxtaposition; D2).
- **The graph as the reasoning surface.** EGs are a candidate *cognitive* logic — the medium of thought, not
  a record of it ([Pietarinen 2011, *History and Philosophy of Logic* 32(3):265–281](https://doi.org/10.1080/01445340.2011.555506)).
  *Implication:* the minimal in-view set must be *sufficient to make the next move*, not merely to display the
  current state.
- **The sheet of assertion as a bounded field of attention.** The sheet is a continuous surface asserting
  everything scribed on it within one universe; nesting depth carries logical force ([Shin 2002, *The Iconic
  Logic of Peirce's Graphs*](https://mitpress.mit.edu/9780262194709/the-iconic-logic-of-peirces-graphs/);
  Roberts 1973). *Implication:* Peirce already drew the boundary; we choose which *region* (which nesting
  neighborhood around the focus) to keep lit — and **nesting depth is the natural distance metric** for the
  degree-of-interest rule (§6, S1). The endoporeutic universe — the line of identity as a *chosen individual*
  ([commens: endoporeutic](http://www.commens.org/encyclopedia/article/pietarinen-ahti-veikko-endoporeutic-method))
  — is precisely a discourse referent under an assignment (§6), which is why the narration check works.

## 6. Relevance, discourse scoping, and the keep-vs-collapse rule (precedent register 2 — the *technique* and the *discourse science*)

### 6.1 The objective function and the formal rule

- **Relevance.** Cognition tends to maximize cognitive effect for minimum processing effort ([Sperber &
  Wilson; Wilson & Sperber 2004](https://www.dan.sperber.fr/wp-content/uploads/2004_wilson_relevance-theory.pdf)).
  *This is the governing objective for the in-view set:* include an element iff its expected effect (does it
  change what can be concluded/decided now?) exceeds its budget cost. Everything in view should pay for itself.
- **Degree of Interest.** The formal keep-vs-collapse rule: `DOI(x | focus=y) = API(x) − D(x, y)` — a priori
  importance minus distance from focus ([Furnas 1986, Generalized Fisheye Views, CHI '86, pp. 16–23](https://doi.org/10.1145/22627.22342)).
  *For Arisbe:* `D` = cut-nesting + line-of-identity distance from the focus;
  `API` = structural importance (sheet-level assertions, the focal predicate's direct arguments). Keep the
  top-budget items by DOI, collapse the rest. **The overview budget is literally a DOI threshold** (S1, e).
- **The frame problem.** After an action, an agent must determine what changed without re-checking everything;
  the deep difficulty is selecting what is even *relevant* to reconsider ([frame problem](https://en.wikipedia.org/wiki/Frame_problem);
  McCarthy & Hayes 1969; Dennett 1984 "Cognitive Wheels"). *For Arisbe:* the diachronic rule is "after this
  move, what must I re-attend?" — surface the **effect set**, leave the provably-unaffected folded. EG
  transformation rules have *known local effects*, so this is computable by construction (D3).
- **Common ground.** Interlocutors need not re-state what is mutually presupposed; only updates are
  communicated ([Clark 1996, *Using Language*](https://web.stanford.edu/~clark/pubs.html)). *For Arisbe:* the
  interpretive ground is common ground made explicit but kept *off-canvas* — present, one glance away, never
  consuming sheet budget (S4). The moment common ground is in doubt, reasoning stalls — so it must be
  *nameable and inspectable*, not *displayed*.

### 6.2 The discourse science that powers the check (§10)

- **Discourse Representation Theory.** Meaning is built *incrementally* from text into a DRS: a **box** with a
  universe of **discourse referents** and **conditions**; boxes nest under negation/implication/quantification;
  a referent's **accessibility** is fixed by box subordination ([Kamp, van Genabith & Reyle, DRT handbook
  chapter](https://www.ims.uni-stuttgart.de/archiv/kamp/files/2011.kamp.van.genebith.reyle.discourse.representation.theory.handbook.pdf);
  Kamp & Reyle 1993). The match to a Beta EG is near-exact:

  | DRT | Existential Graph (Beta) |
  |---|---|
  | DRS box | area (sheet / cut interior) |
  | nested box (negation / conditional) | nested cut(s) — negation is a cut; the conditional/universal is the scroll |
  | discourse referent | line of identity (an existential individual) |
  | condition (predicate over referents) | relation edge (spot) over lines |
  | **accessibility** by box subordination | **scope** by cut nesting |
  | incremental DRS construction across sentences | the transformation chain across steps |

  So a narration *is* a chain of DRSs and a DRS *is* an EG. **Credit where it is due: the structural
  isomorphism "a DRS is (structurally) a Beta EG" is not ours — it is John Sowa's**, stated explicitly in
  *From Existential Graphs to Conceptual Graphs* ("Kamp's DRSs … the logical structure is isomorphic to
  Peirce's existential graphs"), and tracing to Kamp (1981), who arrived at the box-and-scope apparatus
  independently of Peirce. What is *not* in the prior literature is the **dynamic** half: aligning EG
  *transformation steps* with DRT *discourse-update* dynamics and **scoring** that alignment (Centering +
  focus-stack). The static kinship is Sowa/Kamp; the operational diagram↔narration *scorer* is Arisbe's
  contribution, and it is the theoretical warrant for the narration check.
- **Segmented DRT.** Adds rhetorical relations (Explanation, Elaboration, Contrast…) linking Elementary
  Discourse Units into a hierarchy with a "right frontier" governing attachment ([Asher & Lascarides 2003,
  *Logics of Conversation*](https://philpapers.org/rec/ASHLOC)). *For Arisbe:* a *chain* of diagrams ↔ a chain
  of utterances is an SDRS; the rhetorical relation between steps ("hence," "but," "to see this") is the *edge
  type* in the transformation DAG (`HistoryBranchType`: linear / exploration / alternative). The right
  frontier is the discourse twin of the current focus.
- **Centering Theory.** Each utterance has a *ranked* set of forward-looking centers `Cf` (salient entities)
  and one backward-looking center `Cb` (what it is "about"); transition types (Continue > Retain > Smooth-Shift
  > Rough-Shift) form a tested coherence ordering ([Grosz, Joshi & Weinstein 1995](https://aclanthology.org/J95-2003/)).
  *For Arisbe:* `Cf` *is* the small ranked salient set carried across one step — the focal in-view set; `Cb` is
  the element the step is about (the spot/line a rule applies at). Centering gives a **per-step, empirically
  grounded prediction** of the in-view set to score against (§10, metric 1).
- **Attentional state as a stack.** Discourse attention is a **stack of focus spaces** pushed when a segment
  opens a subordinate purpose and popped when it completes ([Grosz & Sidner 1986](https://aclanthology.org/J86-3001/)).
  *For Arisbe:* this is **diachronic scoping = a stack discipline** — focus spaces are the in-view set, push/pop
  is chaptering. `overview_projection` open/collapse over the cut hierarchy *is* a focus-space stack; "now,
  within this case… / returning to the main claim" is the narrator audibly pushing and popping (§10, metric 3).
- **Bounded held-set in language.** Comprehension cost rises with the number of open dependencies held and
  the distance between dependents ([Gibson, Dependency Locality Theory](https://pubmed.ncbi.nlm.nih.gov/9775516/);
  [Just & Carpenter 1992, a capacity theory of comprehension](http://www.ccbi.cmu.edu/reprints/Just_Carpenter_PsychRev-1992_capacity-theory.pdf)).
  *For Arisbe:* converging, modality-independent evidence for a small bounded focal budget; DLT's storage cost
  (open dependencies) is the linguistic analogue of `boundary_degree` (ligatures crossing the frontier) — a
  measurable per-step load (§10, metric 4).

### 6.3 The visualization canon, mapped to Arisbe's primitives

- Shneiderman's "overview first, zoom and filter, details on demand" = tap-to-expand (axis i; already shipped).
- Semantic zoom (Pad++/Jazz/Piccolo) = the placeholder's interior level-of-detail — but Arisbe's is *attested*.
- Cartographic **legend / inset / gazetteer**, "the map is not the territory" = the invisible ground made into
  chrome — the answer to Failure A (d).
- Graph-drawing **metanodes / clustering** = the quotient, done soundly; **NodeTrix** (switch to a matrix for
  dense regions) = the breadth-cliff hub case.
- **Nelson transclusion** ("the same content, knowably, in more than one place" — include by reference, stored
  once) = the missing "reference, not inline" primitive (b). Today [`cl_import_resolver.py`](../src/cl_import_resolver.py)
  does the *opposite* — it inlines the import closure.
- Database **views vs. materialized views** = the oracle ([`domain_oracle.py`](../src/domain_oracle.py), a
  *view* over M) vs. [`model_materialization.py`](../src/model_materialization.py) (a *materialized view*, the
  least Herbrand model). Arisbe has the DB-views architecture for axis (iii); it lacks a *rendering* of the
  view's relevant slice (c).
- Ontology tools (Protégé / WebVOWL / OntoGraf) are the nearest neighbors and **have not solved this** — they
  degrade to clutter or switch to matrices, and crucially *none offers a soundness contract on its
  level-of-detail.* **This is where Arisbe is ahead:** the quotient is §3.3-correspondent, the fold is
  isomorphism-gated, the oracle verdict is a real homomorphism. Its abbreviations are *logically attested*, not
  merely visual.

## 7. How experts keep arguments scoped *without* recapitulation (the answer to the second question)

*What keeps a complicated proof effective without recapitulating the whole domain on every thought?* Four
attested mechanisms — and Arisbe already instantiates each, soundly:

1. **Accessibility** (DRT, §6.2): only box/cut-subordinate referents are in scope. → cut-nesting scope on
   lines of identity. *Structural* scoping: most of the universe is simply out of scope at any position.
2. **Focus-stack discipline** (Grosz & Sidner; SDRT right frontier): a push/pop stack holds only the active
   segment's salient set. → `overview_projection` open/collapse = chaptering.
3. **Long-term working memory** — *the core answer.* Experts encode task content into long-term memory via
   retrieval structures and hold in attention only **retrieval cues**, re-accessing content on demand
   ([Ericsson & Kintsch 1995](https://pubmed.ncbi.nlm.nih.gov/7740089/)). A mathematician does not hold the
   domain in mind; she holds cues that retrieve it. → the **oracle** (M queried, not held — the cue is the
   negation-free fragment `g`; `resolve(g)` retrieves only the touched neighborhood) and **fold-to-definition**
   ([`definitions.py`](../src/definitions.py): `expand_at` unfolds *one* spot for a check, `fold` refolds,
   `fold ∘ expand_at = id`; there is deliberately **no global unfold** — `expand` is quarantined to
   verification, so the Borges-map blowup is structurally impossible; see [`DEFINITION_NODE.md`](DEFINITION_NODE.md)).
4. **The math register's black-boxing** ([Tanswell & Inglis 2023, *The Language of Proofs*](https://philsci-archive.pitt.edu/22002/1/Tanswell%20and%20Inglis%20(2023)%20The%20Language%20of%20Proofs%20A%20Corpus%20Linguistic%20Study.pdf);
   Hersh 1993, "Proving is convincing and explaining"): "by Lemma 3" (reference-not-inline), "recall that"
   (retrieval cue), "WLOG / similarly" (suppress a symmetric sub-derivation). → `LogicalProvenance.rule_citation`
   / folded definition nodes / collapsed sibling placeholders.

Chunking underwrites all of it: experts recall meaningful configurations as single units, not parts (Chase &
Simon 1973; de Groot). The named lemma *is* an expert chunk — Peirce's own hypostatic abstraction. **So
Arisbe's fold / oracle / reference primitives are not conveniences; they are formal, sound versions of how
minds already stay scoped.** That is the strongest evidence the architecture is pointed the right way.

## 8. Domain precedents for managing the working set (mechanics to borrow)

- **Proof assistants** (Coq / Lean / Isabelle). Each open goal is a sequent `Γ ⊢ G`: local hypotheses above,
  goal below; tactics actively *curate* what is visible — `clear` (drop an unneeded hypothesis),
  `generalize`/`revert` (abstract), `intro` (bring in), `unfold` (= [`definitions.py`](../src/definitions.py)).
  *Borrow:* a sequent-style minimal display — the focal region is the "goal," its required ground the "local
  context," the rest hidden; expose `clear`-like (fold/hide) and `generalize`-like (fold-to-definition) as
  *view* commands.
- **IDEs / debuggers.** Call stack + locals + watch window = a minimal live slice; code folding hides bodies;
  **sticky scroll / breadcrumbs** keep the enclosing scope pinned while you work inside. *Borrow:* pin the
  enclosing cut-context as a sticky header (S3), expose the nesting path as a breadcrumb (`⊙ sheet › ¬ › ¬ ▸
  here`), offer a user-curated **watch list** of lines/predicates to keep visible regardless of DOI.
- **Version control (git).** Keeps the full history but shows `HEAD`, the staged delta, and one line per commit
  by default; squash/tags chapter the trajectory. The transformation-history DAG is already git-shaped.
  *Borrow:* current snapshot + immediate delta by default; older history as a one-line-per-step log; tag/chapter
  key snapshots; squash corollarial runs (D1, D4).
- **Progressive disclosure** (Nielsen / NN/g). Essentials first, detail on request. *Borrow:* the interaction
  policy for *every* collapse — the placeholder is the disclosed essential, the full sub-graph the on-request
  detail, unfolding the disclosure act; the overview is thereby self-documenting.

## 9. The rules of the minimal in-view set

Each rule: statement — justification — the Arisbe primitive it tunes. These are the normative spine; §10 makes
them falsifiable.

### Synchronic (how much surrounding structure / ground to keep around the focus)

- **S1 — DOI budget.** *Keep visible the highest-`DOI` items (`DOI = API − D`, `D` = cut-nesting + identity
  distance) up to ~4 chunks (≤7 for browsing); collapse the rest to form-only placeholders.* — Cowan's ~4 sets
  the cap, Furnas's DOI the ranking; nesting depth supplies `D` (Peirce). — *Tunes* the overview budget
  ([`layout_service.generate_overview_layout`](../src/web_api/services/layout_service.py),
  `DEFAULT_OVERVIEW_BUDGET`).
- **S2 — Chunk, not node.** *Count the budget in chunks; a folded sub-graph or definition is one chunk.* —
  Miller's chunk is the unit; Sweller's element-interactivity says cost tracks *interacting* elements. —
  *Tunes* fold/unfold ([`definitions.py`](../src/definitions.py)).
- **S3 — Sticky ground / breadcrumb.** *Always keep the enclosing cut-context visible as a pinned breadcrumb,
  even when its contents are collapsed.* — Larkin–Simon (enclosing scope must stay co-present) + IDE sticky
  scroll; near-zero cost for high effect (Relevance). — *Tunes* the ContextReflex panel
  ([`context-reflex.js`](../src/web_viewer/js/context-reflex.js)).
- **S4 — Ground named, not shown.** *Keep the interpretive ground (universe, commitments, standing, which-M)
  off-canvas, one glance away, never consuming sheet budget — but instantly inspectable.* — Clark's common
  ground + Clark–Chalmers' Parity Principle (the queryable store is part of the mind). — *Tunes* ContextReflex
  + the oracle.
- **S5 — Focus stays manipulable.** *The focal region remains fully editable/extensible at all times; collapse
  applies to the periphery, never freezes the focus into a read-only summary.* — Peirce's theorematic reasoning
  introduces new elements *into* the diagram, so the place where work happens cannot be frozen (Pietarinen's
  reasoning surface). — *Constrains every option below.*

### Diachronic (how much history to keep co-present)

- **D1 — HEAD + delta.** *By default show the current snapshot plus the explicit delta from the prior one;
  render older history as a one-line-per-step log.* — git's HEAD/index/`--oneline`; Hutchins (the system holds
  the trajectory). — *Tunes* the history-DAG view.
- **D2 — Flag the change.** *Make each transformation's delta attention-grabbing, not merely present.* — change
  blindness (Simons & Chabris; Rensink); Stjernfelt (inference lives in the movement). — *Tunes* delta
  rendering on the DAG.
- **D3 — Effect set / frame rule.** *After a transformation, surface only the regions whose truth or scope
  changed; leave the provably-unaffected folded.* — the frame problem, solved by construction since EG rules
  have known local effects. — *Tunes* the diff/effect computation over [`egi_transformation_history.py`](../src/egi_transformation_history.py).
- **D4 — Chapter and squash.** *Let users tag key snapshots as chapters and squash runs of corollarial steps;
  keep theorematic moves visible; co-present history ≤ ~4–7 chunks.* — Cowan/Miller bound the diachronic view
  too; Peirce's corollarial/theorematic split says *which* steps are routine enough to squash; git tags/squash
  + progressive disclosure supply the mechanic. — *Tunes* the history-DAG view.

**The two budgets are one principle along two distances.** Relevance, capped at ~4 chunks, applied along
*cut-nesting/identity distance* in space (Furnas DOI on the sheet) and *transformation distance* in time
(steps from HEAD on the DAG). And the four primitives line up one-to-one with the four precedents: overview
budget = DOI (Furnas/Cowan); fold = chunking (Miller/Sweller); ContextReflex = common ground (Clark); oracle =
the off-loaded store (Clark–Chalmers / Ericsson & Kintsch).

*The D-rules govern co-presence — how much history stands side by side, time flattened into space. The
genuinely temporal axis (the **rate** of succession: which transitions get dwell, how compressed stretches
stay honest) is ruled separately in [`RATE_AND_INTELLIGIBILITY.md`](RATE_AND_INTELLIGIBILITY.md), with its
own pre-registered hypotheses (2026-07-03).*

## 10. The validation methodology — the diagram↔narration correspondence check

The rules in §9 are *hypotheses about how people think*. They must be testable, or they are decoration. The
test: **a line of thought, narrated by an expert, is the serialized trace of the same reasoning a diagram-chain
records — so Arisbe's computed in-view/referenced sets along a proof's diagram-chain should track the expert's
narrated present/referenced sets along the matching narration-chain.** Where they disagree across a corpus, the
rule is wrong.

### Why this is admissible, not hand-waving

Verbal reports of the *current contents of attention* (Level 1–2) are veridical data on cognition; only reports
of *why/strategy* (Level 3) distort ([Ericsson & Simon, *Protocol Analysis*](https://mitpress.mit.edu/9780262550239/protocol-analysis/);
the limit named by [Nisbett & Wilson 1977](https://home.csulb.edu/~cwallis/382/readings/482/nisbett%20saying%20more.pdf)).
So the harness collects narration *as a step is taken* ("what do you have in mind here?") and **never** "why
this rule." And discourse science (§6.2) supplies *tested, operationalizable* models of the cross-utterance
salient set (Centering) and its stack discipline (Grosz & Sidner) — so "what stays in view in speech" is a
measurable quantity.

### The harness (designed, not built)

- **Input.** A worked diagram-chain `D = ⟨G₀ →r₁ G₁ → … → Gₙ⟩` (the transformation history), plus a per-step
  expert **narration** `Nᵢ`. The ground-truth fixture is [`tomos/universes/theorem_praeclarum/`](../tomos/universes/theorem_praeclarum)
  — Leibniz's Praeclarum Theorema as the *transcribed* Dau derivation, whose step segmentation Arisbe did not
  design (honest ground truth). Additional chains: the EPG scenarios and `ProofChain`/`TransformationChain`.
- **Arisbe's side.** For each `Gᵢ`, compute the predicted **focal set** `Φᵢ` (via [`overview_projection`](../src/overview_projection.py))
  and **referenced set** `Ρᵢ` (folded definition nodes + oracle-resolved fragments + cited rules).
- **Narration side.** Parse each `Nᵢ` into (a) entities/relations made **present** (named or pronominalized
  salient items) and (b) items merely **referenced** ("by Lemma…", "recall…", "as before"). Map narration
  entities to graph elements via [`nl_to_logic.propose`](../src/nl_to_logic.py) (English→FOL→EGI fragment),
  aligned to `Gᵢ` by [`graph_isomorphism_engine`](../src/graph_isomorphism_engine.py) / `eg_navigation`.

### Falsifiable metrics

1. **Centering overlap (per step).** Treat `Nᵢ` as an utterance; compute its `Cf` ranking and `Cb`. Score
   set-overlap and rank-correlation between `{Cb, top-k Cf}` and `Φᵢ`. *Falsifier:* the narration's salient
   entities systematically fall outside Arisbe's focal set.
2. **Fold-matches-reference.** Does each narration *reference* cue ("by/recall/WLOG/similarly") align with a
   folded/placeholdered/oracle-resolved element, and each *restated* item with an element in `Φᵢ`? Report
   precision/recall of fold-decisions against narration cues. *Falsifier:* Arisbe folds what experts restate,
   or restates what experts fold.
3. **Segment-boundary alignment.** Detect narration segment boundaries (Grosz & Sidner push/pop cues; SDRT EDU
   breaks) and compare to chapter/area boundaries in the DAG (focus moves, `HistoryBranchType` edges, cut
   open/collapse events), windowed (e.g. WindowDiff). *Falsifier:* expert chaptering and Arisbe chaptering
   disagree.
4. **Load corroboration (optional).** Correlate per-step `boundary_degree` and `|Φᵢ|` with narration
   difficulty markers (hesitations, restarts). *Falsifier:* steps Arisbe scores low-load are the ones experts
   struggle to narrate.

### Honest limits

- Narration varies by speaker — run a *corpus* of narrations per chain and report inter-narrator agreement
  first; only the *converged* in-view set is ground truth.
- Think-aloud is valid but **incomplete** (a narrator may hold something silently). The check therefore tests
  **alignment** ("does Arisbe scope the way expert speech scopes?"), **not optimality** ("is this budget the
  cognitively ideal one?"). That is exactly the falsifiable claim the thesis makes.
- The static EG≅DRS isomorphism is **Sowa's** (tracing to Kamp 1981); what is unpublished is the *dynamic*
  step↔update alignment + its scorer. The `nl_to_logic` alignment is heuristic ("LLM proposes, Arisbe
  disposes") — so element-mapping errors must be *reported*, not hidden.

### The check is already half-built

No new storage is needed — every chain node/edge already carries its narration:
`StateSnapshot.natural_language_summary` + `linear_forms`, `TransformationStep.natural_language_description`,
`LogicalProvenance.rule_citation` (all in [`egi_transformation_history.py`](../src/egi_transformation_history.py)).
The translators exist (`egif_generator_dau`, `clif_generator_dau`, `cgif_generator_dau`, `egi_to_fol`) and the
NL bridge exists ([`nl_to_logic.py`](../src/nl_to_logic.py)). **The check needs a scorer, not a schema.**

### The prototype scorer (built — corpus result)

The scorer is built and run across **the whole corpus of narrated worked chains** (8 UoDs, 35 steps):
[`src/diagram_narration_check.py`](../src/diagram_narration_check.py) +
[`tools/run_diagram_narration_check.py`](../tools/run_diagram_narration_check.py) +
[`tests/test_diagram_narration_check.py`](../tests/test_diagram_narration_check.py) (21 tests, incl. two
falsifiers + a per-chain corpus parametrization). Read-only — it observes the immutable per-state EGIs and the
slim on-disk `chain.jsonl` narration (`parameters.description` / Peirce label), mutates nothing, asserts no truth.

Per move `Gᵢ₋₁ →r Gᵢ` it computes, all as exact functions of the two EGIs + the recorded gold `selection`:
the **focal set** `Φ` = the move's delta `added∪removed` ∪ the selection ∪ each one's **sticky enclosing cut**
(S3) ∪ the **effect set** (D3 — survivors whose *enclosing scope changed* because a cut was inserted/erased
around them, the full subtree of each changed cut ∩ survivors); and the **referenced set** `Ρ` (standing
material the move reuses — the iteration/deiteration source).

**The corpus forced the model's shape — this is the harness doing its job.** A first two-role parse (operated
object vs. locative address) scored a clean 100 % on the two Alpha *construction* proofs (Praeclarum,
Peirce's-law: INS/IT+/DC+) but **failed systematically on every eliminative/macro chain** (DC-/ERA/IT-: 38–75 %).
The misses were not noise — they were all a **third role** the two-role model had no bucket for: predicates in a
clause *restating the resulting proposition* ("→ every S is P", ", **leaving** (R)", "**landing** S on the
sheet", "the **bare theorem** e = f"). So the parse now splits each mention into three Centering/DRT roles by the
region of its earliest occurrence:

| role | what it is (Centering/DRT) | must resolve to | marker |
|---|---|---|---|
| **operated** | the utterance's *center* — the move's object | the focal set `Φ` | before any locative/restatement marker |
| **locative** | the spatial/back-referential *anchor* | standing material `Ρ` | after `into` / `around` / `holding` / `copy of` … |
| **restatement** | *discourse-old* restatement of the upshot proposition | in-view `V` | after a dash / `→` / `leaving` / `landing` / `the bare theorem` … |

| metric | claim | falsifier | corpus |
|---|---|---|---|
| **center coverage** (operated→Φ) | every operated predicate has a bearer in `Φ` | an operated token sits outside the focal set | **100 %** (7/7) |
| **locative grounding** (locative→Ρ) | every locative anchor resolves to *standing* material, not freshly-added structure | a locative token names what the move just introduced | **100 %** (7/7) |
| **restatement-in-view** (restatement→V) | every restated upshot is visible | a restated item has been collapsed off-view | **100 %** (7/7) |
| **salient-in-view** (salient→V) | every narrated item survives the focus-centered overview collapse (S1) | a narrated item lies inside a collapsed cut | **100 %** (degenerate on 7 sub-budget chains; **live on `crowded_modus_ponens`**) |
| **reference alignment** | the narration's introduce/reference stance is structurally witnessed | stance and structure disagree | **100 %** on 7/8; **88 % on `group_identity`** |

**Result: the EG↔DRT step-update bridge holds across the corpus** for all three salience roles (a narrated proof
step = a DRS update; the operated/referential/restated mentions = the update's new / anchoring / discourse-old
referents). The two falsifiers prove the metrics *bite* (a doctored "Iterate S" drops coverage; a doctored "into
the cut around R" on the inserting step drops grounding) — the 100 % is earned, not vacuous. **The one honest
residual is itself a finding:** `group_identity` step-1 is a **squashed macro move** ("insert the f-connection,
merge, erase the freed double cut" collapsed into one chain node) whose narrated stance is *introduce* yet whose
net delta is *pure removal* — so reference-alignment correctly fails. That is the **D4 squash phenomenon** the
rules name; aligning it needs sub-step expansion of macro moves, not a metric patch.

### The spatial rule goes live — the super-budget chain

The seven transcribed chains are all **sub-budget** (max area fan-out ≤ 7), so the spatial overview metric
degenerates on them (the visible set is the whole graph). To make **S1** falsifiable we authored the corpus's
first super-budget chain — [`tomos/universes/crowded_modus_ponens`](../tomos/universes/crowded_modus_ponens)
(`tools/build_crowded_modus_ponens_chain.py`): the fact `(A)` and the matching rule `A⊃B` sit on a sheet beside
**ten unrelated rules** `Dk⊃Ek` — twelve sibling chunks, well over budget — and the proof does ordinary modus
ponens (IT-, DC-) on the *one* matching rule, landing `(B)`. Every step a real, attestable Dau-rule application;
an authored demonstration at low warrant.

The harness now models S1 directly (`spatial_visible`): at each step it collapses the graph to ~7 chunks around
that step's focus, ranking cuts by **cut-nesting distance** (Furnas DOI) and hiding the interiors of the far
ones (a focus-centered overview, the §9 S1 budget — *not* the shipped `layout_service` engine; a model of it). On
`crowded_modus_ponens` the matching rule and the fact stay in view at both steps while all ten distractor
consequents `Ek` (each two cuts deep) collapse off-view. **The proof's own narration names only the fact and the
matching rule — it ignores the crowd — so salient-in-view scores 100 %**: direct evidence for S1 (an expert keeps
the narration within a bounded focus-neighborhood even amid a dozen competing chunks). A fourth falsifier proves
the spatial metric *bites*: a doctored "…but recall (Ek)" naming a collapsed distractor drops salient-in-view
below 100 %, because the budget dropped exactly what the doctored narration tried to keep salient. (The metric is
scoped to its job — a token the *rule erased* is not an in-view failure, only a token that *exists but is
collapsed* is.)

**Honest limits stay surfaced** (`honest_limits`): deterministic relation-name alignment, **not** the
`nl_to_logic` LLM bridge — sound only for the controlled Peircean register (alphabets like {P,Q,R,S}/{M,=}); a
**single** transcribed narration per chain, not a corpus of narrators (so *alignment*, never *optimality*, and no
inter-narrator agreement); token-level salience (a name credited to any bearer, not the specific copy); and the
spatial collapse is a *model* of the overview budget (focus-centered DOI), not the production layout engine.
**Next falsifications** (what earns the rules their keep): a *corpus of narrations* per chain for inter-narrator
agreement; the LLM alignment bridge for *free* narration; sub-step expansion of squashed macro moves (the
`group_identity` residual); wiring the spatial metric to the *production* overview engine; and metric 3
(chapter-boundary) once a branching DAG fixture is narrated.

### Candidate validation rules (to adopt as the rules earn their keep)

1. **Centering-alignment** — `Φᵢ` contains `Cb` and ranks top-k `Cf` consistently (Grosz/Joshi/Weinstein).
2. **Fold-matches-reference** — fold/placeholder/oracle iff narration references rather than restates (Ericsson
   & Kintsch; the math register).
3. **Chapter-boundary** — DAG chapters coincide (within a window) with narration push/pop + EDU boundaries
   (Grosz & Sidner; SDRT).
4. **No-global-unfold (Borges)** — no path expands all definitions for reading; expansion is local-and-refold
   (already enforced in [`definitions.py`](../src/definitions.py)).
5. **Bounded-frontier load** (optional, quantitative) — per-step `boundary_degree` and `|Φᵢ|` stay small and
   predict narration difficulty (Gibson DLT; Just & Carpenter).

## 11. Options menu (engineering, in service of the rules)

| # | What | Axis | Rule(s) | Extends | New? | Cost |
|---|---|---|---|---|---|---|
| a | overview → all modes (esp. Agon) | i | S1 | `layout_service.generate_overview_layout` | extend | low |
| b | **reference / transclusion node** | iii (+i,ii) | S4 | `egi_core_dau` + §3.3 | **NEW** | high |
| c | relevant-neighborhood M-rendering — **✅ BUILT 2026-06-28** (`m_render.m_fragment`) | iii | S1,S4 | `domain_oracle` + overview | extend | medium |
| d | ground / legend panel — **✅ BUILT 2026-06-28** (`m_render.vocabulary_overlap`) | A (all) | S3,S4 | `context-reflex.js` | extend | low |
| e | degree-aware / fisheye budget | i | S1 | `layout_service._resolve_collapsed` | extend | low–med |
| f | chapter / flag the diachronic DAG | ii | D1–D4 | `egi_transformation_history` + DAG view | extend | medium |
| g | **diagram↔narration validation harness** | — (validates all) | the whole rule set | the §10 assets | **NEW (research)** | medium |

- **(a)** Port the shipped `lod=overview&expand=…` path into Agon. Already doctrine-clean; the enabler for (c).
- **(b)** A spot pointing at another UoD / module / definition by **name + provenance** instead of inlining it
  — semantics = the oracle, law = expand-on-demand. The general form of (c) and of Nelson transclusion; inverts
  `cl_import_resolver.py`'s inlining. **Touches `egi_core_dau` and §3.3 — a real architectural fork** (see §12).
- **(c)** Draw only the M-fragment that G touches (the oracle's ego-graph slice), projected through the
  quotient, with a **horizon map-symbol** ("more of M lies here"). M enters as low-warrant backdrop, conditioned
  in the scroll `cut[ M cut[G] ]` ([`LEVEL_ZERO_AND_THE_REGISTERS.md`](LEVEL_ZERO_AND_THE_REGISTERS.md)). Both
  halves exist; only the join is new. **This is the direct answer to "render M."**
- **(d)** Extend the shipped ContextReflex with M-aware fields (which-M, standing, horizon). The direct answer
  to Failure A.
- **(e)** Replace the uniform `DEFAULT_OVERVIEW_BUDGET` BFS with a DOI budget penalizing high-`boundary_degree`
  hubs — the known cliff driver ([`ADAPTIVE_SCOPE_VIEWER.md`](ADAPTIVE_SCOPE_VIEWER.md) §9). The principled S1.
- **(f)** Chapter the history DAG, flag deltas, compute effect sets. Largely UI over existing data.
- **(g)** The keystone build — implements §10. Leverages the already-present narration slots, the translators,
  and the Praeclarum fixture. **Validates whether the whole rule set is right.**

All of (a)(c)(d)(e)(f)(g) are **read-only navigation / chrome / measurement** over attested objects — the
"fourth thing," never a corpus-promotion source. They honor every floor: no mark bears actuality
([`MANIFEST_AND_MEANING.md`](MANIFEST_AND_MEANING.md) floor #6); every abbreviation expands to the attested
truth (the expansion law / map-symbol gate, [`MODALITY_WITHOUT_GAMMA.md`](MODALITY_WITHOUT_GAMMA.md) §5); none
freezes the focus (S5).

## 12. Recommendation and sequencing

**Near-term, doctrine-clean (safe to build):** **(d) + (c)**, together, meet the Agon "render M" need *and*
answer both failure modes — G drawn full-fidelity, the touched M-neighborhood drawn-and-badged, the
interpretive ground stated in the legend. **✅ BUILT 2026-06-28** as `src/m_render.py` (`vocabulary_overlap` =
(d), `m_fragment` = (c)), wired into the Agon interpret payload (`render_m`) and drawn in `agon.html` (the
legend + a small M-fragment board in the reading strip). M is drawn as read-only chrome, never asserted. **(a)** falls out of (c); **(e)** is the follow-on hardening against
the breadth cliff; **(f)** is the natural diachronic companion (mostly UI over the existing DAG).

**Highest research leverage — recommend prototyping first:** **(g), the validation harness**, even minimally on
Praeclarum. It turns §9's rules from assertions into tested claims *before* we tune their parameters, and it
operationalizes the EG↔DRT bridge — the static isomorphism is Sowa's/Kamp's, but the *dynamic*
step↔update scorer is a genuine contribution. Tuning S1–S5 / D1–D4 without (g) is guessing.

> **Update (2026-06-29):** the law is now de-risked (`src/reference_resolution_check.py`, proving
> `RESOLVE ≡ INLINED-AND-ATTESTED` with no core change) and the three decisions below are taken in a
> design-of-record — **[REFERENCE_AND_TRANSCLUSION_NODE.md](REFERENCE_AND_TRANSCLUSION_NODE.md)**:
> Form 2 (a relation-shaped reference *edge* generalizing the definition node), additive-first, with the
> second-order-frontier invariant banked.

**The open architectural question (the author's to decide): (b), the reference / transclusion node.** It is the
general form of (c) and the only real fork, because it touches `egi_core_dau` and the §3.3 contract. Three
decisions:

1. **Form** — a new element kind, an annotated edge, or a metadata overlay (`annotations.py` / `provenance.py`)?
   This determines whether §3.3 totality/correspondence must be *extended*.
2. **Calculus entry** — how does a reference node enter without violating level-0 doctrine (conditioned inside a
   cut, never naked on the recto — [`LEVEL_ZERO_AND_THE_REGISTERS.md`](LEVEL_ZERO_AND_THE_REGISTERS.md))?
3. **Attestation contract** — an `attest_reference` analogous to `attest_overview`, with the law "resolve ≡
   inlined-and-attested."

**Safe / decision split.** (a)(c)(d)(e)(f) are safe read-only extensions and may proceed when scheduled. **(g)
and (b) need the author's decision before any core/build work** — (g) because it is a research commitment worth
making deliberately, (b) because it changes the core.

---

## References

*All entries below were verified against publisher / index metadata (Crossref, ACL Anthology, SEP,
publisher pages). DOIs are given where one exists; the two pre-DOI* Computational Linguistics *articles and the
older monographs carry their canonical stable URLs.*

### Cognition & attention

- Miller, G. A. (1956). The magical number seven, plus or minus two: Some limits on our capacity for
  processing information. *Psychological Review* 63(2), 81–97. https://doi.org/10.1037/h0043158
- Cowan, N. (2001). The magical number 4 in short-term memory: A reconsideration of mental storage capacity.
  *Behavioral and Brain Sciences* 24(1), 87–114. https://doi.org/10.1017/S0140525X01003922 *(NB: "~4" is the
  focus-of-attention figure; the language-processing sources below support "small and bounded," not a
  universal integer.)*
- Baddeley, A. D., & Hitch, G. (1974). Working memory. In G. H. Bower (Ed.), *The Psychology of Learning and
  Motivation* (Vol. 8, pp. 47–89). Academic Press. https://doi.org/10.1016/S0079-7421(08)60452-1
- Baddeley, A. (2000). The episodic buffer: a new component of working memory? *Trends in Cognitive Sciences*
  4(11), 417–423. https://doi.org/10.1016/S1364-6613(00)01538-2
- Sweller, J. (1988). Cognitive load during problem solving: Effects on learning. *Cognitive Science* 12(2),
  257–285. https://doi.org/10.1207/s15516709cog1202_4 *(The intrinsic/extraneous/germane taxonomy was
  formalized later in Sweller, Van Merriënboer & Paas 1998,* Educational Psychology Review *10(3), 251–296.)*
- Simons, D. J., & Chabris, C. F. (1999). Gorillas in our midst: Sustained inattentional blindness for dynamic
  events. *Perception* 28(9), 1059–1074. https://doi.org/10.1068/p281059
- Rensink, R. A., O'Regan, J. K., & Clark, J. J. (1997). To see or not to see: The need for attention to
  perceive changes in scenes. *Psychological Science* 8(5), 368–373.
  https://doi.org/10.1111/j.1467-9280.1997.tb00427.x
- Endsley, M. R. (1995). Toward a theory of situation awareness in dynamic systems. *Human Factors* 37(1),
  32–64. https://doi.org/10.1518/001872095779049543
- Larkin, J. H., & Simon, H. A. (1987). Why a diagram is (sometimes) worth ten thousand words. *Cognitive
  Science* 11(1), 65–100. https://doi.org/10.1111/j.1551-6708.1987.tb00863.x
- Hutchins, E. (1995). *Cognition in the Wild*. MIT Press. https://doi.org/10.7551/mitpress/1881.001.0001
- Kirsh, D., & Maglio, P. (1994). On distinguishing epistemic from pragmatic action. *Cognitive Science*
  18(4), 513–549. https://doi.org/10.1207/s15516709cog1804_1
- Kirsh, D. (1995). The intelligent use of space. *Artificial Intelligence* 73(1–2), 31–68.
  https://doi.org/10.1016/0004-3702(94)00017-U
- Clark, A., & Chalmers, D. (1998). The extended mind. *Analysis* 58(1), 7–19.
  https://doi.org/10.1093/analys/58.1.7
- Scaife, M., & Rogers, Y. (1996). External cognition: How do graphical representations work? *International
  Journal of Human-Computer Studies* 45(2), 185–213. https://doi.org/10.1006/ijhc.1996.0048
- Ericsson, K. A., & Kintsch, W. (1995). Long-term working memory. *Psychological Review* 102(2), 211–245.
  https://doi.org/10.1037/0033-295X.102.2.211
- Chase, W. G., & Simon, H. A. (1973). Perception in chess. *Cognitive Psychology* 4(1), 55–81.
  https://doi.org/10.1016/0010-0285(73)90004-2
- de Groot, A. D. (1965). *Thought and Choice in Chess*. Mouton. https://archive.org/details/thoughtchoiceinc0000groo

### Verbalization methodology

- Ericsson, K. A., & Simon, H. A. (1984; rev. ed. 1993). *Protocol Analysis: Verbal Reports as Data*. MIT
  Press. https://mitpress.mit.edu/9780262550239/protocol-analysis/
- Nisbett, R. E., & Wilson, T. D. (1977). Telling more than we can know: Verbal reports on mental processes.
  *Psychological Review* 84(3), 231–259. https://doi.org/10.1037/0033-295X.84.3.231
- Wilson, T. D. (1994). The proper protocol: Validity and completeness of verbal reports. *Psychological
  Science* 5(5), 249–252. https://doi.org/10.1111/j.1467-9280.1994.tb00621.x

### Discourse / NL↔diagram

- Kamp, H., & Reyle, U. (1993). *From Discourse to Logic* (Studies in Linguistics and Philosophy 42). Kluwer /
  Springer. https://doi.org/10.1007/978-94-017-1616-1
- Sowa, J. F. *From Existential Graphs to Conceptual Graphs* — states the DRS≅EG isomorphism explicitly
  (tracing to Kamp 1981). http://www.jfsowa.com/pubs/eg2cg.pdf **(the source of the static bridge this
  harness operationalizes — credited, not claimed).**
- Kamp, H., van Genabith, J., & Reyle, U. (2011). Discourse Representation Theory. In D. M. Gabbay & F.
  Guenthner (Eds.), *Handbook of Philosophical Logic* (2nd ed., Vol. 15, pp. 125–394). Springer.
  https://doi.org/10.1007/978-94-007-0485-5_3
- Asher, N., & Lascarides, A. (2003). *Logics of Conversation*. Cambridge University Press.
  https://philpapers.org/rec/ASHLOC
- Shin, S.-J., Lemon, O., & Mumma, J. (2025). Diagrams. In E. N. Zalta & U. Nodelman (Eds.), *The Stanford
  Encyclopedia of Philosophy* (first publ. 2001; rev. Sept. 2025). https://plato.stanford.edu/entries/diagrams/
- Pietarinen, A.-V. (2011). Existential Graphs: What a Diagrammatic Logic of Cognition Might Look Like.
  *History and Philosophy of Logic* 32(3), 265–281. https://doi.org/10.1080/01445340.2011.555506
- Grosz, B. J., Joshi, A. K., & Weinstein, S. (1995). Centering: A Framework for Modeling the Local Coherence
  of Discourse. *Computational Linguistics* 21(2), 203–225. https://aclanthology.org/J95-2003/
- Grosz, B. J., & Sidner, C. L. (1986). Attention, Intentions, and the Structure of Discourse. *Computational
  Linguistics* 12(3), 175–204. https://aclanthology.org/J86-3001/
- Gibson, E. (1998). Linguistic complexity: locality of syntactic dependencies. *Cognition* 68(1), 1–76.
  https://doi.org/10.1016/S0010-0277(98)00034-1
- Gibson, E. (2000). The Dependency Locality Theory: A Distance-Based Theory of Linguistic Complexity. In A.
  Marantz, Y. Miyashita & W. O'Neil (Eds.), *Image, Language, Brain* (pp. 95–126). MIT Press.
- Just, M. A., & Carpenter, P. A. (1992). A capacity theory of comprehension: Individual differences in
  working memory. *Psychological Review* 99(1), 122–149. https://doi.org/10.1037/0033-295X.99.1.122

*The **static** EG≅DRS isomorphism is published — John Sowa states it explicitly (*From Existential Graphs
to Conceptual Graphs*: a DRS's "logical structure is isomorphic to Peirce's existential graphs"), tracing to
Kamp (1981). What was **not** found in the literature is a **dynamic** reduction aligning EG transformation
steps with DRT discourse updates, with a scoring metric — so the operational diagram↔narration scorer is
Arisbe's contribution; the underlying correspondence is borrowed and credited (Sowa; Kamp & Reyle).*

### Math register & Peirce

- Tanswell, F. S., & Inglis, M. (2024). The Language of Proofs: A Philosophical Corpus Linguistics Study of
  Instructions and Imperatives in Mathematical Texts. In B. Sriraman (Ed.), *Handbook of the History and
  Philosophy of Mathematical Practice* (pp. 1235–1255). Springer. https://doi.org/10.1007/978-3-031-40846-5_50
- Hersh, R. (1993). Proving is convincing and explaining. *Educational Studies in Mathematics* 24(4), 389–399.
  https://doi.org/10.1007/BF01273372
- Stjernfelt, F. (2007). *Diagrammatology: An Investigation on the Borderlines of Phenomenology, Ontology, and
  Semiotics* (Synthese Library 336). Springer. https://doi.org/10.1007/978-1-4020-5652-9
- Stjernfelt, F. (2011). Peirce's Notion of Diagram Experiment: Corollarial and Theorematical Experiments with
  Diagrams. In R. Heinrich et al. (Eds.), *Image and Imaging in Philosophy, Science and the Arts* (Vol. 2, pp.
  305–340). Ontos Verlag. https://wab.uib.no/ojs/index.php/agora-ontos/article/view/2200
- Shin, S.-J. (2002). *The Iconic Logic of Peirce's Graphs*. MIT Press.
  https://mitpress.mit.edu/9780262194709/the-iconic-logic-of-peirces-graphs/
- Roberts, D. D. (1973). *The Existential Graphs of Charles S. Peirce* (Approaches to Semiotics 27). Mouton.
  https://doi.org/10.1515/9783110226225

### Relevance & HCI / the frame problem

- Sperber, D., & Wilson, D. (1986; 2nd ed. 1995). *Relevance: Communication and Cognition*. Blackwell.
  https://www.wiley.com/en-us/Relevance%3A+Communication+and+Cognition%2C+2nd+Edition-p-9780631198789
- Wilson, D., & Sperber, D. (2004). Relevance Theory. In L. R. Horn & G. Ward (Eds.), *The Handbook of
  Pragmatics* (pp. 607–632). Blackwell. https://www.dan.sperber.fr/?p=93
- Furnas, G. W. (1986). Generalized Fisheye Views. In *Proceedings of CHI '86* (pp. 16–23). ACM.
  https://doi.org/10.1145/22627.22342
- McCarthy, J., & Hayes, P. J. (1969). Some Philosophical Problems from the Standpoint of Artificial
  Intelligence. In B. Meltzer & D. Michie (Eds.), *Machine Intelligence 4* (pp. 463–502). Edinburgh University
  Press. https://philpapers.org/rec/MCCSPP
- Dennett, D. C. (1984). Cognitive Wheels: The Frame Problem of AI. In C. Hookway (Ed.), *Minds, Machines and
  Evolution* (pp. 129–150). Cambridge University Press. https://philpapers.org/rec/DENCWT
- Clark, H. H. (1996). *Using Language*. Cambridge University Press. https://www.cambridge.org/9780521567459
- Nielsen, J. (2006). *Progressive Disclosure*. Nielsen Norman Group.
  https://www.nngroup.com/articles/progressive-disclosure/
- *Proof-assistant context management:* the Lean and Coq/Rocq tactic documentation (`clear`, `generalize`,
  `unfold`) — https://leanprover.github.io/theorem_proving_in_lean/tactics.html
