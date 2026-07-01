"""The first *open* membrane — a replayable discourse feed.

Design-of-record: ``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §4b. The closed loop's membrane
(``agon_evolution.CorpusProposer`` / ``MutationProposer``) draws doubt from the corpus; an
**open** membrane renews doubt *from outside*. This module builds the first one in its
**raise-only** flavour (the argument-forum / opinion register): a stream of dated, sourced
propositions that generate propositions and conflicts, but which M cannot check against the
world. What the referee enforces here is therefore not truth but **cross-source consistency**
— you model *the discourse, not the world* (honest and useful; not knowledge of facts). A
*raise-and-resolve* membrane (a live API / prediction market that returns a verdict over
time) plugs into the very same :class:`agon_evolution.Proposer` socket later; only the
verdict source differs.

Why Arisbe *runs on* messy, conflicting input rather than fearing it (the design's floor):
the low-warrant floor (*entertain, don't endorse*) plus **provenance** make ``P@sourceA`` vs
``¬P@sourceB`` a natively representable **contested M** — a conflict becomes a
``challenge_to_M`` or a **DAG branch** (the LLM Agonothetes, Stage 3), never a crash. Two free
fits fall out: **diachrony** (a day is a generation — the feed is dated) and the **modal lens**
(◇/□ over the trajectory reads *settled vs. contested* belief; see ``modal_query``).

This membrane is **offline and deterministic** by construction (a replayable feed, no
network), so it is CI-safe and reproducible — the online sources it stands in for attach at
the same socket. Additive, geometry-free, imports no protected module's internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Set

from egif_parser_dau import parse_egif
from eg_navigation import same_graph
from egi_core_dau import RelationalGraphWithCuts


# --------------------------------------------------------------------------- #
# A dated, sourced proposition                                                 #
# --------------------------------------------------------------------------- #

@dataclass
class DiscourseItem:
    """One utterance in the feed: a ``source`` (who says it), a ``day`` (when — the
    generation), the propositional ``egif`` content, and whether the source **denies** it (a
    ``¬`` reading, emitted as a sheet-level cut around the content). The *content* is the
    thing two sources may agree or disagree about; the ``deny`` flag is the stance."""
    day: str
    source: str
    egif: str
    deny: bool = False

    def emitted_egif(self) -> str:
        """What is scribed onto the sheet this round — the content, or its negation."""
        return f"~[ {self.egif} ]" if self.deny else self.egif


@dataclass
class Conflict:
    """A content the discourse is **contested** on: asserted by some sources, denied by
    others (``P@sourceA`` vs ``¬P@sourceB``). The raise-only referee reports this rather than
    adjudicating it — it cannot check the world, only cross-source coherence."""
    content_egif: str
    asserted_by: List[str]
    denied_by: List[str]


# --------------------------------------------------------------------------- #
# The feed as a Proposer (the membrane)                                        #
# --------------------------------------------------------------------------- #

class DiscourseFeed:
    """A raise-only open membrane: replays a dated, sourced feed one item per round, in order
    (a day → a generation). Implements the ``agon_evolution.Proposer`` socket, so it drives
    ``run`` exactly like the closed proposers — but the propositions come from *outside* the
    corpus, and they may conflict. ``emitted`` records what was scribed for inspection."""

    def __init__(self, items: Sequence[DiscourseItem]):
        self._items = list(items)
        self.emitted: List[DiscourseItem] = []

    def propose(
        self, model: RelationalGraphWithCuts, round_idx: int
    ) -> Optional[str]:
        i = round_idx - 1
        if not (0 <= i < len(self._items)):
            return None                       # the feed is exhausted → ends the run cleanly
        item = self._items[i]
        self.emitted.append(item)
        return item.emitted_egif()

    @property
    def days(self) -> List[str]:
        """The distinct days in feed order — the generations the run steps through."""
        seen: List[str] = []
        for it in self._items:
            if it.day not in seen:
                seen.append(it.day)
        return seen


# --------------------------------------------------------------------------- #
# The raise-only referee: cross-source consistency (not truth)                 #
# --------------------------------------------------------------------------- #

def consistency_report(items: Sequence[DiscourseItem]) -> List[Conflict]:
    """The coherence check a *raise-only* membrane can actually make: which contents are
    asserted by one source and denied by another (``P@A`` vs ``¬P@B``). It does **not** decide
    who is right — with no world to consult, it enforces only cross-source consistency and
    surfaces the contested points for the game (a ``challenge_to_M`` or a DAG branch) to
    dispose of. Contents are matched by ``same_graph`` (surface EGIF may differ)."""
    groups: List[dict] = []
    for it in items:
        g = parse_egif(it.egif)
        for grp in groups:
            if same_graph(parse_egif(grp["egif"]), g):
                grp["stances"].append((it.source, it.deny))
                break
        else:
            groups.append({"egif": it.egif, "stances": [(it.source, it.deny)]})

    conflicts: List[Conflict] = []
    for grp in groups:
        asserted = sorted({s for s, deny in grp["stances"] if not deny})
        denied = sorted({s for s, deny in grp["stances"] if deny})
        if asserted and denied:
            conflicts.append(Conflict(grp["egif"], asserted, denied))
    return conflicts


def contested_contents(items: Sequence[DiscourseItem]) -> Set[str]:
    """The set of contents (EGIF) the discourse disagrees about — the ◇-contested points the
    modal lens will read off the trajectory as *not settled*."""
    return {c.content_egif for c in consistency_report(items)}


__all__ = [
    "DiscourseItem", "Conflict", "DiscourseFeed",
    "consistency_report", "contested_contents",
]
