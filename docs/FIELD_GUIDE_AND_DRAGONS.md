# A Field Guide to Existential Graphs — with the Dragons Marked

*For someone just starting with Peirce's graphs, or just starting with Arisbe.
No prior logic required. The deep, technical, historical treatments live in the
companion docs (named at the end); this guide serves as the on-ramp and the map
of the places where beginners, famous experts, and Peirce himself tend to fall in.*

Old maps wrote **hic sunt dracones** — "here be dragons" — at the edges of the
known, where ships were lost. Existential Graphs have a handful of such places:
spots where the picture looks like it says one thing and means another, or where
a natural-seeming move breaks the rules, or where a question feels deep but
arrives malformed. This guide marks them, explains why each tempts, and gives the
antidote — each worked in Arisbe's own notation, which you can type into the
viewer and check.

*(This guide is about the **graphs**. For the story of where Arisbe knowingly
**departs** from Peirce and the traditions that read him — the doubts, the
arguments, and what changed — see the plain-language
[FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md). Dragon 6 below is its
doorway.)*

---

## The marks, in plain sight

Before any dragons, the whole alphabet — four marks in all, and you can
draw every one of them with a pen:

- **The sheet** — the page. To **draw something on it is to assert it** (to claim
  it). The empty page asserts nothing, and so stands simply **true**.
- **A cut** — a closed curve. To put something inside
  a cut is to **deny** it. One cut = **not**.
- **Nested cuts** — a cut inside a cut, with a claim in the ring between them,
  reads as **"if … then …"**. (This shape has a name, the *[scroll](GLOSSARY.md#scroll)*; "if-then" is
  all you need.)
- **A line** — a heavy line joining marks says **"the same one"**; a line on its
  own says **"something exists."**

That exhausts the visual language. **The picture is the real thing**; everything
in logic that matters here, you can *see*.

**The written shorthand.** Because you can't always draw in a text box, Arisbe also
has a typed form (called Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif))) — the examples below use it, so here is the key:

| You type | It means | In a drawing |
|----------|----------|--------------|
| `(Cat *x)` | "there is a cat" — `*x` starts a **new** line | a spot labelled *Cat* on a fresh line |
| `(On x *y)` | "…it is on some *y*" — bare `x` reuses the **same** line | the same line, now also at *On* |
| `~[ … ]` | a **cut** around `…` — "**not** …" | a cut enclosing those marks |
| `~[ A ~[ B ] ]` | "**if** A **then** B" — A in the ring, B nested deeper | nested cuts (the scroll) |
| `~[ ]` | a cut around **nothing** = **false** (the impossible) | an empty cut |

So `(Cat *x) (On x *y) (Mat y)` says just "a cat is on a mat," and
`~[ (Human *x) ~[ (Mortal x) ] ]` says "if something is human, then it is mortal."
Keep this key nearby and you can read every example below.

---

## Before the dragons: four things to hold onto

**1. The graph *is* the proposition — not a picture about it.** A bar chart is a
picture *about* some numbers. An Existential Graph is not about a proposition; it
**is** the proposition, drawn. You reason *inside* it, by changing the picture
under rules that never let it come to say something false.

**2. The blank sheet is the one free truth.** An empty sheet of assertion says
nothing — and *because* it denies nothing, it is simply **true**. It alone in the
whole system cannot be wrong; every proof starts from it, and you can always
erase back to it.

**3. Two utterly different ways something gets onto the sheet.** No distinction
in this guide matters more, and half the dragons grow from it:

