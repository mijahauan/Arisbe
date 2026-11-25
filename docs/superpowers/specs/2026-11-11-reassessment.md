# Arisbe reassessment, 11 November 2026

> **Provenance.** Written by Claude (Opus) in a Claude Code session in this checkout on the evening
> of 2026-11-11 (local time; transcript `676a8c41-bc25-49d0-a531-bb02ec743312`, final reply at
> 2026-11-12T02:41Z), at HEAD `655a88c`. The session offered to save it here and never did; it was
> recovered verbatim from the session transcript on 2026-11-25 and saved here without edits to its
> text. The three audit reports it drew on follow as appendices, also verbatim. Like the tenability
> assessment, it is the same author-and-model loop examining itself (it says so in its last section).
>
> **State of the tree since it was written:** unchanged. HEAD is still `655a88c`; no commit has
> landed since 2026-09-26, so every recommendation below was still open on 2026-11-25.
>
> **Superseding note (2026-11-25).** The author has ruled that the calculus comes first: bring it into
> conformance with Dau or annotate each departure, make it provably sound by per-move derivation
> certificates, and split fused moves into discrete Dau steps — before any outreach. See
> [2026-11-25-calculus-conformance.md](2026-11-25-calculus-conformance.md).

**My verdict: proceed, but stop building for a while.** The instrument is worth continuing, and its strongest result is one the project has not yet named as its contribution. The case against rests on three things: nobody outside has ever read it, its public documents still claim what September refuted, and the theory layer has absorbed most of the effort for mostly null results.

I changed nothing in the repository. Three read-only audits ran in parallel, and I reproduced each finding I lean on below.

## History

The repository starts on 29 July 2025 and holds 1,214 commits. The shape matters more than the count:

| Period | Commits | What happened |
|---|---|---|
| Jul–Oct 2025 | 194 | Dau data model, the rules, the parsers, the Qt GUI. September 2025 also deposited the 62 "validation theatre" tests that cannot fail. |
| Nov 2025–Feb 2026 | 1 | Dormant. |
| Mar–May 2026 | 61 | Return; Qt archived; web viewer becomes canonical. |
| June 2026 | 261 | The exact correspondence engine, the three modes, freeform drawing, the Agon interpretation register. |
| July 2026 | 504 | Automated game, Wikidata runs, the quotation opening of the core, the beta release, then the theory layer: measure of knowledge, kytos, commens, West series, four letters drafted. |
| August 2026 | 85 | The self-skeptical turn: channel audit, tenability assessment. |
| September 2026 | 108 | The calculus tested directly against Dau; fix arc; integrity review; alphabet ruling. |
| Since 26 Sept | 0 | — |

Sixty-three percent of all commits fall in June and July 2026.

**What stayed the same:** Peirce's aim, Dau as the authority, the correspondence problem as the centre, immutability, and the universe of discourse as a process, not a picture.

**What sharpened:**
- Correspondence went from "round-trips" to an exact geometric check with three regimes.
- "Dau guarantees correctness" went from an assumption to something measured.
- The "protected core" went from a claimed guarantee to an honest map plus an attestation suite.
- Numbers went from narrated to derived.

**What changed:** scope. An environment for existential graphs became an automated knowledge-development loop, and then a theory of knowledge, community and scaling.

The project expanded steadily through July and then contracted twice, each time because of a test. Drafting the West letter triggered a code audit that refuted its three central claims. Testing the engine against the book found moves Dau does not license, some of which turned a true graph false. Both contractions left something better behind.

The uncomfortable part is the order. Your own rule says the instrument licenses the program, never the reverse. In time it ran the other way: the program was built in July on an engine first tested against Dau in September.

## Internal inconsistencies

The public face has not caught up with September. These are the ones that matter:

1. **[SOUNDNESS_BOUNDARY.md](docs/SOUNDNESS_BOUNDARY.md), a book chapter, still says the six rules are "machine-verified" sound.** It also says an implementation divergence is something "the next tier catches". That tier caught none of it; a new suite did.
2. **[VISION_AND_SCOPE.md](docs/VISION_AND_SCOPE.md) bedrock 1 says the rules "run in full compliance".** The calculus ledger holds 17 open departures from Dau, eight awaiting your ruling. Five of Dau's rules have no entry point at all. I read the remaining soundness-layer entry in full: every remaining departure is sound or merely incomplete. No known truth-losing move remains.
3. **The README claims "Round-trip fidelity: Guaranteed" and "All rules validated".** It also carries three different test counts and describes the model as living at level 1 of the world-scroll, a shape retired in July.
4. **The draft letter to Dau is not marked held, and it should be.** It says "the calculus in the engine remains yours, deliberately unimproved" and leans on the protected core. September corrected each of its three central claims.
5. **The tenability assessment and the September readiness review both exempt the calculus.** One says "not on trial"; the other says "the shortfall is not in the calculus". The suite found otherwise five days after the second. Neither is annotated.
6. **CLAUDE.md contradicts itself on the calculus suite.** It says the deiteration controls are still held as expected failures (they are fixed), and that five implemented rules have no oracle (a nearby entry says every rule is judged). This is the file I am loaded with every session.
7. **There are three "next" lists and no reconciliation.** The roadmap's (July) is documentation sweep and first paper. August's was "build the slot-question", which was never built and is absent from the docket. September's is the alphabet docket. The roadmap has no workstream for calculus integrity, so September's 108 commits sit outside the declared programme.
8. **Smaller ones:** [THE_KYTOS.md](docs/THE_KYTOS.md) gives both answers on West because corrections were layered over the original text; [FIDELITY_AND_DEPARTURES.md](docs/FIDELITY_AND_DEPARTURES.md) has four departures where five documents say three; departures from Dau have no document at all, only ledger entries; and "warrant", "UoD" and "attested" each carry three senses.

## Gaps I think are unnamed

**A reader.** This is the largest. In sixteen months, no letter has been sent, the repository has three stars, and every examination was run by the same author-and-model pair. Your own doctrine says judgment cannot be owned. The West episode showed that merely drafting a letter to a competent stranger found what five internal examinations had not.

**A fresh install that works.** The "greenfield install" CI check has failed on all 17 recorded runs. That is exactly the path an outside reader would take.

**Completeness.** The contribution document claims a "Beta-complete" engine. The ledger says vertex insertion works only in negative contexts, same-context deiteration is refused, and five rules are missing. The engine is sound as far as tested; I would not yet call it complete.

**An ablation of the diagram.** Your own rule says attribution requires ablation. The automated game is geometry-free by its own description: the peel is a Horn model check and the materializer is Datalog. Nobody has run the same loop with a plain text first-order referee. Until someone does, the claim that existential graphs matter to that loop is unattributed. This is my inference, not a measurement.

**A mechanization.** No Lean, Coq or Isabelle formalization of Dau's Beta calculus was found. Your independent legality oracle and Tarski evaluator are halfway to a specification. A proof would also settle the eight provisional ledger entries by theorem instead of by ruling.

## Research connections

The survey ran about sixty searches. Several 2026 items were seen only as abstracts, and audience sizes are estimates.

