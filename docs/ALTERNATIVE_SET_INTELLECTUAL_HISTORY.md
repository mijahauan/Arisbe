# Alternative Set: Intellectual History and Unification

## Opening: The Core Insight

An **AlternativeSet** is the formal structure underlying deliberation across all domains: interrogative reasoning, hypothetical thinking, modal exploration, counterfactual imagination, agentive choice, epistemic inquiry, and metacognitive reflection. This structure unifies a century of fragmented insights from logic, philosophy, cognitive science, and computer science into a single, computable form. **Deliberation is holding alternatives in mind, testing them, narrowing them, and committing to one.** This document traces how that insight emerged, what each tradition got right, and how Arisbe synthesizes them.

---

## The Arc of Previous Thinking

### 1. Peirce's Inquiry (1878–1909): Abduction as Testing Alternatives

**Pioneers:** Charles Sanders Peirce (1839–1914), especially his *Illustrations of the Logic of Science* (1877) and *Pragmatism as a Principle and Method of Right Thinking* (1907).

**What it formalized:**
Peirce grounded logic in *semiosis* — the triadic sign-relation of icon, index, and symbol. But more radically, he grounded reasoning itself in **doubt**. Not psychological doubt but dialogical doubt: the explicit holding of incompatible hypotheses until experience or inference eliminates some. Inquiry is *abductive* — inferring from effect to cause by proposing a hypothesis that "would render the fact a matter of course." A scientist holds competing theories, tests them, and commits to the survivor.

**What it got right:**
- Reasoning is *fundamentally interrogative*: the mind holds "what if?" questions
- Alternatives structure thought before any formal logic does
- **Resolution happens through testing**, not declaration
- The doubter is integral to the system (no view from nowhere)

**What it missed:**
Peirce never formalized the structure of "holding alternatives." He had no calculus of the alternative-set itself, only narrative descriptions. His logic was still primarily syllogistic, with abduction grafted on philosophically but not computationally.

**How we build on it:**
AlternativeSet makes Peirce's doubt operational. The `kind` field encodes the semantic type of deliberation (interrogative, hypothetical, modal, agentive, epistemic, metacognitive). Peirce's emphasis on fallibility is carried by the **materiality vector** — what a consequence trace *discovered* about the alternatives (material / bare / spurious, with the diverging relations named), never a degree-of-assurance scalar; assurance vocabulary ("warrant") stays with the repo's doctrinal gradient (posited → derived → withstood), which rises only by surviving challenge. The lifecycle (emergence, tracing, resolution, settlement) mirrors the abductive cycle, and every stage cites the chain step that earned it.

---

### 2. Kripke's Possible Worlds (1959–): Formal Holding of Alternatives

**Pioneers:** Saul Kripke (1940–), *Naming and Necessity* (1972); David Lewis (1941–2001), *Counterfactuals* (1973).

**What it formalized:**
Modal logic seized on the insight that necessity and possibility are *relative to alternative scenarios*. A proposition is **necessarily true** if it holds in all possible worlds accessible from the current world. Kripke grounded this formally: a **Kripke frame** is a set of worlds W with an accessibility relation R, where ◇φ = "∃w ∈ W(Rww′ ∧ φ(w′))" (possibility) and □φ = "∀w′ ∈ W(Rww′ → φ(w′))" (necessity).

**What it got right:**
- Alternatives can be *held formally as a set*
- Accessibility captures the constraints on which alternatives matter
- Context-relative truth emerges naturally

**What it missed:**
Kripke frames are **timeless**. They model a static space of possibilities, not a *diachronic process* of deliberation. There is no notion of how an agent's alternatives narrow through time, or how new alternatives emerge. The agent is absent — worlds exist independent of anyone holding them.

**How we build on it:**
AlternativeSet lives in a **DAG (directed acyclic graph)** — Arisbe's transformation history. Each state has alternatives; moving to a new state via rule application narrows or reopens them. The record's step references (`emerged_from` → `traced_by` → `resolved_by`) map onto the accessibility relation, but *temporally* — the path is the chain itself, not a stored copy of it. We add what Kripke lacked: **the dynamics of deliberation in the actual history of reasoning**.

---

### 3. Reiter's Default Logic (1980): Alternatives to Default Assumptions

**Pioneers:** Raymond Reiter (1941–2002), *A Logic for Default Reasoning* (1980).

