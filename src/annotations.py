"""
Annotation layer — marginalia *about* a UoD, its chain, a step, or an element.

A comment is a **telling about** the reasoning, not part of it.  So annotations
live in a side layer, never baked into the EGI, the ``ChainStep`` record, or the
``UoDMetadata`` — exactly as regime-3 presentation deltas ride alongside the
graph without being part of it.  Three consequences follow, and they are the
whole contract of this module (see ``docs/ORGANON_IMPORT_WALKTHROUGH.md`` §3):

- **Outside §3.3.** An annotation is not a sign in the existential graph, so the
  correspondence chord does not answer for it.  This module imports no layout,
  renderer, or attestation code and performs no attestation — by construction.
- **Many-per-target.** Unlike a delta (one override per element), a target may
  carry *several* annotations (a thread of marginalia).  The layer is therefore
  a **list** of self-describing entries, not a dict keyed by target.
- **Four scopes.** An entry names what it is about:

      uod      — the universe as a whole          (no target keys)
      chain    — the worked derivation as a whole  (no target keys)
      step     — one ``ChainStep``                 (step_id)
      element  — a vertex / edge / cut in a state   (state_id + element_id)

  ``chain`` is kept distinct from ``uod`` even for single-chain UoDs: a remark
  on *the proof* ("this is the classic non-intuitionistic move") is not a remark
  on *the universe*, and the two read differently.

The existing per-step ``ChainStep.user_annotation`` is **not** replaced — it is
the author's own rationale *baked into the chain* (it travels with the proof as
authored).  This layer is **additive**: it adds external / marginal commentary
at any scope, including *further* step-scoped notes alongside the baked-in one.

This module owns the data shape only.  Persistence is
``tomos_service.save_annotations`` / ``load_annotations`` (a ``annotations.json``
side-file, mirroring ``bibliography.json``); read paths surface it.
"""

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

SCOPE_UOD = "uod"
SCOPE_CHAIN = "chain"
SCOPE_STEP = "step"
SCOPE_ELEMENT = "element"
_SCOPES = (SCOPE_UOD, SCOPE_CHAIN, SCOPE_STEP, SCOPE_ELEMENT)

# Which target fields each scope requires.  uod/chain address the whole thing;
# step needs the step it annotates; element needs the state and the element.
_REQUIRED_TARGET: Dict[str, tuple] = {
    SCOPE_UOD: (),
    SCOPE_CHAIN: (),
    SCOPE_STEP: ("step_id",),
    SCOPE_ELEMENT: ("state_id", "element_id"),
}


@dataclass(frozen=True)
class Annotation:
    """One comment, self-describing its target.

    ``scope`` is one of the four constants; the target keys
    (``state_id`` / ``step_id`` / ``element_id``) are populated per
    ``_REQUIRED_TARGET[scope]`` and left ``None`` otherwise.  ``tags`` carries
    free labels (e.g. ``["crux"]``, or engineering metadata like
    ``["fixture", "beta-crux"]`` — a comment that is also a test note rides on a
    tag, not a new scope).  ``id`` is stable: derived from content when not
    supplied, so re-running a seeding tool is idempotent.
    """

    scope: str
    text: str
    id: str = ""
    author: Optional[str] = None
    created: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    state_id: Optional[str] = None
    step_id: Optional[str] = None
    element_id: Optional[str] = None

    def validate(self) -> None:
        """Raise ``ValueError`` if the scope or its required target is malformed."""
        if self.scope not in _SCOPES:
            raise ValueError(f"Annotation: unknown scope {self.scope!r}")
        if not (self.text or "").strip():
            raise ValueError("Annotation: text must be non-empty")
        for key in _REQUIRED_TARGET[self.scope]:
            if not getattr(self, key):
                raise ValueError(
                    f"Annotation scope {self.scope!r} requires {key!r}"
                )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scope": self.scope,
            "text": self.text,
            "author": self.author,
            "created": self.created,
            "tags": list(self.tags),
            "state_id": self.state_id,
            "step_id": self.step_id,
            "element_id": self.element_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Annotation":
        return cls(
            scope=d["scope"],
            text=d["text"],
            id=d.get("id", ""),
            author=d.get("author"),
            created=d.get("created"),
            tags=list(d.get("tags", [])),
            state_id=d.get("state_id"),
            step_id=d.get("step_id"),
            element_id=d.get("element_id"),
        )


def _derive_id(
    scope: str,
    text: str,
    state_id: Optional[str],
    step_id: Optional[str],
    element_id: Optional[str],
) -> str:
    """A stable id from scope + target + text — deterministic (no time/random),
    so a seeding tool that re-creates the same annotation produces the same id.
    """
    basis = "|".join(
        [scope, state_id or "", step_id or "", element_id or "", text]
    )
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:8]
    return f"ann_{digest}"


def make_annotation(
    scope: str,
    text: str,
    *,
    author: Optional[str] = None,
    created: Optional[str] = None,
    tags: Optional[List[str]] = None,
    state_id: Optional[str] = None,
    step_id: Optional[str] = None,
    element_id: Optional[str] = None,
    ann_id: Optional[str] = None,
) -> Annotation:
    """Build and validate an annotation; derive a stable id when none is given."""
    ann = Annotation(
        scope=scope,
        text=text,
        id=ann_id or _derive_id(scope, text, state_id, step_id, element_id),
        author=author,
        created=created,
        tags=list(tags or []),
        state_id=state_id,
        step_id=step_id,
        element_id=element_id,
    )
    ann.validate()
    return ann


# ----- query helpers (for read paths) -----

def for_scope(anns: List[Annotation], scope: str) -> List[Annotation]:
    """All annotations of a given scope (e.g. the uod- or chain-level notes)."""
    return [a for a in anns if a.scope == scope]


def for_step(anns: List[Annotation], step_id: str) -> List[Annotation]:
    """Step-scoped annotations attached to one ``ChainStep``."""
    return [a for a in anns if a.scope == SCOPE_STEP and a.step_id == step_id]


def for_element(
    anns: List[Annotation], state_id: str, element_id: str
) -> List[Annotation]:
    """Element-scoped annotations anchored to one element in one state."""
    return [
        a
        for a in anns
        if a.scope == SCOPE_ELEMENT
        and a.state_id == state_id
        and a.element_id == element_id
    ]


def for_state(anns: List[Annotation], state_id: str) -> List[Annotation]:
    """All element-scoped annotations within one state (any element)."""
    return [
        a for a in anns if a.scope == SCOPE_ELEMENT and a.state_id == state_id
    ]


def annotations_to_list(anns: List[Annotation]) -> List[Dict[str, Any]]:
    """Serialize an annotation list to JSON-ready dicts."""
    return [a.to_dict() for a in anns]


def annotations_from_list(items: List[Dict[str, Any]]) -> List[Annotation]:
    """Rehydrate an annotation list from JSON dicts."""
    return [Annotation.from_dict(d) for d in items]


__all__ = [
    "Annotation",
    "SCOPE_UOD",
    "SCOPE_CHAIN",
    "SCOPE_STEP",
    "SCOPE_ELEMENT",
    "make_annotation",
    "for_scope",
    "for_step",
    "for_element",
    "for_state",
    "annotations_to_list",
    "annotations_from_list",
]