- **The mathematical frontier has moved to string diagrams.** Bonchi, Di Giorgio, Haydon and Sobociński (LICS 2024) give a complete axiomatization with full first-order expressivity. As foundations, Dau's 2006 formalization is no longer where the theory is.
- **The tooling frontier has not moved.** The best public tool, Peirce My Heart, is Alpha-only. A 2021 thesis could still say no programmatic existential-graph tools exist. No tool found implements Dau's Beta, re-reads its own drawings, or tests its engine against independent semantics.
- **The nearest proof-assistant work is Donato's Flower Calculus** (2024), an intuitionistic variant with Coq metatheory.
- **A new workshop, DIALOCO (July 2026), names existential graphs and visual proof assistants as topics.** That and the Diagrams conference are the natural audience, perhaps 100–200 people.
- **"LLM proposes, checker disposes" is crowded and well funded.** Recent evidence says diagrams do not help language models reason and may hurt. The defensible argument for a graph referee is human auditability, not model ergonomics.
- **Peirce editors have a real, small need.** The existing LaTeX package needs PSTricks and checks nothing. Your pdflatex-native, structure-checked exporter fills a visible hole for a few dozen people.
- **The theory layer's neighbours are either better formalized or not taken seriously.** Active inference has real mathematics; forecast-scored epistemics is respectable; Peircean readings of language models and "semiotic cell" theories sit near work that is not. West-style exponents are fragile even for cities.

## Contribution or passé?

The instrument is a real contribution, as engineering and as a finding. The strongest single publishable result is September's: an implementation written carefully from Dau's text was unsound in iteration, deiteration and the ligature rules, and differential testing against an independent evaluator found it. Theory-first work does not produce that kind of result, and it argues for the mechanization nobody has done.

The second is the runtime correspondence check, with one caution. The field does not name this as an open problem, so a paper must argue that it is a gap and not a problem nobody feels.

The case that it is passé is real: the mathematicians have moved on from Dau, verified reasoning has standardized on Lean and SMT, and the speculative layer invites dismissal of the whole. The rebuttal holds only if the core is published separately from the program, and first.

## Codebase condition

The calculus core and its test discipline are in good shape. The quality gate passed today (166 core tests), and the full-suite CI was green on its last three pushes in September. I did not re-run the hour-long suite.

The edges are not in good shape:

- **One real defect:** the scratch-draft delete route removes whatever path it is given. I reproduced it in a sandbox: `delete("..")` emptied the parent directory. The server allows any origin and has no authentication. Exposure is localhost only, and whether `..` survives the HTTP layer is untested, but the fix is five lines.
- **Two of three gates do not work.** The pre-commit hook calls a `python` that does not exist on this machine, and the greenfield CI is red.
- **Clutter:**
  - 45 of 144 scripts in `tools/` import modules that no longer exist.
  - 8 of 15 mandatory dependencies are imported nowhere.
  - `archive/` holds more Python than `src/`.
  - `runs/` is 63 GB.
  - 136 modules share one flat namespace, 55 of them experimental and unreachable from the web app.
- **No linter or type checker is configured.** There are 231 broad exception handlers and no use of `logging`.
- **Documentation is voluminous and partly stale.** The docs total 635,000 words and the plan alone 94,000. The API reference predates the alphabet change. CLAUDE.md works as a changelog, not an orientation.

## My own perspective

The project's best trait is that claims shrink when tested and it writes down the shrinkage. Few projects do that.

Its characteristic risk is the one you may be sensing. A fluent model and a single author can produce doctrine faster than either can check it. July produced 504 commits and a theory of knowledge at five scales. The examinations are a genuine counterweight, but they are the same loop examining itself, and so is this assessment. A newer model reads more carefully; it remains the same kind of reader.

So I would redefine "proceeding" for the next stretch, in this order:

1. **Correct the public claims** to match September, and mark the Dau letter held.
2. **Fix the delete route, the hook and the greenfield check.**
3. **Rewrite the Dau and Pietarinen letters around the September findings and send them.** "We tested our engine against your book and here is where it failed" is a far better letter than the July one.
4. **Write the one system-and-findings paper.**
5. **Freeze the program layer** until someone outside answers, and move it out of the calculus's namespace.

Docket item 10 (the language of a universe of discourse) is sound calculus work, but it is more inward work. I would hold it behind the first letter.

If you want, I can save this as a dated assessment in the repository alongside the tenability assessment, with the three audit reports attached.

---

## Appendix A — Research landscape survey (subagent report)

### Where the project sits relative to 2019–2026 research

**Method and limits.** About 60 web searches and fetches, November 2026. Most sources were seen as abstracts or search snippets, not full texts. Anything tagged **[memory]** is from my own recall and was not confirmed by search. Absence claims ("no tool does X") mean "not found in these searches", not proof. No project or owner names were used in queries.

#### A. Existential graphs research proper

The field is active, but its centre of gravity is philosophy/history and category theory, not software.

- **Editions and philosophy.** Pietarinen's *Logic of the Future* continues: vol. 3/1 *Pragmaticism* (2024) and vol. 3/2 *Correspondence* (listed December 2025; one repository record says 2024) [1]. Bellucci & Pietarinen's "analysis of EGs" papers run from RSL 2016 (Alpha) to Synthese 2021 (Beta) [2]. Stjernfelt's *Sheets, Diagrams, and Realism in Peirce* appeared in 2022 [3]. Chiffi/Bellucci/Pietarinen's assertive graphs are a side branch [4].
- **String diagrams, the mathematical frontier.** Haydon & Sobociński (Diagrams 2020) [5] led to Bonchi, Di Giorgio, Haydon & Sobociński, "Diagrammatic Algebra of First Order Logic" (LICS 2024) [6]. The journal-length version, "The Calculus of Neo-Peircean Relations" (arXiv 2505.05306), was submitted to LMCS [7]. It gives a complete axiomatisation with full first-order expressivity. Haydon's 2024 TalTech thesis consolidates the line [8]. Melliès & Zeilberger (LICS 2016) is the older bifibrational refinement of Brady & Trimble [9].
- **Proof theory.** Ma & Pietarinen relate Alpha to Brünnler's deep inference (Studia Logica 2017) and give a graphical deep-inference system for intuitionistic logic [10]. Donato's "Flower Calculus" (FSCD 2024) is an intuitionistic first-order refinement with Coq-mechanised metatheory and a prover GUI [11]. His "Scroll nets" (arXiv 2025) is a Curry–Howard reading of the scroll [12]. Caterina, Gangle & Tohmé give a syntactic soundness proof for Alpha (Synthese 2022) [13].
- **Mechanisation.** The only proof-assistant work found is Donato's Coq development, covering flowers and Alpha. I found no Lean, Isabelle or Agda formalisation of Beta, and none of Dau's EGIs.
- **Community.** DIALOCO, the first workshop on diagrams in logic and computation, was co-located with LICS/FLoC in Lisbon in July 2026. It names existential graphs and "visual and interactive proof assistants" as topics [14]. Diagrams 2026 (Tallinn, August) listed a "Peirce's Philosophy of Notation" workshop (snippet only) [15].
- **Dau and Sowa.** I found no post-2010 EG work by Dau [memory: he left academia]. Sowa's latest located material is 2018–2023 drafts and mailing-list posts [16]. EGIF is Sowa's convention; the ISO standard's annexes cover CLIF, CGIF and XCL only [memory].

#### B. Existing software

