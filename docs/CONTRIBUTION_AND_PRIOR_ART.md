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

*Confidence note: "no prior art found" means absence in a focused web survey, not proof of
nonexistence — particularly for unpublished or obscure tools. Treat the originality claims as
"best available evidence," not certainty.*
