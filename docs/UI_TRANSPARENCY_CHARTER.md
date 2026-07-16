# The UI Transparency Charter

> **What this is.** The seven principles that govern every Arisbe interface surface, each
> with an **operational test** so that auditing a screen is mechanical, not a matter of
> taste. The aim, in the author's words (2026-07-11): *the UI should not interfere with the
> learning* — it is a **transparent layer between what the user is thinking and what she
> wants to do about it**. A user is never confused about where she is or what she can do
> there; the common verbs work the same way everywhere; help is a gesture away.
>
> This is the behavioral twin of [WEB_VIEWER_DESIGN.md](WEB_VIEWER_DESIGN.md) (which governs
> visual chrome: tokens, cameras, panels). Every future UI change should name the principles
> it touches — and must not fail any test below.

## Where the principles come from

Each principle fuses an established interaction-design heuristic (Nielsen's usability
heuristics; Norman's *gulf of execution* — can I see how to do what I intend? — and *gulf of
evaluation* — can I see what just happened?) with Arisbe's own standing doctrine. The fusion
matters: a generic heuristic says "speak the user's language"; Arisbe's floor adds *which*
language claims are allowed in (correspondence, not truth; the graph is judged, never the
grapher). The principles are therefore not imported wholesale — they are the canon **as
constrained by the project's honesty commitments**.

## The seven principles

### P1 · You always know where you are and what can happen here
Every mode states, in plain words, persistently visible: its name, its regime ("nothing here
is asserted yet"), and what *cannot* happen here ("read-only — the corpus is untouched").
*Canon:* Nielsen #1, visibility of system status.
**Test:** a cold reader answers "where am I / what can I do / what can't I do" from visible
text alone — no hover, no documentation.

### P2 · One word, one place, one way
The same verb — import, save, export, style, search, help — has the same name, the same
position, and the same behavior in all three modes. Mode-specific nuance lives in the
tooltip, never in a divergent label.
*Canon:* Nielsen #4, consistency — extending the house "one word per concept" rule
(move, state) from the calculus vocabulary to the chrome.
**Test:** grep the UI: any one concept with two labels fails; any mode missing a common verb
without a stated reason fails.

### P3 · Recognition, never recall
Nothing asks the user to remember or invent what the system already knows: acronyms expand
where they stand, identifiers are suggested, vocabulary defines itself in place.
*Canon:* Nielsen #6, recognition over recall.
**Test:** no bare jargon without a ≤1-hover definition; no free-text field the system could
have pre-filled.

### P4 · The picture never lies; state changes announce themselves
A refused act snaps back visibly and immediately. Phase, standing, and attestation are
visible *before* anything fails, not only in the failure message. Every mode-changing toggle
announces its consequence at the moment of toggling.
*Canon:* Norman's gulf of evaluation; the project's drawn-shape-authoritative commitment —
the drawn form **is** the sign, so a stale preview is not cosmetic debt, it is a false sign.
(The settle-editor snap-back fix, commit `e44f283`, is this principle enforced.)
**Test:** no UI state can display an act the engine rejected.
*Worked example (2026-07-16):* Organon's chain player on a **branching** episode read
"state 5 / 9" — a total that aggregated two *incompatible* futures into one line, with `»`
landing on whichever branch's leaf happened to be authored last. The counter was a false
sign about the shape of the reasoning. The fix (the ⑂ branch strip): the player follows
one branch at a time and the counter's total is the *active branch's* length — "state 2 / 2
· on wind-rises (branch 1 of 2) · lines converge here". The rule generalizes: **a counter
never aggregates incompatible futures.**

### P5 · Prevent, don't punish
What is illegal *here, now* is visibly unavailable, with its reason — the server refusal is
the backstop, never the teacher. A learner discovers a rule's requirements by looking, not by
being refused.
*Canon:* Nielsen #5, error prevention; closes the oldest named dogfood friction ("rule
requirements not discoverable; §3.3 invisible until it fails").
**Test:** a user can discover any rule's requirements without triggering a refusal.

### P6 · Errors speak the learner's language and say what to do next
Every refusal maps to a plain-language sentence, a concrete next step, and a ≤2-click path to
the exact help — while keeping the engine's precise message (the honesty is in the pairing:
plain words *and* the real reason).
*Canon:* Nielsen #9, help users recognize and recover from errors.
**Test:** no raw code (`CORRESPONDENCE_VIOLATION`) or bare "refused:" shown without a
translation beside it.

### P7 · Help lives where the question arises
A definition is ≤1 hover away; an explanation is ≤2 clicks away (primer, or a book anchor) —
from every surface, for every term the surface uses.
*Canon:* Nielsen #10, help and documentation; the author's steer.
**Test:** from any control or term, count gestures to its explanation; more than two fails.

## Doctrine riders (unchanged, restated)

The principles operate **inside** the project's standing floors — a transparency fix may
never trade these away:

- **Correspondence, not truth** — §3.3 attests that picture and proposition denote the same
  object; no UI copy may imply the system certifies truth.
- **Polarity in words, never hue** — hue/line-style/texture stay reserved; a legality reason
  or orientation cue is worded, not colored.
- **The graph is judged, never the grapher** — no skill gating, no per-user scrutiny levels.
- **No auto-promotion** — the corpus is reached only through Agon (or style-only
  reprojection); no transparency shortcut may blur that boundary.
- **Progression, not progress** — developmental copy says *develops / revises / withstands*,
  never *improves toward truth*.
- **Per-mode camera doctrine** (fit / keep / hold) and **design tokens only** (no color
  literals) — per WEB_VIEWER_DESIGN.md.

## How to audit a surface (the recipe)

1. **Cold-walk it** (P1): load the page logged-out-of-context; write down what you believe
   you can and cannot do, from visible text only. Compare with reality.
2. **Grep the verbs** (P2): list every label for import/save/export/style/search/help across
   the three modes; any synonym pair is a finding.
3. **Circle the jargon** (P3, P7): mark every term a newcomer wouldn't know; hover each —
   no definition within one hover is a finding; no path to a fuller explanation within two
   clicks is a finding.
4. **Refuse things on purpose** (P4, P5, P6): attempt the illegal — a rule on the wrong
   polarity, a boundary-crossing drag, an out-of-phase act. Any lingering false picture
   (P4), any refusal that was *discoverable in advance* but wasn't shown (P5), any raw code
   without translation (P6) is a finding.
5. **File findings against principles**, fix in tiers, and re-run the walk.

## Status

Adopted 2026-07-12. First application: the transparency docket built from the 2026-07-11
three-mode cold-walk (rule-button self-description, orientation strips, verb unification,
glossary-on-hover, error mapper, legality preview, forward links, id suggestion). See git
history for the tiered landing.
