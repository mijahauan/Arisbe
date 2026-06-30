# Jargon & Word-Choice Audit (for review)

**Status:** proposal awaiting author sign-off (2026-06-30). **Policy chosen:** *conservative —
keep + introduce.* Keep proper technical terms **and** load-bearing project coinages, but
**introduce/gloss each on first use** (a plain phrase + a Glossary link); **replace only the
gratuitous idiosyncrasies** with plainer terms. `peel` is kept but introduced on first use.

**How to read this:** annotate the **Action** column (✓ approve / ✗ keep as-is / edit the
proposed wording). Counts are approximate, across all of `docs/` (book + dev). After sign-off I
apply it the same way as the abbreviation pass: first-use edits in the source docs + Glossary
anchors for any term that needs a link target. Dev-only docs can be left or swept too — your call.

---

## Class A — Proper technical terms (Peirce / Dau / logic): **keep, ensure introduced + glossed**

These are real terms of art; the fix is a first-use gloss + a Glossary link, not replacement.
Several need a **new Glossary entry/anchor** (marked ⊕).

| Term | ~count | Meaning | Action |
|---|---|---|---|
| endoporeutic | 136 | Peirce's "outside-in" reading of a graph | keep; gloss on first use ("read outside-in"); already in Glossary |
| Agonothetes ⊕ | 123 | the game's *interpretant* role — turns a true/false outcome into an act of inquiry | keep; needs a Glossary entry + first-use gloss (it's central to Agon) |
| scroll | 89 | a nested double-cut `~[ M ~[ P ] ]` = "P given M" | keep; in Glossary; gloss on first use |
| scribe / scribed | 57 | to draw/assert a graph on the sheet (Peirce's verb) | keep in formal contexts; soften to "draw/write" where casual |
| recto ⊕ / verso ⊕ | 56 / 15 | the asserted (recto) vs negated (verso) side of the sheet | keep; needs Glossary entries + first-use gloss |
| tincture ⊕ | 35 | Peirce's Gamma colourings (modal marks) | keep; needs Glossary entry + first-use gloss |
| teridentity ⊕ | 1 | a three-way point of identity (branch in a line of identity) | keep; gloss inline on its one use |
| tomos | 46 | the on-disk corpus (Greek "volume") | keep; in Glossary; ensure first-use reads "the *tomos* corpus" |
| co-resident | 4 | the two graph structures sharing one element set | keep (mild); fine as-is |

## Class B — Load-bearing coinages: **keep, but introduce on first use**

Pervasive and defined; introduce with a plain phrase + Glossary link on first use per chapter.

| Term | ~count | Proposed first-use introduction / gloss | Action |
|---|---|---|---|
| peel | 67 | "read G from the outside in — *peel* it — against the model M" (link to Glossary) | keep + introduce **+ cite precedent** |
| floor | 82 | "the **floor** (the baseline every import/claim starts at)" on first use | keep + introduce; ⊕ add Glossary entry |
| membrane | 54 | "the **membrane** (the boundary where the sheet meets the world, the only place error is corrected)" | keep + introduce; ⊕ Glossary entry |
| ~~inning~~ → **episode** | — | DECIDED: replace with **episode** (keeps Peirce's Greek register). ✅ **DONE** (whole-word, all docs + CLAUDE.md). | replaced |
| (style) ladder | 37 | "the style **ladder** (default → sparse exemplars → extrapolated regularity)" | keep + introduce; ⊕ Glossary entry |
| seam | 33 | "the **seam** (the boundary between two UoDs / where a reference crosses)" | keep + introduce |
| horizon | 27 | "the **horizon** (what lies beyond the part currently in view / open-world unknowns)" | keep + introduce |
| trajectory | 35 | fairly standard; light gloss "a legal trajectory (a path through the history)" on first use | keep |
| warrant / standing | 187 | epistemology term; already in Glossary as a gradient | keep; ensure first-use link |
| crystallise | 7 | replace with "fix / settle" in most spots | lean replace |

## Class C — Gratuitous idiosyncrasies / borrowed metaphors: **replace with plainer**

| Term | ~count | Proposed replacement | Action |
|---|---|---|---|
| hinge | 3 | "the crux" / "the pivotal point" | replace |
| palimpsest | 1 | "a layered/overwritten log" | replace |
| dogfood(ing) | 1 | "using it ourselves" / "our own first user" | replace |
| absorbed (prose) | 21 | "subsumed / resolved / accounted for" — *but* keep `departure_absorbed` as a verdict label (gloss it once) | replace in prose, keep label |
| hot-seat | 10 | "two players sharing one screen" (gloss once, then 'shared-screen') | replace/gloss |
| motte-and-bailey | 4 | keep the term **once** with a one-line gloss (it's precise); don't scatter it | keep + gloss once |
| spine (of docs) | 26 | "the core / orienting docs" where it reads as jargon | lean replace (low priority) |
| the larger game | 7 | "the wider question of …" (context-dependent) | replace case-by-case |
| four-beat (grammar) | 6 | "four-step (Spot → Subject → Commit → Settle)" | keep + introduce |
| voidness / "not even wrong" | 2 / 4 | keep; **cite clearly** → ✅ **DONE**: first use now reads *"not even wrong," the dismissal attributed to the physicist Wolfgang Pauli (German nicht einmal falsch)…* | keep + cited |

---

## A note on ADVERSARIAL_EXAMINATION.md

It is deliberately written as an adversarial legal brief (prosecution / defense / **Ruling:
`departure_absorbed` (confidence 0.79)** / "booked as an unpaid debt"). Plain-languaging it
wholesale would gut its character. **Recommended:** keep the register, add a one-paragraph
*"How to read this"* note at the top, and gloss the specialist terms (motte-and-bailey, the
verdict labels) on first use — rather than rewrite it. (Confirm.)

## On "peel" — precedent (verified)

`peel` is **not** an Arisbe idiosyncrasy: it has precedent in the EG literature, in this exact
game context — **John F. Sowa, *From Existential Graphs to Conceptual Graphs*** (the `eg2cg`
source in `docs/references/`): *"If g has negations, Graphist and Grapheus would take turns
**peeling off** negations and mapping subgraphs of g to M (Sowa 2011)."* That is the same
proposer/skeptic, outside-in, against-a-model setup Arisbe calls "the peel."

**Not verified as Peirce's own word.** It does not appear in our Peirce source (Roberts,
*Existential Graphs of Peirce*); Peirce's own writings and Pietarinen's *Signs of Logic* are not
text-extracted in the repo, so an attribution to Peirce himself is unverified and must not be
asserted (the no-fabricated-citation floor). **Action:** keep `peel`; add an explicit reference to
**Sowa (2011)** in the Glossary entry and on first use in `ENDOPOREUTIC_GAME_GUIDE.md`. If a Peirce
passage using "peel" can be supplied, cite that too.

## Resolved decisions (author, 2026-06-30)

- **`inning` → `episode`** (not "round") — keeps Peirce's Greek register. ✅ applied.
- **"not even wrong"** — cite clearly → attributed to Wolfgang Pauli. ✅ applied.
- **`peel`** — keep + introduce + cite Sowa (2011). (pending the first-use pass)
- All other audit rows approved as written.

## After sign-off

1. Add Glossary entries + anchors for the ⊕ terms (Agonothetes, recto, verso, tincture, floor,
   membrane, style ladder, teridentity).
2. First-use introduce/gloss the Class A + B terms (Glossary-linked), per chapter, like the
   abbreviation pass (parallel agents, strict spec).
3. Replace the Class C terms with the approved plainer wording.
4. Add the "How to read this" note to ADVERSARIAL_EXAMINATION (if approved).
5. Re-render + verify; commit.