| Tool | Scope | Maturity |
|---|---|---|
| Peirce My Heart (RAIR Lab, RPI) [17] | Alpha only; web proof builder | 11 GitHub stars, about 1,200 commits, Vitest unit tests, no publication found |
| VisualLogic (Bram-Hub) [18] | Propositional | Student-grade |
| TalTech "Diagrammatic Logic Editor" (Jõgi, 2021) [19] | Beta editor | Evaluator never built; states that no tools exist for programs to interface with EGs |
| Flower Prover / Actema (Donato) [11] | Intuitionistic variant | Research-grade, with Coq metatheory |
| ASP-Graph [20] | Equilibrium-logic variant | Niche |
| CoGui (LIRMM) [21] | Conceptual graphs | Newest dated material found is 2019 |
| egpeirce [22] | Drawing only | States that it does not check syntactic rules |

Amine and CharGer status were not verified. RDF Surfaces (Hochstenbach, De Roo, Verborgh et al., 2024) is the one live applied use of Peirce-style negative surfaces, in the semantic web; reviewers noted missing formal semantics [23].

I found no tool that implements Dau's Beta calculus, re-reads its own drawings to check them against the formula, or differentially tests its rule engine against an independent semantics.

#### C. Diagrammatic reasoning as a field

Diagrams is biennial (2024 Münster, LNAI 14981; 2026 Tallinn) with main, philosophy and psychology/education tracks [15, 24].

- **Mature tooling is on the Euler/spider side.** Speedith and Diabelli (Urbas, Jamnik, Stapleton) verify diagrammatic steps and connect to Isabelle [25]. Euler-diagram generation from abstract descriptions (Stapleton, Rodgers, Howse) is a recognised problem [26].
- **String-diagram assistants** (Quantomatic, chyp, homotopy.io) verify rewrites, not drawing↔sentence denotation [27].
- **Openproof/Hyperproof** remains the reference for heterogeneous reasoning; the core paper is from 2008 [28].
- **Is the correspondence problem recognised?** The abstract/concrete (type/token) syntax distinction is canonical, including in Dau's own work [memory]. "Runtime machine-verified drawing↔formula correspondence" is not a named open problem. That makes it either a gap or a problem the community does not feel; the paper must argue which.

#### D. LLM plus formal verifier

This area is crowded and well funded.

- **Provers and pipelines.** AlphaProof (Nature, November 2025) [29]. Logic-LM and LINC, where LINC reported 13–38% FOL syntax-error rates and distinct failure modes [30]. VERGE (FOL plus Z3, 2026) [31]. A neuro-symbolic conjecture–criticism framework that is itself named PEIRCE (ACL 2025 demo), so the name space is crowded [32].
- **Argumentation and debate.** ArgLLMs (AAAI 2025) run deterministic argumentation semantics over LLM-built frameworks [33]. Snaith & Wells (2024) put formal dialogue games over LLMs [34].
- **Belief revision.** AGM-Bench (ICLR 2026 listing), Belief-R (EMNLP 2024) and BeliefMem [35].
- **Wikidata.** Adam & Kliegr verify Wikidata statements with traceable LLM justification (IP&M 2025) [36]. Nothing found uses ranks or references as dispute structure.
- **Ontology autoformalisation.** SUMO/SUO-KIF with Vampire consistency checks (Thompson, Pease et al., NeSy 2025) [37].
- **A caution.** Chan, Gaizauskas & Zhao (2026) argue that logical soundness is not a reliable criterion for neurosymbolic fact-checking [38]. That applies directly to "the calculus decides".

Is a diagrammatic calculus as referee novel? Yes; I found no precedent. Is it better than text FOL or Lean? There is no supporting evidence, and some against:

- Beiser et al. (2025) show the intermediate formal language changes accuracy by up to about 50 points, with FOL beating logic-programming languages [39]. So the choice matters, but EGs are untested.
- Ando & Mineshima (2026) find diagrams give LLMs limited benefit on syllogisms [40]. Wu et al. (ACL Findings 2026) find they can hurt on invalid cases [41].
- Pedretti, Picca & Rodighiero (2025) report VLMs confusing negation scope on five Alpha graphs [42].

The defensible argument is human auditability and locality: each step is a small, licensed, replayable graph edit. It is not LLM ergonomics.

#### E. Game semantics and dialogical logic

Pietarinen's work is the canonical bridge from the endoporeutic method to Hintikka's game-theoretic semantics [43] [memory: *Signs of Logic*, 2006]. Rahman's dialogical framework remains philosophically active [44] [memory: *Immanent Reasoning*, 2018]. Implementations are old or pedagogical (DiaLogic, Lorenzen-game websites around 2013, Lorenzen–Hamblin dialogue systems) [45]. I found no implementation of the endoporeutic game, and no semantic-game model checker over EGs. A three-valued, outside-in evaluator on EGs appears unoccupied, though it is conceptually close to standard evaluation games.

#### F. The speculative layer's neighbours

- **Rigorous but contested.** Active inference and the free-energy principle have a real mathematical literature. They face standing unfalsifiability critiques and a demonstrated error in a key lemma (Biehl et al. 2021) [46].
- **Rigorous and empirical.** Forecast-scored epistemics: ForecastBench [memory] and KalshiBench (2025), which finds most models worse than base rates on Brier skill [47]. This is the respectable neighbour of a "track-record" knowledge measure.
- **Contested empirics.** West/Bettencourt urban scaling is real but the exponents are fragile (Nomaler et al. 2014: the law fits knowledge production poorly) [48]. 2026 multi-agent LLM work finds diminishing returns and coordination bottlenecks, not clean superlinear exponents [49].
- **Soft or fringe.** Peircean-semiotic readings of LLMs (Picca 2025; Friedman & Thellefsen 2025; Thellefsen et al. 2025; a 2025 *Philosophy & Technology* paper) are mostly conceptual essays or preprints [50]. Biosemiotics-for-AI is small and humanities-facing [51]. The ruliad is widely regarded as unfalsifiable metaphysics (Natal 2024) [52].

A "semiotic cell at every scale" theory with scaling exponents will be read by default as belonging to the last group.

#### G. Scholarly-edition context

The Peirce Edition Project is still listed at IU Indianapolis under De Tienne, aiming at 30 volumes [53]. Volume 8 is the latest I could confirm; the status of volumes 9 and 11 is unverified. NEH terminated grants widely in April 2025 [54]; the effect on the Project specifically is unverified.

*Logic of the Future* was typeset by Nikulainen. His egpeirce package (CTAN v1.0.0, 2023) is PSTricks-based, needs a DVI→PS route or XeLaTeX, and does no syntax checking [22]. Houghton has re-digitised 233 items (15,695 IIIF images); metaLAB's "Peirce Interprets Peirce" and the 2025 VLM paper show digital-humanities interest in machine-readable graphs [42, 55].

Demand is real but small: a few dozen editors and authors worldwide [estimate]. A pdflatex-native, structure-checked exporter fills a visible gap.

#### H. Standards

