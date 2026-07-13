# The modern second-order landscape, and where Arisbe stands in it

> **Status: design-of-record memo (2026-07-13), not a book chapter.** Written at the
> author's request alongside [FORCING_AND_THE_GAMMA_CROSSING](FORCING_AND_THE_GAMMA_CROSSING.md):
> the crossing into gamma/second-order territory should be as consistent with Peirce's
> thought as possible, *but it proceeds beyond Peirce, so it can be shaped by what has
> been learned since*. This memo surveys that learning — the semantics fork, the
> ontology dispute, the comprehension ladder, the predicate dragons, the tame
> fragments — and ends each section with the concrete consequence for Arisbe. §6 gives
> the verdict on "are we properly heading there." It feeds the two author crossing
> decisions (A: the comprehension floor; B: opening the core) recorded in
> [SECOND_ORDER_CORRESPONDENCE_CONTRACT](SECOND_ORDER_CORRESPONDENCE_CONTRACT.md) and
> [SECOND_ORDER_CORE_OPENING](SECOND_ORDER_CORE_OPENING.md).

## §1 The semantics fork — the biggest post-Peirce fact

Peirce died before the fork existed. Second-order logic (SOL) now names two different
things, and everything downstream depends on which is meant:

- **Standard ("full") semantics.** Second-order variables range over *all* subsets and
  relations of the domain. Rewards: categoricity (Dedekind: PA₂ pins the natural
  numbers up to isomorphism; likewise analysis). Costs: **no complete proof calculus**
  (Gödel), no compactness, no Löwenheim–Skolem — and, most tellingly,
  **non-absoluteness**: second-order *validity* is entangled with set theory.
  Väänänen's arresting form of the point: there is a second-order sentence whose
  validity is equivalent to the Continuum Hypothesis — so *Cohen's forcing changes
  which second-order sentences are valid*. The very technique of the companion memo
  is the demonstration that full SOL's "logical truth" depends on which set-theoretic
  universe you inhabit (Väänänen 2001, 2012; the internal-categoricity program —
  Väänänen & Wang 2015, Väänänen 2021, Fischer & Zicchetti 2023 — is the live attempt
  to keep categoricity's benefits without a set-theoretic metatheory; Button & Walsh
  2018 is the book-length assessment).
- **Henkin / general semantics** (Henkin 1950). Second-order variables range over a
  *specified* family of subsets/relations. Rewards: completeness, compactness,
  Löwenheim–Skolem all return — because Henkin SOL *is* many-sorted first-order logic
  in disguise. Cost: categoricity is lost. Lindström's theorem (1969) explains why
  this is not an accident: first-order logic is the *strongest* logic with compactness
  and Löwenheim–Skolem — anything with full SOL's expressive power must give up the
  properties a calculus lives on.

**Consequence for Arisbe.** Arisbe's bedrock ethos — *the calculus decides*; every
step machine-checkable; §3.3 attested at runtime; correspondence, not truth — is a
completeness ethos. It mandates the **Henkin-read, predicative side of the fork**: the
second-order layer must assert nothing whose warrant could depend on which
set-theoretic universe the reader inhabits. Full-semantics categoricity claims are
exactly the kind of unearned warrant the project refuses elsewhere. (This is also why
the companion memo insists `(forces s φ)` enter as a defined relation: its semantics
is fixed by finite computation, not by a background universe.)

## §2 The ontology dispute — what a second-order variable *is*

