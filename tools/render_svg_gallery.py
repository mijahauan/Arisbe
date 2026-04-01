#!/usr/bin/env python3
"""
Render a gallery of EGI diagrams as SVGs for visual validation.

Uses the ELK layout engine + SimpleSVGRenderer to produce one SVG per graph.
Output goes to output/svg_gallery/.

Usage:
    python tools/render_svg_gallery.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from elk_layout_engine import ELKLayoutEngine
from simple_svg_renderer import SimpleSVGRenderer
from style_loader import load_default_style

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "svg_gallery"

# Test cases: (filename, title, egif_string)
TEST_CASES = [
    # Basic
    ("01_single_predicate", "Single Predicate", "(Human *x)"),
    ("02_constant", "Constant Vertex", '(Human "Socrates")'),
    ("03_binary_relation", "Binary Relation", "(Loves *x *y)"),
    ("04_two_predicates", "Two Predicates Sharing Vertex", "(Human *x)(Mortal x)"),

    # Cuts (negation)
    ("05_simple_negation", "Simple Negation", "~[ (Cat *x) ]"),
    ("06_double_cut", "Double Cut (Double Negation)", "~[ ~[ (Cat *x) ] ]"),
    ("07_nested_cuts", "Nested Cuts (if Cat then Animal)",
     "~[ (Cat *x) ~[ (Animal x) ] ]"),
    ("08_sibling_cuts", "Sibling Cuts", "~[ (Cat *x) ] ~[ (Dog *y) ]"),

    # Complex
    ("09_syllogism_premise", "Syllogism: All humans are mortal",
     "~[ (Human *x) ~[ (Mortal x) ] ]"),
    ("10_modus_ponens", "Modus Ponens Setup",
     '(Human "Socrates") ~[ (Human *x) ~[ (Mortal x) ] ]'),
    ("11_three_deep", "Three Levels of Nesting",
     "~[ (A *x) ~[ (B x) ~[ (C x) ] ] ]"),
    ("12_conjunction", "Conjunction on Sheet",
     "(Cat *x)(Furry x)(Cute x)"),
    ("13_cross_boundary", "Cross-Boundary Ligature",
     "*x (Human x) ~[ (Mortal x) ]"),
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    engine = ELKLayoutEngine()
    renderer = SimpleSVGRenderer()
    style = load_default_style()

    print(f"Rendering {len(TEST_CASES)} diagrams to {OUTPUT_DIR}/\n")

    for filename, title, egif_str in TEST_CASES:
        try:
            egi = parse_egif(egif_str)
            dto = engine.generate_layout(egi, style)
            svg = renderer.render_to_svg(dto, title, egif_str, egi=egi)

            out_path = OUTPUT_DIR / f"{filename}.svg"
            out_path.write_text(svg, encoding="utf-8")
            print(f"  ✅ {filename}.svg  —  {title}")
        except Exception as exc:
            print(f"  ❌ {filename}.svg  —  {title}: {exc}")

    # Also render corpus examples if available
    corpus_dir = Path(__file__).parent.parent / "tomos" / "graphs"
    if corpus_dir.exists():
        print(f"\nCorpus examples from {corpus_dir}:")
        from egi_io import load_egi_json
        for egi_file in sorted(corpus_dir.glob("**/*.egi.json"))[:5]:
            try:
                egi = load_egi_json(egi_file)
                egif_str = generate_egif(egi)
                dto = engine.generate_layout(egi, style)
                name = egi_file.parent.name
                svg = renderer.render_to_svg(dto, name, egif_str, egi=egi)
                out_path = OUTPUT_DIR / f"corpus_{name}.svg"
                out_path.write_text(svg, encoding="utf-8")
                print(f"  ✅ corpus_{name}.svg")
            except Exception as exc:
                print(f"  ❌ corpus_{name}.svg: {exc}")

    # Render domain model imports
    print("\nDomain model imports:")
    try:
        from domain_model_importer import from_clif_file, from_type_lattice
        clif_path = Path(__file__).parent.parent / "corpus" / "domain_models" / "animal_taxonomy" / "animal_taxonomy.clif"
        if clif_path.exists():
            result = from_clif_file(clif_path)
            egif_str = generate_egif(result.egi)
            dto = engine.generate_layout(result.egi, style)
            svg = renderer.render_to_svg(dto, "Animal Taxonomy (CLIF)", egif_str, egi=result.egi)
            out_path = OUTPUT_DIR / "domain_animal_taxonomy.svg"
            out_path.write_text(svg, encoding="utf-8")
            print(f"  ✅ domain_animal_taxonomy.svg")

        json_path = Path(__file__).parent.parent / "corpus" / "domain_models" / "peirce_categories" / "peirce_categories.json"
        if json_path.exists():
            result = from_type_lattice(json_path)
            egif_str = generate_egif(result.egi)
            dto = engine.generate_layout(result.egi, style)
            svg = renderer.render_to_svg(dto, "Peirce Categories (JSON Lattice)", egif_str, egi=result.egi)
            out_path = OUTPUT_DIR / "domain_peirce_categories.svg"
            out_path.write_text(svg, encoding="utf-8")
            print(f"  ✅ domain_peirce_categories.svg")
    except Exception as exc:
        print(f"  ❌ Domain models: {exc}")

    print(f"\nDone. Open {OUTPUT_DIR}/ to inspect.")


if __name__ == "__main__":
    main()
