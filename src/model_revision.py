"""
model_revision — the minimal step by which a reference model M *transforms
through ongoing dialog*.

An inning of the Endoporeutic Game is *given M, then G*: a proposal G is peeled
against the model M and disposed of (a theorem, a refutation, a new fact, …). What
the disposition taxonomy names but the engine did not yet enact is **revising M
itself** — the model is not frozen, and the dialogue is exactly how it grows and is
corrected. This module supplies that step.

Two moves, and they are the two the calculus already licenses on the sheet of a
model (docs/MANIFEST_AND_MEANING.md floor #1–#2; docs/LEVEL_ZERO_AND_THE_REGISTERS.md §5):

  * **Enlargement** — admit a new ground fact (the ``new_fact`` disposition: an
    *independent* proposal the dialogue accepts as evidence). The fact is juxtaposed
    onto M's sheet — a new posit, entering at **low warrant**, never asserted true.
  * **Relinquishment** — retract a fact (the dual: *free to demote*, ERA in the
    positive context M's facts inhabit). Nothing in a model is ever frozen; the only
    bedrock is the blank sheet.

A model so revised is a **diachronic UoD**: each revision is a recorded transition,
so M carries its own history (the ``ProofChain`` / ``save_uod_with_chain`` machinery),
and "how M came to be what it is" is replayable — the dialogue, drawn. The verdict a
later inning gives can flip as M grows, which is the whole point: *fact is the
defeasible status of the last-standing trajectory*, answerable to new evidence.

Geometry-free except for the §3.3 attestation that ``save`` already enforces on the
resulting model. Used by ``tools/build_dialog_model_evolution.py``.
"""

from __future__ import annotations

from typing import List, Optional

from egi_core_dau import RelationalGraphWithCuts
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif

# Disposition kinds this module enacts (a subset of the Agon taxonomy that *revises M*).
DISPOSITION_NEW_FACT = "new_fact"        # admit an independent proposal as evidence
DISPOSITION_RETRACT = "retract_fact"     # relinquish a fact (free to demote)


def assert_fact(model: RelationalGraphWithCuts, fact_egif: str) -> RelationalGraphWithCuts:
    """**Enlargement.** Admit ``fact_egif`` into the model by juxtaposing it onto
    M's sheet (conjunction). The result is a new posit at low warrant — the model
    has *grown*, not been proven. Returns a fresh EGI (M ∧ fact)."""
    base = generate_egif(model).strip()
    fact = fact_egif.strip()
    combined = f"{base} {fact}".strip() if base else fact
    return parse_egif(combined)


def _atom_egif(model: RelationalGraphWithCuts, edge) -> str:
    """The EGIF of one ground-fact atom: relation name + its constant arguments."""
    name = model.rel.get(edge.id)
    args = []
    for v in model.nu.get(edge.id, ()):
        label = model.get_vertex(v).label
        args.append(f'"{label}"' if label else "*x")
    return f"({name} {' '.join(args)})" if args else f"({name})"


def retract_relation(
    model: RelationalGraphWithCuts, relation: str
) -> RelationalGraphWithCuts:
    """**Relinquishment.** Drop every sheet-level fact named ``relation`` from M
    (the dual of enlargement — *free to demote*). Rebuilds M from its surviving
    atoms, so the model can fall as well as grow. Raises if no such fact is present
    (a retraction must have something to retract)."""
    from eg_navigation import area_of
    sheet_edges = [e for e in model.E if area_of(model, e.id) == model.sheet]
    if not any(model.rel.get(e.id) == relation for e in sheet_edges):
        raise ValueError(f"no sheet-level fact named {relation!r} to retract")
    keep = [e for e in sheet_edges if model.rel.get(e.id) != relation]
    return parse_egif(" ".join(_atom_egif(model, e) for e in keep))


def revise_with_disposition(
    model: RelationalGraphWithCuts,
    disposition: str,
    *,
    fact_egif: Optional[str] = None,
    relation: Optional[str] = None,
) -> RelationalGraphWithCuts:
    """Enact a model-revising disposition, returning the revised M.

      * ``new_fact``     — ``fact_egif`` is admitted (enlargement).
      * ``retract_fact`` — every fact named ``relation`` is relinquished.
    """
    if disposition == DISPOSITION_NEW_FACT:
        if not fact_egif:
            raise ValueError("new_fact disposition requires fact_egif")
        return assert_fact(model, fact_egif)
    if disposition == DISPOSITION_RETRACT:
        if not relation:
            raise ValueError("retract_fact disposition requires relation")
        return retract_relation(model, relation)
    raise ValueError(f"disposition {disposition!r} does not revise M")
