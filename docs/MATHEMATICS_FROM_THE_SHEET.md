# Mathematics from the sheet

> How arithmetic grows out of logic when you draw it — and what you learn about
> Existential Graphs by watching it happen.

This is a ladder, not a list. Each rung teaches one device of the graphs and earns
one piece of mathematics with it, in the order Peirce himself builds them. Climb it
and you should end up understanding both things better than you would have learned
either alone: that is the whole claim.

The mathematics is Peirce's ("On the Logic of Number," 1881 — the first successful
axiom system for the naturals, later shown equivalent to Dedekind's and Peano's).
The reading of it follows Jessica Carter, *Logic of Relations and Diagrammatic
Reasoning* (in Reck & Schiemer, eds., *The Prehistory of Mathematical
Structuralism*, OUP 2020, ch. 10), whose thesis is the one that makes the ladder
possible:

> For Peirce a number is **not an object but a position in a relational system**.
> Mathematics is the *activity* of drawing necessary conclusions — construct a
> diagram, experiment on it, observe what must be so.

Code: [`src/peirce_arithmetic.py`](../src/peirce_arithmetic.py),
[`src/proof_character.py`](../src/proof_character.py). Corpus:
`peirce_order_1881`, `arithmetic_from_two_laws`, `numeral_three_unfolds` (built by
[`tools/build_arithmetic_ladder.py`](../tools/build_arithmetic_ladder.py) — open
them in Organon and step through the moves).

---

## Rung 0 — the blank sheet

Nothing is scribed. Nothing is asserted. This is the one unconditioned context, and
it is worth a moment: everything below is *added* to it, and a graph means nothing
until it is asserted *somewhere*.

## Rung 1 — a relation, not a number

**Draw:** `(lt "1" "2")` — a spot with two hooks, and two names on them.

Here is the first surprise, and it is the whole of Peirce's structuralism: the
primitive is the **relative**, not the number. He does not begin with 1, 2, 3 and
then notice they are ordered. He begins with an *order* and lets the numbers be the
places in it. Carter: the naturals are introduced "as a collection together with a
particular relation defined on it."

*The EG lesson:* a relation is a spot; its arguments are the lines that touch it.
Argument order is drawn, not written.

## Rung 2 — the scroll: a cut inside a cut is *if–then*

**Draw:** transitivity.

```
~[ (lt *x *y) (lt y *z) ~[ (lt x z) ] ]
```

Read it aloud the way Peirce reads it: *"It is not the case that (x<y and y<z) while
also not (x<z)."* — which is exactly *if x<y and y<z, then x<z*. The outer cut with
an inner cut is the **scroll**: implication, drawn.

And look at the lines. `*x` declares a line; `x` re-uses the *same* line. The line
of identity crossing the inner cut is what makes the conclusion talk about the very
same individuals as the premiss. **The variable is a line, and the line is
literally continuous.** That is the thing no algebraic notation can show you.

*The EG lesson:* the scroll; the line of identity as the variable.

## Rung 3 — the order: cut depth *is* quantifier alternation

**Draw:** Peirce's six axioms (Shields' reconstruction; all six live in
`peirce_arithmetic.ORDER_AXIOMS` and every one of them parses and renders).

| | axiom | what it says |
|---|---|---|
| P1 | `~[ [*x] (lt x x) ]` | nothing is less than itself |
| P2 | `~[ [*x] [*y] [*z] (lt x y) (lt y z) ~[ (lt x z) ] ]` | the order is transitive |
| P3 | `~[ [*x] [*y] ~[ (lt x y) ] ~[ (= x y) ] ~[ (lt y x) ] ]` | any two are ordered, or the same |
| P4 | `~[ [*x] ~[ [*y] (lt x y) ~[ [*z] (lt x z) (lt z y) ] ] ]` | each has a *next* — nothing squeezes between |
| P5 | `[*x] ~[ [*y] ~[ (lt x y) ] ~[ (= x y) ] ]` | the count starts somewhere |
| P6 | `~[ [*x] ~[ [*y] (lt x y) ] ]` | and never has to stop |

Now count the cuts in **P4**. It is three deep, and its logical shape is
∀x ∃y ¬∃z — *for every x there is a y with nothing between*. The nesting **is** the
quantifier alternation. You are not encoding ∀ and ∃; you are *seeing* them: an
odd number of cuts around a line makes it universal, an even number makes it
existential. Nothing else in logic shows a student that so directly.

Together P1–P6 say: **a discrete linear order, with a least element, going on
forever.** That is the naturals — and not one numeral has been written.

