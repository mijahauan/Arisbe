# Arisbe — Contribution & Prior Art

> **What this is.** An honest assessment of what Arisbe genuinely contributes to its field, measured
> against the connected literature and existing software. It aims to *distinguish real contribution
> from faithful re-implementation*, not to flatter the project. Three adversarial
> web-research sweeps (2026-06-27) stand behind it: the [EG](GLOSSARY.md#eg)-software landscape, the formal/theoretical claims, and the
> [endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in)/iconicity claims. Every claim below traces to a cited source; where evidence came back
> "not found" rather than "proven absent," we say so.
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) · [CAPABILITY_MAP.md](CAPABILITY_MAP.md).
>
> *Consolidated: 2026-06-27 · "The graded concordance map" added 2026-07-26 (the two-strata
> reorganization sitting).*

---

## The honest headline

Arisbe makes a **genuine contribution, though it counts as engineering, operationalization, and
integration, not a new theoretical result.** In nearly every case the underlying logical or
structural fact belongs to *established literature that must be cited*. The defensible novelty lies
in what Arisbe builds: a *working, calculus-faithful system* doing what the literature had described
only as theory or noted only as a static correspondence.

One element stands out as having **no prior art found anywhere** in the surveyed literature or
competing tools: **the linear↔graphical correspondence treated as a continuously runtime-attested
invariant over a live, editable EG system.** That remains the strongest basis for an originality
claim.

Two places carry real **over-claim risk** and should always travel with their prior art:
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
   calculus*. Arisbe treats it instead as a *live monitor on an editable system's every state*, and
   no surveyed tool or paper does this. The project's signature lies here.

2. **Beta-complete, Dau-faithful, interactive EG environment.** The only actively-maintained
   interactive EG prover found (Peirce-My-Heart) covers Alpha only. Beta (lines of identity / FOL)
   with the full six-rule calculus, enforced by construction, fills an apparently empty niche.

3. **An integrated reason + evaluate + corpus + import environment under one correspondence-attested
   roof.** Taken singly, each piece connects to an existing thread. The *integration* carries the
   contribution: proof, semantic-game evaluation, a provenanced corpus, and ontology/NL import all
   share one EG-native, attested representation, and that combination remains unusual.

4. **The diagram↔narration scorer** (Centering + focus-stack alignment of EG transforms with DRT
   updates) and **the diachronic-DAG-as-drawn-Kripke-frame** framing. Two narrower pieces, both with
   no prior art found, both riding on established theory (Sowa's isomorphism; the standard
   translation).

5. **The first running implementation of the endoporeutic evaluation game** (outside-in peel +
   3-valued open-world verdict + witness/counterexample + automated minimax opponent).

---

## Where to be careful (over-claim ledger)

- **EG≅DRS is Sowa's, not ours.** Always cite Sowa (*From Existential Graphs to Conceptual Graphs*)
  and Kamp 1981. Our contribution rests in the *scorer*, not the isomorphism.
- **The linear notations are Sowa + ISO Common Logic.** We implement and bind them; we did not invent
  EGIF/CGIF/CLIF.
- **"Gamma is unnecessary" is contrarian, and the broken cut has been rehabilitated.** Ma & Pietarinen
  (*Gamma graph calculi for modal logics*, Synthese 2018) give *sound and complete* graphical broken-cut
  calculi for fifteen normal modal logics, using Peirce's own apparatus with "only (DMN), (B), (5) new".
  They also name diagrammatic advantages the standard translation discards: position and polarity read
  off cut topology, no negation normal form, the ambient sheet absorbing structural bookkeeping. So the
  claim must be worded
  **"no modal *mark* needed for Arisbe's architecture," not "Gamma is dispensable for logic."**
  [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) ("What not using Gamma costs" + "What Gamma
  keeps") carries the full honest accounting: what the no-Gamma stance genuinely forgoes (second-order
  + metalinguistic content; perspicuity/decidability) against what costs only perspicuity.
- **"Interactive EG editor" and "soundness by construction" are baselines, not differentiators.**
  Prior tools already claim them. Ours differs by *Beta + Dau + the invariant + breadth*.
- **The banner ("moving pictures of thought") is Peirce/Stjernfelt/Pietarinen.** Rhetorically apt,
  not a contribution.

