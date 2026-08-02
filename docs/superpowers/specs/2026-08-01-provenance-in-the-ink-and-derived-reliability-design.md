# Provenance in the ink, and reliability derived rather than stored

**Design, 2026-08-01.** Executes candidates 1 and 2 of
[the received-world sitting](2026-08-01-the-received-world-boundary-controls-and-socialization.md)
§7, which §6a ruled the standing direction. Scope ruled by the author this session:
**general machinery only** — the record and the reader. No C-series change;
`Unit.peers` keeps working untouched, and its retirement is a later pass with its own
before/after measurement.

Design decisions were settled by **probe against the running system**, not by argument;
the probes and what they returned are recorded in §5 because two of them changed the
shape.

---

## 1 · What this fixes

`docs/superpowers/specs/2026-08-01-…-socialization.md` §6 records a three-tier
diagnosis. The third tier — *private Python register: no ink, not in the DAG, not
re-derivable* — has `Unit.peers` (reliability) as its largest occupant. Under the
author's own commens doctrine a reliability that is never scribed, never crosses a
membrane, and never becomes a mark **was never part of the shared reality**. That is a
prior explanation for typification's inertness which does not depend on scarcity.

§6a ruled the fix: move it into the graphs. Reliability becomes a question **only once
alternate sources appear** (§5.2's plurality), it attaches to **a provenance record in
the ink** rather than to a peer, and it is **derived from the record's own resolution
history** — so no field anywhere holds a score.

**A constraint added by Examination VIII (2026-08-01).** Legitimacy must be
**address-blind**: computed from resolution history, never from reach or proximity.
The author's case is the prophet without honour in his own country — provenance and
legitimacy run independently of network intimacy and sometimes inversely. In a system
where near contact is cheap, an uptake rule that weighted by contact would silently
weight the near. Nothing in the reader below can see who is near, which makes this
hold by construction rather than by discipline.

## 2 · The record — the author's conditional form

**Ruled shape (2026-08-01): the antecedent *is* the provenance.** One cell:

```
~[ (provided_by "<source>" "<key>") ~[ <the notion> ] ]
```

read as *given that `<source>` provided this, the notion*. This is §5.1's resolution —
the received world entering as a conditional whose antecedent is what was given — with
the provenance atom standing where §5.1's bare `A` stood. Nothing contingent stands at
depth 0; the notion never claims standing a record would have had to license.

**The affirmation** is a second cell, the bare atom:

```
(provided_by "<source>" "<key>")
```

Assert that the arrival happened and **the notion derives** — through the existing Horn
forward-chainer in `model_materialization`, since `~[ B ~[ H ] ]` is exactly the shape
it already reads. No new inference code. Retract the affirmation and the notion goes
with it, because it was never stored.

**`<key>` is load-bearing, not cosmetic** — see §5.2. It is a deterministic
content-derived id of the notion's canonical form, so the same notion from the same
source always keys identically and two different notions never collide.

**Plurality falls out literally.** Two sources contributing one notion make two
conditionals with distinct keys; the notion is derivable from either. That is §5.2's
second authoritative adult *and* corroboration — one mechanism, as the sitting said,
now with one implementation.

**No quotation in the conditional** — see §5.3. In this form the **consequent is its
own decoder**: what `<key>` names is standing beside it. Banking needs `⌜…⌝` because
the banked prose exists nowhere else in the graph; here it would restate what the
record already shows.

## 3 · The reader — reliability derived, never stored

A pure function over a `TransformationChain`. For a source: collect its conditionals,
ask how each consequent stands across the branching DAG, and count discharge against
abandonment.

```python
@dataclass(frozen=True)
class SourceStanding:
    source: str
    relation: Optional[str]   # VII's domain-index at the granularity we have
    contributed: int          # conditionals recorded from this source
    affirmed: int             # of those, antecedent affirmed
    necessary: int            # consequent □ across the reachable worlds
    possible: int             # ◇ but not □
    absent: int               # ¬◇
    discharged: int           # entertained exhibits discharged
    abandoned: int            # entertained exhibits abandoned
```

**No scalar.** `SourceStanding` carries counts and **exposes no aggregate property** —
no `score`, no `ratio`, no `net`. This is `THE_MEASURE_OF_KNOWLEDGE`'s vector guard,
and it is also the re-measurement pass's own hard-won rule: a derived scalar invites a
gate, and `net_score` was observed rising in **both** directions of the thing it was
meant to gate. A caller that wants a comparison states it on the components.

**Domain-indexing.** Examination VII ruling 1 made the credential domain-indexed.
The general machinery has no "domain" concept, so the index is the **relation name** of
the notion — which is also exactly how `Unit.peers` already keys (`per-author,
per-relation`), making the eventual migration like-for-like rather than a redesign.

**Modality.** Composed from `modal_query.possibly` / `necessarily` over a predicate
"this state holds the notion". `scribes_relation` is too coarse (any atom of that
relation) and `equals_graph` too strict (whole-sheet identity), so the reader supplies
its own predicate over `world_scroll.m_view`.

## 4 · Modules, and what they depend on

| Module | Contents | Depends on |
|---|---|---|
| `src/provenance.py` (new) | `notion_key`, `provenance_cell`, `record_provenance`, `affirm_provenance`, `provenance_records`, and the two chain-step recorders | `world_scroll`, `m_steps`, EGIF parse/generate |
| `src/source_reliability.py` (new) | `SourceStanding`, `standing_of`, `standings` | `provenance`, `modal_query`, `world_scroll` |

Both **geometry-free** (no layout import, so no §3.3 obligation) and **unprotected**.
The dependency runs one way: reliability reads provenance, never the reverse.

**No new chain act.** Both moves are one licensed INS-of-cell, so both record through
the existing `m_steps.admit_step` (act `m_enlargement`, derivation `["INS"]`). The
standing polarity gate `test_corpus_polarity_discipline.py` therefore covers them with
no change to `M_ACTS`.

## 5 · What the probes found

Recorded because two of these changed the design, and because a figure that lives only
in prose is unprotected (the re-measurement pass's own lesson).

**5.1 · The conditional lands in `m_view` as a conditional.** `enlarge_m(m, '~[ (…) ~[ … ] ]')`
produces a cell whose interior reads back as the conditional, and the scroll still
recognises its cells and hold. Verified before anything was designed on it.

**5.2 · A generic antecedent over-fires — the defect that made `<key>` load-bearing.**
With `*p` in the antecedent, two conditionals from one source and **one** affirmation
derived **both** consequents: a notion never affirmed (`tall "s1"`) arrived anyway. A
source affirming one thing would have licensed everything it ever contributed.
Content-keyed antecedents discriminate correctly, and the affirmed notion alone
derives.

**5.3 · The quotation breaks Horn recognition — silently.** Attaching a quotation oval
to the key vertex succeeds (a **constant** vertex takes `sort=proposition` and an oval
without complaint), but the materializer then reads the oval as an extra cut in the
body and reports `SkippedRule(reason='complex_body')`. **The notion is not derived, and
nothing raises.** The rule stops firing while the graph still looks right. Hence §2's
"no quotation in the conditional".

*Named but not taken:* the arguably more principled fix is to make Horn-shape
recognition skip quotation cuts, since an oval is mention and should not count as body
content. That touches shared inference machinery and is not needed here; recorded as a
candidate, not a plan.

**5.4 · A quotation-bearing M has no linear form.** `generate_egif` raises
`SecondOrderNotInLinearForm` on any graph carrying sorted lines and ovals. It does not
bite this design now that the oval is gone, but **any path that serializes M as EGIF
breaks on quotations** — which will matter to the C-series migration, whose segment
carry is already structural JSON for a related reason (Examination IV ④).

## 6 · Testing

New: `tests/test_provenance.py`, `tests/test_source_reliability.py`.

Each of §5.1–5.4 becomes a pinned test, including the two falsifiers — the generic
antecedent over-firing and the quotation silently disabling derivation — so that a
regression is a failure rather than a surprise. Plus: key determinism across
re-parses; key distinctness for distinct notions; the affirm→derive→retract cycle;
plurality (two sources, one notion, either support sufficient); a chain round-trip
through `admit_step` satisfying the standing polarity gate; and for the reader,
address-blindness stated as a test — two identical records differing only in a source
name that no reach structure is consulted for.

## 7 · Out of scope, and why

- **Seeding by DC+ · INS · IT+** (§7 candidate 3) and **retiring `Unit.peers`** — the
  author's staging ruling. They move measured C-series figures; this pass moves none.
- **A source as a kytos-level entity with its own model** — assistant default, flagged
  in session: nothing in the derived computation needs a source to have a model, so
  giving it one now would be speculative structure. A source is a name.