**What it formalized:**
In the real world, we rarely have complete information. Agents reason under **defaults**: "typically birds fly; Tweety is a bird; so Tweety flies" — unless we learn otherwise. Reiter formalized this with **default rules**: ϕ : ψ / χ (read: "if φ is believed and ψ is consistent with what's believed, then infer χ"). The alternative is retraction: when a counterexample arises, we abandon the default.

**What it got right:**
- Reasoning is *revisable*: alternatives emerge when defaults fail
- Monotonicity is unrealistic; non-monotonic logic is necessary
- Belief sets evolve as new information enters

**What it missed:**
Default logic focuses on *rules and their revision*, not the *structure of alternatives themselves*. It doesn't model "which alternatives are currently under consideration" — it models what to infer given a belief set.

**How we build on it:**
The abductive moment when a default fails is a *recorded challenge*: the counterexample arrives as a peel verdict or reception, the over-general law is relinquished by a licensed retraction, and the re-opened question stands as a fresh (or re-touched — same content key, the standing question) AlternativeRecord. Defaults are *implicit* in the UoD's history: which alternatives survived is the record.

---

### 4. Hintikka's Doxastic Logic (1962–): Agent's Belief Alternatives

**Pioneers:** Jaakko Hintikka (1929–2015), *Knowledge and Belief* (1962).

**What it formalized:**
An agent's beliefs are not a set of formulas, but a set of *possible worlds consistent with their beliefs*. If you believe φ, then φ is true in all your belief-worlds. Hintikka formalized this: **K(a, φ)** = "agent a knows φ" ≡ "φ holds in all worlds compatible with a's knowledge."

**What it got right:**
- Beliefs are *agent-relative*: different agents hold different alternatives
- Epistemic states are *model-theoretic*, not just syntactic
- The agent's perspective is built into the semantics

**What it missed:**
Hintikka's agents are **frozen in time**. Their belief-worlds don't evolve through reasoning or action. There's no notion of how an agent *learns* by narrowing alternatives, or how deliberation *changes* which worlds are still possible.

**How we build on it:**
AlternativeSet formalizes what Hintikka assumed: the *actual state of an agent's alternatives* at a point in the reasoning process. The presupposition (what must be true for this alternative-set to matter) is the chain state the record's `emerged_from` step points into — recoverable by id, never stored as a copy; `alternatives` is the set of possible outcomes under consideration. Embedding this in Arisbe's DAG adds the **diachronic dimension** Hintikka lacked — alternatives narrow and re-emerge as reasoning unfolds.

---

### 5. Gabbay's Labeled Deductive Systems (1996): Context-Scoped Reasoning

**Pioneers:** Dov Gabbay (1944–), *Labelled Deductive Systems, Volume 1* (1996).

**What it formalized:**
Classical logic has no way to express "at time t" or "in context c" or "by agent a." Gabbay introduced **labels** — arbitrary objects (times, contexts, agents, worlds) that annotate formulas and rules. A sequent is not just Φ ⊢ ψ but **t : Φ ⊢ ψ** (from Φ at time t, infer ψ). Rules can manipulate labels too.

**What it got right:**
- Context is *structural*, not a meta-level afterthought
- Different label spaces (time, agent, world) can coexist
- Rules can enforce label constraints (e.g., time monotonicity)

**What it missed:**
Labeled deductive systems are a framework, not a solution. They don't tell you *what* to label or *how* to use labels in reasoning about alternatives. They're a syntactic wrapper, not a semantic foundation.

**How we build on it:**
AlternativeRecord's step references (`emerged_from`, `traced_by`, `resolved_by`) are labels — they anchor the record in the DAG of Arisbe's transformation history. The UoD itself is a labeled deductive system where **states are labels** and transformations obey label constraints (e.g., rules can only apply at compatible states).

---

### 6. Milner's Process Algebra (CCS 1980, π-calculus 1992): Internal vs External Choice

**Pioneers:** Robin Milner (1934–2010), *A Calculus of Communicating Systems* (1980); Milner et al., *The π-calculus* (1992).

**What it formalized:**
A **process** is a state machine that can **internally choose** (the process nondeterministically picks an alternative) or **externally choose** (the environment picks, and the process adapts). CCS notation:
- **a.P** = do action a, then behave as P (sequential)
- **P + Q** = internal choice: choose P or Q nondeterministically
- **P | Q** = parallel: run P and Q simultaneously
- **a(x).P** = receive input a, then continue as P (external choice)

