"""An open membrane with *conflict + resolution structure* — wiki disputes.

Design-of-record: ``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §4b, which names *argument forums /
Wikipedia dispute records* as the recommended first real membrane precisely because they carry
**both** the conflict (an edit war) **and** its resolution (consensus / a reliable-source
citation / an admin decision — or none). That is richer than the plain discourse feed
(``discourse_membrane``), which surfaces conflict but never resolves it, and it sits *between*
raise-only and raise-and-resolve: the resolution is **editorial/social**, not the physical
world — so warrant differs by *mechanism* (a reliable source outranks a bare consensus), and a
later reliable source can **overturn** an earlier consensus.

This is exactly the shape the automated Endoporeutic Game feeds on:

  * an **edit war** = a run of asserts and reverts on a claim (its ``reverts`` count is the
    contestedness / friction signal);
  * a **resolution** carries a ``mechanism`` and a ``settled`` verdict, scribed as ground truth
    for the mechanical panel to dispose — a consensus generalization is admitted, a
    reliable-source counterexample **relinquishes** an over-general standing law (the same
    ``challenge_to_M`` the swan uses), an unresolved dispute is *entertained at low warrant*
    and left on the ◇-contested frontier.

The point (the author's): **take advantage of what we can learn from this.** So a wiki-dispute
run feeds straight into the §6 meta-learning instruments (``agon_metalearning``), where the
dispute structure becomes learnable — *which resolution mechanism produces durable knowledge*
(stick-rate by mechanism), *where the edit wars are* (friction), and *what stays contested*
(the honest horizon). See ``WikiDisputeFeed.episodes``.

Offline and replayable (a recorded dispute record), so CI-safe; a live wiki/forum source
attaches at the same ``agon_evolution.Proposer`` socket. Additive, geometry-free, imports no
protected module's internals. Correspondence-not-truth holds: an editorial resolution is
*low-warrant data* (consensus can be wrong, sources retracted); M self-certifies a track
record, not truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

# The editorial mechanisms that can end a dispute, in rough descending warrant. ``unresolved``
# is not a resolution — it is the honest absence of one (the claim stays contested).
RESOLUTION_MECHANISMS = ["reliable_source", "admin", "consensus", "unresolved"]


@dataclass
class WikiEdit:
    """One edit in a dispute's history: an editor either *asserts* the claim (adds/keeps it) or
    reverts it (removes it). The sequence is the edit war."""
    editor: str
    asserts: bool


@dataclass
class Resolution:
    """How (and whether) a dispute ended. ``mechanism`` is the editorial route;
    ``settled`` is the outcome — ``True`` the claim stands, ``False`` it is rejected, ``None``
    it stays contested (``mechanism='unresolved'``)."""
    mechanism: str
    settled: Optional[bool]


@dataclass
class WikiDispute:
    """A dispute over one ``claim_egif``: its edit-war ``edits`` and its ``resolution``.
    ``world_egif`` is the ground truth scribed when it resolves — defaulting to the plain claim
    if it stands, a bare negation if rejected, the claim (tentative) if unresolved; a
    *law-relinquishing counterexample* (e.g. ``(author "Yolanda") ~[ (reliable "Yolanda") ]``) is
    supplied explicitly so the Challenger sees it."""
    claim_egif: str
    edits: List[WikiEdit]
    resolution: Resolution
    world_egif: Optional[str] = None

    @property
    def reverts(self) -> int:
        """Edit-war intensity — how many edits removed the claim (the contestedness signal)."""
        return sum(1 for e in self.edits if not e.asserts)

    @property
    def contested(self) -> bool:
        return self.reverts > 0

    @property
    def editors(self) -> List[str]:
        seen: List[str] = []
        for e in self.edits:
            if e.editor not in seen:
                seen.append(e.editor)
        return seen

    def ground_truth(self) -> str:
        """What is scribed onto M this round (the panel disposes it)."""
        if self.world_egif is not None:
            return self.world_egif
        if self.resolution.settled is False:
            return f"~[ {self.claim_egif} ]"
        return self.claim_egif                   # settled True, or unresolved (tentative)


# --------------------------------------------------------------------------- #
# The feed as a Proposer (the membrane)                                        #
# --------------------------------------------------------------------------- #

class WikiDisputeFeed:
    """A wiki-dispute open membrane: replays a recorded dispute record one dispute per round,
    scribing each resolution's ground truth for the mechanical panel to dispose. Implements the
    ``agon_evolution.Proposer`` socket. ``episodes(result)`` hands the run to the meta-learning
    layer so the dispute structure becomes learnable."""

    def __init__(self, disputes: Sequence[WikiDispute]):
        self._disputes = list(disputes)

    def propose(self, model, round_idx: int) -> Optional[str]:
        i = round_idx - 1
        if not (0 <= i < len(self._disputes)):
            return None                          # the record is exhausted → ends the run
        return self._disputes[i].ground_truth()

    def dispute_report(self) -> List["DisputeSummary"]:
        """The raise-only-with-resolution referee's lens: per dispute, its contestedness and how
        it ended — without adjudicating (the mechanism did that editorially)."""
        return [
            DisputeSummary(d.claim_egif, d.reverts, d.contested,
                           d.resolution.mechanism, d.resolution.settled, d.editors)
            for d in self._disputes
        ]

    def episodes(self, result) -> List["object"]:
        """Build the dispute-aware meta-learning records for this run — pairing each dispute
        (in order) with the loop's outcome and its stickiness. Returns
        ``agon_metalearning.DisputeEpisode`` objects."""
        from agon_metalearning import DisputeEpisode, stickiness
        episodes = []
        for d, outcome in zip(self._disputes, result.outcomes):
            stuck, by_decay = stickiness(outcome, result)
            episodes.append(DisputeEpisode(
                claim_egif=d.claim_egif,
                mechanism=d.resolution.mechanism,
                settled=d.resolution.settled,
                reverts=d.reverts,
                disposition=outcome.disposition,
                stuck=stuck,
                erased_by_decay=by_decay,
            ))
        return episodes


@dataclass
class DisputeSummary:
    claim_egif: str
    reverts: int
    contested: bool
    mechanism: str
    settled: Optional[bool]
    editors: List[str] = field(default_factory=list)


__all__ = [
    "RESOLUTION_MECHANISMS", "WikiEdit", "Resolution", "WikiDispute",
    "WikiDisputeFeed", "DisputeSummary",
]
