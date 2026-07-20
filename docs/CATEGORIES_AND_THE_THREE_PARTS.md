# The categories and the three parts — the reduction thesis, Thirdness, and the bootstrap

> **Status: design-of-record memo (2026-07-15), not a book chapter.** Occasioned by the
> author's question, standing at the second-order frontier: how do Peirce's **reduction
> thesis** (every n-adic relation reduces to triads; triads reduce no further) and the
> doctrine that **all thought is Thirdness** relate to how Arisbe models Alpha, Beta, and
> Gamma? The author's suspicion, which this memo affirms and sharpens: Alpha ≈ Firstness,
> Beta ≈ Secondness, Gamma ≈ Thirdness *as analogy*; our **employment** of Thirdness is a
> prerequisite (even where unmodelled) for modelling any of the three; the effort is a
> bootstrap; and much of the project's standing discipline has consisted of keeping what is
> plainly a higher-order concern (e.g. teleology) from **leaking** into the modelling of
> lower-order structure. Companion to
> [SECOND_ORDER_FRONTIER](SECOND_ORDER_FRONTIER.md),
> [SECOND_ORDER_LANDSCAPE_AND_POSITIONING](SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md),
> [FORCING_AND_THE_GAMMA_CROSSING](FORCING_AND_THE_GAMMA_CROSSING.md),
> [M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE](M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md), and
> [MODALITY_WITHOUT_GAMMA](MODALITY_WITHOUT_GAMMA.md). It bears on the two author crossing
> decisions (A: the comprehension floor; B: opening the core) by giving them a categorial
> footing — it forces neither.
>
> **Attribution note (house pattern).** Two glosses below are the assistant's proposals,
> flagged where they occur — **(gloss a)** the universe-rank reading of the analogy in §1,
> and **(gloss b)** the degenerate-Thirdness reading of DAG-modality in §6. The author
> approved recording them as proposals (2026-07-15); they stand open to correction, and any
> later verdict should be written back into this memo rather than silently applied.

## §0 Why this memo

The project has crossed nothing yet. The second-order prep is complete (the
`second_order_check` harness, the two contract memos, the landscape survey, the forcing
dictionary), and only the author's two decisions gate advance. This is exactly the moment to
ask what the *categories* say about the terrain — because if the analogy Alpha/Beta/Gamma ≈
Firstness/Secondness/Thirdness holds in any load-bearing way, it should either ratify or
correct the choices already nominated. The finding of this memo is that it **ratifies them,
and explains them**: the discipline the project has been enacting piecemeal (keep warrant out
of the EGI, keep modality off the sheet, keep the gloss from becoming a fifth form, keep
teleology out of Beta) turns out to be one discipline with a categorial statement — *don't
let the interpretant write itself into the object-sign* — and the second-order landscape
verdict (many-sorted · predicative · Henkin · grounded-partial · conservative) turns out to
be that same discipline in mathematical dress.

## §1 The analogy's true grain: parts ranked by what they newly quantify over *(gloss a)*

Taken strictly — Alpha *is* Firstness, Beta *is* Secondness, Gamma *is* Thirdness — the
analogy fails fast: Alpha already contains the cut (opposition, denial — Secondness-flavored)
and the scroll (conditionality — Thirdness-scented). Each part internally *employs* all three
categories, as anything articulate must (Peirce: no pure Firsts in experience).

The defensible form is: **the three parts are graded by the categorial rank of the universe
their machinery newly makes addressable.**

| Part | Its new primitive | What becomes addressable | Categorial rank |
|---|---|---|---|
| Alpha | the sheet + the cut | whole propositions as unanalyzed monads — qualities of assertion, sheer compossible presence on the sheet | Firstness |
| Beta | the line of identity / the spot with hooks | *existents* — the index, haecceity, "this, here" (quantification over individuals) | Secondness |
| Gamma | the dotted oval, the graph of a graph, abstraction | *representations themselves* — signs, laws, would-bes as objects | Thirdness |

This version also inherits Peirce's involution doctrine for free: Thirdness involves
Secondness involves Firstness, exactly as Gamma presupposes Beta presupposes Alpha (the
dotted second-order line still needs a line of identity to hang on; the line still lives
among cuts). The analogy is *architectural*, not exegetical — Peirce never mapped the parts
to the categories one-to-one, and his Gamma bundled three ambitions (modal, second-order,
metalanguage) that later readers pull apart. But as an account of **why there are three
parts, and why they come in this order**, the universe-rank reading holds.

## §2 The reduction thesis is already ink in Beta — as structure, not as content

