"""
Tests for the authentic-Peirce LaTeX/TikZ exporter (``src/peirce_latex.py``).

The exporter is wedded to the EGI: it draws the §3.3-attested ``LayoutDTO``'s
own coordinates, so the printed picture *is* that DTO.  The tests reflect the
two tiers of guarantee:

* **Corpus-wide (every UoD), fast string-level** — every graph exports; the
  pair is §3.3-attested (``generate_layout`` would raise otherwise); the ``.tex``
  is *total* (every cut / predicate / vertex id appears, traceable to the EGI)
  and the macro counts match the EGI's.
* **Reader-faithfulness on a curated representative subset** — the drawing reads
  back (``eg_reader.read_drawing`` + ``reading_matches_egi``) to the *same* EGI,
  argument order included.  (The reader's recovery degrades on dense ontologies
  such as ``bfo_core`` / ``skos_core`` — a property of the reader's heuristics,
  not the exporter; §3.3 still attests those, covered by the corpus tier.)
* **Actual ``pdflatex`` compilation** of a curated handful (gated on a LaTeX
  toolchain), proving the emitted document and the shipped ``arisbe-eg.sty``
  macros are valid — using the universal ``article`` fallback class when the
  ``standalone`` class is absent (e.g. BasicTeX).

Compiling every UoD cold is too slow for CI, hence the curated compile subset.
"""

import dataclasses
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from eg_reader import read_drawing, reading_matches_egi
from layout_dto import Point
from peirce_latex import export_peirce_latex
from presentation_deltas import PresentationDelta
from tomos_service import TomosService
from web_api.services import export_service
from web_api.services.layout_service import generate_layout

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"
PEIRCE_STYLE = "peirce-authentic@1.0"

_HAS_PDFLATEX = shutil.which("pdflatex") is not None


def _standalone_cls_available() -> bool:
    if shutil.which("kpsewhich") is None:
        return False
    try:
        return subprocess.run(
            ["kpsewhich", "standalone.cls"], capture_output=True
        ).returncode == 0
    except Exception:  # pragma: no cover - environment plumbing
        return False


# Use the publication-correct standalone class when present, else the universal
# article fallback (the macros + body are identical either way).
_DOC_CLASS = "standalone" if _standalone_cls_available() else "article"


def _uod_ids():
    """Enumerate UoD IDs from the tomos corpus at collection time."""
    return [u["uod_id"] for u in TomosService(TOMOS_ROOT).list_uods()]


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


# --------------------------------------------------------------------------- #
# Corpus-wide: exported, attested, total, traceable                           #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_corpus_export_is_total_and_traceable(uod_id, tomos):
    """Every corpus graph exports to authentic-Peirce TikZ; the pair is
    §3.3-attested (generate_layout would raise otherwise); every EGI element id
    appears in the output (totality + traceability) and the macro counts match."""
    egi = tomos.load_uod(uod_id).current_egi
    dto, _svg = generate_layout(egi, style_name=PEIRCE_STYLE)  # attests §3.3
    tex = export_peirce_latex(dto, egi, standalone=False)

    assert "\\begin{tikzpicture}" in tex and "\\end{tikzpicture}" in tex

    for cut in egi.Cut:
        assert cut.id in tex, f"cut {cut.id} missing from output"
    for edge in egi.E:
        assert edge.id in tex, f"predicate {edge.id} missing from output"
    for v in egi.V:
        assert v.id in tex, f"vertex {v.id} missing from output"

    assert tex.count("\\egcut{") == len(egi.Cut)
    assert tex.count("\\egpred{") == len(egi.E)


# --------------------------------------------------------------------------- #
# Reader-faithfulness on a curated representative subset                       #
# --------------------------------------------------------------------------- #

_FAITHFUL_FORMS = {
    "alpha_double_cut": "~[ ~[ ] ]",
    "alpha_pred_in_cut": "~[ (P) ]",
    "beta_shared_vertex": "(Human *x) ~[ (Mortal x) ]",
    "scroll_conditional": "~[ (Man *x) ~[ (Mortal x) ] ]",
    "teridentity": "(loves *x *y) (knows x y) (likes x y)",
    "constant": '(Human "Socrates")',
}