**What it got right:**
- Nondeterminism is distinct from concurrency
- **Internal choice** (the agent decides) vs **external choice** (the environment decides) is a crucial distinction
- Processes can be **composed** — alternatives at different points interact

**What it missed:**
Process algebra is **synchronous** — it models discrete, instantaneous transitions. It doesn't model the *reasoning process* itself, only concurrent systems. And it has no notion of **testing alternatives** — it just executes one and moves on.

**How we build on it:**
AlternativeSet models the **internal choice** — the agent's deliberative alternatives at a point in time. Commitment to one branch is a *licensed act on the chain* (an admission or discharge the record's `resolved_by` cites). The rule application models **external choice** — the system (logic, physics, other agents) responds to the choice made. The non-determinism is explicit: multiple selection paths can coexist as branches in the DAG.

---

### 7. Gärdenfors' AGM Belief Revision (1985–): Evolution of Epistemic Alternatives

**Pioneers:** Peter Gärdenfors (1941–), *Knowledge in Flux: Modeling the Dynamics of Epistemic States* (1988).

**What it formalized:**
When new information arrives, an agent's belief set must change. **AGM theory** (Alchourrón, Gärdenfors, Makinson) axiomatizes rational belief revision:
- **Expansion** (K + φ): add φ to K
- **Contraction** (K ÷ φ): remove φ from K, keeping the rest consistent
- **Revision** (K * φ): add φ, discarding whatever was necessary to maintain consistency

Belief sets are ranked by *entrenchment* — some beliefs are harder to give up than others.

**What it got right:**
- Belief **dynamics** are rational, not arbitrary
- Retraction and addition are dual operations
- Some beliefs are *core* (essential) and others *peripheral* (dispensable)

**What it missed:**
AGM is *episodic* — each revision is instantaneous. There's no notion of an agent *holding multiple theories in mind simultaneously* while deciding between them. Revision models "I had belief K; now I have belief K*φ," not "I'm deliberating between K and K*φ."

**How we build on it:**
An open record with a traced materiality models *partial revision* — the agent hasn't committed, but the consequences of each branch are already derived and on the record. Final commitment is the licensed resolution (`resolved_by` citing the admitting or discharging step). Entrenchment's analogue is discovered, not declared: a *material* question (whose branches provably diverge in traced consequences) outranks a *bare* one in the attention economy, and the doctrinal warrant gradient — which rises only by surviving challenge — remains the repo's only assurance vocabulary. Arisbe's DAG preserves the full history: you can see every alternative entertained and every step of narrowing, the **deliberative trace** that AGM leaves hidden.

---

### 8. Johnson-Laird's Mental Models (1983–): Cognitive Holding of Alternatives

**Pioneers:** Philip N. Johnson-Laird (1936–), *Mental Models: Towards a Cognitive Science of Language, Inference, and Consciousness* (1983).

**What it formalized:**
People don't reason with formal symbols; they reason with **mental models** — spatial/kinetic simulations of situations. To understand "the circle is above the square," you construct a mental image. To understand "if the light is on, then the door is open; the light is on," you construct models of possible states and eliminate inconsistent ones.

**What it got right:**
- Reasoning is *constructive*, not deductive
- The mind holds *multiple models* and compares them
- Inconsistency is detected by looking for models where premises hold but conclusion fails
- Cognitive load matters — people can only hold a few models at once

**What it missed:**
Mental models are cognitive phenomena, not formal structures. Johnson-Laird gives no *calculus* of models, only psychological predictions. And models are **synchronic** — they don't explain how models are updated, revised, or reordered through time.

**How we build on it:**
AlternativeSet formalizes the structure of "multiple models held in mind." The `alternatives` field is the set of possible models, and Johnson-Laird's cognitive load is now *engineering, not metaphor*: the register of open questions and the S/A vocabulary registers are **capacity-bounded** (`KyteProfile`), with least-recently-touched displacement counted rather than silent — a bounded mind that must reallocate to learn. By embedding this in Arisbe's DAG, we add the **temporal dimension**: you can see how the agent's model-space evolved through a reasoning episode, and rebuild it from the chain alone.

---