ISO/IEC 24707:2018 was reviewed and confirmed in 2023; no revision is under way [56]. Use is narrow but real: BFO-2020 has a normative Common Logic axiomatisation in ISO/IEC 21838-2:2021 [57], and COLORE holds several hundred CLIF ontologies [58]. Tool support (Hets, Macleod) was described as ad hoc in older sources [58]. SUMO uses SUO-KIF, not Common Logic [37]. OWL dominates practice [memory]. CGIF has little living use outside the conceptual-graphs community [memory].

#### Synthesis

**(i) Novel or unoccupied.**
- A working Beta-level engine faithful to Dau. Nothing comparable was found; existing tools are Alpha-only or unfinished.
- Runtime re-reading of every drawing against its graph. No analogue was found in any EG tool; Speedith verifies steps, not geometry.
- Differential testing against an independent Tarski evaluator, with the resulting unsoundness findings. This is the most publishable single result. It shows that implementing iteration/deiteration and ligature rules from Dau's text is error-prone, and no mechanised Beta formalisation exists to lean on.
- An implemented endoporeutic evaluator.
- Belief revision recorded as licensed graph transformations over Wikidata ranks and references. I found no precedent for this combination.

**(ii) Duplicating better-resourced efforts.**
- "LLM proposes, checker disposes" as an architecture (Lean, AlphaProof, Logic-LM, VERGE, ArgLLMs).
- Forecast-scored models and AGM-style LLM belief revision.
- Foundations of diagrammatic first-order logic, where the neo-Peircean calculus is mathematically stronger than anything a set-theoretic EGI implementation offers.
- The theory layer, whose neighbours are either better formalised (active inference) or not taken seriously.

**(iii) Audiences** (sizes are my estimates).
- Peirce scholars: hundreds, active, low technical capacity, underserved by tools.
- The Diagrams/DIALOCO community: about 100–200, the best fit.
- Logic educators: large, but Openproof-entrenched; no classroom evaluation of any EG tool was found.
- Neurosymbolic AI: very large, and indifferent unless there is an ablation showing benefit.
- Ontology engineers: Common Logic users number in the tens.

**(iv) Venues and framings.**
1. A system-and-findings paper for Diagrams 2028, a DIALOCO successor, or J. Logic, Language and Information: verified correspondence plus the differential-testing unsoundness results.
2. The TikZ exporter as a CTAN package with a TUGboat or digital-humanities note, pitched to the Peirceana and Edition Project editors.
3. A NeSy or *Neurosymbolic AI* journal paper only with a controlled comparison of an EG referee against a text-FOL referee.

**(v) Passé?**
- *Strongest case.* The research community has moved from Dau's 2006 EGIs to string diagrams with complete axiomatisations. Verified LLM reasoning has standardised on Lean and SMT. Current evidence says diagrams do not help LLMs. The speculative layer invites dismissal of the whole.
- *Strongest rebuttal.* That community produces theory and editions but no infrastructure. A 2021 thesis could still say no programmatic EG tools exist, and the best public tool is Alpha-only. Reporting unsoundness found in one's own Dau-following engine is exactly the kind of result that theory-first work does not generate.

The rebuttal holds only if the core is published separately from, and ahead of, the speculative layer.

#### References