@pytest.mark.parametrize("name", list(_FAITHFUL_FORMS))
def test_drawing_reads_back_to_egi(name):
    """The authentic-Peirce drawing reads back to the same EGI — argument order
    included — so the picture provably denotes the EGI it was drawn from."""
    egi = parse_egif(_FAITHFUL_FORMS[name])
    dto, _svg = generate_layout(egi, style_name=PEIRCE_STYLE)
    # The exporter is a pure function of this DTO, so a faithful DTO ⇒ faithful .tex.
    assert reading_matches_egi(read_drawing(dto), egi, ordered=True)
    tex = export_peirce_latex(dto, egi, standalone=False)
    assert "\\begin{tikzpicture}" in tex


def test_faithfulness_check_has_teeth():
    """Falsifier: doctoring the drawing (move a vertex into a cut it is outside)
    makes the reader recover a *different* graph — proving reading_matches_egi
    is a real check, not vacuous."""
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    dto, _svg = generate_layout(egi, style_name=PEIRCE_STYLE)
    assert reading_matches_egi(read_drawing(dto), egi, ordered=True)

    cut_id = next(iter(egi.Cut)).id
    b = dto.cut_bounds[cut_id]
    vid = next(iter(dto.vertex_positions))
    moved = dict(dto.vertex_positions)
    moved[vid] = Point((b.min_x + b.max_x) / 2.0, (b.min_y + b.max_y) / 2.0)
    doctored = dataclasses.replace(dto, vertex_positions=moved)

    assert not reading_matches_egi(read_drawing(doctored), egi, ordered=True)


# --------------------------------------------------------------------------- #
# Style honored                                                               #
# --------------------------------------------------------------------------- #


def test_peirce_output_uses_oval_cuts_and_heavy_lines():
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    dto, _svg = generate_layout(egi, style_name=PEIRCE_STYLE)
    tex = export_peirce_latex(dto, egi, standalone=False)
    assert "\\egcut{" in tex           # oval cuts via the macro layer
    assert "\\egloi{" in tex           # heavy lines of identity
    assert "\\egset{" in tex           # knobs set from the style


def test_standalone_inlines_macros_and_is_self_contained():
    egi = parse_egif("~[ (P) ]")
    dto, _svg = generate_layout(egi, style_name=PEIRCE_STYLE)
    tex = export_peirce_latex(dto, egi, standalone=True)
    assert "\\documentclass" in tex
    assert "\\newcommand{\\egcut}" in tex   # macros inlined, no external .sty needed
    assert "\\makeatletter" in tex and "\\makeatother" in tex


# --------------------------------------------------------------------------- #
# Service / route wiring                                                       #
# --------------------------------------------------------------------------- #


def test_format_registered_and_available():
    fmts = {f["format"]: f for f in export_service.available_formats()}
    assert "peirce-tikz" in fmts
    assert fmts["peirce-tikz"]["available"] is True
    assert fmts["peirce-tikz"]["ext"] == "tex"


def test_export_egi_dispatches_peirce_tikz():
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    art = export_service.export_egi(egi, "peirce-tikz", basename="demo")
    assert art["filename"] == "demo.tex"
    assert art["is_binary"] is False
    assert "\\begin{tikzpicture}" in art["content"]
    assert "\\egcut{" in art["content"]


# --------------------------------------------------------------------------- #
# Peirce Edition Project: export the *adjusted* arrangement (regime-3 deltas)  #
# --------------------------------------------------------------------------- #


