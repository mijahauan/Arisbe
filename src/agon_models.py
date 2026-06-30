"""
Curated reference-model scenarios for the Agon interpretation register.

An inning of the Endoporeutic Game is *given M, then G* — but you can only play if
there is an M to choose.  These are ready-to-use reference models (with a sample
proposal each), so a newcomer can select one and immediately see the peel:
the five persona innings from ``docs/ARISBE_PERSONAS.md`` /
``docs/GENERATION_AND_TESTING.md``, one per outcome (holds / fails / independent).

Real models also come from the tomos corpus (any UoD's asserted EGI); these examples
are the on-ramp, not the whole supply.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ExampleModel:
    """A selectable reference model M, with a sample proposal G to test against it."""

    id: str
    title: str
    model_egif: str       # the reference world M (ground facts, optionally + Horn rules)
    closed: bool          # asserted-complete (a miss is FALSE) vs sampled (UNKNOWN)
    sample_proposal: str  # a G that shows this model's characteristic outcome
    note: str             # what the inning illustrates
    materialize: bool = False  # M is a *theory* — forward-chain its Horn rules before the peel


EXAMPLE_MODELS: List[ExampleModel] = [
    ExampleModel(
        id="teacher-mammals",
        title="Mammals — a closed zoology (holds)",
        model_egif='(mammal "Rex") (warmblooded "Rex") (mammal "Whale") (warmblooded "Whale")',
        closed=True,
        sample_proposal='~[ (mammal *x) ~[ (warmblooded x) ] ]',
        note="“Every mammal is warm-blooded” is a theorem of this closed world — the Proposer wins.",
    ),
    ExampleModel(
        id="student-sea",
        title="Sea creatures — a closed survey (fails)",
        model_egif='(seacreature "Whale") (warmblooded "Whale") (seacreature "Cod") (coldblooded "Cod")',
        closed=True,
        sample_proposal='~[ (seacreature *x) ~[ (coldblooded x) ] ]',
        note="“All sea creatures are cold-blooded” is refuted by Whale — the counterexample the peel names.",
    ),
    ExampleModel(
        id="researcher-coast",
        title="Wetland & coast — an open record (independent)",
        model_egif='(wetland "Marsh") (sustains "Marsh" "CoastTown") (coastal "CoastTown")',
        closed=False,
        sample_proposal='(coastal "CoastTown") (generates_tourism "CoastTown")',
        note="Open world: the tourism claim is independent — neither confirmed nor denied (a candidate new fact).",
    ),
    ExampleModel(
        id="physician-ward",
        title="Ward chart — closed but incomplete (fails on silence)",
        model_egif='(mammal "Biscuit") (mammal "Whale") (warmblooded "Whale")',
        closed=True,
        sample_proposal='~[ (mammal *x) ~[ (warmblooded x) ] ]',
        note="FALSE — but Biscuit's warm-bloodedness is merely unrecorded: complete M, don't reject the rule.",
    ),
    ExampleModel(
        id="logician-open",
        title="One mammal — open world (the horizon)",
        model_egif='(mammal "Rex") (warmblooded "Rex")',
        closed=False,
        sample_proposal='~[ (mammal *x) ~[ (warmblooded x) ] ]',
        note="The same universal reads UNKNOWN open / TRUE closed — closing the world is what licenses ∀.",
    ),
    # --- Boards drawn from the corpus domain-model exemplars (docs/EXEMPLARS.md). ---
    # These inline the same EGIF as the `zoo_world` / `harbor_town` corpus UoDs
    # (built by tools/build_domain_model_exemplars.py), so they double as one-click
    # innings against the richer boards. The corpus UoDs are the source of truth.
    ExampleModel(
        id="zoo-chain",
        title="Zoo world — a Horn taxonomy (holds via the chain)",
        model_egif=(
            '(dog "Rex") (cat "Tom") (whale "Moby") (sparrow "Pip") '
            '~[ (dog *x) ~[ (mammal x) ] ] ~[ (cat *x) ~[ (mammal x) ] ] '
            '~[ (whale *x) ~[ (mammal x) ] ] ~[ (sparrow *x) ~[ (bird x) ] ] '
            '~[ (mammal *x) ~[ (warmblooded x) ] ] ~[ (bird *x) ~[ (warmblooded x) ] ]'
        ),
        closed=True,
        materialize=True,
        sample_proposal='~[ (dog *x) ~[ (warmblooded x) ] ]',
        note="“Every dog is warm-blooded” holds — decided through the materialized "
             "dog→mammal→warm-blooded chain, not stated directly. Horn rules forward-chained.",
    ),
    ExampleModel(
        id="zoo-refuted",
        title="Zoo world — over-broad universal (fails, names Pip)",
        model_egif=(
            '(dog "Rex") (cat "Tom") (whale "Moby") (sparrow "Pip") '
            '~[ (dog *x) ~[ (mammal x) ] ] ~[ (cat *x) ~[ (mammal x) ] ] '
            '~[ (whale *x) ~[ (mammal x) ] ] ~[ (sparrow *x) ~[ (bird x) ] ] '
            '~[ (mammal *x) ~[ (warmblooded x) ] ] ~[ (bird *x) ~[ (warmblooded x) ] ]'
        ),
        closed=True,
        materialize=True,
        sample_proposal='~[ (warmblooded *x) ~[ (mammal x) ] ]',
        note="“Every warm-blooded thing is a mammal” is refuted — Pip the sparrow is the "
             "counterexample the peel names (warm-blooded via bird, yet no mammal).",
    ),
    ExampleModel(
        id="harbor-open",
        title="Harbor town — an open civic world (independent)",
        model_egif=(
            '(town "Bayside") (harbor "Bayside") (island "Greyrock") '
            '(ferry "Bayside" "Greyrock") (lighthouse "Greyrock")'
        ),
        closed=False,
        sample_proposal='(harbor "Bayside") (hosts_market "Bayside")',
        note="Open world: “Bayside hosts a market” is neither confirmed nor denied — "
             "UNKNOWN, a candidate new fact, not a falsehood.",
    ),
]


def list_example_models() -> List[ExampleModel]:
    return list(EXAMPLE_MODELS)
