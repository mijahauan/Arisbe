"""What typification does once the world contains an unreliable speaker.

THE OCCASION. Task 6 reported that typification changed nothing and gave the
implementer's own diagnosis for it: "THIS SERIES HAS NO UNRELIABLE SPEAKER.
Typification defends against differential reliability; no unit here lies,
guesses, or has a noisier field than another. The mechanism was measured in a
world with nothing for it to sort." Examination VII recorded the same thing as
VII.4 and the author ruled the field should get speaker-variance, which it now
has (`ObserverNoise`). This file asks the question that ruling opened: **given
something to sort, does typification sort it?**

The answer is no, and the reason is not the one anybody expected. It is not that
the ledger is too weak to notice a liar. It is that **a liar cannot get a lie
into the channel at all**, so there is nothing for the ledger to notice.

These are measurements taken and then pinned, NOT pre-registered predictions.
The series' own discipline distinguishes the two and the distinction is worth
keeping: nothing below was written down in advance, so each figure is a
description of what this world does, and the pre-registered claim it licenses is
stated at the end of `test_the_binding_constraint_is_the_question_not_the_field`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from c_field import Field, ObserverNoise, apertures_for, default_spec  # noqa: E402
from test_c_channels import _play_ask_and_challenge  # noqa: E402

import dataclasses  # noqa: E402

SEEDS = [1, 2, 3, 4, 5, 7, 42, 99]
ROUNDS = 60

ONE_LIAR = (("u1", ObserverNoise(spurious=0.9)),)
ALL_LIARS = tuple((f"u{i}", ObserverNoise(spurious=0.9)) for i in range(4))


def _arm(typify, liars, keys):
    out = {k: 0 for k in keys}
    for seed in SEEDS:
        t = _play_ask_and_challenge(seed, ROUNDS, ask=True, typify=typify,
                                    liars=liars)
        for k in keys:
            out[k] += t[k]
    return out


def test_the_liar_really_does_mis_observe():
    """THE MECHANISM-IS-EXERCISED GATE, and this file's first obligation.

    Tasks 6 and 7 both published a first cut that read wrong, and the rule they
    left behind is to verify that the thing being measured actually happened
    before reporting what it did. A finding of "no effect" from a mechanism that
    never ran is worth nothing at all — it is P-G1's "no category to measure"
    wearing a verdict's clothes."""
    spec = dataclasses.replace(default_spec(seed=1), observers=ONE_LIAR)
    field = Field(spec)
    liar = apertures_for(spec, 4)[1]
    assert liar.unit_id == "u1"

    fabricated = 0
    for r in range(ROUNDS):
        truth = set().union(*(set(field.deliver(n, r)) for n in liar.domains))
        fabricated += len(set(field.at(liar, r)) - truth)

    assert fabricated > 200, (
        f"u1 perceived only {fabricated} atoms the field never delivered; the "
        f"liar is not lying, so nothing below would be measuring testimony")


def test_a_liar_cannot_volunteer_a_lie_because_the_channel_only_answers():
    """**THE FINDING. 314 fabrications perceived, none transmitted.**

    A unit at `spurious=0.9` mis-observes several hundred atoms across a run and
    gets essentially none of them into anybody else's record: 0 fabricated
    adoptions of 798 uptakes at 0.9, and 1 of 819 at 0.5, over eight seeds.

    THE REASON IS THE CHANNEL'S SHAPE, not the ledger's weakness. `Unit.answer`
    answers open questions from its own facts, and a question names an atom the
    asker's own record already licenses — so an answer either carries THAT atom
    or is not an answer. A fabricated atom is one nobody asked about, and there
    is no move in this channel by which a unit volunteers something. Task 6's
    "the ask channel is a confirmation channel, not a discovery channel — it can
    import neither error nor novelty" was inferred from the field's own spurious
    atoms; here it is demonstrated against a speaker built to lie.

    So giving the field speaker-variance was NECESSARY and is NOT SUFFICIENT.
    The unreliability is real at the unit's membrane and cannot cross."""
    keys = ["adopted_fabricated", "uptakes", "questions"]
    hi = _arm("prefer", ONE_LIAR, keys)
    assert hi["uptakes"] > 500, "the channel must be carrying something"
    assert hi["adopted_fabricated"] == 0, (
        f"expected a lying speaker to transmit nothing, got "
        f"{hi['adopted_fabricated']} of {hi['uptakes']} uptakes")