1. Pietarinen (ed.), *Logic of the Future*, vols. 3/1 (2024) and 3/2 (2025), De Gruyter, Peirceana. https://www.degruyterbrill.com/serial/pei-b/html
2. Bellucci & Pietarinen, "An analysis of Existential Graphs, part 2: Beta", Synthese 199, 2021. https://cris.unibo.it/bitstream/11585/819425/4/Bellucci-Pietarinen2021_Article_AnAnalysisOfExistentialGraphsP.pdf
3. Stjernfelt, *Sheets, Diagrams, and Realism in Peirce*, De Gruyter, 2022. https://vbn.aau.dk/en/publications/sheets-diagrams-and-realism-in-peirce
4. Bellucci, Chiffi & Pietarinen, "Assertive graphs", J. Applied Non-Classical Logics, 2018. https://scholars.hkbu.edu.hk/en/publications/assertive-graphs/
5. Haydon & Sobociński, "Compositional Diagrammatic First-Order Logic", Diagrams 2020. https://ws.lib.ttu.ee/digibase/en/Publ/Item/876f94b5-d7bf-4301-9ce8-903b72146807/Print
6. Bonchi, Di Giorgio, Haydon & Sobociński, "Diagrammatic Algebra of First Order Logic", LICS 2024. https://arxiv.org/abs/2401.07055
7. Same authors, "The Calculus of Neo-Peircean Relations", arXiv 2505.05306, 2025. https://arxiv.org/pdf/2505.05306
8. Haydon, *Peirce's Existential Graphs and the Logic of String Diagrams*, PhD thesis, TalTech, 2024. https://digikogu.taltech.ee/en/Download/8b41aae1-d8a8-4ee7-9c7a-352604bf6afe
9. Melliès & Zeilberger, "A bifibrational reconstruction of Lawvere's presheaf hyperdoctrine", LICS 2016. https://arxiv.org/abs/1601.06098
10. Ma & Pietarinen, "Proof Analysis of Peirce's Alpha System of Graphs", Studia Logica 105, 2017. https://scholars.hkbu.edu.hk/en/publications/proof-analysis-of-peirces-alpha-system-of-graphs/ ; "A Graphical Deep Inference System for Intuitionistic Logic". https://scholars.hkbu.edu.hk/en/publications/a-graphical-deep-inference-system-for-intuitionistic-logic/
11. Donato, "The Flower Calculus", FSCD 2024. https://arxiv.org/abs/2402.15174 ; thesis: https://www.lix.polytechnique.fr/Labo/Pablo.DONATO/papers/thesis.pdf
12. Donato, "Scroll nets", arXiv 2507.19689, 2025. https://arxiv.org/abs/2507.19689
13. Caterina, Gangle & Tohmé, Synthese, 2022 (syntactic soundness proof for Alpha; title not retrieved). https://link.springer.com/article/10.1007/s11229-022-03903-8
14. DIALOCO 2026 workshop page. https://dialoco.github.io/dialoco26/
15. Diagrams 2026. https://diagrams-conference.org/2026/ ; CFP: https://easychair.org/cfp/DIAGRAMS2026
16. Sowa, publications page. https://jfsowa.com/pubs/
17. Peirce My Heart, RAIR Lab. https://www.github.com/RAIRLab/Peirce-My-Heart
18. VisualLogic. https://bram-hub.github.io/VisualLogic
19. Jõgi, "Diagrammatic Logic Editor", BSc thesis, TalTech, 2021. https://digikogu.taltech.ee/en/Download/ce5f58ff-8fb3-4682-b6d9-2ae92dd6c320
20. ASP-Graph. https://github.com/Minimuino/ASP-Graph
21. CoGui, LIRMM. https://www.lirmm.fr/cogui
22. Nikulainen, egpeirce, CTAN, 2023. https://ctan.org/pkg/egpeirce
23. Hochstenbach et al., "RDF Surfaces: Enabling Classical Negation on the Semantic Web", arXiv 2406.10659, 2024. https://arxiv.org/pdf/2406.10659
24. Lemanski, Johansen, Manalo et al. (eds.), *Diagrammatic Representation and Inference* (Diagrams 2024), LNAI 14981. https://www.sack.de/lemanski-johansen-manalo-diagrammatic-representation-and-inference/9783031712906
25. Urbas, Jamnik & Stapleton, "Speedith: A Reasoner for Spider Diagrams", JoLLI, 2015. https://www.cl.cam.ac.uk/~mj201/publications/jolli-speedith.pdf ; Urbas & Jamnik, "Diabelli", IJCAR 2012. https://www.cl.cam.ac.uk/~mj201/publications/diabelli-IJCAR2012.pdf
26. Stapleton, Rodgers, Howse & Zhang, inductive Euler diagram generation, IEEE TVCG, 2011. https://www.cs.kent.ac.uk/pubs/2010/2990/content.pdf
27. Kissinger & Zamdzhiev, "Quantomatic", 2015. https://arxiv.org/abs/1503.01034v2 ; chyp: https://pypi.org/project/chyp/0.5.1/
28. Barker-Plummer et al., "Openproof – A Flexible Framework for Heterogeneous Reasoning", Diagrams 2008. https://csli.stanford.edu/projects/openproof-project
29. Hubert et al., "Olympiad-Level Formal Mathematical Reasoning with Reinforcement Learning", Nature, 2025. https://research.google/pubs/olympiad-level-formal-mathematical-reasoning-with-reinforcement-learning/
30. Olausson et al., "LINC", EMNLP 2023. https://arxiv.org/pdf/2310.15164
31. "VERGE: Formal Refinement and Guidance Engine for Verifiable LLM Reasoning", arXiv 2601.20055, 2026. https://arxiv.org/html/2601.20055v1
32. Quan, Valentino, Carvalho, Dalal & Freitas, "PEIRCE: Unifying Material and Formal Reasoning via LLM-Driven Neuro-Symbolic Refinement", ACL 2025 Demos. https://aclanthology.org/2025.acl-demo.2
33. Freedman et al., "Argumentative Large Language Models for Explainable and Contestable Decision-Making", AAAI 2025. https://arxiv.org/abs/2405.02079v2
34. Snaith & Wells, "Formal Dialogue and Large Language Models", 2024. https://rgu-repository.worktribe.com/output/2613516/formal-dialogue-and-large-language-models
35. "AGM-Bench: Do Large Language Models Revise Beliefs Rationally?", ICLR 2026 listing. https://iclr.cc/virtual/2026/10017503
36. Adam & Kliegr, Wikidata statement verification with LLMs, Information Processing & Management, 2025. https://arxiv.org/pdf/2409.07507v2
37. Thompson, Pease, Kölsch & Toutsios, "Grounding Terms from an Ontology for use in Autoformalization", NeSy 2025, PMLR 284. https://proceedings.mlr.press/v284/thompson25a.html
38. Chan, Gaizauskas & Zhao, "Position: Logical Soundness is not a Reliable Criterion for Neurosymbolic Fact-Checking with LLMs", arXiv 2604.04177, 2026. https://arxiv.org/pdf/2604.04177
39. Beiser, Penz & Musliu, "Intermediate Languages Matter: Formal Choice Drives Neurosymbolic LLM Reasoning", arXiv 2502.17216, 2025. https://arxiv.org/abs/2502.17216v2
40. Ando & Mineshima, "Do Diagrams Help Large Language Models Reason? Evidence from Syllogistic Reasoning", arXiv 2607.23513, 2026. https://arxiv.org/pdf/2607.23513
41. Wu et al., "Unlocking Human-Like Visible Logic", Findings of ACL 2026. https://aclanthology.org/2026.findings-acl.1602.pdf
42. Pedretti, Picca & Rodighiero, "Moving Pictures of Thought: Extracting Visual Knowledge in Charles S. Peirce's Manuscripts with Vision-Language Models", Anthology of Computers and the Humanities 3, 2025. https://arxiv.org/abs/2511.13378
43. Pietarinen, "The Endoporeutic Method", Commens Encyclopedia, 2014. https://scholars.hkbu.edu.hk/en/publications/the-endoporeutic-method/
44. "Dialogical Logic", Stanford Encyclopedia of Philosophy. https://plato.stanford.edu/archives/fall2022/entries/logic-dialogical
45. DiaLogic, FAU. https://cs.fau.de/?p=1138 ; Kacprzak & Sawicka, Argumentation, 2014. https://link.springer.com/10.1007/s10503-014-9324-4
46. Biehl, Pollock & Kanai, technical critique of the free energy principle, Entropy 23(3), 2021. https://www.mdpi.com/1099-4300/23/3/293 ; Sánchez-Cañizares, "The Free Energy Principle: Good Science and Questionable Philosophy", 2021. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7922226/
47. "Do Large Language Models Know What They Don't Know? KalshiBench", arXiv 2512.16030, 2025. https://arxiv.org/abs/2512.16030
48. Nomaler, Frenken & Heimeriks, "On Scaling of Scientific Knowledge Production in U.S. Metropolitan Areas", PLoS ONE, 2014. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4212974/
49. "Scaling Behavior of Single LLM-Driven Multi-Agent Systems", arXiv 2606.00655, 2026. https://arxiv.org/abs/2606.00655 ; "Do Agent Societies Develop Intellectual Elites?", arXiv 2604.02674, 2026. https://arxiv.org/abs/2604.02674v1 ; Google Research, "Towards a science of scaling agent systems". https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/
50. Picca, "Not Minds, but Signs: Reframing LLMs through Semiotics", arXiv 2505.17080, 2025. https://arxiv.org/abs/2505.17080v2 ; Thellefsen et al., arXiv 2509.14250, 2025. https://arxiv.org/abs/2509.14250v1 ; *Philosophy & Technology*, 2025. https://link.springer.com/article/10.1007/s13347-025-00975-5
51. Lacková Bennett, "Toward a biosemiotics framework for AI", Sign Systems Studies, 2025. https://ojs.utlib.ee/index.php/sss/article/view/26389
52. Natal, "Refuting the Metaphysics of Wolfram and Tegmark", arXiv 2411.12562, 2024. https://arxiv.org/html/2411.12562v3
53. Peirce Edition Project. https://liberalarts.indianapolis.iu.edu/centers/peirce-edition/index.html
54. American Antiquarian Society, "NEH Funding Update", 2025. https://www.americanantiquarian.org/node/13306
55. "Peirce Interprets Peirce", metaLAB at Harvard. https://metalab.harvard.edu/p/peirce-interprets-peirce
56. ISO/IEC 24707:2018. https://www.iso.org/standard/66249.html
57. ISO/IEC 21838-2:2021 (BFO). https://standards.iteh.ai/catalog/standards/iso/1cac031c-2e73-4e51-a4f1-5e4075f26d27/iso-iec-21838-2-2021
58. COLORE. https://github.com/gruninger/colore ; Macleod. https://github.com/thahmann/macleod ; "Proof Support for Common Logic". https://www.inf.unibz.it/~okutz/resources/Proof-Support-for-Common-Logic.pdf

**Not verified by search, stated from memory:** the Brady & Trimble (2000) citation details; Ma & Pietarinen's Gamma-graph papers; Dau's post-academic career; EGIF's non-ISO status; Edition Project volume status beyond volume 8; ForecastBench details; Amine, CharGer and ICCS status; all audience-size estimates. Several 2026 arXiv items [31, 38, 40, 41, 49] were seen only as abstracts or snippets.

---

## Appendix B — Internal-consistency audit (subagent report)

