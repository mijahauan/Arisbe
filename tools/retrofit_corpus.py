"""
Retrofit the pre-existing tomos corpus *up to spec* — attach a typed provenance
bundle (``src/provenance.py``) + an annotation layer (``src/annotations.py``) to
every curated UoD, so the whole corpus carries the same outside-record the
import-walkthrough fixtures do (``docs/ORGANON_IMPORT_WALKTHROUGH.md`` §5).

The corpus is **two populations**, and honesty (the manifest floor — *attest
correspondence, not truth*; warrant is a gradient) requires keeping them distinct:

  * **cited** — a real published proposition/diagram behind it: a ``theorem_source``
    citation (cross-referenced to ``docs/references/eg_proofs.bib`` where a bibkey
    exists).  ``theorem_praeclarum`` is the one with a *transcribed proof*.
  * **synthetic / authored-here** — a structural or pedagogical exemplar *named
    after a tradition* but not a transcription; ``theorem_source`` is absent and a
    note records what it exercises.  Fabricating a page citation for these is
    exactly the un-attested truth-claim the floor forbids.

Each bundle also carries an **import kind** (``exemplar`` / ``proof`` / ``pattern``
/ ``domain_model`` / ``ontology``) so Organon can shelve it and Agon can query it
("give me a domain model to play in", "an argument pattern to apply").  Everything
here is **outside §3.3** — provenance and annotations describe the source, they
are not signs in the graph; no attestation runs.  Idempotent: re-running rewrites
the side-files from this table.  Run: ``uv run python tools/retrofit_corpus.py``.
"""

import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from annotations import SCOPE_UOD, annotations_to_list, make_annotation
from provenance import (
    KIND_DOMAIN_MODEL,
    KIND_EXEMPLAR,
    KIND_PATTERN,
    KIND_PROOF,
    authored_proof,
    make_provenance,
    transcribed_proof,
)
from tomos_service import TomosService

# --------------------------------------------------------------------------- #
# Shared citations (CSL-compatible; bibkey → docs/references/eg_proofs.bib)     #
# --------------------------------------------------------------------------- #

PEIRCE_CP = {"type": "book", "author": "Peirce, Charles Sanders",
             "title": "Collected Papers of Charles Sanders Peirce",
             "publisher": "Harvard University Press", "year": "1931",
             "bibkey": "peirce1931collected"}
ROBERTS_1973 = {"type": "book", "author": "Roberts, Don D.",
                "title": "The Existential Graphs of Charles S. Peirce",
                "publisher": "Mouton", "year": "1973",
                "bibkey": "roberts1973existential"}
SOWA_2011 = {"type": "article-journal", "author": "Sowa, John F.",
             "title": "Peirce's Tutorial on Existential Graphs",
             "container_title": "Semiotica", "year": "2011", "pages": "345-394",
             "bibkey": "sowa2011tutorial"}
SOWA_CS = {"type": "book", "author": "Sowa, John F.",
           "title": "Conceptual Structures: Information Processing in Mind and Machine",
           "publisher": "Addison-Wesley", "year": "1984"}
DAU_MLD = {"type": "book", "author": "Dau, Frithjof",
           "title": "Mathematical Logic with Diagrams",
           "note": "manuscript; the page/edition of the p.112 ligature example "
                   "remains to be verified against a fixed copy"}
DAU_2008 = {"type": "misc", "author": "Dau, Frithjof",
            "title": "A Computer Animated Proof of Leibniz's Praeclarum Theorema",
            "year": "2008", "bibkey": "dau2008animated"}
LEIBNIZ = {"type": "incollection", "author": "Leibniz, Gottfried Wilhelm",
           "title": "Addenda to the Specimen of the Universal Calculus",
           "container_title": "Leibniz: Logical Papers", "year": "1966",
           "bibkey": "leibniz1966addenda"}

# Method-source shorthands (the calculus the graph is drawn / reasoned in).
M_PEIRCE = dict(PEIRCE_CP, note="Peirce's existential-graph notation")
M_DAU = {"type": "book", "author": "Dau, Frithjof",
         "title": "The Logic System of Concept Graphs with Negation",
         "publisher": "Springer", "year": "2003", "bibkey": "dau2003logic"}
M_SOWA = dict(SOWA_2011)
M_ROBERTS = dict(ROBERTS_1973)


def _exemplar(text: str, tags: List[str]) -> List[dict]:
    return annotations_to_list([make_annotation(SCOPE_UOD, text, tags=tags)])


# --------------------------------------------------------------------------- #
# The curated table: uod_id -> (provenance, annotations)                        #
# Cited items carry a theorem_source; synthetic ones are authored-here.         #
# --------------------------------------------------------------------------- #