### 9. Ciardelli et al.'s Inquisitive Semantics (2010–): Questions as Semantic Objects

**Pioneers:** Ivano Ciardelli, Jeroen Groenendijk, & Floris Roelofsen (2012), *Inquisitive Semantics and a New Notion of Entailment* (2012).

**What it formalized:**
Classical semantics treats questions as *pragmatic* — outside the logic. Inquisitive semantics makes questions **semantic objects**. A sentence denotes a *set of possible answers* (called an **inquisitive content**). "Is it raining?" denotes the set {it's raining, it's not raining}. A **declarative** like "it's raining" denotes a singleton {it's raining}. **Entailment** is defined on inquisitive content: φ entails ψ if every answer to φ is an answer to ψ.

**What it got right:**
- Questions are not second-class citizens; they're formulas with content
- An answer is not a single world, but a *proposition* (set of worlds)
- Multiple questions can be **resolved together** — "who is it and what did they do?" expects pairs (agent, action)
- Inquisitivity is the property of having multiple possible answers

**What it missed:**
Inquisitive semantics is still **static**. It gives the space of possible answers but not the *dynamics* of how an agent narrows answers through inference or learning. And it has no notion of *agent commitment* — at what point does a deliberating agent stop considering alternatives and commit?

**How we build on it:**
AlternativeSet embodies inquisitive semantics made dynamic. The `alternatives` field is the inquisitive content — the set of possible answers (for the built interrogative kind, the atom and its denial: exhaustive and exclusive by construction). The presupposition is the chain state where the question emerged. The `kind: "interrogative"` marks this as a question. What inquisitive semantics lacks arrives as the record's step references: the trace that discovered which answers *differ in consequences*, and the `selection` + `resolved_by` pair naming how — and by what licensed act — the agent committed.

---

### 10. Proof Assistants (Martin-Löf 1972, Coq 1989, Agda 2007): Goal States as Alternatives to Close

**Pioneers:** Per Martin-Löf (1942–), *An Intuitionistic Theory of Types* (1972); Thierry Coquand & Gérard Huet, *Coq* (1989); Ulf Norell, *Agda* (2007).

**What it formalized:**
In proof assistants, the user doesn't write a proof top-down; they manipulate a **goal state**. The system shows:
```
goal 1: A → B
goal 2: B → C
...
```
Each **tactic** applies an inference rule, eliminating a goal or breaking it into sub-goals. The proof is **complete** when all goals are closed. This is a *proof search* — at each step, the prover can try multiple tactics, and the search space branches.

**What it got right:**
- Proof construction is **goal-directed** — work backwards from what you want to prove
- Sub-goals are *alternatives* at each step — which tactic to apply?
- The proof is an *ordered sequence* of choices (tactics), not a static formula
- Proof terms carry the computation, not just the logic

**What it missed:**
Proof assistants treat alternatives as a **computational device** for search, not a first-class semantic entity. Once a goal is closed, the alternative disappears from the record. There's no notion of *holding multiple proof paths in mind* or *revisiting earlier choices*.

**How we build on it:**
AlternativeSet models the **proof state** as a semantic object. The `alternatives` field is the set of possible next moves at this stage; the sequence of choices made so far *is* the chain of recorded steps the record indexes. Crucially, by embedding this in Arisbe's DAG, we preserve the **full search tree** — all alternatives tried, all branches taken. This enables *meta-learning* about proof search: which strategies worked? Which led to dead ends? This is absent in proof assistants, where only the successful proof is kept.

---

## Critical Mistakes to Avoid

Each tradition contains a pitfall that AlternativeSet must dodge:

### Mistake 1: Confuse Possible Worlds (Timeless) with Epistemic States (Dynamic)

**Source:** Classical modal logic (Kripke frames).

**The Error:** Treating alternatives as a fixed space. Once a Kripke frame is defined, its possible worlds don't change; we just evaluate formulas in different worlds.

**Lesson We Apply:** AlternativeSet is not timeless. It lives in a DAG — its alternatives *narrow and deepen through time* as reasoning unfolds. The chain of steps the record indexes tracks this evolution, making dynamics primary.

---

### Mistake 2: Separate What-the-Agent-Holds from Logical-Content

**Source:** Early doxastic logic (Hintikka).

**The Error:** Treating the agent's epistemic state as *separate* from the logical content. "Agent a believes φ" is modeled as a modal operator K(a, φ), not as *part of the proof system itself*.

**Lesson We Apply:** AlternativeSet embeds the agent's state *into the reasoning system*. The UoD carries not just the current EGI (the logical content) but also the alternatives being entertained (the agent's deliberative state). They are one entity, not two.