---

## Gaps in the field Arisbe is positioned to fill

- **No machine-checked (Coq/Lean/Isabelle) formalization of Dau's EG calculus was found.** Arisbe's
  ~1000-test executable spec + the runtime attestation do not amount to a machine-checked proof, but
  they stand as the closest *operational* guarantor located. A formal mechanization would count as a
  clear field contribution, and a natural future direction.
- **Dau is the de-facto standard *for software* but not uncontested in philosophy** (SEP surveys
  Zeman/Roberts/Shin and omits Dau). Arisbe's choice of Dau as bedrock holds up, and arguably counts
  as the right engineering call, but the project should not present Dau as universally "the"
  formalization.
- **Description Logic ([DL](GLOSSARY.md#dl))/Web Ontology Language ([OWL](GLOSSARY.md#owl))-as-diagrams already exists** (a sound-complete diagrammatic system for ALC; Graphol ≈ OWL 2).
  Arisbe's EG-native subsumption-by-freeze-a-witness counts as a reasonable extension, not a new bridge.
- **No system was found that plays an *automated* role-based dialogue game to build a knowledge
  model from scratch under a *sound* referee.** A 2026-06-30 deep-research pass (25 verified
  claims, 0 refuted) found every neighbour holds at most two of {multi-agent role dialogue,
  build-from-scratch, sound formal referee}. Dialogue and debate systems (Black & Hunter inquiry
  dialogues, PARMA, AI-safety-via-debate, Du et al., SPAG, CAMEL, DeepMind oversight) carry the roles
  but offload truth to participants, to humans, or to weak-LLM judges. Belief-revision + ILP
  (AGM-for-Dung, ILASP/CDILP, AutoSpec) and FunSearch carry a sound engine but run single-agent or
  single-proposer. Arisbe's **automated Endoporeutic Game** (Graphist/Grapheus/Agonothetes under the
  §3.3-attested peel, with the correspondence-not-truth floor) sits in that empty intersection; see
  [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md) §8. (Threads 5–6, automated
  science and LLM ontology construction, were not exhaustively verified; read as *"none among the
  verified set."*)

---

## Concordances — the neighboring programs

*(Added 2026-07-17, from the whole-of-Arisbe step-back. These count as **concordances**: programs
that arrived at structurally similar answers from independent starting points. They make no
lineage claim and count as no prior art in the verdict-table sense. Arisbe did not derive from
them, and none of them anticipates the correspondence invariant. They stand recorded because each
one names, in its own vocabulary, a part of what Arisbe builds, and because the differences
instruct as much as the agreements. The design consequences live in
[BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md](BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md).)*

- **Pragmatist inquiry (Peirce, *The Fixation of Belief*; Dewey's reflex arc and pattern
  of inquiry).** The ground, not a neighbor. *The Fixation of Belief* (1877) supplies the
  engine itself: inquiry driven by the **irritation of doubt** (a state of friction that
  disrupts action), ending not in abstract truth but in a settled *habit of action*. Doubt →
  inquiry → settled belief names the loop the automated game mechanizes. Dewey contributes
  twice. *The Reflex Arc Concept in Psychology* (1896) dismantled the linear
  stimulus–response picture in favor of a **continuous perception–action loop**: actions
  dictate what stimuli arrive, and the current internal state dictates how they get
  interpreted. That circuit the directed-engagement design closes. His later
  "indeterminate situation" (*Logic*, 1938) names the membrane's raw deliverance before it
  becomes a legible proposal. We state this here so the newer concordances below read as
  *corroborations of a Peircean design*, not as its sources.

- **Neo-pragmatism (Rorty, *Philosophy and the Mirror of Nature*; *Consequences of
  Pragmatism*; *Contingency, Irony, and Solidarity*).** The most philosophically pointed
  concordance, because it cuts *both ways*, and because Rorty himself had little use for
  Peirce (in *Consequences of Pragmatism* he credits Peirce chiefly with naming pragmatism
  and stimulating James). So it amounts to a concordance of discipline, not of lineage.
  Where does Arisbe agree with him? The **correspondence-not-truth floor** enacts
  anti-representationalism in practice: the §3.3 invariant attests a correspondence between
  two of *our own* signs, the drawn form and the written one, never between sign and world,
  declining the Mirror of Nature exactly where Rorty says it must be declined. The phrase
  **"progression, not progress"** and the dissolved terminus (Departure I in
  [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md)) side with Rorty *against
  Peirce's own* Final-Opinion convergence, since the game is scored against no summit. And
  the **ironist's** "radical and continuing doubts about the final vocabulary she is using"
  becomes the validity discipline made syntax: M, the system's working vocabulary about its
  world, resides only inside cuts and never gets asserted at the sheet level, so irony
  survives as an *invariant the gate checks*, not as a temperament the inquirer must
  sustain. Two departures follow, both instructive. (i) The Fidelity examinations **concede
  the mind-independent comparative efficacy-vector** (structural realism: "a genuinely better
  instrument" names an ordinal fact the world settles, not merely better-by-our-lights),
  which Rorty would refuse. (ii) Rorty deflates justification to conversation, solidarity
  without a tribunal beyond one's peers; Arisbe keeps a **sound mechanical referee**. The
  Endoporeutic Game stays conversation, but *with an incorruptible referee*, a middle position
  Rorty's dichotomy of solidarity-or-objectivity does not name. Solidarity supplies the
  warrant (in-context competence), the calculus supplies validity, and neither one gets asked
  to do the other's work.

- **Predictive processing / active inference (Helmholtz; Friston; Clark, *Surfing
  Uncertainty*; Seth).** The closest formal neighbor, and the one with the deepest root.
  Helmholtz's **unconscious inference** (1860s) cast perception as the brain *predicting*
  what the senses will report and processing only the difference. Friston's free-energy
  principle (2006–) formalizes that ancestor: free energy ≈ surprisal ≈ *doubt*, minimized
  either by updating the model (perceptual inference) or by acting on the world (active
  inference). The interpretant functioning as a *prediction*, doubt as
  *prediction error*, and model revision as error-minimization together make up this
  literature's core loop, and Arisbe's resolving membrane (forecast recorded before the
  outcome; the `PredictionLedger`) implements its perception side. The Markov blanket and
  Arisbe's *membrane* stand as independent coinages doing the same job: naming the boundary
  across which a model meets what it models. Precision-weighting has a discrete cousin in the
  warrant gradient. Two honest differences remain. Arisbe's updates come as **recorded,
  warranted, rule-licensed steps**, a chain a reader can inspect, where free-energy
  minimization runs as a gradient flow that keeps no such record. And Arisbe's three-valued
  verdict distinguishes *abstention* (Kleene UNKNOWN, open-world) from *error*, a distinction
  a scalar surprisal collapses. What does the neighbor have that Arisbe lacks? The **action
  arm**, acting on the world to reduce expected error. Arisbe names it and has not built it:
  "directed engagement."

- **Cybernetics (Wiener; W. R. Ashby; Conant & Ashby).** Wiener (1948) made the feedback
  loop, error correction, the general mechanism of biological and machine intelligence.
  Ashby's **Homeostat** (1948; *Design for a Brain*, 1952) came first among *physical*
  implementations of remodeling driven by environmental friction: when its variables were
  pushed out of bounds (its doubt), it re-randomized its own internal wiring until a
  configuration restored equilibrium. Ashby called that **ultrastability**, the mechanical
  bootstrap. The good-regulator theorem (Conant & Ashby 1970) — "every good regulator of a
  system must be a model of that system" — supplies the one-line *external* justification
  for M's existence: anything that must cope with a world carries a model of it. The law of
  requisite variety adds that the regulator must carry **at least** the variety it regulates,
  and the *economy of research* supplies the complementary upper bound, to carry **no more**
  than the engaged slice. Arisbe reached that design fact empirically, and disuse-decay
  enforces it, bounding M's variety to the engaged world-slice rather than the archive.

- **Cellular automata (Conway's Game of Life).** The concordance that shaped the automated
  loop's design directly, and the one whose *differences* carry doctrine.
  [AUTOMATED_MODEL_DEVELOPMENT.md](AUTOMATED_MODEL_DEVELOPMENT.md) §1 holds the full
  analysis; this entry only summarizes it. The analogy survives "at the level of *structure*:
  simple repeated step → iterated over generations → emergent global behaviour nobody
  scripted." Three instructive breaks follow. A generation counts as a **round of the game**,
  and "its outcomes are **negotiable**, not determined", since the rule that fires comes as a
  disposition chosen by agents rather than a neighbour-count. Life's *death*, its whole
  character, finds no analogue in monotone materialization ("growth-to-saturation is not
  emergence; it's closure") and reappears instead as **relinquishment and disuse-decay**. And
  "the decisive structural difference is **closure of the dynamics**": Life stands
  canonically defined on the *infinite* lattice ℤ², as unbounded as the sheet of assertion,
  yet advances by a *fixed* local rule, so its growth stays bounded *by the rule*, while the
  sheet's is bounded only by **selection from outside**, which is why the membrane holds the
  crux. Life runs a closed determinism bounded by its fixed rule; the Agon loop runs an open
  negotiation bounded by the world. (Whether Life itself is worth encoding as a closed
  CA-in-EG demo remains a named backlog item there.)

- **Scaling science (Geoffrey West, *Scale*; Kleiber; Bettencourt).** The author's
  pointer, and the one that makes the fractal reading *quantitative*. West's program
  analyses systems that aggregate, interact, and distribute resources through
  space-filling hierarchical networks, and finds discoverable **scaling exponents**
  (quarter-power metabolic laws; cities superlinear in innovation, companies sublinear
  and mortal). The mapping runs like this. Deliverance throughput serves as the system's
  metabolism, the membrane hierarchy as its distribution network, decay as its cellular
  turnover. So the measure's components should themselves *scale lawfully*, and the
  exponents stand as empirical questions the run corpus can already ask: how do derived
  atoms scale with explicit atoms (K3's exponent), and how does question-yield scale with
  |M|? The most striking correspondence lies in West's **companies die, cities don't** —
  bounded closed systems scale sublinearly toward stagnation while open-networked ones
  scale superlinearly — which restates the halting-duals thesis with fifty years of data
  behind it. A closed Arisbe crystallizes or evaporates; an open-membraned one with growing
  sensor and action spaces takes a city's shape. One honest differentiator remains: West's
  laws emerge from energy optimization under physical network constraints, and whether
  *semiotic* networks obey analogous constraints stays a conjecture Arisbe is positioned to
  test, not assume.
  *(Since tested five times: the West-in-kytē program E1–E3b, 2026-07-22→26 — see "The
  graded concordance map" below for the verdicts, including the refuted priors.)*

- **Reinforcement learning & artificial curiosity (Sutton's temporal-difference learning;
  Schmidhuber; Oudeyer & Kaplan).** The machine-learning face of the same loop. The **TD
  error**, the delta between expected and experienced, names the doubt-delta exactly, and
  its fixed point reads as Peircean: **when the expected TD error is zero (the update's fixed
  point) the agent stops learning, which is Peirce's settled belief** (a habit no longer
  irritated). Schmidhuber's artificial
  curiosity inverts the drive, making reward = **compression progress**, so the agent *seeks
  out* what it cannot yet predict in order to resolve it. That means doubt-seeking, not
  merely doubt-resolving, which Arisbe's musement pole and docket of doubts implement in
  recorded form. Two honest differences again. RL's learning signal stays a scalar folded
  into weights, where Arisbe's arrives as a *disposition with a recorded mode and
  derivation*. And the curiosity literature carries its own hard lesson: target learning
  *progress*, never raw error, else the noisy TV captures the agent. The
  directed-engagement design adopts it as a standing guard.

- **Evolutionary epistemology / falsificationism (Popper; Campbell's blind-variation-and-
  selective-retention; Lakatos's research programmes).** This book already cites Popper
  elsewhere. The finer concordance maps Campbell's schema onto the loop, with proposer =
  variation, peel = selection, decay = the bound on retention, and maps Lakatos onto the
  *development practice*: the run logs' pre-registered priors and disposed findings
  (the `Pⁿ`/`Fⁿ` discipline of the run logs under `runs/`) amount to a research-programme
  record in Lakatos's sense, kept mechanically honest. One difference wants stating.
  Selection in Arisbe runs through a *sound referee* over a recorded game, not through
  survival alone.

- **Biosemiotics / enaction (von Uexküll's Umwelt and functional circle; Hoffmeyer;
  Maturana & Varela's autopoiesis and structural coupling).** The Peirce-*native* bridge.
  Modern biosemiotics (Sebeok, Hoffmeyer) rests on Peirce's sign theory and reads von
  Uexküll's Umwelt *through* it (Uexküll himself, d. 1944, was not Peircean; the fit came
  retrofitted, not original), so the vocabulary transfers with least distortion. The
  vocabulary-bounded horizon ("enough of M = what the proposal
  touches," [DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md)) amounts to an Umwelt: the world
  *as addressable by this organism's sign-repertoire*, with an honest horizon beyond it.
  Uexküll's functional circle (perceive → act → perceive) names exactly the circuit that
  closes only when directed engagement gets built; until then Arisbe holds the perception arc
  of the circle, not the action arc. Structural coupling names what a long-running live
  membrane would become, model and source shaping each other's history. One instructive break
  follows. Maturana & Varela's autopoiesis stays militantly anti-representationalist,
  rejecting exactly the model-of-the-world framing M reinstates.

- **Belief revision & reason maintenance (AGM; Doyle's TMS; de Kleer's ATMS).** The
  disposition taxonomy answers the problem AGM axiomatizes, namely how a rational corpus
  absorbs a contradiction. Arisbe's revisions differ by coming *syntactic, drawn, and
  derivation-carrying*, each one a licensed rule application with its recorded act, rather
  than as postulate-constrained set operations. A transformation chain whose steps carry
  their derivations works as a truth-maintenance system whose justifications rest on **sound
  rules**, not on mere dependency links. It stands to a TMS as the
  [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) comparison table records for Git and Datomic:
  the commit already validates.

- **Berger & Luckmann (*The Social Construction of Reality*, 1966).** Objectivation and
  internalization; institutionalization as **reciprocal typification of habitualized actions by
  types of actors**, which *cannot occur in an individual*. The concordance sits under
  Arisbe's UoD/commens distinction and under the honesty guard that the automated EPG *models*
  an institution rather than working as one.
  See [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md).
- **Conant & Ashby (the good-regulator theorem, 1970; requisite variety, 1956).** See
  Cybernetics, above, for the theorem statement. The concordance licenses the three EPG
  roles as an instance's internal model of the institution of inquiry: *model-of, never
  instance-of*. See [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §3.

*Confidence note: the mappings above record the project's own readings (2026-07-17, assistant-
drafted, author-reviewed), made at the level of structural role. We claim no influence in
either direction between these programs and Arisbe's design.*

---

## The graded concordance map

*(Added 2026-07-26, at the two-strata reorganization sitting.)* This map gives the **graded,
evidential sharpening** of the prose concordances above: the same neighbors, now read as the
evidence table for Stratum II's nexus thesis — *the operational Peirce core (signs + sound
transformation + earned record) is the common formal substrate the twentieth-century traditions
lacked; each is a tributary, a partial view of Peirce's program*. That thesis speaks as **a
proposition scribed into the wider Endoporeutic Game**. It proposes and never asserts; refutation
counts as a lawful, invited move; and **the grades below are the proposition's warrant
annotations**. So every refuted prior stays *listed*, never hidden, since a refuted prior counts
as a peel already played and belongs to the proposition's honesty. The grades stay a vector over
rows, never a ranking of the traditions, under the same guard as "vector, never a scalar" in
[THE_MEASURE_OF_KNOWLEDGE.md](THE_MEASURE_OF_KNOWLEDGE.md).
[SYNECHISM_AND_CONTINUITY.md](SYNECHISM_AND_CONTINUITY.md) treats the connective doctrine that
lets one map carry rows of such different kinds, continuity across the discretizations, and
[THE_KYTOS.md](THE_KYTOS.md) holds the anatomy the "face of the kytos" column refers to.

**The formalization lineage is not a row.** Roberts, Zeman, Shin, and Sowa, culminating in
**Dau's** *Mathematical Logic with Diagrams*, stand **distinct in kind** from every tradition
below. They serve as Stratum I's guarantor, the mathematics that makes the instrument sound, not
as a concordance mapped onto it. The tributaries raised doubts and lacked machinery; the formalization
lineage *is* the machinery's warrant, credited in the verdict table at the top of this document
and never graded here.

| Tradition | The doubt it raised | The machinery it lacked | Face of the kytos | Arisbe evidence | Grade |
|---|---|---|---|---|---|
| von Neumann / Conway / aLife | Can iterated simple steps yield unscripted global order? | Semantics and negotiation — dynamics under a fixed rule; no assertion, no negotiated outcome | The doubt-cycle as a *round of a game* | `agon_evolution.py` (gate `test_agon_evolution.py`); the open-membrane runs (`runs/`); the halting duals ([THE_KYTOS.md](THE_KYTOS.md)) | **built-and-gated** (the loop) · **queued-conjecture** (the open-endedness *reading* — that the negotiated sheet achieves what fixed rules cannot is not yet a measured claim) |
| Ashby / Conant (cybernetics) | Must every good regulator be a model of its world? | An assertion calculus — the model held, with no licensed way to assert, retract, or test it | Interior M | The M-residence discipline ([M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md](M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md)); `world_scroll.py`; the peel (`semantic_game.py`); gate `test_corpus_polarity_discipline.py` | **built-and-gated** |
| West (*Scale*) | Do aggregated units obey discoverable scaling laws? | What the unit *does* — economics of the unit without its semantic work; the scalar→vector return-gift | Budget & rates — the kytē's metabolism | Measured **five times** (`runs/WEST_E1_LOG.md` … `WEST_E3B_LOG.md`; program [WEST_IN_KYTE_PROGRAM.md](WEST_IN_KYTE_PROGRAM.md)): E1 all four priors held, FED ~5.2× cheaper at equal K2 · E2 β_mono 1.277 > β_fed(I) 1.025; 25× cost spread from coordinator scan discipline · E2b interior N\*=3; coherence broke by decay at N=1 · E3 endogenous partition → N=3 granularity, multi-basin · E3b all 36 starts → N=3; 19 optima; the 10/1/1 family = 75% attractor mass within 1.4% of floor. **Refuted/limited priors listed:** P1² separation-only · PB3 refuted (broker never fired) · PB4 undetermined · PE2, PE5 refuted · PM4 refuted | **measured-with-priors** |
| Berger & Luckmann | How does the subjective become objective — objectivation, institutionalization? | Mechanism — a description of typification with nothing that executes it | The commens — the community-of-kytē face | [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §2(c) (judgment objectivated, never owned); the E1–E3 federation runs as the first instrumented step | **ratified-doctrine** |
| Popper / Campbell (evolutionary epistemology) | Knowledge grows by conjecture and refutation | A record — selection with no earned, replayable transcript | The doubt-cycle's disposal arm — the project level of the fractal | The `Pⁿ`/`Fⁿ` run-log discipline itself (`runs/`): pre-registered priors, mechanical verdicts, author disposal | **measured-with-priors** *(as practice — the discipline is exercised on every run, not itself a measured claim)* |
| Uexküll / Hoffmeyer (biosemiotics) | The organism's world is its sign-repertoire — the Umwelt | Soundness — a membrane with no calculus behind it | Membrane + horizon | [THE_KYTOS.md](THE_KYTOS.md) (the membrane doctrine, incl. the reception taxonomy and the two apertures); the vocabulary-bounded horizon ([DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md)); vault custody (`vault_world.py`) | **ratified-doctrine** |
| AGM / TMS (belief revision) | How does a rational corpus absorb a contradiction? | Ink — postulate-constrained operators with no drawn, derivation-carrying step | Interior M's revision moves (and decay) | `model_revision.py` + `m_steps.py` (licensed ERA/INS, derivations recorded); gate `test_corpus_polarity_discipline.py` | **built-and-gated** |
| Friston / active inference | Perception and action as one economy of prediction error | A deliberative record — a gradient flow keeps no inspectable chain | Budget & rates — the attention economy | `attention_economy.py`; the alternatives-in-abeyance register (`alternative_index.py`, AS1–AS4 attestation; gate `test_alternative_persistence.py`) | **built-and-gated** *(the concordance stays a concordance — cited neighbor, never load-bearing vocabulary)* |
| Erotetics (Hamblin / Belnap / Wiśniewski) | The question as a first-class logical object | An economy of attention — no cost, severity, or decay on the standing question | The abeyance register of the doubt-cycle | `alternative_index.py` / `alternative_trace.py` / `alternative_survey.py`; the `swan_alternatives` corpus exemplar; full history in [ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md](ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md) (this row links to it, never duplicates it) | **built-and-gated** |
| Graeber & Wengrow (*The Dawn of Everything*) | Was there ever one ladder of social development — or many viable commens from the start? | Measurement — historical evidence of plurality, with no cost/durability instrumentation | The commens face — plurality of settlements | The Examination VI triangulation (2026-07-27): the apportionment conjecture *predicts* plural settlements; the E-series *measured* them (multi-basin, 21 known optima, balance strands, stranding a positive-measure dear basin — PE2/PM4/PS1 refutations kept as findings); G&W supply the *historical* form. Deliberate, reversible basin-crossing (their evidence) against rare random escape (E3c) is recorded as the finding *politics = coordinated basin-crossing* | **ratified-doctrine** *(the negative claim only — no teleology; the book's sweeping narrative not adopted; reading discipline planted in [THE_KYTOS.md](THE_KYTOS.md) §4)* |
| The deliberative-interval reading of agency | Is freedom the determined considering between branching-at-doubt and licensed resolution? | — (the project's own reading; queued until examined) | The quasi-mind — the agentive face | Examination VI Unit IV (2026-07-27), ratified with four additions: the interval as *where determination happens* (computational irreducibility); responsibility **earned cumulatively by record, never by origin**; the three-ground predestination disposal with the forecast/foretell guard; the accounting sufficient-not-exhaustive. Any "operational model of consciousness" reading of this map still stays in this row — the reflexive run remains queued | **ratified-doctrine** *(promoted by Examination VI per this map's own rule; measurement awaits the reflexive run)* |

**The four grades** (never flattened into one scale):

- **built-and-gated** — shipped code in `src/`, held by a standing test gate in `tests/` that
  would fail if the correspondence claimed here broke; re-checked on every suite run.
- **measured-with-priors** — a pre-registered prior run against the built system, its mechanical
  verdict logged and author-disposed in a run log under `runs/`; refuted priors stay in the row.
- **ratified-doctrine** — an author-ruled doctrine document: a reading the project commits to in
  prose, carrying no measurement claim.
- **queued-conjecture** — named and deliberately unexamined; on the docket for a future sitting,
  with no evidence claimed.

How a grade changes: **promotion is only by the author's ruling** — a queued-conjecture becomes
ratified-doctrine by a ruling at a sitting, and reaching a measured grade additionally requires a
pre-registered run (priors logged *before* the run executes), while built-and-gated requires
shipped code under a standing gate. A grade can also **fall**: a deleted or vacuously-passing
gate demotes built-and-gated, and a measured row whose run log cannot be replayed or whose
priors were registered after the fact reverts to conjecture. Either movement is itself a move
in the wider game, recorded where the evidence lives.

---

## From concordance to measure — knowledge quantified

*(Graduated from the design-of-record 2026-07-19, by the author's ruling; drafted by the
assistant from the author's seeds and ratified 2026-07-17/19. Everything below checks
against running instruments; the section makes no claim an instrument cannot
compute.)*

The concordances above converge on one operational definition. The author's own earlier
formulation seeded it — *"knowledge exists when someone reliably does something
(thinks, speaks, acts) that works"* — and Arisbe's vocabulary revises it into this:
**knowledge is the resident content of a model M whose habits reliably mediate its
membrane's deliverances, always indexed to the horizon within which the record was
earned.** A four-component vector quantifies it, each component with a running instrument:

- **K1 — severity-weighted track record**: reliable success on tests that could have
  refuted (`PredictionLedger` × the attention economy's severity term). One worked case
  stands out. Fermat's conjecture, five confirmations deep, never amounted to knowledge.
  Nobody had tested it where it could fail, and at F5 it died (the rung-1 exemplar, Euler
  1732 recapitulated by attention in six rounds).
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
