# A Field Guide to Existential Graphs — with the Dragons Marked

*For someone just starting with Peirce's graphs, or just starting with Arisbe.
No prior logic required. The deep, technical, historical treatments live in the
companion docs (named at the end); this is the on-ramp and the map of where
beginners — and famous experts, and Peirce himself — tend to fall in.*

Old maps wrote **hic sunt dracones** — "here be dragons" — at the edges of the
known, where ships were lost. Existential Graphs have a handful of such places:
spots where the picture looks like it says one thing and means another, or where
a natural-seeming move is illegal, or where a question feels deep but is actually
malformed. This guide marks them, explains why each is tempting, and gives the
antidote — each worked in Arisbe's own notation, which you can type into the
viewer and check.

---

## Before the dragons: three things to hold onto

**1. The graph *is* the proposition — not a picture about it.** A bar chart is a
picture *about* some numbers. An Existential Graph is not about a proposition; it
**is** the proposition, drawn. You reason *inside* it, by changing the picture
under rules that never let it come to say something false.

**2. The blank sheet is the one free truth.** An empty sheet of assertion says
nothing — and *because* it denies nothing, it is simply **true**. It is the one
thing in the whole system that cannot be wrong, and the thing every proof starts
from and can always be erased back to.

**3. Two utterly different ways something gets onto the sheet.** This is the
single most important distinction in the whole guide, and the source of half the
dragons:

- You can **posit** it — scribe a premise, a thing you are *claiming*. "Take this
  as given." It might be false.
- You can **derive** it — reach it from the blank by the rules, which are
  truth-preserving. A derived graph *cannot* be false; the system handed it to
  you.

A drawing on the sheet does not, by looking at it, tell you which of these it is.
Keeping them apart is most of wisdom here.

---

## The first dragon, answered: "I saw `cat-on-mat` on a blank sheet — how is that possible?"

You open Arisbe, and there on the sheet is

```
(Cat *x) (On x *y) (Mat y)
```

— "a cat is on a mat." But cats are not on mats *as a matter of logic*. How did
a blank sheet, which is supposed to yield only guaranteed truths, give you a
contingent fact about furniture and animals?

**It didn't.** Nobody *derived* cat-on-mat. Someone **posited** it — scribed it
as a premise (in Arisbe: imported it, or sent it to be tested). The rules will
*never* hand you `(Cat *x) (On x *y) (Mat y)` from the blank, because it is
**contingent** — it could be false — and the rules only ever preserve truth. So
if it is sitting on the sheet, it got there by assertion, not by proof.

The confusion is real and it is not your fault: textbooks routinely print a
*posited premise* and a *derived theorem* on the same blank sheet, side by side,
**with no mark telling them apart**. Peirce's late work (the 1906 "Phemic
Sheet") is clear that to assert is to *take responsibility* for a claim — an act,
not a feature of the drawing — but the everyday alpha/beta presentations leave
the seam unmarked. Arisbe marks it: a posited premise enters at **low warrant**
(carrying where it came from), while a theorem is the end of a chain of sound
steps. Same picture; two completely different standings; which one it is *is* the
question.

> **Try it.** Ask Arisbe to *derive* an unenclosed contingent atom from the blank
> sheet. You can't — there is no legal sequence of rules that does it. Then notice
> what you *can* derive from the blank: scaffolding like `~[ (P *x) ~[ (P x) ] ]`
> ("if P then P"), which is true no matter what P is. The blank is generous with
> *form* and gives you no *contingent content* for free.

---

## The map of dragons