---

### Mistake 3: Make Choice Purely External

**Source:** Most formal systems (they have no notion of the deliberating agent's internal state).

**The Error:** Treating choice as something that happens *to* the system (the environment picks), not *by* the system (the agent decides). This loses agency — the distinction between "I decided" and "it happened to me."

**Lesson We Apply:** AlternativeSet distinguishes **internal choice** (the agent commits by a licensed act the record cites) from external pressure (the rule system transforms the EGI, narrowing what's logically possible). Both are recorded in the DAG, so the full causal story is preserved.

---

### Mistake 4: Lose the Purpose (Inquiry, Semiosis)

**Source:** Abstract model theory (where models exist independently of anyone reasoning with them).

**The Error:** Formalizing the structure of alternatives without asking *why* an agent holds them. What is the purpose? To resolve doubt? To find a proof? To make a decision?

**Lesson We Apply:** The `kind` field in AlternativeSet encodes purpose: "interrogative" (resolving a question), "hypothetical" (finding the best theory), "agentive" (choosing an action), etc. Semantics is tied to purpose, not divorced from it.

---

### Mistake 5: Ignore Temporality and Diachronicity

**Source:** Static formal systems (nearly all of them).

**The Error:** Modeling alternatives *at a moment*, not *through a history*. This loses the narrative — how did we get here? What alternatives were considered and rejected?

**Lesson We Apply:** AlternativeSet lives in Arisbe's transformation DAG. Every state preserves the alternatives and narrowing up to that point. This enables *diachronic* reasoning: "in state s3, agent x held alternatives {A, B}; by state s7, only {B} remained. Why?" The trace is preserved.

---

### Mistake 6: Treat Alternatives as Reducible to Classical Propositions

**Source:** Proof assistants, default logic, AGM revision.

**The Error:** Treating the set of alternatives as just another set of formulas, ignoring the *meta-level structure* (which ones are incompatible? which can coexist? which subsume others?).

**Lesson We Apply:** Alternatives in AlternativeSet are **semantic objects** (Ciardelli's inquisitive content, not just formulas). They can be inconsistent, overlapping, partially ordered by entailment. The structure of alternatives is what matters, not just their individual truth conditions.

---

## The Unification: AlternativeSet

The table below shows how AlternativeSet synthesizes all traditions:

| Tradition | What It Held | AlternativeRecord / register element | How We Use It |
|-----------|---|---|---|
| Peirce | Purpose (doubt, testing, abduction) | `kind: "interrogative"` + `materiality` | Semantics + fallibilism (discovered, never assumed) |
| Kripke | Formal set of alternatives | `alternatives` (validated EGIF propositions) | Core structure |
| Reiter | Revision when defaults fail | recorded challenge + the re-touched standing record (content key) | Hypothesis expansion |
| Hintikka | Agent's epistemic state | the `emerged_from` chain state + `alternatives` | Presupposition + possible answers |
| Gabbay | Context-scoped reasoning | `emerged_from` / `traced_by` / `resolved_by` step refs | Embedded in DAG labels |
| Milner | Internal vs external choice | licensed resolution (internal) + rule transformation (external) | Deliberation + reasoning |
| Gärdenfors | Evolution of beliefs | `status`: untraced → traced → resolved | Narrowing stages, each citing its step |
| Johnson-Laird | Multiple models held in mind | `alternatives` + bounded registers (`KyteProfile`) | Cognitive load made engineering |
| Ciardelli | Questions as semantic content | `alternatives` + `kind: "interrogative"` | Inquisitive semantics + dynamics |
| Proof Assistants | Goal-directed proof search | `alternatives` as next choices | Full proof tree preserved in DAG |

---

## What's Novel in Our Approach

Three contributions that don't exist in the literature alone:

### 1. Unification Across Modalities

**The novelty:** No prior work handles interrogative, modal, agentive, epistemic, metacognitive alternatives in one structure. The literature fragments these:
- Logic handles interrogatives (questions)
- Modal logic handles modal alternatives (possible worlds)
- AGM handles epistemic alternatives (belief revisions)
- Process algebra handles agentive alternatives (process choice)
- Cognitive science handles metacognitive alternatives (what I might think)

We unify them in a single structure (`kind` discriminates the type). An agent can hold *interrogative* alternatives (which answer is correct?) *while* deliberating an *agentive* choice (which action to take?). These are structurally isomorphic — both are sets of incompatible possibilities the agent hasn't yet committed to.

### 2. Embedding in Diachronic History

**The novelty:** Alternatives exist in the DAG (UniverseOfDiscourse), not in isolation. Every state has alternatives; every transformation narrows or re-opens them. The **lifecycle is traceable** — you can ask:
- "Which alternatives emerged at state s3?"
- "When was alternative A ruled out?"
- "Which states entertained both A and B before narrowing to B?"

This is absent in prior work. Kripke models are static. AGM revision is episodic (old state → new state, the intermediate deliberation is invisible). Proof assistants discard failed branches. Arisbe keeps the full **deliberative trace**.

### 3. Peircean Grounding with Formal Precision

**The novelty:** Peirce said inquiry is holding alternatives. But he had no *computable* formalization. We provide:
1. A **data structure** (`AlternativeRecord`, in a bounded content-keyed register) that encodes alternatives formally — as an *index over the reasoning record*, never a second authority
2. **Acts** that enact deliberation, each earned at record time: the consequence trace (a PEEL-twin chain step whose result recomputes forever), licensed resolution (an admission/discharge the record cites), settlement observed from the chain
3. **Semantics** tied to purpose (`kind` field — interrogative, modal, agentive, etc.)
4. **History preservation** — every choice is recorded in the DAG, and the whole register rebuilds from the chain alone
5. **A law** (AS1–AS4: the index resolves; the trace recomputes; resolution is licensed; the horizon is honest) with a boundary attestation hook — deliberation that cannot re-derive cannot stand

This completes Peirce's vision: **inquiry made operational**.

---

## Scope & Limits

What AlternativeSet does *not* claim:

- **Complete formalization of consciousness:** The structure of alternatives may be necessary for conscious deliberation, but it's not sufficient. Qualitative experience, unified awareness, subjective perspective — these remain open.
- **A metaphysics of free will:** AlternativeSet formalizes the structure of choice; it does not adjudicate the universe's causal texture. What it *does* support is a practical, compatibilist description (author's formulation, 2026-07-26): freedom as **the determined situation of considering and decision** — the interval between the conception of options (the branching at a point of doubt) and the agentic resolution among them in an action necessary *for this agent in its particular history*. "Uncaused, genuinely open" choice is not required and not assumed — openness is the genuine UNKNOWN plus the real branching the DAG records, and responsibility rides on the **accounting** (the earned, re-derivable record of the deliberation) and the **uniqueness** (the decision is indexed to this agent's own bounded registers and history). The deeper examination of this reading remains queued.
- **Solution to all reasoning problems:** AlternativeSet is a structure, not an algorithm. It doesn't tell you *which* alternative to select when multiple options are empirically equivalent.

What it *does* provide:

- **Formal vocabulary for deliberation:** Interrogative, hypothetical, modal, agentive, epistemic, metacognitive alternatives are now precisely defined.
- **Unifying framework:** Previously fragmented concepts (questions, possible worlds, belief revision, proof goals, mental models) are unified in one structure.
- **Computational substrate:** Arisbe's DAG realizes this structure. You can run deliberation, log it, query it, learn from it.
- **Foundation for inquiry, consciousness, agency:** As *continuous phenomena*. Not as binary properties ("conscious or not"), but as gradual specializations of a fundamental structure.

---

## Closing: The Arc Resolves

From Peirce's philosophical insight — **inquiry is holding alternatives** — through a century of formal logic fragments (Kripke's worlds, Hintikka's beliefs, Ciardelli's questions, proof assistants' goals), Arisbe arrives at unification. We have:

1. **Recovered Peirce's vision**, stripped of the psychology and formalized with precision
2. **Synthesized all the logic-family traditions** into one structure
3. **Made it computable** — deliberation is a sequence of immutable records indexing real, re-checkable steps in Arisbe's DAG
4. **Preserved diachronicity** — the full history of deliberation is kept, enabling meta-learning and retrospection
5. **Grounded consciousness, free will, and agency** in a formal structure that can be reasoned about

The reduction theorem that emerges is simple: **Everything reduces to holding and testing alternatives.** Whether you're solving a logic puzzle, deciding where to go for lunch, imagining counterfactuals, or reasoning about your own reasoning, the underlying structure is the same. AlternativeSet is that structure. Arisbe is its realization.

---

## From Held Evidence to Indexed Evidence (the 2026-07-26 re-housing)

This document's first draft (2026-07-25) described an implementation in which the
AlternativeSet *held* its own evidence: a `warrant` float carried assurance, a
`selection_path` list carried history, and methods on the dataclass
(`narrow_to()`, `select()`, `deepen()`, `remerge_with()`) enacted the lifecycle.
**Examination V** (ADVERSARIAL_EXAMINATION §V, four independent panels) found
that shape unsound while affirming the philosophy above: the warrant float
corrupted the repo's doctrinal vocabulary (assurance granted on mere agreement,
never challenge); a scalar collapsed distinct epistemic situations; the
lifecycle methods silently wiped evidence at the moment of commitment; and the
structure was the one overlay in the codebase with no law, no attestation hook,
and no path into the reasoning record.

The **index-over-ink re-housing** (spec 2026-07-26, built and merged the same
day) resolved this by making the record *point instead of hold*: every
evidentiary claim is a reference to a real chain step — the peel that surfaced
the question (`emerged_from`), the trace that discovered its materiality
(`traced_by`, an identity-transform step whose result the standing gate
recomputes forever), the licensed act that resolved it (`resolved_by`). The
register of open questions is a bounded cache over the chain, rebuildable from
it; the AS1–AS4 law with its attestation hook makes a record that cannot
re-derive impossible to persist; and assurance vocabulary returned to the
doctrinal gradient where it lives. Nothing in the intellectual arc above had to
change — which is the point. The traditions were right about *what deliberation
is*; the correction was about *where its evidence must live*: in the reasoning
record, earned, or nowhere.

---

## Sourcing & Citations

### Classic Foundational

- **Peirce, C. S.** (1877). "Illustrations of the Logic of Science," *Popular Science Monthly* 12–13. https://www.commens.org/
  - Introduces the triadic sign and abduction as inference to the best explanation. Essential for understanding inquiry as testing hypotheses.

- **Peirce, C. S.** (1903). *Lectures on Pragmatism*, Lecture IV. https://www.commens.org/
  - Explicit treatment of doubt as the engine of reasoning. "We must not begin by doubting everything, but by doubting those things about which doubt is really necessary" (Principle of Kant's, adopted by Peirce).

- **Kripke, S. A.** (1972). *Naming and Necessity*. Harvard University Press.
  - Foundational for possible-worlds semantics. Establishes that modality is relative to accessibility relations between worlds.

- **Lewis, D.** (1973). *Counterfactuals*. Harvard University Press.
  - Semantics of counterfactuals as truth in nearby possible worlds. Critical for understanding how alternatives are ordered by similarity.

### Modern Logic

- **Ciardelli, I., Groenendijk, J., & Roelofsen, F.** (2012). "Inquisitive Semantics and a New Notion of Entailment," *The Philosophical Review* 122.2: 517–563. https://doi.org/10.1215/00318108-1595446
  - Makes questions semantic objects. Shows how inquisitive content (sets of possible answers) can be integrated into classical logic. Foundational for treating alternatives as formal content.

- **Hintikka, J.** (1962). *Knowledge and Belief: An Introduction to the Logic of the Two Notions*. Cornell University Press.
  - Introduces doxastic logic: what you know is true in all your knowledge-worlds. Establishes that epistemic states are model-theoretic, not syntactic.

- **Gabbay, D. M.** (1996). *Labelled Deductive Systems, Volume 1*. Oxford University Press.
  - Systematic treatment of how to label formulas with context (time, agent, world, etc.). Shows that labels can be manipulated by rules, making context structural.

### Cognitive Science

- **Johnson-Laird, P. N.** (1983). *Mental Models: Towards a Cognitive Science of Language, Inference, and Consciousness*. Harvard University Press.
  - People reason by constructing and manipulating mental models. Models are alternatives; inference is model elimination. Bridges cognitive and formal approaches.

- **Stanovich, K. E., & West, R. F.** (2000). "Individual Differences in Reasoning: Implications for the Rationality Debate?" *Behavioral and Brain Sciences* 23.5: 645–665. https://doi.org/10.1017/S0140525X00003435
  - Shows that people systematically fail at formal reasoning, but their "failures" are often rational responses to holding multiple competing models or interpretations.

### Computer Science & Formal Methods

- **Milner, R.** (1980). *A Calculus of Communicating Systems*. Springer-Verlag.
  - Process algebra as a foundation for concurrent systems. Introduces internal choice (+) and input-driven external choice (?). Distinctions essential for agent deliberation.

- **Milner, R., Parrow, J., & Walker, D.** (1992). "A Calculus of Mobile Processes, I & II," *Information and Computation* 100.1: 1–77. https://doi.org/10.1016/0890-5401(92)90008-4
  - The π-calculus: process algebra for systems with mobility and dynamic process creation. Shows how agents (as processes) can create new alternatives.

- **Gärdenfors, P.** (1988). *Knowledge in Flux: Modeling the Dynamics of Epistemic States*. The MIT Press.
  - Foundational for AGM (Alchourrón–Gärdenfors–Makinson) belief revision. Shows how to rationally update belief sets when new information arrives. Entrenchment captures which beliefs are harder to abandon.

- **Alchourrón, C. E., Gärdenfors, P., & Makinson, D.** (1985). "On the Logic of Theory Change: Partial Meet Contraction and Revision Functions," *The Journal of Symbolic Logic* 50.2: 510–530. https://doi.org/10.2307/2274239
  - Axiomatization of belief revision. Shows that revision is not arbitrary but obeys rational principles (consistency, minimality, etc.).

### Proof Assistants

- **Martin-Löf, P.** (1972). "An Intuitionistic Theory of Types: Predicative Part," *Studies in Logic and the Foundations of Mathematics* 80: 73–118. https://doi.org/10.1016/S0049-237X(08)70713-3
  - Intuitionistic type theory. Types as propositions; proofs as witnesses. Establishes that proof construction is goal-directed.

- **Coquand, T., & Huet, G.** (1989). "Constructions: A Higher Order Proof System for Mechanizing Mathematics," *European Conference on the Theory and Practice of Software Development*, 151–183. Springer.
  - The Coq proof assistant: shows how tactics manipulate goal states to guide proof search. Proof is a sequence of choices (which tactic to apply).

- **Norell, U.** (2007). *Towards a Practical Programming Language Based on Dependent Types*. PhD thesis, Chalmers University of Technology.
  - Agda: extends Coq with dependent types and pattern matching. Demonstrates that proof search is a *structured exploration of alternatives*.

### Philosophical Foundations

- **Rawls, J.** (1971). *A Theory of Justice*. Harvard University Press.
  - Reflective equilibrium as a method for moral reasoning: hold principles and convictions, test them against each other, narrow and revise until equilibrium. AlternativeSet models this structure for *any* domain of deliberation, not just ethics.

- **Fricker, M.** (2007). *Epistemic Injustice: Power and the Ethics of Knowing*. Oxford University Press.
  - Uptake as a social precondition for knowledge. An agent's alternatives must be *recognized* by others to count as knowledge. Unfinished agenda for Arisbe.

- **Dennett, D. C.** (1991). *Consciousness Explained*. Little, Brown.
  - Consciousness as parallel processing with a "user illusion" of unity. Suggests consciousness emerges from the brain holding and comparing multiple competing narratives (alternative interpretations).

---

## Unfinished: The Action Arm

This document traces how AlternativeSet unifies *representational* traditions (logic, model theory, cognitive science). One tradition remains unintegrated: **action theory**. Peirce distinguished between doubt-driven *semiosis* (the sign-relation) and *action* (the organism responding to the sign). Arisbe has no formalized action arm yet.

The agenda:
1. Extend AlternativeSet to agentive alternatives that are not just deliberated but *executed*
2. Add a feedback loop: action → outcome → new alternatives → deliberation
3. Model *agency* as the capacity to hold alternatives *before* committing to action

This remains open for future work.

---

**AlternativeSet.** The structure of deliberation. The unity underlying Peirce, Kripke, Ciardelli, cognitive science, proof assistants. The foundation of inquiry, consciousness, and free will made computational.