def _bundle(uod_id: str):
    P = make_provenance
    table = {
        # ---- cited exemplars -------------------------------------------------
        "peirce_cp_4_394_man_mortal": (
            P(theorem_source=dict(PEIRCE_CP, pages="4.394",
                                  note="the man–mortal scroll (CP 4.394)"),
              method_sources=[M_PEIRCE], kind=KIND_EXEMPLAR),
            _exemplar("Peirce's own man–mortal scroll (CP 4.394): "
                      "Human(Socrates) ⊃ Mortal(Socrates) — the canonical Alpha "
                      "implication, a constant carried across the cut.",
                      ["pedagogy", "alpha", "cited"]),
        ),
        "roberts_1973_p57_disjunction": (
            P(theorem_source=dict(ROBERTS_1973, pages="57",
                                  note="disjunction P ∨ Q as ~[ ~[P] ~[Q] ]"),
              method_sources=[M_ROBERTS], kind=KIND_EXEMPLAR),
            _exemplar("Disjunction drawn the Peircean way (Roberts 1973, p.57): "
                      "P ∨ Q = ~[ ~[P] ~[Q] ] — two negated cuts inside a cut.",
                      ["pedagogy", "alpha", "cited"]),
        ),
        "sowa_2011_p356_quantification": (
            P(theorem_source=dict(SOWA_2011, pages="356",
                                  note="∀x (Human(x) → Mortal(x)) example"),
              method_sources=[M_SOWA], kind=KIND_EXEMPLAR),
            _exemplar("Sowa's quantification example (2011 tutorial, p.356): a "
                      "shared line of identity threads Human(x) and Mortal(x).",
                      ["pedagogy", "beta", "cited"]),
        ),
        "sowa_cat_on_mat": (
            P(theorem_source=dict(SOWA_CS,
                                  note="'the cat is on the mat' — Sowa's canonical "
                                       "conceptual-graph stock example"),
              method_sources=[M_SOWA], kind=KIND_EXEMPLAR),
            _exemplar("Sowa's canonical 'cat on a mat': a 3-relation Beta graph "
                      "with two lines of identity — the minimal n-ary relation "
                      "drawn as one spot.", ["pedagogy", "beta", "cited"]),
        ),
        "dau_2006_p112_ligature": (
            P(theorem_source=dict(DAU_MLD, pages="112",
                                  note="ligature example; page/edition to verify"),
              method_sources=[M_DAU], kind=KIND_EXEMPLAR),
            _exemplar("Dau's ligature example (Mathematical Logic with Diagrams, "
                      "≈p.112): one line of identity feeding P(x) on the sheet and "
                      "both Q(x), R(x) inside a cut. Source page to be verified.",
                      ["pedagogy", "beta", "cited", "verify-page"]),
        ),
        # ---- the one transcribed proof --------------------------------------
        "theorem_praeclarum": (
            P(theorem_source=dict(LEIBNIZ,
                                  note="Praeclarum Theorema: "
                                       "((p→r)∧(q→s)) → ((p∧q)→(r∧s))"),
              proof_source=transcribed_proof(dict(DAU_2008,
                  note="Dau's animated EG proof; the seven-step Alpha derivation "
                       "transcribed here")),
              method_sources=[M_DAU, M_PEIRCE], kind=KIND_PROOF),
            _exemplar("Leibniz's Praeclarum Theorema — the one corpus item with a "
                      "*transcribed* proof (Dau's animated EG derivation), not an "
                      "authored-here one. Theorem: Leibniz 1966 Addenda.",
                      ["proof", "alpha", "cited", "transcribed"]),
        ),
        # ---- argument pattern ------------------------------------------------
        "peirce_modus_ponens": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              method_sources=[M_PEIRCE], kind=KIND_PATTERN),
            _exemplar("The modus-ponens argument form in EG: P(x) asserted "
                      "alongside the scroll P(x) ⊃ Q(x). An authored pattern (not a "
                      "transcription) — a move available to Agon.",
                      ["pattern", "beta", "authored"]),
        ),
        # ---- domain model ----------------------------------------------------
        "roberts_domain_modeling": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              method_sources=[M_PEIRCE], kind=KIND_DOMAIN_MODEL),
            _exemplar("A small modelled universe of discourse (professor / course "
                      "/ student / teaches / has): an authored domain model — the "
                      "kind of board the Endoporeutic Game is played within.",
                      ["domain-model", "beta", "authored"]),
        ),
        # ---- synthetic / authored-here structural & pedagogical exemplars ----
        "dau_theorem_proving": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              method_sources=[M_DAU], kind=KIND_EXEMPLAR),
            _exemplar("A deep nested-implication shell in the style of Dau's "
                      "theorem-proving examples — authored here as a structural "
                      "exemplar (not transcribed from a fixed page).",
                      ["structural", "alpha", "authored"]),
        ),
        "mixed_quantifier_complex": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              kind=KIND_EXEMPLAR),
            _exemplar("Structural exemplar: mixed quantifier scope across cuts "
                      "(∀ outside, ∃ inside). Authored as a test case.",
                      ["structural", "beta", "authored"]),
        ),
        "peirce_complex_scope": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              kind=KIND_EXEMPLAR),
            _exemplar("Structural exemplar: a 3-adic generic Relation nested two "
                      "cuts deep — deep scope with a positive innermost area.",
                      ["structural", "beta", "authored"]),
        ),
        "shared_constant_disjunction": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              kind=KIND_EXEMPLAR),
            _exemplar("Structural exemplar: a constant (Socrates) shared between a "
                      "sheet assertion and a double-cut — constant interning across "
                      "polarity. Authored as a test case.",
                      ["structural", "beta", "authored"]),
        ),
        "sibling_cuts_shared_variable": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              kind=KIND_EXEMPLAR),
            _exemplar("Structural exemplar: one line of identity running into two "
                      "sibling cuts — the crossing-sequence stress case. Authored "
                      "as a test.", ["structural", "beta", "authored"]),
        ),
        "ternary_relation_challenge": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              kind=KIND_EXEMPLAR),
            _exemplar("Structural exemplar: a single 3-adic relation Between(x,y,z) "
                      "with three lines — exercises argument-order rendering. "
                      "Authored as a test.", ["structural", "beta", "authored", "arg-order"]),
        ),
        "stanford_nested_quantifiers": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              kind=KIND_EXEMPLAR),
            _exemplar("Pedagogical exemplar: nested quantifiers, ~[ ∃x ∃y Loves(x,y) ] "
                      "(nobody loves anybody). Authored as a teaching case in the "
                      "nested-quantifier idiom.", ["pedagogy", "beta", "authored"]),
        ),
        "beta_modus_ponens": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              kind=KIND_EXEMPLAR),
            _exemplar("Beta exemplar: P(x) ∧ Q(x) on one line of identity — the "
                      "conclusion shape of a Beta modus ponens. Authored.",
                      ["beta", "authored"]),
        ),
        "beta_converse_mp": (
            P(proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
              kind=KIND_EXEMPLAR),
            _exemplar("Beta exemplar: R(x,y) ∧ S(y,x) — a relation and its converse "
                      "sharing two lines. Authored as a test case.",
                      ["beta", "authored", "arg-order"]),
        ),
    }
    return table.get(uod_id)


