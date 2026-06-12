"""
Tests for the domain model importer.

Validates both import pathways (CLIF files and JSON type lattices),
composition of multiple models, UoD wrapping, and integration with
the game engine.
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from clif_parser_dau import parse_clif
from domain_model_importer import (
    DomainModelImporter,
    ImportResult,
    as_uod,
    compose_models,
    from_clif_file,
    from_clif_text,
    from_type_lattice,
    from_type_lattice_dict,
)
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif


CORPUS_ROOT = Path(__file__).resolve().parent.parent / "corpus" / "domain_models"


# ---------------------------------------------------------------------------
# CLIF parser enhancements (if / iff / cl-text / multi-sentence)
# ---------------------------------------------------------------------------

class TestCLIFParserEnhancements:
    """Test the new CLIF constructs needed for ontology import."""

    def test_material_conditional(self):
        egi = parse_clif("(forall (x) (if (Human x) (Animal x)))")
        egif = generate_egif(egi)
        assert "Human" in egif
        assert "Animal" in egif
        # Should produce ~[ ... ~[ ... ] ] structure
        assert egif.count("~[") >= 1

    def test_biconditional(self):
        egi = parse_clif("(iff (A x) (B x))")
        egif = generate_egif(egi)
        # iff produces two implications
        assert egif.count("~[") >= 2

    def test_multi_sentence(self):
        clif = "(forall (x) (if (Cat x) (Animal x)))\n(forall (x) (if (Dog x) (Animal x)))"
        egi = parse_clif(clif)
        egif = generate_egif(egi)
        assert "Cat" in egif
        assert "Dog" in egif
        assert "Animal" in egif

    def test_cl_text_wrapper(self):
        clif = "(cl-text test-ontology\n  (forall (x) (if (Cat x) (Animal x)))\n)"
        egi = parse_clif(clif)
        egif = generate_egif(egi)
        assert "Cat" in egif
        assert "Animal" in egif

    def test_comments_stripped(self):
        clif = ";; comment\n(Human Socrates)\n;; another\n(Mortal Socrates)"
        egi = parse_clif(clif)
        egif = generate_egif(egi)
        assert "Human" in egif
        assert "Mortal" in egif

    def test_nested_if_exists(self):
        clif = "(forall (x) (if (Cat x) (exists (y) (and (Owns y x) (Person y)))))"
        egi = parse_clif(clif)
        egif = generate_egif(egi)
        assert "Cat" in egif
        assert "Owns" in egif
        assert "Person" in egif


# ---------------------------------------------------------------------------
# CLIF file import
# ---------------------------------------------------------------------------

class TestCLIFImport:
    """Test importing domain models from CLIF files."""

    def test_from_clif_text(self):
        clif = "(forall (x) (if (Cat x) (Animal x)))\n(Cat Biscuit)"
        result = from_clif_text(clif)
        assert isinstance(result, ImportResult)
        assert result.source_format == "clif"
        assert len(result.egi.V) > 0
        assert len(result.egi.E) > 0

    def test_from_clif_file(self):
        clif_path = CORPUS_ROOT / "animal_taxonomy" / "animal_taxonomy.clif"
        if not clif_path.exists():
            pytest.skip("Corpus file not found")
        result = from_clif_file(clif_path)
        assert result.source_format == "clif"
        assert result.num_types > 0
        assert len(result.egi.V) > 0
        assert len(result.egi.E) > 0
        assert len(result.egi.Cut) > 0

    def test_from_clif_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two small CLIF files
            Path(tmpdir, "a.clif").write_text(
                "(forall (x) (if (Cat x) (Animal x)))"
            )
            Path(tmpdir, "b.clif").write_text(
                "(forall (x) (if (Dog x) (Animal x)))"
            )
            importer = DomainModelImporter()
            result = importer.from_clif_directory(tmpdir)
            egif = generate_egif(result.egi)
            assert "Cat" in egif
            assert "Dog" in egif
            assert "Animal" in egif

    def test_cl_imports_extracted(self):
        clif = "(cl-imports http://example.org/base)\n(forall (x) (if (A x) (B x)))"
        result = from_clif_text(clif)
        assert "http://example.org/base" in result.cl_imports

    def test_colore_style_block_comment_header_is_stripped(self):
        # Every COLORE file carries a /* Copyright … */ header; words inside it
        # ("Toronto **and** others") would tokenise as keywords and break the parse
        # if the block comment were not stripped before parsing.
        clif = (
            "/*****\n * Copyright (c) University of Toronto and others.\n"
            " * if not for this, the parser would choke on 'and'/'if'/'not'.\n *****/\n"
            "(cl-text http://colore.oor.net/x/y.clif\n"
            "  (cl-imports http://colore.oor.net/x/base.clif)\n"
            "  (forall (a b) (if (and (rel a b) (not (= a b))) (other a b))))"
        )
        result = from_clif_text(clif)
        assert len(result.egi.E) > 0
        # the http:// in the cl-imports IRI must NOT be mistaken for a comment
        assert "http://colore.oor.net/x/base.clif" in result.cl_imports

    def test_reused_variable_names_do_not_collapse_independent_universals(self):
        # Two independent universals that both happen to use `x`.  Without
        # alpha-renaming, parse_clif unifies the two `x`s into one line of identity
        # — turning (∀x A→B) ∧ (∀x C→D) into the weaker ∃x (A→B)∧(C→D).  Each must
        # keep its own line.
        result = from_clif_text(
            "(forall (x) (if (A x) (B x))) (forall (x) (if (C x) (D x)))")
        # two distinct lines of identity, not one shared existential
        assert len(result.egi.V) == 2
        # neither universal binds an outer (sheet-level) vertex
        assert not [v for v in result.egi.V if v.id in result.egi.area[result.egi.sheet]]


# ---------------------------------------------------------------------------
# Function-term relationalization (COLORE function-bearing modules)
# ---------------------------------------------------------------------------

class TestFunctionRelationalization:
    """A nested function term ``(f t₁ … tₙ)`` in argument position is not
    accepted by the protected CLIF parser, but functions are EG-expressible by
    relationalization: ``(density (dmv v m))`` ↦ ``∃z (dmv(v,m,z) ∧ density(z))``.
    The importer does this meaning-preserving reduction so COLORE's
    function-bearing modules (the majority) import."""

    def _same(self, a, b):
        from eg_navigation import same_graph
        return same_graph(a, b)

    def test_function_term_imports_and_round_trips(self):
        # (density (dmv v m)) ⇒ ∃z (dmv v m z) ∧ (density z)
        result = from_clif_text(
            "(forall (v m) (if (something v m) (density (dmv v m))))")
        rels = set(result.egi.rel.values())
        assert {"something", "dmv", "density"} <= rels
        # dmv used 2-arily as a function ⇒ a 3-ary graph relation
        dmv_edges = [e for e in result.egi.E if result.egi.rel[e.id] == "dmv"]
        assert dmv_edges and len(result.egi.nu[dmv_edges[0].id]) == 3
        # structure survives an EGIF round-trip
        rt = parse_egif(generate_egif(result.egi))
        assert self._same(result.egi, rt)

    def test_relationalization_matches_hand_written_relational_form(self):
        # The lifted form must denote the same graph as the relational form a
        # human would write by hand.
        functional = from_clif_text(
            "(forall (v m) (if (something v m) (density (dmv v m))))").egi
        relational = from_clif_text(
            "(forall (v m) (if (something v m) "
            "(exists (z) (and (dmv v m z) (density z)))))").egi
        assert self._same(functional, relational)

    def test_nested_function_terms_lift_inside_out(self):
        # (P (f (g x))) ⇒ ∃z1 z2 (g x z2) ∧ (f z2 z1) ∧ (P z1).  Compared against
        # the hand-written relational form (an EGIF round-trip is unreliable here:
        # the generator mishandles a positive-body universal — a pre-existing,
        # function-independent limitation).
        functional = from_clif_text("(forall (x) (if (Q x) (P (f (g x)))))").egi
        relational = from_clif_text(
            "(forall (x) (if (Q x) (exists (z1 z2) "
            "(and (g x z2) (f z2 z1) (P z1)))))").egi
        assert {"P", "f", "g"} <= set(functional.rel.values())
        assert self._same(functional, relational)

    def test_equality_between_function_terms(self):
        # COLORE's value-as-equality case: (= (dmv x y) (dmv z y)) — both sides
        # relationalize, then (= z1 z2).
        result = from_clif_text(
            "(forall (x y z) (if (= (dmv x y) (dmv z y)) (= x z)))")
        assert "=" in result.egi.rel.values()
        assert "dmv" in result.egi.rel.values()
        # two dmv occurrences (one per side)
        assert sum(1 for r in result.egi.rel.values() if r == "dmv") == 2

    def test_function_in_negative_context(self):
        # The ∃-rewrite is sound in any polarity (the value exists everywhere).
        result = from_clif_text("(not (density (dmv v m)))")
        assert {"dmv", "density"} <= set(result.egi.rel.values())
        rt = parse_egif(generate_egif(result.egi))
        assert self._same(result.egi, rt)

    def test_relation_atom_untouched(self):
        # A plain relational atom (no nested term) is not rewritten.
        a = from_clif_text("(forall (x) (if (Cat x) (Animal x)))").egi
        b = parse_clif("(forall (x) (if (Cat x) (Animal x)))")
        assert self._same(a, b)

    def test_function_bearing_import_wraps_as_ontology_uod(self):
        # The /agon-selectable path: a function-bearing module imports to a
        # standard EGI that wraps as a DOMAIN_MODEL UoD like any other (the lifted
        # function relation is an ordinary relation downstream).  Mirrors COLORE's
        # density: (density (dmv v m)) with the value-as-equality axiom.
        result = from_clif_text(
            "(forall (v m) (if (and (amount m) (spatial_volume v)) "
            "(density (dmv v m))))\n"
            "(forall (x y z) (if (= (dmv x y) (dmv z y)) (= x z)))")
        uod = as_uod(result, name="Density (function-bearing)")
        assert uod.metadata.category.name == "DOMAIN_MODEL"
        assert "dmv" in uod.current_egi.rel.values()

    def test_functionality_axioms_optional(self):
        # By default no functionality axioms are added; opt-in emits totality +
        # uniqueness (which use equality, so they are non-Horn residue).
        from domain_model_importer import _relationalize_functions
        plain = _relationalize_functions("(forall (v m) (density (dmv v m)))")
        assert "_fa_z" not in plain
        withax = _relationalize_functions(
            "(forall (v m) (density (dmv v m)))", assert_functionality=True)
        assert "_fa_z" in withax
        # the uniqueness axiom is itself valid CLIF
        assert parse_clif(withax) is not None


# ---------------------------------------------------------------------------
# JSON type lattice import
# ---------------------------------------------------------------------------

class TestTypeLatticeImport:
    """Test importing domain models from JSON type lattice files."""

    def test_minimal_lattice(self):
        lattice = {
            "name": "Test",
            "types": [
                {"name": "Animal", "supertypes": []},
                {"name": "Cat", "supertypes": ["Animal"]},
            ],
            "relations": [],
            "individuals": [],
            "axioms": [],
            "disjoint": [],
        }
        result = from_type_lattice_dict(lattice)
        assert result.source_format == "type_lattice"
        assert result.num_types == 2
        egif = generate_egif(result.egi)
        assert "Cat" in egif
        assert "Animal" in egif

    def test_lattice_with_individuals(self):
        lattice = {
            "name": "Test",
            "types": [{"name": "Cat", "supertypes": []}],
            "relations": [],
            "individuals": [{"name": "Biscuit", "types": ["Cat"]}],
            "axioms": [],
            "disjoint": [],
        }
        result = from_type_lattice_dict(lattice)
        assert result.num_individuals == 1

    def test_lattice_with_disjointness(self):
        lattice = {
            "name": "Test",
            "types": [
                {"name": "Cat", "supertypes": []},
                {"name": "Dog", "supertypes": []},
            ],
            "relations": [],
            "individuals": [],
            "axioms": [],
            "disjoint": [["Cat", "Dog"]],
        }
        result = from_type_lattice_dict(lattice)
        # Disjointness produces a cut structure
        assert len(result.egi.Cut) > 0

    def test_lattice_with_verbatim_axioms(self):
        lattice = {
            "name": "Test",
            "types": [],
            "relations": [],
            "individuals": [],
            "axioms": ["(forall (x) (if (Person x) (exists (y) (Owns x y))))"],
            "disjoint": [],
        }
        result = from_type_lattice_dict(lattice)
        egif = generate_egif(result.egi)
        assert "Person" in egif
        assert "Owns" in egif

    def test_from_lattice_file(self):
        json_path = CORPUS_ROOT / "animal_taxonomy" / "animal_taxonomy.json"
        if not json_path.exists():
            pytest.skip("Corpus file not found")
        result = from_type_lattice(json_path)
        assert result.num_types == 9
        assert result.num_relations == 2
        assert result.num_individuals == 4

    def test_peirce_categories(self):
        json_path = CORPUS_ROOT / "peirce_categories" / "peirce_categories.json"
        if not json_path.exists():
            pytest.skip("Corpus file not found")
        result = from_type_lattice(json_path)
        assert result.num_types == 18
        assert result.num_relations == 6
        assert len(result.egi.V) > 0


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------

class TestComposition:
    """Test composing multiple domain models."""

    def test_compose_two_models(self):
        r1 = from_clif_text("(forall (x) (if (Cat x) (Animal x)))")
        r2 = from_clif_text("(forall (x) (if (Dog x) (Animal x)))")
        composed = compose_models(r1, r2)
        assert composed.source_format == "composed"
        # Composed should have elements from both
        assert len(composed.egi.E) >= len(r1.egi.E)
        assert len(composed.egi.E) >= len(r2.egi.E)

    def test_compose_empty(self):
        composed = compose_models()
        assert len(composed.egi.V) == 0

    def test_compose_corpus_models(self):
        clif_path = CORPUS_ROOT / "animal_taxonomy" / "animal_taxonomy.clif"
        peirce_path = CORPUS_ROOT / "peirce_categories" / "peirce_categories.json"
        if not clif_path.exists() or not peirce_path.exists():
            pytest.skip("Corpus files not found")
        r1 = from_clif_file(clif_path)
        r2 = from_type_lattice(peirce_path)
        composed = compose_models(r1, r2)
        # Should be larger than either alone
        assert len(composed.egi.V) >= max(len(r1.egi.V), len(r2.egi.V))
        assert len(composed.egi.E) >= max(len(r1.egi.E), len(r2.egi.E))


# ---------------------------------------------------------------------------
# UoD wrapping
# ---------------------------------------------------------------------------

class TestUoDWrapping:
    """Test wrapping import results as UoD."""

    def test_as_uod(self):
        result = from_clif_text("(Cat Biscuit)")
        uod = as_uod(result, name="Test Domain")
        assert uod.metadata.name == "Test Domain"
        assert len(uod.current_egi.E) > 0


# ---------------------------------------------------------------------------
# Integration: imported M used in game engine
# ---------------------------------------------------------------------------

class TestGameIntegration:
    """Test that imported domain models work as M in the EPG."""

    def test_imported_model_as_game_context(self):
        from endoporeutic_game import EndoporeuticGame

        # Import a simple domain model
        result = from_clif_text(
            "(forall (x) (if (Cat x) (Animal x)))\n(Cat Biscuit)"
        )
        # The M is ready
        assert len(result.egi.E) > 0

        # Create a game: "Is Biscuit an Animal?"
        game = EndoporeuticGame()
        state = game.new_game('~[ (Cat "Biscuit") ~[ (Animal "Biscuit") ] ]')
        assert state is not None
        assert len(state.current_egi.Cut) > 0