Quine's famous charge: SOL is "set theory in sheep's clothing" — its variables smuggle
in an ontology of sets while claiming the innocence of logic. Boolos's reply (1984):
monadic second-order quantification can be read as **plural** quantification ("there
are some things such that…"), ontologically innocent. The third, deflationary reading:
Henkin SOL is **many-sorted first-order logic** — the "second order" is just more
sorts, honestly declared.

**Consequence for Arisbe.** Memo 1's design instinct — *vary the sort, not the rules*
— is simultaneously the Peirce-continuous move (the tinctures generalized into a
drawable sortal layer) and the Quine-proof one. A dotted line of identity for
propositions is not a claim about a universe of sets; it is an honestly declared
second sort, with the same Dau rules running over it. The drawn sortal layer should be
documented as exactly that: **many-sorting made visible**, the least metaphysically
committed reading available, and the one that keeps the existing soundness story
intact.

## §3 The comprehension ladder — pricing hypostatic abstraction

Peirce's ascent operator is **hypostatic abstraction**: "opium puts people to sleep" →
"opium *has a dormitive virtue*" — a predicate reified into a subject. Modern logic's
name for licensing such moves is a **comprehension principle**, and the century since
Peirce has priced comprehension with real precision:

- **The catastrophe.** Frege's Basic Law V — unrestricted abstraction over extensions
  — is inconsistent (Russell). The first and permanent lesson: *not every drawable
  abstraction may be asserted*.
- **The calibrated ladder.** Reverse mathematics (Friedman; Simpson's *Subsystems of
  Second Order Arithmetic*) orders comprehension strength: RCA₀ ⊂ WKL₀ ⊂ ACA₀ ⊂ ATR₀
  ⊂ Π¹₁-CA₀ — with ACA₀ (arithmetical comprehension: sets defined *without*
  second-order quantifiers) conservative over first-order PA. Predicativism (Weyl's
  *Das Kontinuum*; Feferman's analysis, with Γ₀ as the ordinal bound) is the
  principled stopping point: only define a whole by quantifying over what is already
  defined.
- **The rehabilitation.** Girard's System F shows impredicativity is not *per se*
  inconsistent (polymorphic comprehension normalizes). And neo-logicism (Wright, Hale)
  shows some abstraction principles — Hume's Principle — are consistent and strong
  (Frege's theorem: HP + SOL yields arithmetic), while others in the same syntactic
  family explode. The **Bad Company problem** — *which* abstraction principles are
  safe — remains without a settled criterion.

**Consequence for Arisbe.** Crossing decision A — which comprehension floor — is the
Bad Company problem in Arisbe's own dress, and the ladder says where to stand: memo
1's default (**predicative stratification with the enclosure escape**) sits at the
well-charted, conservative, ACA₀-like rung. Two refinements the ladder adds: (i) the
rungs above are *named and ordered*, so a later climb (a demonstrated need for
stronger abstraction) is a measured step, not a leap — the same discipline memo 2
applies to opening the core; (ii) Girard's result means the floor is a **design
choice, not a forced retreat** — Arisbe chooses predicativity because it matches the
warrant doctrine and dragon-9 discipline, not because everything above is broken.

## §4 The predicate dragons — hazards for a quotation/`forces`/truth layer

The user asked for the modern controversies by name. These are the ones that bite a
project adding *names of graphs* and *relations on those names* — each with the guard
Arisbe already carries or must add. They are drafted here in field-guide voice as
candidate dragons 10–13 (whether they enter the book's
[FIELD_GUIDE_AND_DRAGONS](FIELD_GUIDE_AND_DRAGONS.md) is the author's call).

**Dragon 10 — Montague's collapse** (the most on-point for `(forces s φ)`).
Montague (1963): treat necessity — or knowledge, or validity — as a **predicate on
sentence names** rather than an operator, assume only modest reflection principles
(the analogues of the T-scheme and necessitation), and the theory is inconsistent.
This is not exotic: it is the default failure mode of any system that lets a spot
apply to a quoted statement and axiomatizes how the spot "should" behave.
*Guard:* `forces` (and any successor: `warranted`, `attested`, `derivable`) enters
**by definition, not by axiom** — a decidable relation over finite quoted objects,
whose properties are theorems of the implementation, never assumed schemas. Plus S1's
enclosure rule for the impredicative instances. The nomination in the companion memo
§5 is conditioned on exactly this.

**Dragon 11 — Curry's trap.** Curry's paradox derives anything from a
self-applicable conditional — *no negation needed*; validity-Curry (Beall & Murzi
2013) does the same to a naive validity predicate. The lesson: paradox does not
require the Liar's negation; self-application plus detachment suffices.
*Guard:* the same two as dragon 10 — groundedness by definition, stratification (S1)
for self-application. A drawn scroll whose antecedent quotes the whole scroll is the
canonical dragon-11 shape and must be malformed-unless-enclosed.

**Dragon 12 — ungroundedness (the Liar's whole family).** The modern map of truth:
Tarski's hierarchy (stratified truth predicates, no self-application), **Kripke's
fixed points (1975)** — a *partial* truth predicate, grounded sentences getting
values by transfinite closure, the Liar left ungrounded — built over **Strong Kleene
K3**; revision theory (Gupta & Belnap) for the circular remainder. Yablo (1993)
sharpened the diagnosis: an infinite chain of sentences each about the *next* is
paradoxical with **no self-reference at all** — so syntactic self-mention checks are
insufficient; **groundedness** (well-founded resolution) is the real invariant.
*Deep consonance to surface:* **Arisbe's `Verdict3` is K3.** The peel already computes
Kleene three-valued verdicts with UNKNOWN as the honest residue — which is exactly the
shape of Kripke's grounded truth. So the native Arisbe answer to the Liar family is
not (only) a rigid Tarski tower but a **grounded-partial reading**: a quotation layer
whose semantic predicates are partial, with ungrounded instances reading UNKNOWN
rather than crashing or being syntactically banned. This materially informs decision
A: the floor can be *Kripkean-partial* where it is semantic and *stratified* where it
is syntactic — S1 controls what may be **drawn flat**; K3-partiality controls what an
evaluation **returns**. Yablo is why S4's honest horizon (and S5's per-state variant)
matters as much as S1: name what does not resolve; never assume mention-checking
catches everything.

**Dragon 13 — Bad Company.** As §3: abstraction principles syntactically alike divide
into the consistent and the explosive, with no settled demarcation. *Guard:* Arisbe
never licenses an abstraction *schema* — each hypostatic abstraction / definition node
enters as a checked, individual, revocable act (the definition machinery; fold/unfold
with R1–R4), and the comprehension floor is parameterized in the harness so the
demarcation can tighten without rebuilding.

**The discipline that binds them: conservativity.** Axiomatic truth theory (Halbach's
*Axiomatic Theories of Truth*; the Enayat–Visser conservativity proof for
compositional truth CT⁻; the "Tarski boundary" program of Łełyk, Wcisło, Cieśliński;
Fujimoto & Halbach 2024 on classical determinate truth) has made one question central:
*does adding the truth/satisfaction layer prove anything new in the base language?*
Conservative extensions add expressive reach without new first-order commitments;
non-conservative ones (full compositional truth with induction) are substantive
theory. **Consequence:** name **conservativity over the Dau core** as the crossing
invariant — the second-order layer must prove no new first-order theorems; every
first-order consequence must remain derivable by the six rules alone. That is the
formal content of "Dau remains the guarantor," and it is testable: the harness can
check that quotation-layer reasoning never licenses a base-level assertion the base
calculus refuses.

## §5 The tame fragments — the stations between first and second order

"Between first- and second-order" is not empty space; it is charted territory with
named stations, and Arisbe should know which one it is standing at:

- **Monadic second-order logic (MSO).** Decidable over strings and trees (Büchi 1960;
  Rabin's S2S, 1969) — the celebrated tame fragment. Arisbe's quantifications one
  order up are, so far, over *whole named graphs* and *DAG states* — tree-shaped,
  finitely presented objects — much closer to MSO over the derivation tree than to
  full relation-quantification.
- **Fixpoint logics and descriptive complexity.** Fagin (1974): existential SOL
  captures exactly NP; least-fixpoint FOL captures P on ordered structures. Two
  Arisbe-relevant morals. First, second-order quantifiers have *computational* teeth,
  priced precisely. Second — and decisive for the registers — **over a finite model,
  second-order truth is decidable**: model checking costs complexity, never
  undecidability. Arisbe's M is always a finite EGI. So the **Agon register
  (truth-in-a-finite-M) is safe territory for second-order claims** — the peel
  extends; whereas the **theorem/validity register (`theory_query`, and any future
  `forces`-as-theorem reading) is where the §1 restraint binds**, because that is
  where full-semantics undecidability and non-absoluteness live.
- **Game-theoretic semantics, IF logic, team semantics.** Hintikka's game-theoretic
  semantics; his Independence-Friendly logic reaching Σ¹₁ expressiveness with
  imperfect-information games; Väänänen's dependence logic and team semantics as the
  contemporary form. This lineage matters doubly: it *is* the modern development of
  the Endoporeutic Game (Hintikka acknowledged Peirce; Pietarinen has documented the
  descent), and it shows a **respectable, live tradition that gains expressive power
  by enriching the game, not the ontology**. Arisbe's semantics is already
  game-theoretic; extending along the GTS axis is continuous with both Peirce and
  the modern mainstream.
- **Simple type theory / HOL.** Church (1940) + Henkin semantics is the engineering
  proof-of-life: Isabelle/HOL and its kin run typed higher-order logic, complete under
  the general-models reading, in industrial mechanized mathematics. The lesson for
  the sortal layer: a *simple* type discipline suffices for enormous reach; dependent
  types and univalence (Coq/Lean/HoTT) are magnificent but solve problems Arisbe does
  not have. The drawn sort layer ≈ simple types, Henkin-read — that is the proven
  configuration.
- **Absolute generality.** The Rayo–Uzquiano/Williamson debate — can one quantify over
  *absolutely everything*? — is the modern form of a constraint Arisbe already draws:
  the **enclosure cap** ([MEANING_BY_HISTORY](MEANING_BY_HISTORY.md)): a tendency (or
  a totality) is sayable *within* a context, malformed when scribed as the structure
  of the unenclosable whole. The sheet of assertion is not a set; Arisbe's refusal to
  let a flat graph quantify over "all graphs including this one" (S1) is its native,
  drawable answer to absolute generality.

## §6 The verdict — are we properly heading there?

**Yes — and the landscape says the heading is not merely defensible but close to the
uniquely sensible one.** The configuration the settled decisions plus memo defaults
describe is, in modern terms:

> a **many-sorted** (drawn-sortal), **predicative** (S1 floor, enclosure escape),
> **Henkin-read** (completeness kept; no set-theoretic hostages),
> **grounded-partial** (K3/`Verdict3`; UNKNOWN for the ungrounded) quotation layer,
> **conservative over the Dau core** (the guarantor untouched), with second-order
> assertion **free at the model-checking register** (finite M; the peel) and
> **restrained at the validity register** (where undecidability and non-absoluteness
> live), extended along the **game-theoretic axis** that is simultaneously Peirce's
> own and the live modern tradition.

Point by point against the open decisions:

- **Decision A (floor):** hold the predicative default. The ladder (§3) names the
  rungs above for a measured later climb; the Kripke/K3 consonance (§4, dragon 12)
  refines the default — stratify *formation* (what may be drawn flat), keep
  *evaluation* partial (what a check returns). The minimal first stratum is the
  forcing memo's `{statement-name, state, forces}` — predicative, one step, with
  existing mechanical semantics.
- **Decision B (open-core):** the criterion stands (an asserted, drawn,
  read-back-checkable second-order claim); the nominee is `(forces s φ)`; and dragon
  10 supplies the non-negotiable rider — *defined, grounded, decidable; never
  axiomatized reflection*. When B is taken, add the **conservativity check** to the
  crossing's verification: the quotation layer must be demonstrated (by test, per
  corpus) to license no new base-level assertion.
- **What Peirce lacked and we now have:** he had the devices (dotted line, dotted
  oval, tinctures, hypostatic abstraction) but not the paradox control; the century
  supplied it in four separable pieces — stratification (Tarski/Russell),
  groundedness (Kripke/Yablo), calibrated comprehension (reverse mathematics /
  predicativism), and conservativity (axiomatic truth theory). Arisbe's crossing
  should take exactly those four, in the many-sorted Henkin reading, and nothing
  more — *vary the sort, ground the semantics, price the comprehension, prove the
  conservativity; never touch the rules.*

## §7 References

Semantics fork and its debates: L. Henkin, "Completeness in the theory of types,"
*JSL* 15 (1950); P. Lindström, "On extensions of elementary logic," *Theoria* 35
(1969); S. Shapiro, *Foundations without Foundationalism: A Case for Second-Order
Logic*, OUP (1991); J. Väänänen, "Second-order logic and foundations of mathematics,"
*BSL* 7 (2001); "Second order logic or set theory?," *BSL* 18 (2012); "Tracing
internal categoricity," *Theoria* 87 (2021); J. Väänänen & T. Wang, "Internal
categoricity in arithmetic and set theory," *NDJFL* 56 (2015); M. Fischer &
M. Zicchetti, "Internal categoricity, truth and determinacy," *JPL* (2023); T. Button
& S. Walsh, *Philosophy and Model Theory*, OUP (2018).

Ontology: W.V. Quine, *Philosophy of Logic*, ch. 5 (1970); G. Boolos, "To be is to be
a value of a variable (or to be some values of some variables)," *J. Phil.* 81 (1984).

Comprehension: H. Weyl, *Das Kontinuum* (1918); S. Feferman, "Systems of predicative
analysis," *JSL* 29 (1964); S. Simpson, *Subsystems of Second Order Arithmetic*, 2nd
ed., CUP (2009); J.-Y. Girard, *Interprétation fonctionnelle…* (System F, 1972);
C. Wright, *Frege's Conception of Numbers as Objects* (1983); the Bad Company
literature (e.g. the 2009 *Synthese* special issue).

Predicate dragons: R. Montague, "Syntactical treatments of modality," *Acta Phil.
Fennica* 16 (1963); S. Kripke, "Outline of a theory of truth," *J. Phil.* 72 (1975);
A. Gupta & N. Belnap, *The Revision Theory of Truth*, MIT (1993); S. Yablo, "Paradox
without self-reference," *Analysis* 53 (1993); JC Beall & J. Murzi, "Two flavors of
Curry's paradox," *J. Phil.* 110 (2013); V. Halbach, *Axiomatic Theories of Truth*,
rev. ed., CUP (2014); A. Enayat & A. Visser, "New constructions of satisfaction
classes" (2015); K. Fujimoto & V. Halbach, "Classical determinate truth I," *JSL*
(2024); the Tarski-boundary program (Łełyk, Wcisło, Cieśliński, 2017–2025).

Tame fragments: J.R. Büchi (1960); M. Rabin (1969); R. Fagin, "Generalized
first-order spectra…" (1974); N. Immerman, *Descriptive Complexity* (1999);
J. Hintikka, *The Principles of Mathematics Revisited*, CUP (1996); J. Väänänen,
*Dependence Logic*, CUP (2007); A. Church, "A formulation of the simple theory of
types," *JSL* 5 (1940); A. Rayo & G. Uzquiano (eds.), *Absolute Generality*, OUP
(2006); A.-V. Pietarinen, *Signs of Logic*, Springer (2006) — the Peirce–Hintikka
GTS descent.