# uod_ids to retire entirely (throwaway / non-curated).
RETIRE = ["practice_43480df3"]

# Existing import-walkthrough fixtures: already richly attributed — only stamp
# the import kind onto their bundle, don't overwrite their provenance/annotations.
FIXTURE_KINDS = {"peirce_law": KIND_PROOF, "barbara": KIND_PROOF,
                 "group_identity": KIND_PROOF}


def retrofit(tomos_root: Path) -> Dict[str, int]:
    service = TomosService(tomos_root)
    counts = {"retired": 0, "retrofitted": 0, "kind_stamped": 0, "skipped": 0}

    for uid in RETIRE:
        if service.delete_uod(uid):
            counts["retired"] += 1
            print(f"  retired   {uid}")

    # Stamp the import kind onto the already-attributed fixtures in place.
    for uid, kind in FIXTURE_KINDS.items():
        existing = service.load_provenance(uid)
        if existing is None:
            continue
        if existing.get("kind") != kind:
            existing["kind"] = kind
            uod = service.load_uod(uid)
            service.save_provenance(uod, existing)
            counts["kind_stamped"] += 1
            print(f"  kind={kind:12} {uid}")

    # Retrofit the rest from the curated table.
    for uid in [u["uod_id"] for u in service.list_uods()]:
        if uid in FIXTURE_KINDS or uid in RETIRE:
            continue
        bundle = _bundle(uid)
        if bundle is None:
            counts["skipped"] += 1
            print(f"  SKIP (no table entry) {uid}")
            continue
        prov, anns = bundle
        prov.validate()
        uod = service.load_uod(uid)
        if uod is None:
            counts["skipped"] += 1
            print(f"  SKIP (load failed) {uid}")
            continue
        service.save_provenance(uod, prov.to_dict())
        service.save_annotations(uod, anns)
        counts["retrofitted"] += 1
        k = prov.kind or "?"
        cited = "cited" if prov.theorem_source else "authored"
        print(f"  {k:12} {cited:9} {uid}")

    return counts


def main(argv=None) -> int:
    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    counts = retrofit(tomos_root)
    print(f"\nretired={counts['retired']} retrofitted={counts['retrofitted']} "
          f"kind_stamped={counts['kind_stamped']} skipped={counts['skipped']}")
    return 0 if counts["skipped"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
