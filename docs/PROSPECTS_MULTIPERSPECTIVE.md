# Prospects — Arisbe seen through seven disciplinary lenses

> **What this is.** The forward-looking half of the STORM exercise (companion to
> [STORM_DOCS_AUDIT.md](STORM_DOCS_AUDIT.md)). Seven communities Arisbe borders were each
> asked — via a web survey of their own state of the art — what they would want Arisbe to
> *become*. Their surveyed needs were then put as strategic questions to a repo-grounded
> strategy expert; the unmet ones became prospect candidates with provenance. This is a
> **draft for the author to moderate** (Co-STORM's human seat): a menu of directions with
> external evidence and named tensions, **not** a rewrite of [ROADMAP.md](ROADMAP.md), which
> stays untouched pending the author's disposition. Run 2026-07-06→07; external sources are
> cited **low-warrant background** per the import doctrine — evidence of what communities
> want, not endorsements.

## The seven lenses (and what each community is living)

| Lens | Its state of the art, in one line | Its defining unmet need |
|---|---|---|
| **Peirce / semiotics scholarship** | *Logic of the Future* is the first full EG-manuscript edition; Houghton is digitizing 50k pages; SPIN crowdsources transcription — but the field had to invent `egpeirce` because no semantic encoding for drawn graphs exists. | An edition-grade, citable, attested encoding for manuscript graphs. |
| **Diagrammatic-reasoning research** (Diagrams conf.) | Strong theory (Speedith/Edith provers, observational-advantage theory) but a *graveyard of unmaintained tools*; no shared benchmark of diagrammatic proofs. | A durable, maintained, machine-checkable platform + a shared corpus. |
| **Proof-assistant UX** (Lean/Coq/Isabelle) | mathlib's 550-contributor model; visualization is bolt-on (Paperproof, widgets) — *diagrams are always views onto a textual kernel, never the proof object*. | The diagrams-ARE-the-logic guarantee they only approximate; external checkability. |
| **KR / ontology engineering** | OWL reasoners classify at scale, but *explaining why a class is unsatisfiable* and versioning/provenance are barely-begun; LLM-KG construction forces dual OWL+SHACL validation. | A legible justification/explanation surface + first-class version control. |
| **Agentic-AI epistemology** | LLM agents are fluent but ungrounded; the field is turning to formal checkers over MCP; the *autoformalization gap* (translation faithfulness) is the acknowledged unsolved problem. | A verifier-as-a-service + AGM-style belief-revision memory with provenance. |
| **Logic / math education** | Autograders (Carnap) and gamified ITP (Natural Number Game) are all *sentential*; LLM tutors demonstrably over-validate wrong proofs. | An empirically-validated diagrammatic alternative + verifier-backed tutoring. |
| **HCI / visualization** | Provenance-as-DAG and semantic-zoom are mature; *diagram-first accessibility* is an active frontier; controlled logic-notation studies are scarce. | A provenance view, a soundness-guaranteed semantic zoom, and non-visual access. |

## The convergent signal

The striking result: **independent lenses converged on the same handful of asks.** Where a
direction was named by three or more communities that do not talk to each other, that is the
strongest evidence a prospect is real. Two asks were nearly universal:

1. **Publish the corpus + the §3.3 attestation contract as a versioned, citable, licensed
   community standard/benchmark.** Named by *diagrams (×2), proof-UX, AI-epistemology,
   KR/ontology, Peirce, HCI* — six of seven. The field has **no** shared benchmark of
   diagrammatic proofs, and Arisbe's tomos corpus (provenance-carrying, multi-format,
   attested) is repeatedly called "the closest thing that exists."
2. **External re-checkability of proof chains.** Named by *proof-UX, diagrams (×2),
   AI-epistemology, Peirce*: emit `ChainStep` artifacts an independent minimal checker — or an
   embedding into Lean/Isabelle/Dedukti — can re-verify, so an EG proof counts as
   machine-checked outside Arisbe's own referee (the de Bruijn criterion).

