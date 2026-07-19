# Arisbe — Contribution & Prior Art

> **What this is.** An honest assessment of what Arisbe genuinely contributes to its field, measured
> against the connected literature and existing software — written to *distinguish real contribution
> from faithful re-implementation*, not to flatter the project. Based on three adversarial
> web-research sweeps (2026-06-27): the [EG](GLOSSARY.md#eg)-software landscape, the formal/theoretical claims, and the
> [endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in)/iconicity claims. Every claim below traces to a cited source; where evidence was
> "not found" rather than "proven absent," that is stated.
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) · [CAPABILITY_MAP.md](CAPABILITY_MAP.md).
>
> *Consolidated: 2026-06-27.*

---

## The honest headline

Arisbe makes a **genuine contribution, but it is an engineering / operationalization / integration
contribution, not a new theoretical result.** In nearly every case the underlying logical or
structural fact is *established literature that must be cited*; the defensible novelty is that Arisbe
builds a *working, calculus-faithful system* doing what the literature had described only as theory or
noted only as a static correspondence.

One element stands out as having **no prior art found anywhere** in the surveyed literature or
competing tools: **the linear↔graphical correspondence treated as a continuously runtime-attested
invariant over a live, editable EG system.** That is the strongest basis for an originality claim.

Two places carry real **over-claim risk** and should always be stated with their prior art:
the EG≅Discourse Representation Structure ([DRS](GLOSSARY.md#drs)) isomorphism (textbook Sowa) and "Gamma is unnecessary" (cuts *against* active scholarship
that values Gamma).

---

## Claim-by-claim verdicts

Verdicts use four levels: **NOVEL** (no prior art, new idea) · **OPERATIONALIZED** (known idea, but
Arisbe appears to be the first *working system* to realize it) · **ESTABLISHED** (no real novelty;
must cite) · **CANNOT DETERMINE**.

| # | Claim | Verdict | The prior art it must credit |
|---|---|---|---|
| 1 | Interactive editor enforcing **Dau's full six-rule Beta calculus** | **OPERATIONALIZED** | Interactive EG provers exist but are **Alpha-only** (Peirce-My-Heart, RAIR Lab) or unmaintained (UAH editor). Beta + full Dau rules in a maintained interactive tool appears *unoccupied*. |
| 2 | **Linear↔graphical correspondence as a runtime-attested invariant** | **OPERATIONALIZED → strongest claim** | The *faithfulness concern* is established (heterogeneous reasoning — Barwise & Etchemendy, Shin, Hammer; "free rides" — Shimojima, Stapleton). Runtime invariant-checking is generic. The *combination* — picture↔proposition as a per-operation runtime monitor in a live EG system — **no prior art found.** |
| 3 | **Four-way linear round-trip** (Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif))/Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif))/Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif))/First-Order Predicate Logic ([FOPL](GLOSSARY.md#fopl))) bound to one drawn object | **OPERATIONALIZED** | The notations + their mappings are **Sowa's design + ISO/IEC 24707 Common Logic** — *not* Arisbe's. Binding all four to one drawn EG under a checked invariant is the new part, not the formats. |
| 4 | **"A DRS is a Beta EG"; the EG↔DRT bridge operationalized** | **OPERATIONALIZED (high overclaim risk)** | The isomorphism is **explicitly Sowa's** ("DRS … isomorphic to Peirce's existential graphs"), tracing to Kamp 1981 — *must be cited, never claimed*. The novel part is narrow: the **Centering/focus-stack scorer** aligning EG transforms with Discourse Representation Theory ([DRT](GLOSSARY.md#drt)) discourse updates (no prior art found). |
| 5 | **Modality without Gamma; the diachronic directed acyclic graph ([DAG](GLOSSARY.md#dag)) is the drawn Kripke frame** | **OPERATIONALIZED (caveat)** | "□/◇ → quantifiers over an accessibility relation" is the **standard translation** (van Benthem); Gamma ≅ S4/S5 is **Zeman (1964)**; sheets-as-worlds is widely read into Peirce. "No modal mark needed" runs *against* Ma & Pietarinen, who defend Gamma's diagrammatic advantages. Only the *history-DAG-as-drawn-frame* framing is original. |
| 6 | **The Endoporeutic Game as an operational model-checking engine** | **OPERATIONALIZED** | Endoporeutic-as-game is **Hilpinen (1982)** + **Hintikka GTS (1973)** + **Pietarinen, _Signs of Logic_ (2006)** — including the outside-in [peel](GLOSSARY.md#peel) (reading it from the outside in against the model) and the "lazy, SQL-like" evaluation analogy. 3-valued model-checking with witnesses + minimax are standard. The *running implementation* as an EG evaluator appears new. |
| 7 | **"Logic in pictures, not pictures of logic" / iconicity** | **ESTABLISHED (as philosophy)** | A paraphrase of **Stjernfelt's operational iconicity** and Peirce's "moving pictures of thought" (Shin 2002; Bellucci & Pietarinen). The *banner* is not novel; the *engineering that realizes it* is where any contribution lives. |

---

## The genuine contributions, ranked

1. **The runtime-attested linear↔graphical correspondence invariant.** The most defensible original
   element. The literature treats diagram↔symbol faithfulness as a *theorem proved once about a
   calculus*; Arisbe treats it as a *live monitor on an editable system's every state* — and no
   surveyed tool or paper does this. This is the project's signature.

2. **Beta-complete, Dau-faithful, interactive EG environment.** The only actively-maintained
   interactive EG prover found (Peirce-My-Heart) is Alpha-only; Beta (lines of identity / FOL) with
   the full six-rule calculus, enforced by construction, fills an apparently empty niche.

3. **An integrated reason + evaluate + corpus + import environment under one correspondence-attested
   roof.** Individually, each piece connects to an existing thread; the *integration* — proof,
   semantic-game evaluation, a provenanced corpus, and ontology/NL import all sharing one EG-native,
   attested representation — is unusual and is itself the contribution.

4. **The diagram↔narration scorer** (Centering + focus-stack alignment of EG transforms with DRT
   updates) and **the diachronic-DAG-as-drawn-Kripke-frame** framing — two narrower pieces with no
   prior art found, riding on established theory (Sowa's isomorphism; the standard translation).

5. **The first running implementation of the endoporeutic evaluation game** (outside-in peel +
   3-valued open-world verdict + witness/counterexample + automated minimax opponent).

---

## Where to be careful (over-claim ledger)

- **EG≅DRS is Sowa's, not ours.** Always cite Sowa (*From Existential Graphs to Conceptual Graphs*)
  and Kamp 1981. Our contribution is the *scorer*, not the isomorphism.
- **The linear notations are Sowa + ISO Common Logic.** We implement and bind them; we did not invent
  EGIF/CGIF/CLIF.
- **"Gamma is unnecessary" is contrarian, and the broken cut has been rehabilitated.** Ma & Pietarinen
  (*Gamma graph calculi for modal logics*, Synthese 2018) give *sound and complete* graphical broken-cut
  calculi for fifteen normal modal logics — Peirce's own apparatus, "only (DMN), (B), (5) new" — and name
  diagrammatic advantages the standard translation discards (position/polarity read off cut topology; no
  negation normal form; the ambient sheet absorbing structural bookkeeping). So the claim must be worded
  **"no modal *mark* needed for Arisbe's architecture," not "Gamma is dispensable for logic."** The full
  honest accounting — what the no-Gamma stance genuinely forgoes (second-order + metalinguistic content;
  perspicuity/decidability) versus what is only perspicuity cost — is in
  [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) ("What not using Gamma costs" + "What Gamma keeps").
- **"Interactive EG editor" and "soundness by construction" are baselines, not differentiators.**
  Prior tools already claim them; our differentiator is *Beta + Dau + the invariant + breadth*.
- **The banner ("moving pictures of thought") is Peirce/Stjernfelt/Pietarinen.** Rhetorically apt,
  not a contribution.

---

## Gaps in the field Arisbe is positioned to fill

- **No machine-checked (Coq/Lean/Isabelle) formalization of Dau's EG calculus was found.** Arisbe's
  ~1000-test executable spec + the runtime attestation are not a machine-checked proof, but they are
  the closest *operational* guarantor located. A formal mechanization would be a clear field
  contribution — and a natural future direction.
- **Dau is the de-facto standard *for software* but not uncontested in philosophy** (SEP surveys
  Zeman/Roberts/Shin and omits Dau). Arisbe choosing Dau as bedrock is defensible and arguably the
  right engineering call, but the project should not present Dau as universally "the" formalization.
- **Description Logic ([DL](GLOSSARY.md#dl))/Web Ontology Language ([OWL](GLOSSARY.md#owl))-as-diagrams already exists** (a sound-complete diagrammatic system for ALC; Graphol ≈ OWL 2).
  Arisbe's EG-native subsumption-by-freeze-a-witness is a reasonable extension, not a new bridge.
- **No system was found that plays an *automated* role-based dialogue game to build a knowledge
  model from scratch under a *sound* referee.** A 2026-06-30 deep-research pass (25 verified
  claims, 0 refuted) found every neighbour holds at most two of {multi-agent role dialogue,
  build-from-scratch, sound formal referee}: dialogue/debate systems (Black & Hunter inquiry
  dialogues, PARMA, AI-safety-via-debate, Du et al., SPAG, CAMEL, DeepMind oversight) have roles
  but offload truth to participants / human / weak-LLM judges; belief-revision + ILP (AGM-for-Dung,
  ILASP/CDILP, AutoSpec) and FunSearch have a sound engine but are single-agent / single-proposer.
  Arisbe's **automated Endoporeutic Game** (Graphist/Grapheus/Agonothetes under the §3.3-attested
  peel, with the correspondence-not-truth floor) is positioned in that empty intersection — see
  [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md) §8. (Threads 5–6 — automated
  science, LLM ontology construction — were not exhaustively verified; read as *"none among the
  verified set."*)

---

## Concordances — the neighboring programs

*(Added 2026-07-17, from the whole-of-Arisbe step-back. These are **concordances** — programs
that arrived at structurally similar answers from independent starting points — not lineage
claims and not prior art in the verdict-table sense: Arisbe did not derive from them, and none
of them anticipates the correspondence invariant. They are recorded because each one names, in
its own vocabulary, a part of what Arisbe builds — and because the differences are as
instructive as the agreements. The design consequences live in
[BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md](BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md).)*

- **Pragmatist inquiry (Peirce, *The Fixation of Belief*; Dewey's reflex arc and pattern
  of inquiry).** The ground, not a neighbor: *The Fixation of Belief* (1877) is the engine
  itself — inquiry driven by the **irritation of doubt** (a state of friction that disrupts
  action), ending not in abstract truth but in a settled *habit of action* — and doubt →
  inquiry → settled belief is the loop the automated game mechanizes. Dewey contributes
  twice: *The Reflex Arc Concept in Psychology* (1896) dismantled the linear
  stimulus–response picture in favor of a **continuous perception–action loop** — actions
  dictate what stimuli are received, and the current internal state dictates how they are
  interpreted — the circuit the directed-engagement design closes; his later
  "indeterminate situation" (*Logic*, 1938) is the membrane's raw deliverance before it
  becomes a legible proposal. Stated here so the newer concordances below are read as
  *corroborations of a Peircean design*, not as its sources.

- **Neo-pragmatism (Rorty, *Philosophy and the Mirror of Nature*; *Consequences of
  Pragmatism*; *Contingency, Irony, and Solidarity*).** The most philosophically pointed
  concordance, because it cuts *both ways* — and because Rorty himself had little use for
  Peirce (in *Consequences of Pragmatism* he credits Peirce chiefly with naming pragmatism
  and stimulating James), so this is concordance of discipline, not lineage. Where Arisbe
  agrees with Rorty: the **correspondence-not-truth floor** is anti-representationalism in
  practice — the §3.3 invariant attests a correspondence between two of *our own* signs (the
  drawn and the written form), never between sign and world, declining the Mirror of Nature
  exactly where Rorty says it must be declined; **"progression, not progress"** and the
  dissolved terminus (Departure I in
  [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md)) side with Rorty *against
  Peirce's own* Final-Opinion convergence — the game is scored against no summit; and the
  **ironist's** "radical and continuing doubts about the final vocabulary she is using" is
  the validity discipline made syntax: M — the system's working vocabulary about its world —
  resides only inside cuts, never asserted at the sheet level, so irony is an *invariant the
  gate checks*, not a temperament the inquirer must sustain. Where Arisbe departs from
  Rorty, both departures instructive: (i) the Fidelity examinations **concede the
  mind-independent comparative efficacy-vector** (structural realism — "a genuinely better
  instrument" is an ordinal fact the world settles, not merely better-by-our-lights), which
  Rorty would refuse; and (ii) where Rorty deflates justification to conversation — solidarity
  without a tribunal beyond one's peers — Arisbe keeps a **sound mechanical referee**: the
  Endoporeutic Game is conversation *with an incorruptible referee*, a middle position
  Rorty's dichotomy of solidarity-or-objectivity does not name — solidarity supplies the
  warrant (in-context competence), the calculus supplies validity, and neither is asked to
  do the other's work.

- **Predictive processing / active inference (Helmholtz; Friston; Clark, *Surfing
  Uncertainty*; Seth).** The closest formal neighbor, with the deepest root: Helmholtz's
  **unconscious inference** (1860s) — perception as the brain *predicting* what the senses
  will report and processing only the difference — is the ancestor Friston's free-energy
  principle (2006–) formalizes: free energy ≈ surprisal ≈ *doubt*, minimized either by
  updating the model (perceptual inference) or by acting on the world (active inference).
  The interpretant functioning as a *prediction*, doubt as
  *prediction error*, and model revision as error-minimization is this literature's core loop —
  and Arisbe's resolving membrane (forecast recorded before the outcome; the
  `PredictionLedger`) implements the perception half of it. The Markov blanket and Arisbe's
  *membrane* are independent coinages doing the same job: the boundary across which a model
  meets what it models. Precision-weighting has a discrete cousin in the warrant gradient.
  The honest differences: Arisbe's updates are **recorded, warranted, rule-licensed steps**
  — a chain a reader can inspect — where free-energy minimization is a gradient flow that
  keeps no such record; and Arisbe's three-valued verdict distinguishes *abstention* (Kleene
  UNKNOWN, open-world) from *error*, a distinction a scalar surprisal collapses. What the
  neighbor has that Arisbe lacks: the **action arm** (acting on the world to reduce expected
  error), which is Arisbe's named, unbuilt "directed engagement."

- **Cybernetics (Wiener; W. R. Ashby; Conant & Ashby).** Wiener (1948) made the feedback
  loop — error correction — the general mechanism of biological and machine intelligence;
  Ashby's **Homeostat** (1948; *Design for a Brain*, 1952) was the first *physical*
  implementation of remodeling driven by environmental friction: when its variables were
  pushed out of bounds (its doubt), it re-randomized its own internal wiring until a
  configuration restored equilibrium — **ultrastability**, the mechanical bootstrap. The
  good-regulator theorem (Conant & Ashby 1970) — "every good regulator of a system must be
  a model of that system" — is the one-line *external* justification for M's existence:
  anything that is to cope with a world must carry a model of it. And the law of requisite
  variety explains a design fact Arisbe reached empirically: disuse-decay bounds M's
  variety to the *engaged* world-slice, because a model's variety need only match the
  variety of what it actually regulates, not of the archive.

- **Cellular automata (Conway's Game of Life).** The concordance that shaped the automated
  loop's design directly, and the one whose *differences* are doctrine — the full analysis is
  [AUTOMATED_MODEL_DEVELOPMENT.md](AUTOMATED_MODEL_DEVELOPMENT.md) §1, and this entry only
  summarizes it. The analogy survives "at the level of *structure*: simple repeated step →
  iterated over generations → emergent global behaviour nobody scripted." The instructive
  breaks: a generation is a **round of the game**, and "its outcomes are **negotiable**, not
  determined" — the rule that fires is a disposition chosen by agents, not a neighbour-count;
  Life's *death* (its whole character) has no analogue in monotone materialization
  ("growth-to-saturation is not emergence; it's closure") and reappears as **relinquishment
  and disuse-decay**; and "the decisive structural difference is the plane" — Life's plane is
  **bounded** and its boundary shapes the emergence, while the sheet of assertion is
  **unbounded**, so the bounding force must be **selection from outside**, which is why the
  membrane is the crux. In short: Life is a closed determinism bounded by its edge; the Agon
  loop is an open negotiation bounded by the world. (Whether Life itself is worth encoding as
  a closed CA-in-EG demo is a named backlog item there.)

- **Scaling science (Geoffrey West, *Scale*; Kleiber; Bettencourt).** The author's
  pointer, and the one that makes the fractal reading *quantitative*: West's program
  analyses systems that aggregate, interact, and distribute resources through
  space-filling hierarchical networks, and finds discoverable **scaling exponents**
  (quarter-power metabolic laws; cities superlinear in innovation, companies sublinear
  and mortal). The mapping: deliverance throughput is the system's metabolism, the
  membrane hierarchy its distribution network, decay its cellular turnover — so the
  measure's components should themselves *scale lawfully*, and the exponents are
  empirical questions the run corpus can already ask (how do derived atoms scale with
  explicit atoms — K3's exponent; how does question-yield scale with |M|). The most
  striking correspondence: West's **companies die, cities don't** — bounded closed
  systems scale sublinearly toward stagnation while open-networked ones scale
  superlinearly — is the halting-duals thesis with fifty years of data behind it: a
  closed Arisbe crystallizes or evaporates; an open-membraned one with growing sensor
  and action spaces is city-shaped. The honest differentiator: West's laws emerge from
  energy optimization under physical network constraints; whether *semiotic* networks
  obey analogous constraints is a conjecture Arisbe is positioned to test, not assume.

- **Reinforcement learning & artificial curiosity (Sutton's temporal-difference learning;
  Schmidhuber; Oudeyer & Kaplan).** The machine-learning face of the same loop. The **TD
  error** — the delta between expected and experienced — is the doubt-delta exactly, and
  its fixed point is Peircean: **when the TD error is zero the agent stops learning, which
  is Peirce's settled belief** (a habit no longer irritated). Schmidhuber's artificial
  curiosity inverts the drive: reward = **compression progress**, so the agent *seeks out*
  what it cannot yet predict in order to resolve it — doubt-seeking, not merely
  doubt-resolving, which is what Arisbe's musement pole and docket of doubts implement in
  recorded form. The honest differences: RL's learning signal is a scalar folded into
  weights, where Arisbe's is a *disposition with a recorded mode and derivation*; and the
  curiosity literature's own hard lesson — target learning *progress*, never raw error,
  else the noisy TV captures the agent — is adopted as a standing guard in the
  directed-engagement design.

- **Evolutionary epistemology / falsificationism (Popper; Campbell's blind-variation-and-
  selective-retention; Lakatos's research programmes).** Popper is already cited elsewhere in
  this book; the finer concordance is Campbell's schema mapped onto the loop — proposer =
  variation, peel = selection, decay = the bound on retention — and Lakatos mapped onto the
  *development practice*: the run logs' pre-registered priors and disposed findings
  (the `Pⁿ`/`Fⁿ` discipline of the run logs under `runs/`) are a research-programme record in
  Lakatos's sense, kept mechanically honest. The difference to state: selection in Arisbe is
  by a *sound referee* over a recorded game, not by survival alone.

- **Biosemiotics / enaction (von Uexküll's Umwelt and functional circle; Hoffmeyer;
  Maturana & Varela's autopoiesis and structural coupling).** The Peirce-*native* bridge —
  biosemiotics is itself built on Peirce's sign theory, so the vocabulary transfers with
  least distortion. The vocabulary-bounded horizon ("enough of M = what the proposal
  touches," [DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md)) is an Umwelt: the world *as
  addressable by this organism's sign-repertoire*, with an honest horizon beyond it.
  Uexküll's functional circle (perceive → act → perceive) is exactly the circuit that
  closes only when directed engagement is built; until then Arisbe has the perception arc
  of the circle, not the action arc. Structural coupling names what a long-running live
  membrane would become: model and source shaping each other's history.

- **Belief revision & reason maintenance (AGM; Doyle's TMS; de Kleer's ATMS).** The
  disposition taxonomy is Arisbe's answer to the problem AGM axiomatizes — how a rational
  corpus absorbs a contradiction — with the difference that Arisbe's revisions are
  *syntactic, drawn, and derivation-carrying* (each one a licensed rule application with its
  recorded act) rather than postulate-constrained set operations. A transformation chain
  whose steps carry their derivations is a truth-maintenance system whose justifications are
  **sound rules**, not mere dependency links — the same relation to a TMS that the
  [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) comparison table records for Git and Datomic:
  the commit already validates.

*Confidence note: the mappings above are the project's own readings (2026-07-17, assistant-
drafted, author-reviewed), made at the level of structural role — no claim is made that any
of these programs influenced Arisbe's design or vice versa.*

---

## From concordance to measure — knowledge quantified

*(Graduated from the design-of-record 2026-07-19, by the author's ruling; drafted by the
assistant from the author's seeds and ratified 2026-07-17/19. Everything below is
checkable against running instruments — the section makes no claim an instrument cannot
compute.)*

The concordances above converge on one operational definition, seeded by the author's
own earlier formulation — *"knowledge exists when someone reliably does something
(thinks, speaks, acts) that works"* — revised into Arisbe's vocabulary as: **knowledge
is the resident content of a model M whose habits reliably mediate its membrane's
deliverances, always indexed to the horizon within which the record was earned.** It is
quantified as a four-component vector, each component with a running instrument:

- **K1 — severity-weighted track record**: reliable success on tests that could have
  refuted (`PredictionLedger` × the attention economy's severity term). The worked case:
  Fermat's conjecture, five confirmations deep, was never knowledge — it had not been
  tested where it could fail, and at F5 it died (the rung-1 exemplar, Euler 1732
  recapitulated by attention in six rounds).
- **K2 — durability** under continued revision pressure (the meta-learning stick-rates,
  decay-aware) — with a **modal reading** off the branching history: K2□ (durable on
  every reachable trajectory) vs K2◇ (durable on some), computed by
  `modal_query.durability_modality`.
- **K3 — compression**: how much of the deliverance stream the laws derive
  (`model_materialization.materialization_ratio`, with unevaluable laws weighing the
  denominator — no credit without evaluable evidence).
- **K4 — use**: the habit exercised (atom-level disuse-decay — the operational form of
  "knowledge exists only while it works").

Three guards are part of the measure's definition, not afterthoughts: **never truth**
(the record self-certifies warranted reliability in context — the same posture as the
correspondence invariant, which attests correspondence, not truth); **never a target**
(a knowledge-score optimized directly Goodharts; it is an instrument); and **never a
scalar over agents** (the components stay a vector over knowledge-items and models —
an aggregate ranking of *inquirers* would rebuild the worth-ladder the project's
Fidelity examinations dissolved; competence ≠ worth is a category-fact).

The measure is **scale-transportable**, which cashes out the author's observation that
knowledge has a fractal structure: the same doubt → test → dispose → decay cycle runs
at the level of the atom, the law, the model, the mechanism (knowledge about
knowledge-formation, with its own stick-rates), and the project itself (the
pre-registered-priors run discipline) — one ledger shape at every scale, with the drawn
syntax mirroring it (cuts within cuts, cells within the world-scroll, quotation ovals
within cells) and the conservativity gate guaranteeing no level corrupts the one
beneath. The recursion runs *inside* a single evaluation too (the endoporeutic game
plays sub-games at every nested context), *across time* (the history's branches are
parallel chains of the same cycle), and — prospectively — *socially* (communities of
such systems modeling each other). A recursion with a floor and a discipline, which
natural fractals lack.

---

## Does Arisbe materially improve the field?

**Yes — modestly and specifically, as a systems/operationalization contribution, not as new logic.**
It is of genuine interest because it occupies a niche the surveyed landscape leaves empty: a
maintained, Beta-complete, Dau-faithful, interactive EG environment whose distinguishing idea — the
continuously-attested correspondence between the drawn and written forms — has no located prior art.
Its broader value is making a cluster of established theory (the EG≅DRS bridge, the endoporeutic
game, the modal standard translation, operational iconicity) *actually runnable and inspectable* in
one place. The honest framing for any external write-up: **"we did not invent these ideas; we built
the first system that makes them hold together, faithfully and checkably, in working software"** —
with the correspondence invariant as the one place a stronger originality claim is warranted.

---

## Sources (selected)

**EG software & formalization:** Peirce-My-Heart (RAIR Lab, RPI) · UAH Web-Based EG Editor (Bowen et
al. 2016) · CharGer (Delugach) · Dau, *Mathematical Logic with Diagrams* (habilitation, dr-dau.net) ·
SEP, *Peirce's Deductive Logic* (Zeman/Roberts/Shin) · Wikipedia, *Existential graph*.
**Heterogeneous / diagrammatic reasoning:** Barwise & Etchemendy, *Hyperproof* · SEP, *Diagrams* ·
Blake, Stapleton et al., *Free Rides & Observational Advantages* (JoLLI 2021).
**EG↔DRT:** Sowa, *From Existential Graphs to Conceptual Graphs* & *Peirce's Tutorial on EGs* · Kamp &
Reyle, *From Discourse to Logic* · SEP, *Discourse Representation Theory*.
**Modality:** van Benthem (standard translation; modal = bisimulation-invariant fragment of FOL) ·
Zeman (1964, Gamma ≅ S4/S5) · Ma & Pietarinen, *Gamma graph calculi for modal logics* (Synthese 195(8),
2018; open companion EPTCS 243, 2017) — sound-complete broken-cut calculi for 15 modal logics; the
diagrammatic advantages; "only (DMN), (B), (5) new." See [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md).
**Endoporeutic / games:** Hilpinen (1982) · Hintikka (1973, GTS) · Pietarinen, *Signs of Logic* (2006)
& Commens "The Endoporeutic Method".
**Iconicity:** Stjernfelt, *Diagrammatology* / operational iconicity · Shin, *The Iconic Logic of
Peirce's Graphs* (2002) · Bellucci & Pietarinen, *Two Dogmas of Diagrammatic Reasoning*.
**Concordances (added 2026-07-17):** Peirce, *The Fixation of Belief* (1877) & *Note on the
Theory of the Economy of Research* (1879) · Dewey, *Logic: The Theory of Inquiry* (1938) ·
Dewey, *The Reflex Arc Concept in Psychology* (1896) ·
Rorty, *Philosophy and the Mirror of Nature* (1979), *Consequences of Pragmatism* (1982) &
*Contingency, Irony, and Solidarity* (1989); also *Solidarity or Objectivity?* (1985) ·
Helmholtz, *Treatise on Physiological Optics* (1860s, unconscious inference) ·
Wiener, *Cybernetics* (1948) · Ashby, *Design for a Brain* (1952, the Homeostat) ·
Sutton, *Learning to Predict by the Methods of Temporal Differences* (Mach. Learn. 1988) ·
Friston, *The free-energy principle* (Nat. Rev. Neurosci. 2010) · Clark, *Surfing Uncertainty*
(2016) · Conant & Ashby, *Every good regulator of a system must be a model of that system*
(Int. J. Systems Science 1970) · Ashby, *An Introduction to Cybernetics* (1956) · Gardner,
*The fantastic combinations of John Conway's new solitaire game "life"* (Sci. Am. 1970) ·
Campbell, *Evolutionary Epistemology* (1974) · Lakatos, *The Methodology of Scientific
Research Programmes* · von Uexküll, *A Foray into the Worlds of Animals and Humans* (1934) ·
Hoffmeyer, *Biosemiotics* (2008) · Maturana & Varela, *Autopoiesis and Cognition* (1980) ·
Alchourrón, Gärdenfors & Makinson, *On the logic of theory change* (JSL 1985) · Doyle, *A
Truth Maintenance System* (AIJ 1979) · de Kleer, *An Assumption-based TMS* (AIJ 1986) ·
West, *Scale* (2017) · Bettencourt et al., *Growth, innovation, scaling, and the pace of life in cities* (PNAS 2007) · Schmidhuber, *Formal Theory of Creativity, Fun, and Intrinsic Motivation* (2010) · Oudeyer &
Kaplan, *What is intrinsic motivation?* (2007).

*Confidence note: "no prior art found" means absence in a focused web survey, not proof of
nonexistence — particularly for unpublished or obscure tools. Treat the originality claims as
"best available evidence," not certainty.*