#### Audit of internal inconsistencies in Arisbe (read-only; nothing modified)

Every finding below was checked directly against the files and code at `655a88c` (last commit 2026-09-26); no tests were run. The spine documents stop at 2026-08-02 (VISION, ROADMAP) or 2026-07-28 (GLOSSARY, SOUNDNESS_BOUNDARY), and none mentions the September calculus work.

**Correction to the brief's premise:** the IT− unsoundness is fixed. `tests/test_calculus_it_minus_controls.py:18-22` says "FIXED … The three xfails are gone", and `tests/calculus_extent.json` contains no UNSOUND key. The belief comes from CLAUDE.md:518, which is stale (finding 4).

##### Ranked findings

**1. Contradiction: SOUNDNESS_BOUNDARY (a book chapter) against the September findings.**
- `docs/SOUNDNESS_BOUNDARY.md:32` "The six transformation rules are sound … machine-verified (implementation)"; `:35` "A rule only fires on a legal subgraph — Machine-verified"; `:39` "round-trips exactly … `same_graph` over 87+ tomos examples"; `:23` an implementation divergence is something "the next tier catches".
- Against: CURRENT_PLAN.md:1332 "THE ENGINE MAKES MOVES HE DOES NOT LICENSE, AND SOME OF THEM TURN A TRUE GRAPH FALSE"; three ledger entries still classed SEVERE (applied though Dau-illegal); CLAUDE.md:289 "144 … and 3 by stable re-emission".
- Why it matters: this is the page written to tell an evaluator what each guarantee rests on, and the tier it names caught none of it.

**2. Contradiction: public "full compliance / all implemented" against 17 open ledger entries.**
- `docs/VISION_AND_SCOPE.md:93` "run in full compliance"; `:101` "The move *is* its proof of soundness" (repeated at GETTING_STARTED.md:197 and CHAIN_OF_SEMIOSIS.md:101, 107); `README.md:162` "all implemented"; `README.md:254-256` "Round-trip fidelity: Guaranteed … All rules validated … Z3-verified".
- Against `tests/calculus_ledger.json` (17 entries, 8 marked "PROVISIONAL — for the author") and `tests/calculus_rules.py:32-55` (20 Dau rules, 5 with no entry point).
- Why it matters: no public document discloses any of the open behaviours listed below.

**3. Contradiction: the unsent Dau letter draft.**
- `docs/share/LETTER_DAU_DRAFT.md:18` "The calculus in the engine remains yours, deliberately unimproved"; `:22` "A protected core of tests … must pass on every change"; `:34` "Every pair the system serves … passes a runtime check".
- Against CLAUDE.md:147 "Retired as a guarantee … was never true", the ledger, and CLAUDE.md's own correction that "every served pair is verified" was a flat claim hiding three un-re-attested serve paths.
- Why it matters: the West letter is marked HELD and this one is not, though its three central claims were each corrected in September.

**4. Contradiction inside CLAUDE.md on the calculus suite's current state.**
- `:518` three IT− controls "are UNSOUND and held as strict xfails", against the test file (fixed).
- `:512` "Five *implemented* rules still have no oracle" and `:516` "the **ten** rules `legal()` judges", against `:508` "every IMPLEMENTED rule is judged" and the code (15 `judged=True`).
- `:448` "no test in the repository pairs INS, IT− or DC− with a correspondence check", against `tasks/todo.md:634` "6d. RULED + DONE" (tests exist at test_correspondence_invariant.py:1116-1192).
- Why it matters: this is the file loaded into every session, and it misled the framing of this audit.

**5. Stale: CAPABILITY_MAP, the declared "source of truth".**
- `:47` "83 of 147 round-trips hold; 64 do not … 6 more correctly refused", against CLAUDE.md:289-291 (144 + 3; nine refused).
- `:34` Ligature manipulation "SHIPPED" resting on `test_chapter16_17_ligature_soundness_simplified.py`, which CLAUDE.md calls "ledgered validation theatre"; `:18` says SHIPPED means a passing test exists.
- Absent entirely: the calculus property suite, the admission gate, the calculus map, the suite census, and the D-series (`src/d_world.py`).

**6. Contradiction: "protected core" is described three ways.**
- VISION:120 "blocks edits to **17 named modules**"; CAPABILITY_MAP:281 "(authoritative) … 14 modules guarded"; AGENTS.md:4 "cannot be modified without explicit authorization"; GLOSSARY:598 "a pre-commit guard locks"; `README.md:130-131`.
- Against CLAUDE.md:147-157: a local hook, bypassed by `--no-verify` "on every commit", retired as a guarantee 2026-09-21.

**7. Objective drift: three different "next" lists, and August's was dropped without a record.**
- ROADMAP (2026-07-20): doc sweep, first-paper choice, issue inventory.
- CURRENT_PLAN.md:2001 (August): "NEXT SESSION: BUILD THE SLOT-QUESTION" — not built (`grep slot.question src/c_unit.py src/c_marks.py` returns nothing) and absent from `tasks/todo.md`.
- CURRENT_PLAN.md:14 (September): docket item 10, the UoD alphabet.
- Why it matters: ROADMAP has no workstream for calculus integrity, so about 108 September commits sit outside the declared programme.

**8. Stale: README.**
- `:10` "M resides as a *supposition* at level 1 of … `~[ M ~[ ] ]` … revision = withdrawal of the whole world", against GLOSSARY:514 "cells at level 2" (level-1 retired 2026-07-16).
- `:10`, `:436`, `:489` mention-ascent "deliberately paused pending two author decisions", against ROADMAP's discharged tail (B-min shipped 2026-07-16).

**9. Contradiction: the tenability assessment exempts the calculus on grounds September refuted.**
- `docs/superpowers/specs/2026-08-05-the-tenability-assessment.md:30` "**Not on trial.** It has its own suite and its own gates".
- `docs/superpowers/specs/2026-09-06-readiness-for-external-review.md:15,24` "The engine is ready … The shortfall is not in the calculus".
- Five days after the second, the suite found unsound moves and core tests that could not fail. Neither document is annotated.