## Prospect candidates (each with lens provenance + external evidence)

Ordered roughly by leverage-over-effort. Every candidate must be something Arisbe's bedrock
can carry — Dau-formalized EGs, the correspondence invariant, the diachronic UoD, the game.

| # | Candidate | Lenses | Bedrock seed already present | External evidence |
|---|---|---|---|---|
| **R1** | **Proof certificates + external re-check** — a minimal independent checker for `TransformationChain` steps, and/or an export bridge to Lean/Isabelle/Dedukti | proof-UX, diagrams×2, AI-epist., Peirce | the chain is *already* a replayable proof object (`proof_authoring`, `replay_step`) | de Bruijn criterion; Speedith's lasting value was Isabelle certification; miniF2F-era demand for checkable artifacts |
| **R2** | **Publish the corpus + attestation contract as an open, versioned, licensed benchmark** — stable EGI interchange schema; §3.3 extracted as a prover-agnostic spec | all 7 (near-universal) | tomos corpus + provenance + citation + §3.3 tests already exist | the field has no shared diagrammatic-proof benchmark; `egpeirce` was invented ad hoc for lack of an encoding |
| **R3** | **Verifier-as-an-MCP-service** — expose the referee (Dau validation + the peel + §3.3) as an MCP server for LLM agents to delegate claim-checking | AI-epist., KR, proof-UX | the peel + `semantic_game` + `agon_llm` injectable-client machinery exist | MCP is now the universal tool substrate (~10k servers); theorem provers already wrapped (Numina-Lean-MCP) |
| **R4** | **Non-visual EG projection** — a screen-reader-native structured traversal (sheet→cut→area→ligature) + spoken linear forms | HCI, education | `natural_layout` is *already coordinate-free* — Arisbe *has* the ground-truth structure a11y research must infer | TADA/Umwelt/ChartA11y frontier; an equity/adoption gate every committee will raise |
| **R5** | **Empirical cognitive-efficacy platform** — a study mode: xAPI/Caliper-shaped interaction telemetry, condition randomization, anonymized replay export; observational-advantage metrics per layout | HCI, diagrams×2, education, Peirce | attestation + chain persistence already log every interaction with rare fidelity; EGI + exact geometry both known | the EG-vs-Fitch studies the literature *explicitly says are missing*; observational-advantage theory now formal |
| **R6** | **Manuscript / scholarly-edition integration** — drawn→EGI as edition-grade transcription (IIIF/FromThePage); citation aligned to Robin/*LoF* sigla; a critical-apparatus regime (branching = witness variation) | Peirce, diagrams | `eg_reader` (drawn→EG), `scholarly_citation`, the diachronic DAG, the Peirce-TikZ export | *Logic of the Future* + Houghton's 50k pages + SPIN; TEI has no semantic layer for logic diagrams |
| **R7** | **Ontology explanation surface + UoD-as-version-control** — a drawn attested proof as the human-legible justification for an OWL entailment/incoherence; semantic diffs over the DAG | KR/ontology | `theory_query.entails`, `legible_diff`, the branching UoD, OWL import | reasoners give opaque axiom sets; explanation & versioning are named "barely begun" in OBDA research |
| **R8** | **Verified Socratic tutor + LMS integration** — repurpose the referee'd LLM seats into a tutor whose every hint is reduced-to-artifact; LTI, a graded challenge ladder, misconception diagnostics via `legible_diff` | education, proof-UX | `challenge_mode`, `legible_diff`, `agon_llm` (reduce-to-artifact-and-re-check) | LLM tutors over-validate wrong proofs "where feedback matters most"; verifier-backed tutoring (LeanTutor) is the response |
| **R9** | **Heterogeneous (mixed linear + drawn) proof** — steps taken in EGIF/CLIF *and* drawn form within one attested chain (the modern Openproof) | diagrams×2 | four round-tripped formats + the attested chain already exist | Barwise–Etchemendy/Hyperproof's transfer-rule program has *no maintained successor* |
| **R10** | **An "EG hammer" with legible replay** — proof search over the six Dau rules whose output is *constrained to replay as a step-attested diagram chain* | proof-UX | the rules + `rule_interaction` + the replay machinery | resolves the community's sharpest tension — automation usually sacrifices legibility; Arisbe could uniquely refuse that trade |

## The tensions — where the lenses pull against each other (the author's to weigh)

STORM's real value is not the wish-list but the **contradictions** it surfaces. Four are
load-bearing:

1. **Grow expressiveness vs. remain a federating first-order kernel.** Peirce scholars and
   diagrams researchers want Gamma/Delta/intuitionistic reach; proof-UX notes real
   mathematics lives in dependent type theory; AI-epistemology wants modal/non-Horn. *But*
   the honest-scope discipline and "modality without Gamma" are a principled stance, and
   R1/R3/R9 all assume Arisbe *federates* with external provers rather than growing to match
   them. **The decision:** is the DAG-modality reading a permanent architecture (and the
   frontier is second-order-about-the-graphs, as VISION says), or a way-station toward
   drawn Gamma? Nearly every candidate's shape depends on the answer.

2. **The proof object vs. a view onto someone else's.** proof-UX and HCI both argue the
   *highest-leverage* path is to become a **projection/federation layer** — import a mathlib
   fragment for human inspection, export an Agon-tested chain as a Lean skeleton — not to
   grow a standalone prover audience. *But* the whole vision is "diagrams **are** the logic"
   as a primary medium, the one thing every other tool lacks. R1/R9/R10 lean "primary
   medium"; a pure federation reading would demote the diagram to a view. **The decision
   sets Arisbe's identity**, not just its roadmap.

3. **Curated authority vs. live low-warrant inquiry in one corpus.** KR/ontology raises a
   real quality-control alarm: mixing Wikidata/weather-fed automated law-falsification into a
   *citable* corpus is exactly what careful ontologists distrust; Peirce scholars want a
   provenance grammar distinguishing human assertion / mechanical derivation / LLM proposal.
   The warrant gradient (posited/derived/withstood) exists, but **the promotion gate a domain
   expert must trust is not yet explicit enough to publish** (bears on R2, R6, R7). The same
   corpus cannot be both a firehose and an edition without a visible, defensible membrane
   between them.

4. **Diagram-first primacy vs. accessibility.** Framed as a tension by HCI/education (if the
   diagram *is* the logic, non-visual users are excluded from the primary medium) — but it is
   the **most resolvable and most distinctive**: Arisbe already owns the coordinate-free EGI
   the whole chart-accessibility field must reverse-engineer. R4 turns the apparent conflict
   into a lead. Weight: an equity bar adoption committees *will* raise, and a genuine "first
   accessible diagrammatic-logic environment" claim if taken seriously.

## A distilled shortlist for the author

If the goal is **maximum external leverage per unit of build**, the surveys point at a clear
near-term trio, all resting on machinery that already exists:

- **R2** (publish the corpus + contract) — near-universal demand, lowest effort, and it is
  the precondition several other communities need before they can engage at all.
- **R3** (verifier-as-MCP) — rides the MCP wave; the peel is already the machinery; makes
  Arisbe useful to the fastest-growing adjacent community (LLM agents) immediately.
- **R4** (non-visual projection) — uniquely Arisbe's to claim, distinctive, and an adoption
  gate — turns a tension into a differentiator.

The larger research bets (R1 certificates, R5 study platform, R9 heterogeneous proof) are
where the *field-defining* opportunities lie, but each waits on tension #1 (federate vs.
grow) and tension #2 (medium vs. view). Those two decisions are the author's to make;
everything downstream follows from them.

---

*Method honesty: the persona/lens question-generation and the web surveys ran as multi-agent
workflows; the lens→strategy interrogation round was partly truncated by session rate limits,
so the candidate synthesis above was completed in the main loop from the eight completed web
surveys plus repository knowledge. Every candidate cites a real surveyed community need and a
real in-repo seed; none is invented. Sources for each survey are recorded in the run
transcripts.*