def test_a_lie_enters_by_being_asked_about_not_by_being_told():
    """AND THE ONE ROUTE THAT DOES WORK, which is the finding's sharp edge.

    Make every unit unreliable and fabrications DO cross — 25 of 569 uptakes.
    The extra route is not that liars got better at lying. It is that an
    unreliable **asker** mis-observes a body, so its own record licenses a
    question about an atom the field never licensed, and the channel then
    confirms it. A lie enters this community by being asked about, never by
    being volunteered.

    That is the confirmation structure read from the other side, and it says
    something the series has not said before: the channel's inability to carry
    error is not a safety property. It is the same property as its inability to
    carry news.

    RE-MEASURED 2026-08-04 (the channel audit, `RUN_C_AUDIT_LOG.md` §6): "23 of
    474" was the window-5 reading, narrated past the window-8 ruling of
    2026-07-31 and never updated. The assertion itself checks only
    `> 10` and was never touched by the drift."""
    keys = ["adopted_fabricated", "uptakes"]
    one = _arm("prefer", ONE_LIAR, keys)
    every = _arm("prefer", ALL_LIARS, keys)
    assert one["adopted_fabricated"] == 0
    assert every["adopted_fabricated"] > 10, (
        f"with every unit unreliable, fabrications should cross; got "
        f"{every['adopted_fabricated']} of {every['uptakes']}")


def test_typification_is_still_exactly_inert_with_speakers_to_sort():
    """**P-G3 RE-TESTED IN THE WORLD IT ASKED FOR, AND IT HOLDS UNCHANGED.**

    Task 6 found the typified arm reproducing the untargeted arm digit for digit
    and named the missing ingredient: no unreliable speaker. The world now has
    one, and the arms are STILL identical on every key, at every level of
    unreliability:

        no liar             true_lost 20  conv_lost  0  uptakes 1151  fab  0
        u1 unreliable       true_lost 31  conv_lost  4  uptakes  978  fab  0
        all four unreliable true_lost 59  conv_lost 23  uptakes  569  fab 25

    `occ_bite` — the count of uptake decisions where the preference named
    somebody OTHER than the peer already answering — is **0 in all three**.
    Preferences are earned (0, 2 and 8 of them) and never once disagree.

    So Task 6's stated reason was incomplete rather than wrong. Speaker-variance
    does not rescue typification, because the blocker is not "nothing to sort"
    alone. It is that there is no CHOICE to make: Task 7 measured every one of
    1151 uptake decisions at four units as having exactly one voice behind it,
    and an unreliable speaker does not supply a second one.

    Unreliability does degrade the community — true laws lost go 20 -> 31 -> 59
    and converses 0 -> 4 -> 23 — but by the OBSERVATION path, never the
    testimony path. Units are hurt by what they mis-see, not by what they are
    told.

    RE-MEASURED 2026-08-04 (the channel audit, `RUN_C_AUDIT_LOG.md` §6): every
    number above was narrated at the window-5 default and left standing past
    the window-8 ruling of 2026-07-31 — uptakes 939/798/474, true_lost
    36/45/58, conv_lost 0/2/21, fab 0/0/23, preferences 1/3/5. Nothing here
    changes what the test checks: it asserts the two arms equal on every key,
    never the keys' values, so the drift moved the docstring and not the
    gate."""
    keys = ["true_lost", "conv_lost", "true_ref", "conv_ref", "hits", "misses",
            "net", "uptakes", "questions", "adopted_fabricated", "preferences",
            "occ_bite"]
    for label, liars in (("no liar", ()), ("u1", ONE_LIAR), ("all four", ALL_LIARS)):
        untargeted = _arm(None, liars, keys)
        typified = _arm("prefer", liars, keys)
        assert untargeted == typified, (
            f"{label}: typification finally moved something — "
            f"{[(k, untargeted[k], typified[k]) for k in keys if untargeted[k] != typified[k]]}")
        assert untargeted["occ_bite"] == 0, (
            f"{label}: a preference disagreed with the answering peer "
            f"{untargeted['occ_bite']} times")


def test_the_binding_constraint_is_the_question_not_the_field():
    """WHAT THIS LICENSES, stated as the pre-registered claim the next stage
    should be able to fail.

    The three measurements above compose into a causal chain rather than another
    null, and the chain names its own next move. A liar cannot lie because an
    answer must carry the atom the question named; two peers cannot disagree for
    the same reason (Task 7's structural limit); and typification cannot sort
    speakers because it is never offered two of them. All three are one
    property of the question, and spec 11.2(a)'s **slot-question** `(R *x)` is
    the change that removes it — a pattern with a free slot lets a peer return
    a filler the asker did not name, which is simultaneously the first way two
    answers can differ AND the first way a lie can be volunteered.

    > **PRE-REGISTERED.** With slot-questions and one unreliable speaker,
    > fabricated adoptions rise above zero and the typified arm stops
    > reproducing the untargeted arm. If typification is still inert THERE, the
    > defect is in typification and not in its world, and the "no unreliable
    > speaker" limit is discharged as an explanation.

    This test asserts only the baseline that claim will be read against, so the
    zero is on the record before the mechanism that should move it exists."""
    keys = ["adopted_fabricated", "occ_bite"]
    baseline = _arm("prefer", ONE_LIAR, keys)
    assert baseline == {"adopted_fabricated": 0, "occ_bite": 0}, (
        f"the pre-slot-question baseline moved: {baseline}")