*The EG lesson:* cut depth = quantifier alternation; polarity is countable by eye.

## Rung 4 — identity, and an honest departure

For Peirce, identity is not a relation but the **line of identity itself**: two
hooks joined by one continuous line *are* one individual. It is an icon of identity,
not a statement about it — which is why EG needs no `=` sign at all, and why it is
one of the most beautiful things in the system.

But look again at P3 and P5. They put `x = y` in the **consequent** of a scroll. And
there the icon fails: *you cannot make two lines become one line as the conclusion of
an implication.* A ligature is drawn or it is not — it cannot be *inferred*. So
Arisbe's fixtures use `(= x y)`, an equality **spot**, exactly as first-order logic
with equality does.

**This is a real departure from Peirce, and it is recorded as one**
([FIDELITY_AND_DEPARTURES](FIDELITY_AND_DEPARTURES.md)). What is kept: wherever
identity is merely *asserted*, Arisbe still draws it Peirce's way — as one shared
line. What is given up: iconicity precisely where identity must be *concluded*.

*The EG lesson:* what the line of identity can and cannot do — and the value of
naming a departure instead of quietly patching it.

## Rung 5 — a number is a place

Existential graphs have **no function symbols**. There is no `s(x)`; there is only a
relation. So the successor is scribed `(succ x y)` — "y is next after x" — and a
stretch of the numbers is a chain of them:

```
(succ "0" "1") (succ "1" "2") (succ "2" "3") (succ "3" "4") (succ "4" "5")
```

"3" is now *where you stand*, not something you hold. This is exactly Carter's
point, and the absence of function symbols — which looks like a limitation — turns
out to *enforce* Peirce's own structuralism.

## Rung 6 — the numeral: a type, shown through a token

Peirce: a diagram is a **type**, and can only be shown through a replica — a
**token**. So it is with a numeral. Define:

> **three** (n) := `(succ "0" *a) (succ a *b) (succ b *n)`

Now `(three *k)` is one spot, and *unfolding* it returns the chain — checked
conservative by `same_graph`, so the numeral adds no content, only a **name**. Fold
to compute, unfold to see why. (Corpus: `numeral_three_unfolds`; machinery:
`definitions.py`, already used for the schema/definition track.)

*The EG lesson:* definitions are abbreviations you can always cash out — the logic
under a working notation stays recoverable, one click away.

## Rung 7 — addition: two drawn laws grow the whole table

**Draw two graphs.**

```
~[ (num *x) ~[ (sum x "0" x) ] ]                                  % x + 0 = x
~[ (sum *x *y *z) (succ y *sy) (succ z *sz) ~[ (sum x sy sz) ] ]  % x + s(y) = s(x+y)
```

Both are scrolls — you already know how to read them from rung 2. Now
forward-chain them (`model_materialization`, which computes the least Herbrand
model of the Horn fragment) and watch what happens: **the entire addition table
grows on the sheet.** Twenty-one sums, from two drawn laws and a chain of
successors. Nobody typed in `2 + 3 = 5`.

And then you *read it off the diagram*:

```
(sum "2" "3" "5")   →  TRUE
(sum "2" "3" "6")   →  FALSE
```

This is **corollarial reasoning** in Peirce's exact words: "carefully taking account
of the definitions of the terms." Construct the diagram the hypothesis prescribes;
experiment on it; observe the conclusion. It is not a metaphor for what Arisbe does
— it is a description of what just happened.

**A lesson hides in the verdict.** On the bare successor-chain, before the laws
land, `2 + 3 = 5` reads **FALSE** closed-world — because that system simply *has no
addition*; the laws are what make the claim true. (Open-world it reads UNKNOWN: the
sheet is merely silent.) Peirce again: mathematics "frames and studies the
consequences of hypotheses." Change the hypotheses and you change what is so.

*The EG lesson:* a law is a graph, and drawn laws *do work* — the sheet computes.

## Rung 8 — the character of a proof, decided by machine

Peirce split necessary reasoning in two, and thought it his deepest find in logic
(Hintikka called it "Peirce's first real discovery"):

- **corollarial** — the conclusion is read off the diagram the definitions already
  give you;
- **theorematic** — the proof "requires the invention of an idea not at all forced
  upon us by the terms of the thesis." Euclid I.32 is the type case: to get the
  angle sum you must **draw an auxiliary line** the statement never mentions.

Philosophers have argued about that distinction for a century because it never had a
mechanical criterion. **In Dau's calculus it has one, and it is sharp:**