def test_pep_delta_is_published_as_drawn():
    """Journey 1 (transcribe-then-tune): a scholar nudges the drawing within the
    logic (a regime-3 move_vertex), then exports.  The export reflects the nudge
    ("export what you adjusted to see"), and §3.3 still attests (no raise)."""
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    canonical, _ = generate_layout(egi, style_name=PEIRCE_STYLE)
    vid = next(iter(canonical.vertex_positions))
    before = canonical.vertex_positions[vid]

    delta = PresentationDelta(op="move_vertex",
                              params={"vertex_id": vid, "dx": 40.0, "dy": 0.0})
    adjusted, _ = generate_layout(egi, style_name=PEIRCE_STYLE, deltas=[delta])
    after = adjusted.vertex_positions[vid]
    assert abs(after.x - before.x) > 1.0  # the nudge took effect in the layout

    # The same adjustment, threaded through the export service, reaches the .tex.
    plain = export_service.export_egi(egi, "peirce-tikz")["content"]
    tuned = export_service.export_egi(egi, "peirce-tikz", deltas=[delta])["content"]
    assert plain != tuned  # the published figure differs — it was adjusted


# --------------------------------------------------------------------------- #
# Actual pdflatex compilation (gated)                                         #
# --------------------------------------------------------------------------- #

_COMPILE_FORMS = {
    "alpha_double_cut": "~[ ~[ ] ]",
    "beta_teridentity": "(loves *x *y) (knows x y) (likes x y)",
    "scroll": "~[ (Man *x) ~[ (Mortal x) ] ]",
    "isolated_vertex": "[*x]",
    "empty_cut_and_pred": "(rain) ~[ ]",
    "tex_special_name": "(under_score *x)",  # exercises _tex_escape on `_`
}


@pytest.mark.skipif(not _HAS_PDFLATEX, reason="pdflatex not installed")
@pytest.mark.parametrize("name", list(_COMPILE_FORMS))
def test_standalone_compiles_with_pdflatex(name, tmp_path):
    egi = parse_egif(_COMPILE_FORMS[name])
    dto, _svg = generate_layout(egi, style_name=PEIRCE_STYLE)
    tex = export_peirce_latex(dto, egi, standalone=True, document_class=_DOC_CLASS)

    src = tmp_path / f"{name}.tex"
    src.write_text(tex, encoding="utf-8")
    proc = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
         "-output-directory", str(tmp_path), str(src)],
        capture_output=True, text=True, timeout=60,
    )
    pdf = tmp_path / f"{name}.pdf"
    assert proc.returncode == 0, proc.stdout[-1500:]
    assert pdf.exists() and pdf.stat().st_size > 0


# --------------------------------------------------------------------------- #
# Iconic scroll glyph (opt-in, ink-only)                                       #
# --------------------------------------------------------------------------- #

_SCROLL_FORM = "~[ (Man *x) ~[ (Mortal x) ] ]"


def test_scroll_glyph_is_opt_in_and_ink_only():
    """The iconic scroll is opt-in and ink-only: it changes the stroke for a
    detected scroll but never the DTO, so faithfulness is preserved either way."""
    egi = parse_egif(_SCROLL_FORM)
    dto, _svg = generate_layout(egi, style_name=PEIRCE_STYLE)
    assert reading_matches_egi(read_drawing(dto), egi, ordered=True)

    plain = export_peirce_latex(dto, egi, standalone=False)
    iconic = export_peirce_latex(dto, egi, standalone=False, scroll_glyph=True)

    # Default off: both cuts are plain ovals + a scroll annotation comment.
    assert plain.count("\\egcut{") == len(egi.Cut)
    assert "% scroll:" in plain
    # Opt-in: the outer cut becomes a drawn scroll curve (one fewer \egcut).
    assert "% scroll outer=" in iconic
    assert "\\draw[eg cut" in iconic
    assert iconic.count("\\egcut{") == len(egi.Cut) - 1
    # The DTO is untouched, so the picture still reads back to the same EGI.
    assert reading_matches_egi(read_drawing(dto), egi, ordered=True)
    assert plain != iconic