- You can **posit** it — [scribe](GLOSSARY.md#scribe) a premise, a thing you are *claiming*. "Take this
  as given." It might be false.
- You can **derive** it — reach it from the blank by the rules, which preserve
  truth. A derived graph *cannot* be false; the system handed it to
  you.

The drawing on the sheet will not tell you, just by looking, which of these it
is. Keeping them apart amounts to most of wisdom here.

**4. A fragment is a building block, not the building — so ask after its
context.** This habit protects you from most misreadings, and it merits
keeping for life, not just while learning. When you meet a bare expression
sitting alone — `(Cat *x) (On x *y) (Mat y)` on an otherwise empty page — your
*first* reflex should be: **what context lets me read this?** An isolated graph is
almost always an **extract** — a word pulled from a sentence, a single frame
lifted from a movie, one step cut out of a sequence. Its appearing alone usually
says more about the size of the page, or the one narrow point an author is
illustrating, than about any complete claim. Two kinds of context do silent
work, and both matter:

- **The structural context** — the rest of the graph it was cut from: *which cuts
  enclose it, which lines run through it.* As the dragons below show, one oval more
  or less flips "is" into "isn't," "some" into "every." Show a fragment without
  its enclosing cuts and you have amputated its meaning.
- **The ground** — the universe of discourse the graph is asserted *in*: *whose
  sheet it is, what the parties take as understood between them.* Peirce built this
  in deliberately — the sheet is not a neutral blank but an **index of a universe
  already agreed**. A graph never floats free over nothing; it lies scribed on
  a sheet that already posits a world.

So never take a lone fragment at face value as a finished thought. Find — or ask
for — the whole it belongs to, and the ground it stands on. (The textbook habit of
printing fragments *without* their ground breeds exactly the next
section's confusion.)

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
if it sits on the sheet, it got there by assertion, not by proof.

The confusion is real and not your fault: textbooks routinely print a
*posited premise* and a *derived theorem* on the same blank sheet, side by side,
**with no mark telling them apart**. Peirce's late work (the 1906 "Phemic
Sheet") holds that to assert is to *take responsibility* for a claim — an act,
not a feature of the drawing — but the everyday alpha/beta presentations leave
the [seam](GLOSSARY.md#seam) unmarked. Arisbe marks it: a posited premise enters at **low [warrant](GLOSSARY.md#warrant)**
(carrying where it came from), while a theorem stands at the end of a chain of
sound steps. Same picture; two completely different standings; which one it is *is* the
question.

And pair this with the second reflex (point 4 above): cat-on-mat shown by itself
almost certainly amounts to an **extract**. Even granting that someone posited it, ask *what whole
it is a piece of and what universe it stands in* — is it the premise of an
argument whose conclusion is off the page? a single state in a sequence the author
abbreviated? a sub-graph that, in its real setting, sits inside a cut that would
reverse its force? The bare fragment is a word, not the sentence; a frame, not the
movie. Read it as a building block awaiting its building, and you will not mistake
an illustration for a claim.

> **Try it.** Ask Arisbe to *derive* an unenclosed contingent atom from the blank
> sheet. You can't — no legal sequence of rules does it. Then notice
> what you *can* derive from the blank: scaffolding like `~[ (P *x) ~[ (P x) ] ]`
> ("if P then P"), which is true no matter what P is. The blank deals generously
> in *form* and gives no *contingent content* for free.

---

## The map of dragons

Each entry: 🐉 the mistake · why it tempts (you're in good company) · the antidote
· a worked example you can check.

### 🐉 1. The missing outer cut — "every" vs "some-isn't"

By far the most common beginner error, and the tool will catch you (it caught the
author of this guide while he was writing it).

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
antecedent in the outer ring — is called a **scroll**, and it is the Existential Graph ([EG](GLOSSARY.md#eg)) picture
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
- `x` (no star) **refers back** to a line you already introduced.

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
non-question. Arisbe builds on exactly this discipline: it checks that your
**picture and your sentence say the same thing** (it calls this *correspondence*),
and it **never** claims to measure "truth" or "nearness to reality." Its own motto
is *attest correspondence, never truth.*

**So how does anything get to count as true?** Not by a truth-meter — by
**surviving challenge**. You play a claim out against what you already hold, in
the contest Peirce called the game (Arisbe's *Agon*); a claim that withstands the
attack earns standing, and a claim can always *lose* standing later. "Fact" here
means "the last claim still standing," held open to being overturned — never a
distance-reading on a dial.

And one guard that follows from it: standing is earned by **the claim** passing
**the method** (the test, on its content) — **never granted or denied by who
proposed it.** A newcomer's graph and an expert's graph meet the very same
scrutiny; the badge a graph earns describes the *graph*, never the person. To
dismiss a claim because of *who* made it (rather than test it) is the dragon's
cousin — and it has a name, *epistemic injustice*. (Adherence: the augurs were
rightly demoted by **losing the contest**, not by being barred from it. Breaking:
refusing to look through Galileo's telescope because of who held it.)
[FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md) (Doubt 4) tells the long version of all
this plainly, and `FIDELITY_AND_DEPARTURES.md` tells it precisely — including where Arisbe knowingly
parts from Peirce; you need neither to start.

### 🐉 7. "I need a special mark for *possibly* / *necessarily*"

You want to say "P is **possible**," and you reach for a new kind of ink — a
dotted oval, a colored region. Peirce did too (he tried "broken cuts" and colored
"[tinctures](GLOSSARY.md#tincture)" (Peirce's Gamma colourings) for years). Dragon: you don't need one.

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

**Dragon: a name purchases nothing.** A definition counts as legitimate only because it
**unfolds** back to exactly what it abbreviates and the rules accept the swap —
not because you gave it a dignified label. Likewise "assertion" names no property
of where a mark sits; it names an *act* of taking responsibility, one the game tests.
**Antidote:** whenever a name seems to be doing the work, ask to see the
**expansion** (what does it unfold to?) and the **warrant** (what challenge has it
survived?). If the answer is "just the name," it counts for nothing.

### 🐉 9. The telos you lifted out of its history

You watch a line of reasoning unfold — a universe of discourse growing, a chain of steps — and you
*see a direction in it*: "this was always heading toward X"; "there is a progression here." So you
take that direction, lift it out of the history, and write X flat on the sheet as a thing now
established. Dragon.

**Why it tempts:** the longer a history runs, the more it *sediments* — its authored, path-bound
origin fades and the pattern it traced begins to look like plain fact. (Berger & Luckmann called
exactly this **reification**: treating a history-bound product as an authorless given.) And a good
story really does imply a shape; the momentum is real. The mistake is not *seeing* the direction —
it is *asserting* it.

**Antidote:** a progression is a feature of a *path*, not a fact of the world. Three checks, each a
lock Arisbe already holds:
- The history belongs in the **record**, not on the sheet — nothing reaches the asserted corpus
  except by being tested through the game (Agon). A direction the path merely *implies* has earned
  nothing yet.
- One history scribing X makes X only *possible* (◇: some trajectory reached it), never *necessary*
  (□: every trajectory converges on it). Reifying the telos is a ◇ misread as □ — dragon 7's
  machinery, turned on histories.
- A tendency is sayable *inside* a context — under a cut, as the antecedent of a scroll — and
  malformed the moment it is scribed as the structure of the whole. Keep it enclosed:

```
~[ (inquiry *x) ~[ (reaches_goal x) ] ]   ← conditioned, enclosed — a would-be habit; legitimate
(reaches_goal *x)                          ← scribed flat on the sheet — the reified telos
```

Everything here erases back to the blank; no progression stays frozen. Peirce affirmed a telos of his
own — the growth of concrete reasonableness — but as a *would-be*, a hope that regulates inquiry,
never as a flat assertion. The biography of this dragon lives in
[MEANING_BY_HISTORY.md](MEANING_BY_HISTORY.md).

---

## How to stay afloat — five habits

Five habits keep you afloat. None settles which way to sail; each keeps a dragon
from holing you below the waterline, so you can carry on exploring — and
understanding what you draw:

- **A fragment is a building block — ask after its context and ground.** A lone
  graph is usually an extract: find the whole it was cut from (which cuts enclose
  it) and the universe it is asserted in. A word is not the sentence; a frame is
  not the movie. (Point 4; the silent partner of every dragon below.)
- **Posited vs. derived.** Always know whether a graph is a premise you put there
  or a theorem the rules handed you. (Dragons 1-of-cat-on-mat, 8.)
- **Inside vs. outside a cut flips everything.** One oval is the difference between
  "is" and "isn't," between "some" and "every." Count your cuts. (Dragons 1, 2, 3.)
- **Correspondence, not truth.** Arisbe guarantees the picture and the sentence
  agree. It does *not* sell you truth or "nearness to reality." Surviving
  challenge earns truth, and truth can be lost again. (Dragon 6.)
- **Everything erases back to the blank.** Nothing here stays frozen. The one
  bedrock remains the empty sheet, which says nothing and so cannot be wrong; every
  claim above it can be surrendered. (Dragon 9 — no progression is ever frozen there.)

> **Where to practice in Arisbe itself.** The workshop's **freeform canvas** lets
> you draw a graph by hand and asks Arisbe to *read it back* to you — so you see
> immediately whether your picture says what you meant (dragons 1-5 surface here
> instantly). **Challenge mode** gives you a target proposition, lets you draw it
> freehand, and grades your attempt with a plain-language diff of how it differs.
> The five drawable dragons above each have their own challenge (marked 🐉 in the
> picker): draw `🐉1` "every man is mortal," `🐉2` the empty cut, `🐉3` the
> removable double cut, `🐉4` a shared line of identity, `🐉5` a non-symmetric
> relation — and when your attempt goes wrong, the grader hands you back the
> antidote from this guide. Those two surfaces offer the fastest way to meet the
> dragons safely. (Dragons 6-9 aren't a single drawing — they live in *how a
> graph earns its standing*, not in the ink.)

---

## When you're ready for the dragons' biographies

Each dragon here has a full, technical, historical treatment for when you want it
— including the places where Peirce *himself* was unsettled and where the
scholarship still argues:

- [`FIDELITY_A_PLAIN_ACCOUNT.md`](FIDELITY_A_PLAIN_ACCOUNT.md) — **start here for the
  ideas behind the dragons:** the plain-language story of what Arisbe challenged in
  Peirce and the tradition, how it was argued out, and what changed (no logic
  required; a worked example for every principle).
- `ARISBE_IN_PRACTICE.md` — what Arisbe is, told through the people who use it.
- `CHAIN_OF_SEMIOSIS.md` — why a proof is a *chain* of sound steps (the
  posited-vs-derived distinction, made precise).
- `LEVEL_ZERO_AND_THE_REGISTERS.md` — the deep version of cat-on-mat and dragon 8.
- `MODALITY_WITHOUT_GAMMA.md` — the deep version of dragon 7.
- `FIDELITY_AND_DEPARTURES.md` + `ADVERSARIAL_EXAMINATION.md` — the deep version
  of dragon 6, including the examinations of exactly where Arisbe parts from Peirce
  and why (three departures, then the larger-game and worth-ladder rounds).
- [`MEANING_BY_HISTORY.md`](MEANING_BY_HISTORY.md) — the deep version of dragon 9: how a
  graph's *history* bears meaning (the same picture, a different argument) and why you must never
  reify a telos out of that history onto the sheet.

The point of a field guide is that **you should not need any of those to begin.**
Draw on the blank sheet. Watch the cuts. Ask whether a thing was posited or
derived. The dragons are few, and now they are on the map.

---

**Created**: 2026-06-19. Examples verified against Arisbe's EGIF parser and
Chapter-18 First-Order Predicate Logic ([FOPL](GLOSSARY.md#fopl)) translation.