> A derivation is **corollarial** iff it uses only rules that cannot add content —
> erasure, iteration, deiteration, double-cut. It is **theorematic** iff it needs
> **insertion**: the one rule that scribes a subgraph the premisses do not contain.
>
> *The auxiliary line and the insertion step are the same act.*

Arisbe records every rule application, so this is computable
([`proof_character.py`](../src/proof_character.py)). Run it over the corpus and the
split lands exactly where a mathematician's intuition puts it:

| character | proofs |
|---|---|
| **theorematic** (needs INS) | Peirce's Law · Leibniz's *Praeclarum Theorema* · *ex falso* |
| **corollarial** (no INS) | modus ponens · de Morgan · contraposition · hypothetical syllogism · Barbara |

The theorems that need "a trick" are exactly the ones that need an insertion. A
century-old distinction becomes a property you can compute from an attested
artifact. (Honest limits, kept in the report: the verdict is about the *derivation*,
not the theorem — a better proof may be corollarial; and a *derived* step collapses
primitives the reader cannot see, so it makes a corollarial reading **provisional**
rather than silently clean.)

*The EG lesson:* the six rules are not bureaucracy. One of them — and only one —
can introduce an idea, and that fact carries philosophical weight.

## Rung 9 — where the sheet ends

Try to draw induction.

Peirce's version is the **least-number principle**: every non-empty class of numbers
has a least member. Write it out and you get "*for every property ψ* …" — and there
the sheet runs out. A first-order existential graph can quantify over *individuals*
(that is what a line of identity is), but it cannot quantify over *propositions*:
**there is no line you can draw whose end is a graph.**

So induction is not a graph but a **schema** — a graph with a hole
([`schema.py`](../src/schema.py)'s φ-hole), plus an external rule licensing every
instance. Exactly how PA and ZFC do it.

And notice where this bites, concretely. At rung 7 you could *see* that addition
commutes across the stretch you drew — peel it and it comes back TRUE. But that is
verification on a finite model, not proof for **every** number. To get from "true of
all the ones I drew" to "true of all there are," you need induction — and induction
is the one thing the sheet cannot hold.

That is not a defeat. It is the border between the first order and the second, drawn
precisely where Peirce himself left it, and it is why the frontier
([SECOND_ORDER_FRONTIER](SECOND_ORDER_FRONTIER.md)) is where it is: the crossing
would let that hole become a *line* — a graph about graphs.

---

## What the ladder teaches, in one breath

**For the logician:** a relation is a spot, a variable is a line, implication is a
cut in a cut, quantifier alternation is cut depth, and exactly one of the six rules
can add an idea.

**For the mathematician:** numbers are positions in a relational system; two drawn
laws generate arithmetic; "corollarial vs theorematic" is a computable property of
your proof; and induction is precisely, visibly, the step out of first-order logic.

**For both:** practical mathematics and logic are not neighbours who wave. Draw the
order, and the arithmetic falls out of it.

## References

- C. S. Peirce, "On the Logic of Number," *American Journal of Mathematics* 4
  (1881), 85–95. (CP 3.252–288.)
- C. S. Peirce, "Prolegomena to an Apology for Pragmaticism," *The Monist* (1906).
  (CP 4.530–582 — diagrammatic reasoning; the corollarial/theorematic distinction at
  NE IV, 8.)
- Jessica Carter, "Logic of Relations and Diagrammatic Reasoning: Structuralist
  Elements in the Work of Charles Sanders Peirce," in E. Reck & G. Schiemer (eds.),
  *The Prehistory of Mathematical Structuralism*, OUP (2020), ch. 10.
- Paul Shields, "Peirce's Axiomatization of Arithmetic," in Houser, Roberts & Van
  Evra (eds.), *Studies in the Logic of C. S. Peirce*, Indiana UP (1997), 43–52.
- Jaakko Hintikka, "C. S. Peirce's 'First Real Discovery' and Its Contemporary
  Relevance," *The Monist* 65 (1980), 182–188.

In this repo: [MATH_FIXTURES_ZFC_PEIRCE_1881](MATH_FIXTURES_ZFC_PEIRCE_1881.md) (the
axioms as fixtures, ZFC included) · [SCHEMA_HOLE_CORRESPONDENCE](SCHEMA_HOLE_CORRESPONDENCE.md)
(the φ-hole) · [FIDELITY_AND_DEPARTURES](FIDELITY_AND_DEPARTURES.md) (the equality
departure) · [SECOND_ORDER_FRONTIER](SECOND_ORDER_FRONTIER.md) (what lies past rung 9).