Where does "all n-adic relations reduce to triads, and triads to nothing lower" live in
Arisbe? Not at the Gamma frontier at all. It lives in **the branch point of a ligature —
teridentity**. Peirce's own argument for the reduction thesis was *graphical* (the modern
formalizations are Herzberger's "Peirce's Remarkable Theorem" (1981) and Burch's *A Peircean
Reduction Thesis* (1991)): any higher adicity can be bonded out of triads via teridentity,
but a three-way branch cannot be built from two-ended lines. Beta's data model carries this
irreducible triad as **structure** — the ν-mappings, the ligature machinery, the branch
points the renderer draws as a visible spot when three or more hooks meet
(`peirce_latex.py`'s k≥3 case; the `beta_teridentity` corpus exemplars). Every branching
line of identity on an Arisbe sheet is the reduction thesis, exhibited.

What Beta *refuses* to carry is Thirdness as **content**: law, would-be, purpose. And the
striking historical point is that this refusal — the author's "keeping teleology out of
Beta" — **is Peirce's own discipline, a century before the codebase**. The Alpha/Beta scroll
is the conditional *de inesse* (*Prolegomena*, 1906, CP 4.546; see
[GLOSSARY "Would-be / de inesse"](GLOSSARY.md#would-be--de-inesse)): material implication,
deliberately stripped of the would-be. Peirce knew the law-like conditional was Thirdness
proper and reserved it for Gamma.

Arisbe repeats the move exactly, in the Agon register. A "law" in the domain model M is mere
Beta-shaped ink — `~[ B ~[ H ] ]`, a scroll, a material conditional on a sheet. Its
law-character lives entirely in **use**: the materializer forward-chains it, the peel bets on
it, disuse-decay erodes it when it stops earning re-delivery. That is Peirce's doctrine of
habit made operational — a habit is real but visible only in behavior. The scroll on the
sheet is Secondness-compliant ink; its Thirdness is enacted by the game, never written on the
sheet.

## §3 Thirdness as employed prerequisite: the bootstrap is institutionalized as §3.3

All thought is in signs (the 1868 cognition papers), and a sign is irreducibly triadic —
representation, "A stands for B *to* C," is the paradigm case the reduction thesis exists to
protect from dyadic dissolution. So the act of modelling even Alpha — writing a parser, an
attestation, a correspondence contract — is already an exercise of Thirdness. The author's
suspicion is right, and in Arisbe it is not merely a philosophical observation; it is
institutionalized:

- **The correspondence invariant is a triad.** The linear form and the drawn form are two
  signs of one object (the EGI, the mathematical individual), and the correspondence check
  (§3.3 of [LINEAR_GRAPHICAL_CORRESPONDENCE](LINEAR_GRAPHICAL_CORRESPONDENCE.md)) is the
  **produced interpretant** that binds them. The central engineering problem of the project
  is a Thirdness problem, employed at every level including Alpha.
- **Every rule application is an interpretant event** — the attestation model of
  [CHAIN_OF_SEMIOSIS](CHAIN_OF_SEMIOSIS.md), read categorially.
- **"The LLM argues, the calculus decides"** is the same structure one register up: the
  calculus is the habit, the Third, kept incorruptible precisely by being *employed* rather
  than represented — mechanical, non-negotiable, outside the space of moves it referees.

The tower this yields: Thirdness-in-use (the referee, the attestation, the rules) always
stands one level above whatever is modelled. Gamma / second-order is the moment the system
begins to **mention** what it previously only **used** — and it can never mention all of it,
because the act of mentioning employs a fresh, unmentioned Third. That is why the bootstrap
is not vicious. It is a ladder, not a circle.

## §4 The ladder's Peircean name: hypostatic abstraction

Peirce's ascent operator — "sweet" becomes "sweetness," a predicate-in-use becomes a
subject-mentioned (see [GLOSSARY](GLOSSARY.md#hypostatic-abstraction) and
SECOND_ORDER_FRONTIER's reading of it as the heart of Gamma-as-second-order) — is precisely
the mechanism by which one level's Thirdness becomes the next level's **Firstness**: an
unanalyzed object of a new sort. Both decision-B nominees are instances of it applied to a
whole graph:

- `(forces s φ)` (from FORCING_AND_THE_GAMMA_CROSSING): the graph-in-force — a habit, used —
  becomes a graph-named, an individual of a new sort. The many-sorted half of the landscape
  verdict falls straight out of the operation.
- `(superseded ⌜M⌝ …)` (from M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE): the withdrawn model,
  present-without-force — quotation as the third tense.

And the categories **recur at the new level**, which is the sign that the ascent is genuine:
quoted graphs are the new monads (Firstness); identity-and-difference of quotations — which
is exactly `same_graph`, the full-isomorphism authority — is the new Secondness; and laws
*about* graph-change are the new Thirdness. Note that the third of these is **already
inhabited, informally**: `agon_metalearning.resolution_principles` mines habits about
habit-revision — which disposition durably resolves which situation — from the record of
play. The meta-level exists; decision B only decides whether it gets *ink* (a drawable,
attested, read-back-checkable form) rather than living as an off-sheet instrument.

(Side connection, recorded: Peirce held theorematic reasoning to require hypostatic
abstraction, and the foundations memo of 2026-07-14 made the corollarial/theorematic
distinction decidable from the chain. Mention-ascent is where the theorematic
machinery becomes native rather than borrowed.)

## §5 The landscape verdict *is* the categorial doctrine in mathematical dress

The project's leak-prevention record — each move made independently, on local grounds — reads
as one discipline once stated categorially: **don't let the interpretant write itself into
the object-sign.**

| The move (where) | What leaked, had it gone the other way |
|---|---|
| warrant lives in overlays/annotations, never in the EGI (import model; standing badges) | the interpretant's *appraisal* written into the sign appraised |
| the English gloss is not a fifth form (NL reading) | a non-round-tripping interpretant granted assertoric standing |
| modality read off the DAG, no modal mark on the sheet (MODALITY_WITHOUT_GAMMA) | Thirdness-as-content smuggled into Beta ink |
| M-residence resolved structurally (circumscription), not by metadata | warrant-as-metadata — the forbidden move, caught and rejected |
| the referee mechanical; LLM output reduced to calculus artifacts and re-checked | interpretant-production handed to a negotiable party |
| use/mention fork at the reference node deferred to decision B | mention conflated with use before the discipline existed to separate them |

At the second-order frontier this discipline acquires **formal names**, and they are exactly
the landscape verdict's choices:

- **Conservativity** is the leak-prevention *theorem*: the reflection layer must prove no new
  theorems in the old vocabulary. "Keeping teleology out of Beta" stops being a vigilance and
  becomes a checkable property of the extension.
- **Predicativity** is the honest *bootstrap*: never quantify over a totality that includes
  the very act of quantifying. Decision A's default floor — predicative stratification with
  the enclosure escape — is this acknowledgment drawn as cuts: the modeller's Thirdness
  always stands one enclosure above the modelled.
- **Henkin semantics** is unlimited semiosis *respected*: the second-order quantifiers range
  over the Thirds actually constructed — the interpretants produced so far — never over an
  absolute totality. Full second-order semantics would claim the **final interpretant** as a
  surveyable object; Peirce's doctrine is that semiosis does not terminate, the final
  interpretant being a regulative limit, not an inventory. **Henkin is therefore not the
  timid choice; it is the Peircean one.**

So the categorial reading does not merely decorate decisions A and B. It explains why the
harness defaults are right *as philosophy*, independently of their being right as safety.

## §6 Degenerate Thirdness as a feature *(gloss b)*

Peirce distinguishes genuine from degenerate forms of the higher categories; degenerate
Thirdness is Thirdness resolvable into patterns among Seconds. Read in those terms,
MODALITY_WITHOUT_GAMMA's trajectory reading — possibility and necessity read off the
branching DAG of actual transitions, no modal mark on any sheet — is **deliberately
degenerate Thirdness**: law as a pattern among dyads of states, the would-be known only
through its actualizations.

The proposal of this gloss is that this is a *feature*, and of a piece with the project's
warrant epistemology (§3.3 attests correspondence, not truth; M self-certifies a track
record). The trajectory reading claims exactly as much Thirdness as the record can carry;
genuine Thirdness — the would-be as such — remains **regulative**, the thing the record is
evidence *of*, never an object on the sheet. It also explains Gamma's unfinishedness in
Peirce's hands without imputing failure: Thirdness resists complete objectification *in
principle*, since every representation of representation employs a representation-relation it
does not represent. The consequence for the crossing is a design maxim the memos already
obey, now with its reason attached:

> **Aim at an open, drawable ladder — never a closed Gamma.** Each act of reflection gets
> ink on a sheet, is attested, and is itself subject to further reflection one enclosure up.
> A system that claimed to model *all* its own Thirdness (full semantics, impredicative
> comprehension, a self-applying truth predicate) would be pretending to stand outside the
> semiosis it is a moment of — and dragons 9 and 10 of the landscape survey are what that
> pretense looks like when it fails formally.

## §7 What this memo changes

Nothing is forced, and no code moves. What the categorial reading contributes:

1. **The two crossing decisions gain a philosophical footing.** Decision A's predicative
   floor and decision B's quotation nominees are not merely the technically safe rungs — they
   are what the categories, read through the reduction thesis and unlimited semiosis, *say
   the crossing should look like*. If the author later prefers a different floor or a wider
   opening, the argument to beat is now stated.
2. **The leak-discipline has a name and a test.** Future "does this belong in Beta?"
   questions can be asked as: *is this the interpretant trying to write itself into the
   object-sign?* — and, post-crossing, answered by the conservativity check rather than by
   vigilance alone.
3. **A marker for the recurrence of the categories one level up.** When quotation ink
   arrives, expect the triad to reappear: quoted graphs as monads, `same_graph` as the new
   Secondness, metalearning's principles as the new Thirdness — and expect a *third*-order
   temptation eventually, to be met with the same discipline.

## References (beyond the companions)

- Peirce, "The Logic of Relatives" (*The Monist*, 1897) — the reduction thesis; the 1868
  cognition papers (*Journal of Speculative Philosophy*) — all thought in signs;
  *Prolegomena to an Apology for Pragmaticism* (1906, CP 4.546) — *de inesse* vs would-be.
- Herzberger, "Peirce's Remarkable Theorem" (1981); Burch, *A Peircean Reduction Thesis*
  (1991) — the modern formalizations of the reduction thesis via teridentity/bonding.
- Roberts, *The Existential Graphs of Charles S. Peirce* (1973) — Alpha/Beta perfected,
  Gamma tentative and unfinished (already load-bearing in SECOND_ORDER_FRONTIER).
