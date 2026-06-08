"""
SUO-KIF → existential-graph translator — the honest-partial-import path for a
large, externally-authored, *merged* ontology (SUMO; ``docs/references/SUMO1.2.txt``;
Niles & Pease 2001, built on Sowa's upper ontology, KR 2000).

The manifest floor (*attest correspondence, not truth*; warrant is a gradient)
makes the discipline here non-negotiable: we translate **only** the axiom forms
that are genuinely first-order-EG-expressible, and we **report everything we drop**
— no silent truncation that would read as "imported all of SUMO" when it didn't.

Translatable forms (→ ``ontology_egif`` constructors):

    (subclass-of A B)      → subsumes(A, B)       A ⊑ B
    (disjoint A B)         → disjoint(A, B)        A ⊓ B ⊑ ⊥
    (instance-of X C)      → instance(X, C)        an A-box typing (C an EGIF id)

Deliberately *not* translated (counted and reported as skipped):

    documentation          natural-language strings — metadata, not a sign
    => / <=> / forall       general implications/biconditionals — many are modal
                            (nec/poss) or higher-order in SUMO; not first-order EG
    nth-domain              an argument-typing *abbreviation* over predicates-as-
                            arguments (higher-order); expressible per-relation only
                            once expanded — out of scope for this pass
    = / not / part-of / …   the remainder

Schema/definitional axioms whose arguments are KIF **variables** (``?x``) are not
ground facts and are skipped too.  ``translate(text)`` returns ``(egif, report)``.
Run standalone to print the report for the bundled SUMO file.
"""

import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ontology_egif import OntologyEGIF

# A SUMO/KIF symbol: CamelCase class names are the convention; we accept a
# letter-led alphanumeric token (and treat ?-led tokens as variables to skip).
_SYM = r"[A-Za-z][A-Za-z0-9]*"


def _strip_comments(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(";")
    )


def _top_level_forms(text: str) -> List[str]:
    """Split balanced-paren top-level forms (KIF strings may contain parens; we
    respect double-quoted spans)."""
    forms: List[str] = []
    depth = 0
    start = None
    in_str = False
    for i, ch in enumerate(text):
        if in_str:
            if ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                forms.append(text[start : i + 1])
                start = None
    return forms


def _operator(form: str) -> Optional[str]:
    m = re.match(r"\(\s*([A-Za-z<=>?\-][A-Za-z0-9<=>?\-]*)", form)
    return m.group(1) if m else None


def translate(text: str) -> Tuple[str, Dict]:
    """Translate the EG-expressible ground axioms of a SUO-KIF document.

    Returns ``(egif, report)`` where ``report`` tallies translated forms and,
    crucially, every form *not* translated, by operator — the honest record of
    what did and did not cross into the graph.
    """
    forms = _top_level_forms(_strip_comments(text))
    onto = OntologyEGIF()
    translated = Counter()
    skipped = Counter()

    sub_re = re.compile(rf"^\(\s*subclass-of\s+({_SYM})\s+({_SYM})\s*\)$")
    dis_re = re.compile(rf"^\(\s*disjoint\s+({_SYM})\s+({_SYM})\s*\)$")
    ins_re = re.compile(rf"^\(\s*instance-of\s+({_SYM})\s+({_SYM})\s*\)$")

    for form in forms:
        flat = " ".join(form.split())
        op = _operator(form)
        m = sub_re.match(flat)
        if m:
            onto.subsumes(*m.groups()); translated["subclass-of"] += 1; continue
        m = dis_re.match(flat)
        if m:
            onto.disjoint(*m.groups()); translated["disjoint"] += 1; continue
        m = ins_re.match(flat)
        if m:
            onto.instance(*m.groups()); translated["instance-of"] += 1; continue
        # Not a ground, EG-expressible fact — record why (operator, or "schema"
        # when a subclass/disjoint carried variables).
        if op in ("subclass-of", "disjoint", "instance-of"):
            skipped[f"{op} (variable/non-ground)"] += 1
        else:
            skipped[op or "?"] += 1

    report = {
        "translated": dict(translated),
        "skipped": dict(skipped),
        "classes": sorted(onto.classes),
        "individuals": sorted(onto.individuals),
        "n_axioms": len(onto),
    }
    return onto.egif(), report


def upper_taxonomy(text: str, root: str = "Entity", max_depth: int = 2):
    """The *upper spine* of a subclass taxonomy: keep ground ``subclass-of`` and
    ``disjoint`` axioms among classes within ``max_depth`` of ``root``.  A legible,
    fast-to-render fragment of a large taxonomy.  Returns ``(egif, report, kept)``.
    """
    full_egif, report = translate(text)  # for the full report (what's skipped)
    forms = _top_level_forms(_strip_comments(text))
    sub_re = re.compile(rf"^\(\s*subclass-of\s+({_SYM})\s+({_SYM})\s*\)$")
    dis_re = re.compile(rf"^\(\s*disjoint\s+({_SYM})\s+({_SYM})\s*\)$")
    subs: List[Tuple[str, str]] = []
    diss: List[Tuple[str, str]] = []
    for form in forms:
        flat = " ".join(form.split())
        m = sub_re.match(flat)
        if m:
            subs.append(m.groups()); continue
        m = dis_re.match(flat)
        if m:
            diss.append(m.groups())

    from collections import defaultdict, deque
    children = defaultdict(list)
    for a, b in subs:
        children[b].append(a)
    depth = {root: 0}
    q = deque([root])
    while q:
        n = q.popleft()
        for c in children.get(n, []):
            if c not in depth:
                depth[c] = depth[n] + 1
                q.append(c)
    keep = {c for c, d in depth.items() if d <= max_depth}

    onto = OntologyEGIF()
    kept_sub = [(a, b) for a, b in dict.fromkeys(subs) if a in keep and b in keep]
    kept_dis = [(a, b) for a, b in dict.fromkeys(diss) if a in keep and b in keep]
    for a, b in kept_sub:
        onto.subsumes(a, b)
    for a, b in kept_dis:
        onto.disjoint(a, b)
    kept = {"subsumptions": kept_sub, "disjoints": kept_dis,
            "classes": sorted(keep), "max_depth": max_depth, "root": root}
    return onto.egif(), report, kept


def main(argv=None) -> int:
    path = Path(__file__).resolve().parent.parent / "docs" / "references" / "SUMO1.2.txt"
    text = path.read_text(encoding="latin-1")
    _, report = translate(text)
    print(f"SUO-KIF translation of {path.name}:")
    print("  translated:", report["translated"])
    print("  skipped   :", report["skipped"])
    print(f"  → {report['n_axioms']} EG axioms over {len(report['classes'])} classes")
    egif, _, kept = upper_taxonomy(text)
    print(f"\nupper spine (depth ≤ {kept['max_depth']} from {kept['root']}): "
          f"{len(kept['subsumptions'])} subsumptions + {len(kept['disjoints'])} disjoints "
          f"over {len(kept['classes'])} classes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
