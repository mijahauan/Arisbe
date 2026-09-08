#!/usr/bin/env python3
"""Give ``dau_theorem_proving`` the derivation its provenance already claims.

The record said ``"proof": "Original derivation by Arisbe (Peirce-Sowa EGIF)"``
while the UoD held a single static state and no chain at all — a claim with
nothing behind it. This builds the derivation, so the claim becomes true.

The graph is a deep nested-implication shell in the style of Dau's
theorem-proving examples (the style is Dau's; the graph is Arisbe's, and the
provenance says so). Its interest is that it looks deeper than it is: buried in
the third level sits a vacuous double negation. One DC- removes it, and four
cut levels become three without changing what the graph says.

That is the EG lesson worth more than the shell itself — depth on the sheet is
not the same as logical depth, and the calculus tells them apart.

Usage:
    uv run python tools/build_dau_theorem_proving_chain.py
"""

import sys
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav  # noqa: E402
from annotations import (  # noqa: E402
    SCOPE_CHAIN, SCOPE_STEP, SCOPE_UOD, annotations_to_list, make_annotation,
)
from egif_parser_dau import parse_egif  # noqa: E402
from proof_authoring import ProofChain  # noqa: E402

UOD_ID = "dau_theorem_proving"

SHELL_EGIF = "~[ *x (P x) ~[ *y (Q x y) ~[ ~[ *z (R y z) ~[ (S z) ] ] ] ] ]"
SETTLED_EGIF = "~[ *x (P x) ~[ *y *z (Q x y) (R y z) ~[ (S z) ] ] ]"


def _vacuous_double_cut(g) -> Optional[str]:
    """The cut whose sole content is another cut — a double negation.

    Located by structure rather than by id, so the locator survives a reparse
    and the step replays.
    """
    for cut_id in [c.id for c in g.Cut]:
        inner = g.area.get(cut_id, frozenset())
        if len(inner) == 1 and any(c.id == next(iter(inner)) for c in g.Cut):
            return cut_id
    return None


def build_chain() -> Tuple[object, object]:
    author = ProofChain.from_egif(SHELL_EGIF).apply(
        "DC-", select=_vacuous_double_cut, label="3e",
        note="Erase the vacuous double cut buried at the third level. Two "
             "negations cancel, so nothing the graph says changes — but the "
             "shell loses a level and its real structure shows.",
    )
    return author.to_uod(
        uod_id=UOD_ID,
        name="A Dau-Style Theorem-Proving Shell",
        description=(
            "A deep nested-implication shell in the style of Dau's "
            "theorem-proving examples, and a lesson in reading depth: buried "
            "at the third level is a vacuous double negation. One DC- removes "
            "it and four cut levels become three, with the graph saying "
            "exactly what it said before. Drawn depth is not logical depth, "
            "and the calculus is what tells them apart. The shell is Arisbe's; "
            "the style, and the rules that settle it, are Dau's."
        ),
    )


def provenance() -> dict:
    return {
        "theorem_source": {},
        "proof_source": {
            "kind": "authored",
            "author": "Arisbe",
            "system": "Peirce-Sowa EGIF",
            "note": "one DC- removing a vacuous double negation",
        },
        "method_sources": [{
            "type": "book",
            "author": "Dau, Frithjof",
            "title": "The Logic System of Concept Graphs with Negation",
            "publisher": "Springer",
            "year": "2003",
            "bibkey": "dau2003logic",
        }],
        "warrant": {"theorem": "low", "derivation": "low"},
        "kind": "exemplar",
        "formatted": {
            "theorem": "",
            "proof": "Original derivation by Arisbe (Peirce-Sowa EGIF)",
            "methods": [
                "Dau, Frithjof (2003). The Logic System of Concept Graphs with Negation"
            ],
        },
    }


def build_annotations() -> list:
    anns = [
        make_annotation(
            SCOPE_UOD,
            "A deep nested-implication shell in the style of Dau's "
            "theorem-proving examples. Its point is that it looks deeper than "
            "it is: a vacuous double negation sits at the third level, and one "
            "DC- takes the shell from four cut levels to three without "
            "changing what it says.",
            tags=["pedagogy", "beta", "cited"],
        ),
        make_annotation(
            SCOPE_CHAIN,
            "One step, and the whole of it: erase a double cut. The graph is "
            "logically unchanged and structurally simpler, which is the "
            "distinction the exemplar exists to draw.",
            tags=["derivation"],
        ),
        make_annotation(
            SCOPE_STEP,
            "DC- is meaning-preserving in any context, which is why this is a "
            "simplification and not an inference. Nothing is proved here; "
            "something is *seen*.",
            step_id="step-1", tags=["crux"],
        ),
    ]
    return annotations_to_list(anns)


def main(argv=None) -> int:
    from tomos_service import TomosService

    chain, uod = build_chain()
    assert nav.same_graph(uod.current_egi, parse_egif(SETTLED_EGIF)), (
        "the built derivation does not reach the settled shell"
    )

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=provenance())
    service.save_annotations(uod, build_annotations())
    print(f"Saved '{uod.uod_id}' with a {len(chain.steps)}-step chain.")
    print(f"  rules: {' -> '.join(s.rule_name for s in chain.steps)}")
    print(f"  from : {SHELL_EGIF}")
    print(f"  to   : {SETTLED_EGIF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