Each entry: 🐉 the mistake · why it tempts (you're in good company) · the antidote
· a worked example you can check.

### 🐉 1. The missing outer cut — "every" vs "some-isn't"

By far the most common beginner error, and the tool will catch you (it caught the
author of this guide while it was being written).

You want to say **"every human is mortal"** and you write:

```
(Human *x) ~[ (Mortal x) ]
```

That is **wrong**. With `Human` out on the sheet (asserted) and only `Mortal`
under a cut, this reads **"there is a human who is *not* mortal"** —
`Human(x) ∧ ¬Mortal(x)`. You've drawn the *opposite* of what you meant.

**Why it tempts:** "mortal, negated, attached to a human" *feels* like "humans
must be mortal." It isn't.

**The antidote — the scroll.** "If… then…" needs an **outer cut wrapped around
the whole thing**, with the conclusion nested one deeper:

```
~[ (Human *x) ~[ (Mortal x) ] ]
```

Now it reads `¬(Human(x) ∧ ¬Mortal(x))` = **"every human is mortal"**
(∀x: Human(x) → Mortal(x)). This nested shape — a cut inside a cut with the
antecedent in the outer ring — is called a **scroll**, and it is the EG picture
of implication. The rule of thumb: **a conditional always lives inside an outer
cut.** If your "if-then" has its antecedent sitting bare on the sheet, you have
drawn an existential, not a universal.

### 🐉 2. The blank sheet vs. the empty cut — true vs. false

The blank sheet means **true**. A cut drawn around *nothing* — `~[ ]` — means
**false** (the absurd, the impossible). "Nothing drawn" and "a cut around
nothing" are opposites, not the same.

**Why it tempts:** both look almost empty.

**The antidote:** an empty cut is the strongest claim you can make — it says "this
is impossible." Put one next to anything and you've declared the whole sheet
false. (So `(Human *x) ~[ ]` is not "a human exists and… nothing"; the empty cut
poisons the sheet to falsity.) When you mean "true / I'm done / nothing left to
say," you want the *blank*, not a cut around a blank.

### 🐉 3. The double cut you are *not* allowed to remove

Two cuts directly nested cancel — `~[ ~[ P ] ]` is just `P` (not-not-P), and the
"double-cut" rule (DC−) lets you peel both away. So beginners try to peel *any*
two nested cuts. Dragon.

The rule only applies when there is **nothing in the ring between the two cuts.**
Compare:

```
~[ ~[ (P *x) ] ]            ← nothing between the cuts → DC− removes both → (P *x)
~[ (P *x) ~[ (Q x) ] ]      ← P sits between the cuts → this is a SCROLL (P→Q)
```

The second is the implication from dragon 1. If you "remove the double cut" there,
you turn "if P then Q" into "P and Q" — you've invented a claim. **Antidote:**
before peeling, look in the ring between the two ovals. Anything there? Then it is
not a removable double cut; it is a conditional doing its job.

### 🐉 4. The line of identity — `*x` declares, `x` refers

A heavy line is "something exists," and the **same** line threaded through several
spots says "the same something." In the written form:

- `*x` (with a star) **introduces** a fresh line — "there is an x…"
- `x` (no star) **refers back** to a line already introduced.

So in `~[ (Human *x) ~[ (Mortal x) ] ]`, the *one* line `x` is born in the outer
ring and reaches into the inner cut — that single thread crossing the boundary is
what makes it *the same* individual in "if a human, then *that one* is mortal."

**Why it tempts / the dragon:** writing `*x` twice makes **two different**
individuals; a beginner who writes `(Human *x) ~[ (Mortal *x) ]` has said "some
human, and separately, something is not mortal" — the line never connected.
**Antidote:** star a line **once**, where it first appears; refer to it bare
everywhere else. In the *drawn* form this is automatic — you literally draw one
connected line — which is part of why the picture is often clearer than the text.

### 🐉 5. Argument order — `(Loves *x *y)` is not symmetric

`(Loves *x *y)` means "**x** loves **y**." Swap the hooks and you've said y loves
x — a different claim, and a silent one: nothing *looks* wrong.

**Why it tempts:** the two arguments look interchangeable on the page.
**The antidote:** order is part of the meaning, and it is *drawable* — Peirce
read the hooks clockwise around the spot; Dau numbers the lines 1, 2, …. Arisbe
preserves the order through every transformation and round-trip, and can show the
numerals. When a relation isn't symmetric, *check the order the way you'd check a
minus sign.*

### 🐉 6. "Which graph is *closer to reality*?" — a question with no answer

This one trapped philosophers for a century, so do not feel bad. You have two
rival graphs; you want to ask which is **nearer the truth**, nearer **reality**.

**It is a malformed question — pointless, not merely hard.** Asking whether a
representation is "nearer to *being* the world" is like asking whether a map is
nearer to *being* the territory. A map can be **faithful** (every road in the
right place) without being the land; "how close is this map to being Spain?" is a
non-question. Arisbe is built on exactly this discipline: it checks that your
**picture and your sentence say the same thing** (it calls this *correspondence*),
and it **never** claims to measure "truth" or "nearness to reality." Its own motto
is *attest correspondence, never truth.*

**So how does anything get to count as true?** Not by a truth-meter — by
**surviving challenge**. You play a claim out against what you already hold, in
the contest Peirce called the game (Arisbe's *Agon*); a claim that withstands the
attack earns standing, and a claim can always *lose* standing later. "Fact" here
is "the last claim still standing," held open to being overturned — never a
distance-reading on a dial. (The long version of this, and where it genuinely
parts from Peirce, is in `FIDELITY_AND_DEPARTURES.md`; you don't need it to start.)

### 🐉 7. "I need a special mark for *possibly* / *necessarily*"

You want to say "P is **possible**," and you reach for a new kind of ink — a
dotted oval, a colored region. Peirce did too (he tried "broken cuts" and colored
"tinctures" for years). Dragon: you don't need one.

**The antidote:** "possibly P" means "**in some reachable situation**, P holds" —
and "some situation" is just an *existence* claim, which the ordinary line of
identity already draws. Arisbe keeps the different situations as different sheets
in its history (and its library of models); "possible" = "true on some sheet you
can legally reach," "necessary" = "true on every one." No new mark — the same
quantifiers you already have, ranging over situations that are themselves *drawn*.
(And the hard rule behind it: **no mark may claim "this is the real/actual
world."** That's the map-not-territory dragon again, wearing a costume.)

### 🐉 8. "I named it a *definition* (or an *assertion*), so it counts"

You fold a tangle of graph under a tidy new name and feel you've earned
something; or you call a drawing "an assertion" and feel it now carries force.

**Dragon: a name purchases nothing.** A definition is legitimate only because it
**unfolds** back to exactly what it abbreviates and the rules accept the swap —
not because you gave it a dignified label. Likewise "assertion" is not a property
of where a mark sits; it is an *act* of taking responsibility, tested in the game.
**Antidote:** whenever a name seems to be doing the work, ask to see the
**expansion** (what does it unfold to?) and the **warrant** (what challenge has it
survived?). If the answer is "just the name," it counts for nothing.

---

## How not to get lost — the compass

Four headings that keep you off the rocks:

- **Posited vs. derived.** Always know whether a graph is a premise you put there
  or a theorem the rules handed you. (Dragons 1-of-cat-on-mat, 8.)
- **Inside vs. outside a cut flips everything.** One oval is the difference between
  "is" and "isn't," between "some" and "every." Count your cuts. (Dragons 1, 2, 3.)
- **Correspondence, not truth.** Arisbe guarantees the picture and the sentence
  agree. It does *not* sell you truth or "nearness to reality." Truth is earned by
  surviving challenge and can be lost again. (Dragon 6.)
- **Everything erases back to the blank.** Nothing here is frozen. The one
  bedrock is the empty sheet, which says nothing and so cannot be wrong; every
  claim above it is surrenderable.

> **Where to practice in Arisbe itself.** The workshop's **freeform canvas** lets
> you draw a graph by hand and asks Arisbe to *read it back* to you — so you see
> immediately whether your picture says what you meant (dragons 1-5 surface here
> instantly). **Challenge mode** gives you a target proposition, lets you draw it
> freehand, and grades your attempt with a plain-language diff of how it differs.
> Those two are the fastest way to meet the dragons safely.

---

## When you're ready for the dragons' biographies

Each dragon here has a full, technical, historical treatment for when you want it
— including the places where Peirce *himself* was unsettled and where the
scholarship still argues:

- `ARISBE_IN_PRACTICE.md` — what Arisbe is, told through the people who use it.
- `CHAIN_OF_SEMIOSIS.md` — why a proof is a *chain* of sound steps (the
  posited-vs-derived distinction, made precise).
- `LEVEL_ZERO_AND_THE_REGISTERS.md` — the deep version of cat-on-mat and dragon 8.
- `MODALITY_WITHOUT_GAMMA.md` — the deep version of dragon 7.
- `FIDELITY_AND_DEPARTURES.md` + `ADVERSARIAL_EXAMINATION.md` — the deep version
  of dragon 6, including a five-round examination of exactly where Arisbe parts
  from Peirce and why (and where it owes an argument it does not yet hold).

The point of a field guide is that **you should not need any of those to begin.**
Draw on the blank sheet. Watch the cuts. Ask whether a thing was posited or
derived. The dragons are few, and now they are on the map.

---

**Created**: 2026-06-19. Examples verified against Arisbe's EGIF parser and
Chapter-18 FOPL translation.