**10. Contradiction: the West arm is both retired and live.**
- CURRENT_PLAN.md:1998 "West arm is retired from the live list"; assessment §4 "magnitude questions not at all".
- ROADMAP:121-131 "Payoff … **Next:** rider E3c — running" (the same file's line 324 says E3c was disposed 2026-07-27).
- THE_KYTOS:26 "West re-graded measured" and `:303` "E2 (… the exponent proper) … a *scaling property*", against its own `:282` "yielded no exponent" and `:291` "The prospect stays open".
- THE_KYTOS was amended by layering corrections over the original text, so it now gives both answers.

**11. Contradiction: the correspondence contract's identity check count.**
- `docs/CORRESPONDENCE_CONTRACT.md:96` "P4 — Identity fidelity (three checks)"; SOUNDNESS_BOUNDARY:41 "3-way identity".
- Against `docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md:192` "It said three checks until 2026-09-22, and the third was doing nothing".
- Why it matters: the contract is the document offered to third-party re-checkers.

**12. Ambiguous: the departures.**
- FIDELITY_AND_DEPARTURES.md has four (`:436` "Departure IV — identity is a spot") while its own `:16` and `:34`, VISION:44, GETTING_STARTED:303 and SOUNDNESS_BOUNDARY:47 say "three … each examined adversarially".
- Departures from Dau have no document at all; they exist only as ledger entries, plus Arisbe-specific core fields (`sort`, `quotation`) and silent Σ growth on INS.

**13. Ambiguous: `net_score` is retired in one arm and is the definition of K1 in another.**
- CAPABILITY_MAP:235 "no gate decided by comparing hits − misses BETWEEN arms".
- Against THE_MEASURE_OF_KNOWLEDGE:146 K1 = "Σ severity of hits − Σ severity of misses"; `resolving_membrane.py:176-188` `select_best` ranks arms by `net_score`; ROADMAP:300 "`select_best` **did discriminate**".
- The exemption is stated ("a different class and does not move") but not argued.

**14. Terminology used in more than one sense.**
- "warrant": a gradient (GLOSSARY:506), rule licence (VISION:99), and a code field (`reference_node.py:65`, `quotation_overlay.py:96`), although CAPABILITY_MAP:250 says "No field named `warrant` … never a code attribute".
- "UoD": a diachronic record (GLOSSARY:66), "attested internal model inside the membrane" (`:70`), and the owner of Dau's Σ, which has no code home (CURRENT_PLAN:22).
- "attested": the §3.3 runtime check, a test suite pinning a module (calculus map), and Agon-tested.

**15. Numbers that disagree.**
- Tests passing: README:131 and :264 "4,100+", README:377 "4,620", CAPABILITY_MAP:258 "4232/0", CLAUDE.md:427 "5,207 … 63 cannot fail".
- Corpus: "87 items" or "87+" (README:268, SOUNDNESS_BOUNDARY:39, CLAUDE.md:416 and :501) against 52 in `tomos/index.json`; CLAUDE.md:53 itself calls 87 wrong. "57+ EGIF examples" exceeds the 52 total.
- Rules: "six" everywhere, against 20 rows in the rule table.
- K3: CLAUDE.md:405 "[not built]" against :246 "K3 (2026-07-17)".
- `docs/ARISBE_CORE_API_REFERENCE.md` was last regenerated 2026-07-21, with 13 core commits since and no mention of `derive_alphabet` or `insertion_egif`, yet CLAUDE.md says "Never guess… complete API".

##### Open today and undisclosed in README, VISION, GETTING_STARTED, SOUNDNESS_BOUNDARY or the Dau letter

- **Applied though Dau-illegal** (sound, classed SEVERE): `dc-plus-ignores-target`, `era-auto-closes-a-vertex-selection`, `vertex-era-erases-a-line-with-its-edges`.
- **Not an equivalence:** `vertex-era-erases-a-line-not-an-equivalence`.
- **Structure differs from Dau:** ERA also erases the vertex it isolates; IT+ auto-closes a selection; IT+ reuses rather than copies a vertex.
- **Incomplete:** IT− refuses same-context deiteration; vertex insertion is negative-only and vertex erasure positive-only; INS_EDGE refuses every candidate; MOVE_BRANCHES tries one direction; four "cut named with its contents" refusals.
- **No entry point:** five Dau rules (ORIENT_IDENTITY, LIGATURE_VERTEX, CONSTANT_IDENTITY, CONSTANT_EXISTENCE, SEPARATE_CONSTANT).
- **Outside the ledger:**
  - No UoD-level Σ; INS silently grows the language (todo 10a–d).
  - `discharge_episode` pulls a quoted constant out of its oval (CURRENT_PLAN:124).
  - `attest_served_quotations` is referenced by no test.
  - 63 passing tests cannot fail.
  - The 6j/6k recorded defects.

##### Centre of gravity

Of 167 commits since 2026-08-01, 59 fall in early August (C-series audit, D-1, Examination VIII, the tenability assessment) and 108 in September, after a gap from mid-August. September is almost entirely `tests/` (320 file touches), corpus repair (about 380 under `tomos/`), the three parsers, the rule engine and CLAUDE.md, with 27 touches to `docs/` outside specs. The project's actual work today is re-earning the Dau bedrock: testing the calculus against the book, and auditing whether its own written claims are measured. The theory stratum and the Share/Use/Run roadmap have been dormant since 2026-08-10, and nothing at all has been committed since 2026-09-26. The orienting spine still describes the July programme, and only CLAUDE.md, CURRENT_PLAN.md and `tasks/todo.md` reflect what the project now is.

---

## Appendix C — Codebase audit (subagent report)

#### Arisbe audit — 2026-11-11 (HEAD `655a88c`, last commit 2026-09-26; repo left untouched)

The calculus core and its test discipline are in good shape; the problems are at the edges: one destructive web route, a dead local gate, a red CI check, and a lot of stale periphery. Analysis scripts are in `/private/tmp/claude-501/-Users-mjh-Sync-GitHub-Arisbe/676a8c41-bc25-49d0-a531-bb02ec743312/scratchpad/` (`orphans.py`, `unresolved.py`, `errs.py`, `reach.py`, `trav.py`).

##### Size (measured: `find … | wc -l`, `du -sh`, `git ls-files`)
- **src/**: 168 .py, 74,100 lines; **136 top-level modules in one flat namespace** plus `web_api/` (32 files, 99 endpoints).
- **tests/**: 255 .py, 79,638 lines. **tools/**: 144 .py, 33,272 lines. **Viewer**: 24 JS files (5,477 lines), 6 HTML.
- **docs/**: 435 files, 214 .md, 635,466 words. `CURRENT_PLAN.md` is 94,197 words; `CLAUDE.md` is 20,077 words (151 KB), not 50k.
- **15 largest src files**: routes/ergasterion 2,179 · formal_transformation_rules 2,041 · c_unit 1,882 · presentation_ops 1,621 · egi_core_dau 1,613 · tomos_service 1,538 · oracle_notes 1,488 · elk_layout_engine 1,300 · routes/agon 1,216 · rule_interaction 1,172 · ligature_manipulation_rules 1,158 · west_experiment 1,121 · egif_parser_dau 1,101 · routes/organon 1,072 · agon_evolution 950.
- **`runs/`**: 63 GB, 109,015 files (65 tracked). **`archive/`**: 368 tracked files, 232 .py, 89,641 lines — more Python than `src/`.

##### Findings, by severity

**1. HIGH — `DELETE /ergasterion/scratch/{scratch_id}` can delete the repository.**
- `scratch_store.py:216-222` does `shutil.rmtree(self.root / scratch_id)` with no validation; the default root is `<repo>/scratch` (`paths.py`).
- Measured in a temp sandbox: `ScratchStore(tmp/outer/scratchroot).delete("..")` emptied `outer/`. The route regex `[^/]+` matches `..`.
- `save()` (`scratch_store.py:75-78`) takes `scratch_id` from the request body (`api_models.py:219`), so `../../x` creates directories and writes files outside the store.
- `main.py:24-28` sets CORS `allow_origins=["*"]`; grep finds no auth anywhere in `web_api`.
- Inferred, not tested end to end: uvicorn passes `..` through unnormalised. Exposure is localhost-only via `serve.sh`.
- Other paths look sound: UoD delete goes through an index lookup; both subprocess calls (`node elk_worker.js`, `rsvg-convert`) use argument lists, stdin and a 30 s timeout. There is no `eval`, `exec`, `pickle` or `shell=True` in src.

**2. HIGH — two of the three gates do not work.**
- **Pre-commit hook: confirmed dead.** `.git/hooks/pre-commit` calls bare `python` five times; `which python` returns "not found", so the quality-gate step exits 1. Its `WIP:` bypass reads `$1`, which a pre-commit hook never receives (inferred from git semantics).
- **"Greenfield install" CI: failed on all 17 recorded runs** (`gh run list --workflow=greenfield.yml`). The UoD list call succeeds, then the detail fetch for `agon_evolution_swan` returns an error body and the JSON decode fails. Cause not diagnosed.
- **"Canonical Pipeline CI"** (full `pytest tests/`) is green on the last three pushes, taking 51 min to 1 h 53 min.
- No linter or type checker is configured: no `[tool.ruff]`, mypy or pyright config, and CI runs none.
- `pyproject.toml` has `readme = "docs/README.md"`; that file was deleted 2025-08-22, and `release.yml` runs `uv build`.

**3. MEDIUM — tools/ is about a third dead.**
- 45 of 144 scripts import modules that no longer exist (`definitive_egi_layout_engine`, `entity_storage`, `graphviz_svg_renderer`, PySide6 and others); `tools/test_user_edits_deterministic.py` has a syntax error.
- 112 of 144 are untouched since before 2026-07-11, 72 since before 2026.
- Tracked clutter: `tomos_backups/` 118 files, `test_outputs/` 69, `node_modules/` 46 (despite `.gitignore`), `output/` 21, three `.DS_Store`; empty `test_corpus/` and `transformation_histories/` at root.

**4. MEDIUM — dead or untested src.**
- `chapter20_syntactic_equivalence_fixes.py` (405 lines) has zero importers in src, tests and tools, and imports the nonexistent `chapter18_enhanced_translation`, so it cannot be imported. CLAUDE.md still lists it under "Mathematical Foundation".
- `z3_semantic_validator.py` is imported by no test and sits in an import cycle with `chapter17_soundness_evaluation`.
- 55 of 136 top-level modules (23,071 of 63,295 lines) are unreachable from `web_api`. That is the experimental layer (`c_*`, `west_*`, `*_source`, `oracle_notes`, `vault_*`), sharing the flat namespace with the calculus.
- Three import cycles in total, one spanning 12 modules through `tomos_service`, `world_scroll` and `model_revision`.

**5. MEDIUM — dependencies.**
- 8 of 15 mandatory dependencies are imported nowhere in src, tests or tools: Pillow, graphviz, shapely, pyvisgraph, rectpack, rtree, pdfminer.six, pathfinding.
- `numpy<2.0.0` is pinned for two src files. `certifi` is imported in src but only present transitively.
- `package.json` (version "1.0.0", license "ISC") declares four `d3-*` packages that no src file requires; only `elkjs` 0.11.1 is used. `organon.html` loads unpinned `d3@7` from a CDN.

**6. MEDIUM — documentation drift.**
- **README.md** carries three different test counts ("4,100+" at lines 131 and 264; "4,620 passed" at 377) against 5,566 today, and "87 items" for tomos (lines 268, 535) against 52 in `tomos/index.json`. Its web-viewer-as-canonical instructions are current.
- **`docs/ARISBE_CORE_API_REFERENCE.md`** was generated 2026-07-19; 19 commits have touched the 14 modules since. It has zero mentions of `derive_alphabet`, `derive_rho` or `insertion_egif`, and its overview still says modification "requires explicit authorization", which CLAUDE.md retired.
- **CLAUDE.md** is 565 lines, 17 of them over 2,000 characters (longest 4,676), with 102 date stamps. My judgement: it works as a changelog and reference, not as orientation. Claims checked:
  - "166 core tests": true (`pytest --collect-only` on the 11 gate files).
  - "14 modules": true.
  - 63 cannot-fail tests and 17 calculus-ledger entries: true.
  - "87+" tomos examples (lines 416, 501): false, and contradicted by its own line 53.
  - `test_calculus_rules` entry, "five implemented rules… `judged=False`": stale. The only `judged=False` in `tests/calculus_rules.py` is a comment, and the adjacent `test_calculus_legal` entry (listed twice) says the opposite.
  - Headline 5,557: already 9 behind, one commit later.
- 56 of 212 tracked docs are untouched for over four months; 44 of those are in `docs/archived/`.

**7. LOW–MEDIUM — duplication** (grep over `def` names).
- Seven private sheet-atom extractors: `_sheet_atoms` in four modules, `_sheet_ground_atoms` in two, `_g_sheet_atoms` in routes/agon.
- Three cut-depth walkers in renderers (`peirce_latex`, `tikz_export`, `simple_svg_renderer`) plus `definitions._area_depth` and `model_revision._depth`.
- Three polarity computations: index-backed `area_polarity`; `is_positive_context`, with no callers outside the core; and `contest_context.polarity_of`, a hand walk with a dead assignment at line 78.
- `_tex_escape` twice, `_is_simple_identifier` twice, a local `ancestors()` in four parser/generator files, four session managers, and `sys.path` inserts in 25 src files.
- Layout engines are not duplicated: ELK and tension only.

**8. LOW — error handling and lint.**
- 231 `except Exception` in 63 files, 60 of them in three route files; 22 silent swallows; 2 bare `except` (`tomos_service.py:617,622`).
- 172 `print()` calls in 13 src files; no src file imports `logging`.
- 15 functions over 150 lines; the worst are `render_to_svg` (637) and `check_correspondence` (469).
- 0 mutable default arguments; 4 TODOs, all in `tomos_service`.
- `uvx ruff check src --statistics` (ruff 0.17.4 defaults): 4,826 findings, 3,946 of them typing modernisation. The signal is 227 blind-except, 143 unused imports and 2 undefined names, both in string annotations.
- `nl_to_logic.py:147-151` interpolates user text and vocabulary into the prompt unfenced, reachable from `POST /agon/propose-nl`. `agon_llm.py` fences its inputs (15 `_quarantine` calls).

##### Tests
- `tools/suite_census.py` (3.5 s): **5,566 expected outcomes = 5,553 selected + 13 module skips**, 10 deselected.
- 236 `test_*.py` files, 220 collected. The 16 not collected are 13 e2e suites (no chromium), `test_calculus_pk1` (exhaustive only) and two fixture modules.
- `admission_ledger.json` holds 63 cannot-fail tests across 11 files.
- Recorded timings (CLAUDE.md, not re-measured): full suite 57 min, `test_correspondence_invariant` about 10 min, exhaustive 2 h 29 min.

##### In good shape
- The core gate collects exactly 166 tests, and the 14-module map matches code and API-reference header.
- The census reconciles and runs in seconds; no collection errors.
- The full-suite CI is green on recent pushes.
- No `eval`/`exec`/`pickle`/`shell=True`; subprocess use is safe; no mutable defaults; almost no TODO debt.
- The knowledge graph is current (`graph.json` dated 2026-09-26, 19,958 nodes).
- The working tree is clean apart from `.vscode/settings.json`, and one commit ahead of origin.
- 156 of 212 docs were touched within four months.
- `runs/` and `graphify-out/` are correctly kept out of git, bar 65 files.