@pytest.mark.skipif(not _HAS_PDFLATEX, reason="pdflatex not installed")
def test_scroll_glyph_compiles(tmp_path):
    egi = parse_egif(_SCROLL_FORM)
    dto, _svg = generate_layout(egi, style_name=PEIRCE_STYLE)
    tex = export_peirce_latex(dto, egi, standalone=True,
                              document_class=_DOC_CLASS, scroll_glyph=True)
    src = tmp_path / "scroll.tex"
    src.write_text(tex, encoding="utf-8")
    proc = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
         "-output-directory", str(tmp_path), str(src)],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout[-1500:]
    assert (tmp_path / "scroll.pdf").exists()


# --------------------------------------------------------------------------- #
# Worked-chain document (a reasoning episode in print)                         #
# --------------------------------------------------------------------------- #

_CHAIN_UOD = "beta_modus_ponens"  # a small canonical chain (IT- then DC-)


def test_chain_document_assembles(tomos):
    """A worked transformation chain exports as one document: a title, an
    'Initial graph', one captioned figure per step, all naming their rule."""
    chain = tomos.load_chain(_CHAIN_UOD)
    assert chain is not None and chain.steps
    art = export_service.export_peirce_chain(chain, title="Beta Modus Ponens")
    doc = art["content"]
    assert art["format"] == "peirce-chain" and art["filename"].endswith(".tex")
    assert "Beta Modus Ponens" in doc
    assert "Initial graph" in doc
    # one figure (each body emits exactly one per-figure marker comment) for the
    # initial state + one per step.  (Counting macro names would also catch the
    # inlined .sty's usage-example comments, so key on the exporter's marker.)
    assert doc.count("% authentic Peirce EG") == 1 + len(chain.steps)
    for k, step in enumerate(chain.steps, start=1):
        assert f"Step {k}:" in doc
        assert step.rule_name in doc


@pytest.mark.skipif(not _HAS_PDFLATEX, reason="pdflatex not installed")
def test_chain_document_compiles(tomos, tmp_path):
    chain = tomos.load_chain(_CHAIN_UOD)
    art = export_service.export_peirce_chain(chain, title="Beta Modus Ponens")
    src = tmp_path / "chain.tex"
    src.write_text(art["content"], encoding="utf-8")
    proc = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
         "-output-directory", str(tmp_path), str(src)],
        capture_output=True, text=True, timeout=90,
    )
    pdf = tmp_path / "chain.pdf"
    assert proc.returncode == 0, proc.stdout[-1500:]
    assert pdf.exists() and pdf.stat().st_size > 0


# --------------------------------------------------------------------------- #
# Scholarly citation caption (publication path)                                #
# --------------------------------------------------------------------------- #

_CAPTION = "Peirce, C. S. (1903). MS 280, p. 12. § a & b_c 100% faithful."


def test_caption_is_ink_outside_the_picture():
    """A citation caption is emitted under the figure, TeX-escaped, and leaves the
    tikzpicture body byte-identical (ink outside the picture — §3.3 untouched)."""
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    dto, _svg = generate_layout(egi, style_name=PEIRCE_STYLE)
    plain = export_peirce_latex(dto, egi, standalone=True, document_class=_DOC_CLASS)
    cited = export_peirce_latex(dto, egi, standalone=True, document_class=_DOC_CLASS,
                                caption=_CAPTION)
    assert "footnotesize" not in plain
    assert "footnotesize" in cited
    # TeX-special chars escaped, not raw.
    assert "\\%" in cited and "\\&" in cited and "\\_" in cited
    body = lambda t: t.split("\\begin{tikzpicture}")[1].split("\\end{tikzpicture}")[0]
    assert body(plain) == body(cited)


@pytest.mark.skipif(not _HAS_PDFLATEX, reason="pdflatex not installed")
def test_captioned_document_compiles(tmp_path):
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    dto, _svg = generate_layout(egi, style_name=PEIRCE_STYLE)
    tex = export_peirce_latex(dto, egi, standalone=True, document_class=_DOC_CLASS,
                              caption=_CAPTION)
    src = tmp_path / "cited.tex"
    src.write_text(tex, encoding="utf-8")
    proc = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
         "-output-directory", str(tmp_path), str(src)],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout[-1500:]
    assert (tmp_path / "cited.pdf").exists()
