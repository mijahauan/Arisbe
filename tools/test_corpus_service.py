"""
Test Suite for CorpusService

Validates the unified corpus management API:
1. Creating and managing corpus
2. Saving and loading UoDs
3. Searching and filtering
4. Import/export operations
5. Index management
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime
from corpus_service import CorpusService, CorpusVersion
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDMetadata,
    UoDType,
    UoDCategory,
)
from egi_core_dau import create_empty_graph, create_vertex
import tempfile
import shutil


def test_corpus_initialization():
    """Test CorpusService initialization."""
    print("=" * 70)
    print("TEST 1: CorpusService Initialization")
    print("=" * 70)
    
    # Create temporary corpus
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_root = Path(tmpdir) / "test_corpus"
        
        # Initialize service
        corpus = CorpusService(corpus_root)
        
        # Verify directories created
        assert corpus.corpus_root.exists(), "Corpus root should exist"
        assert corpus.universes_dir.exists(), "Universes dir should exist"
        assert corpus.literature_dir.exists(), "Literature dir should exist"
        assert corpus.index_path.exists(), "Index file should exist"
        
        # Verify index
        assert corpus._index is not None, "Index should be loaded"
        assert corpus._index.corpus_name == "Arisbe Corpus"
        assert corpus._index.version == CorpusVersion.V2
        assert len(corpus._index.universes) == 0, "Should start empty"
        
        print(f"✅ CorpusService initialized successfully")
        print(f"   - Root: {corpus.corpus_root}")
        print(f"   - Version: {corpus._index.version.value}")
        print(f"   - UoDs: {len(corpus._index.universes)}")
        print()


def test_save_and_load_static_uod():
    """Test saving and loading static UoD (literature)."""
    print("=" * 70)
    print("TEST 2: Save and Load Static UoD (Literature)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_root = Path(tmpdir) / "test_corpus"
        corpus = CorpusService(corpus_root)
        
        # Create static UoD
        egi = create_empty_graph()
        vertex = create_vertex(label="Human", is_generic=False)
        egi = egi.with_vertex(vertex)
        
        metadata = UoDMetadata(
            uod_id="peirce_001",
            uod_type=UoDType.STANDALONE,
            name="Peirce's Human Example",
            description="Simple example from Peirce",
            category=UoDCategory.LITERATURE_EXAMPLE,
            created=datetime.now(),
            last_modified=datetime.now(),
            source_citation="Peirce CP 4.394",
            authors=["Charles S. Peirce"],
            tags={"peirce", "simple"},
        )
        
        uod = UniverseOfDiscourse(
            metadata=metadata,
            current_egi=egi,
            history=None
        )
        
        # Save UoD
        corpus.save_uod(uod)
        
        print(f"✅ Saved static UoD: {uod.name}")
        print(f"   - ID: {uod.uod_id}")
        print(f"   - Category: {uod.category.value}")
        
        # Verify in index
        assert len(corpus._index.universes) == 1, "Should have 1 UoD in index"
        assert corpus.uod_exists("peirce_001"), "UoD should exist"
        
        # Load UoD
        loaded = corpus.load_uod("peirce_001", load_history=False)
        
        assert loaded is not None, "Should load successfully"
        assert loaded.uod_id == "peirce_001"
        assert loaded.name == "Peirce's Human Example"
        assert loaded.is_static, "Should be static"
        assert not loaded.is_dynamic, "Should not be dynamic"
        assert len(loaded.current_egi.V) == 1, "Should have 1 vertex"
        
        print(f"✅ Loaded static UoD: {loaded.name}")
        print(f"   - Vertices: {len(loaded.current_egi.V)}")
        print(f"   - is_static: {loaded.is_static}")
        print()


def test_save_and_load_dynamic_uod():
    """Test saving and loading dynamic UoD with history."""
    print("=" * 70)
    print("TEST 3: Save and Load Dynamic UoD (With History)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_root = Path(tmpdir) / "test_corpus"
        corpus = CorpusService(corpus_root)
        
        # Create dynamic UoD
        egi = create_empty_graph()
        vertex = create_vertex(label="Alice", is_generic=False)
        egi = egi.with_vertex(vertex)
        
        metadata = UoDMetadata(
            uod_id="inquiry_001",
            uod_type=UoDType.STANDALONE,
            name="Active Inquiry",
            description="User investigation",
            category=UoDCategory.ACTIVE_INQUIRY,
            created=datetime.now(),
            last_modified=datetime.now(),
            authors=["Current User"],
            tags={"inquiry", "active"},
        )
        
        uod = UniverseOfDiscourse(
            metadata=metadata,
            current_egi=egi,
            current_layout_deltas={"zoom": 1.5},
            history=None
        )
        
        # Promote to historical
        uod.promote_to_historical("Initial state")
        
        # Save UoD
        corpus.save_uod(uod)
        
        print(f"✅ Saved dynamic UoD: {uod.name}")
        print(f"   - ID: {uod.uod_id}")
        print(f"   - Category: {uod.category.value}")
        print(f"   - is_historical: {uod.is_historical}")
        
        # Load UoD
        loaded = corpus.load_uod("inquiry_001")
        
        assert loaded is not None, "Should load successfully"
        assert loaded.uod_id == "inquiry_001"
        assert loaded.is_dynamic, "Should be dynamic"
        assert not loaded.is_static, "Should not be static"
        assert loaded.current_layout_deltas is not None, "Should have layout deltas"
        assert loaded.current_layout_deltas["zoom"] == 1.5
        
        print(f"✅ Loaded dynamic UoD: {loaded.name}")
        print(f"   - is_dynamic: {loaded.is_dynamic}")
        print(f"   - Layout deltas: {bool(loaded.current_layout_deltas)}")
        print()


def test_list_and_filter():
    """Test listing and filtering UoDs."""
    print("=" * 70)
    print("TEST 4: List and Filter UoDs")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_root = Path(tmpdir) / "test_corpus"
        corpus = CorpusService(corpus_root)
        
        # Create multiple UoDs
        for i in range(5):
            egi = create_empty_graph()
            
            if i < 3:
                # Literature examples
                metadata = UoDMetadata(
                    uod_id=f"lit_{i:03d}",
                    uod_type=UoDType.STANDALONE,
                    name=f"Literature Example {i}",
                    description="Test",
                    category=UoDCategory.LITERATURE_EXAMPLE,
                    created=datetime.now(),
                    last_modified=datetime.now(),
                )
            else:
                # Active inquiries
                metadata = UoDMetadata(
                    uod_id=f"inq_{i:03d}",
                    uod_type=UoDType.STANDALONE,
                    name=f"Active Inquiry {i}",
                    description="Test",
                    category=UoDCategory.ACTIVE_INQUIRY,
                    created=datetime.now(),
                    last_modified=datetime.now(),
                )
            
            uod = UniverseOfDiscourse(
                metadata=metadata,
                current_egi=egi,
                history=None
            )
            
            corpus.save_uod(uod)
        
        # List all
        all_uods = corpus.list_uods()
        assert len(all_uods) == 5, "Should have 5 UoDs"
        print(f"✅ Total UoDs: {len(all_uods)}")
        
        # Filter by category
        lit_uods = corpus.list_uods(category=UoDCategory.LITERATURE_EXAMPLE)
        assert len(lit_uods) == 3, "Should have 3 literature UoDs"
        print(f"✅ Literature UoDs: {len(lit_uods)}")
        
        inq_uods = corpus.list_uods(category=UoDCategory.ACTIVE_INQUIRY)
        assert len(inq_uods) == 2, "Should have 2 inquiry UoDs"
        print(f"✅ Inquiry UoDs: {len(inq_uods)}")
        
        # Filter by static/dynamic
        static_uods = corpus.list_uods(is_static=True)
        assert len(static_uods) == 3, "Should have 3 static UoDs"
        print(f"✅ Static UoDs: {len(static_uods)}")
        
        dynamic_uods = corpus.list_uods(is_dynamic=True)
        assert len(dynamic_uods) == 2, "Should have 2 dynamic UoDs"
        print(f"✅ Dynamic UoDs: {len(dynamic_uods)}")
        print()


def test_search():
    """Test searching UoDs."""
    print("=" * 70)
    print("TEST 5: Search UoDs")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_root = Path(tmpdir) / "test_corpus"
        corpus = CorpusService(corpus_root)
        
        # Create test UoDs
        test_data = [
            ("peirce_001", "Modus Ponens", UoDCategory.LITERATURE_EXAMPLE, {"peirce", "logic"}),
            ("peirce_002", "Modus Tollens", UoDCategory.LITERATURE_EXAMPLE, {"peirce", "logic"}),
            ("inquiry_001", "My Investigation", UoDCategory.ACTIVE_INQUIRY, {"custom"}),
        ]
        
        for uod_id, name, category, tags in test_data:
            egi = create_empty_graph()
            metadata = UoDMetadata(
                uod_id=uod_id,
                uod_type=UoDType.STANDALONE,
                name=name,
                description="Test",
                category=category,
                created=datetime.now(),
                last_modified=datetime.now(),
                tags=tags,
            )
            uod = UniverseOfDiscourse(
                metadata=metadata,
                current_egi=egi,
                history=None
            )
            corpus.save_uod(uod)
        
        # Search by query
        results = corpus.search(query="modus")
        assert len(results) == 2, "Should find 2 'modus' UoDs"
        print(f"✅ Search 'modus': {len(results)} results")
        
        # Search by category
        results = corpus.search(category=UoDCategory.LITERATURE_EXAMPLE)
        assert len(results) == 2, "Should find 2 literature UoDs"
        print(f"✅ Search category=LITERATURE: {len(results)} results")
        
        # Search by tags
        results = corpus.search(tags={"peirce"})
        assert len(results) == 2, "Should find 2 UoDs with 'peirce' tag"
        print(f"✅ Search tags={'peirce'}: {len(results)} results")
        
        # Combined search
        results = corpus.search(
            query="ponens",
            category=UoDCategory.LITERATURE_EXAMPLE,
            tags={"logic"}
        )
        assert len(results) == 1, "Should find 1 matching UoD"
        print(f"✅ Combined search: {len(results)} result")
        print()


def test_import_literature():
    """Test importing literature example."""
    print("=" * 70)
    print("TEST 6: Import Literature Example")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_root = Path(tmpdir) / "test_corpus"
        corpus = CorpusService(corpus_root)
        
        # Create EGI to import
        egi = create_empty_graph()
        vertex = create_vertex(label="Socrates", is_generic=False)
        egi = egi.with_vertex(vertex)
        
        # Import
        uod = corpus.import_literature(
            egi=egi,
            name="Socrates is Mortal",
            source_citation="Aristotle, Prior Analytics",
            authors=["Aristotle"],
            tags={"aristotle", "syllogism"}
        )
        
        assert uod is not None, "Should create UoD"
        assert uod.is_static, "Should be static"
        assert uod.category == UoDCategory.LITERATURE_EXAMPLE
        assert uod.metadata.source_citation == "Aristotle, Prior Analytics"
        
        print(f"✅ Imported literature: {uod.name}")
        print(f"   - ID: {uod.uod_id}")
        print(f"   - Citation: {uod.metadata.source_citation}")
        print(f"   - Tags: {uod.metadata.tags}")
        
        # Verify it's in corpus
        assert corpus.uod_exists(uod.uod_id), "Should exist in corpus"
        
        # Verify can be loaded
        loaded = corpus.load_uod(uod.uod_id)
        assert loaded is not None
        assert loaded.name == "Socrates is Mortal"
        print(f"✅ Literature can be loaded from corpus")
        print()


def test_delete_uod():
    """Test deleting UoD."""
    print("=" * 70)
    print("TEST 7: Delete UoD")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_root = Path(tmpdir) / "test_corpus"
        corpus = CorpusService(corpus_root)
        
        # Create UoD
        egi = create_empty_graph()
        metadata = UoDMetadata(
            uod_id="temp_001",
            uod_type=UoDType.STANDALONE,
            name="Temporary UoD",
            description="To be deleted",
            category=UoDCategory.PRACTICE_SESSION,
            created=datetime.now(),
            last_modified=datetime.now(),
        )
        uod = UniverseOfDiscourse(
            metadata=metadata,
            current_egi=egi,
            history=None
        )
        corpus.save_uod(uod)
        
        assert corpus.uod_exists("temp_001"), "Should exist before deletion"
        assert len(corpus.list_uods()) == 1
        
        # Delete
        success = corpus.delete_uod("temp_001")
        assert success, "Deletion should succeed"
        
        assert not corpus.uod_exists("temp_001"), "Should not exist after deletion"
        assert len(corpus.list_uods()) == 0, "Should be empty"
        
        print(f"✅ UoD deleted successfully")
        print(f"   - Remaining UoDs: {len(corpus.list_uods())}")
        print()


def test_statistics():
    """Test corpus statistics."""
    print("=" * 70)
    print("TEST 8: Corpus Statistics")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_root = Path(tmpdir) / "test_corpus"
        corpus = CorpusService(corpus_root)
        
        # Create diverse UoDs
        categories = [
            UoDCategory.LITERATURE_EXAMPLE,
            UoDCategory.LITERATURE_EXAMPLE,
            UoDCategory.ACTIVE_INQUIRY,
            UoDCategory.THEOREM_PROOF,
        ]
        
        for i, category in enumerate(categories):
            egi = create_empty_graph()
            metadata = UoDMetadata(
                uod_id=f"test_{i:03d}",
                uod_type=UoDType.STANDALONE,
                name=f"Test {i}",
                description="Test",
                category=category,
                created=datetime.now(),
                last_modified=datetime.now(),
            )
            uod = UniverseOfDiscourse(
                metadata=metadata,
                current_egi=egi,
                history=None
            )
            corpus.save_uod(uod)
        
        # Get statistics
        stats = corpus.get_statistics()
        
        assert stats["total_uods"] == 4, "Should have 4 UoDs"
        assert stats["static_uods"] == 2, "Should have 2 static"
        assert stats["dynamic_uods"] == 2, "Should have 2 dynamic"
        assert stats["corpus_version"] == "v2"
        
        print(f"✅ Corpus statistics:")
        print(f"   - Total UoDs: {stats['total_uods']}")
        print(f"   - Static: {stats['static_uods']}")
        print(f"   - Dynamic: {stats['dynamic_uods']}")
        print(f"   - By category: {stats['by_category']}")
        print(f"   - Version: {stats['corpus_version']}")
        print()


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("CORPUS SERVICE TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        test_corpus_initialization()
        test_save_and_load_static_uod()
        test_save_and_load_dynamic_uod()
        test_list_and_filter()
        test_search()
        test_import_literature()
        test_delete_uod()
        test_statistics()
        
        # Summary
        print("=" * 70)
        print("ALL TESTS PASSED! ✅")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"   ✅ CorpusService initialization")
        print(f"   ✅ Save and load static UoDs (literature)")
        print(f"   ✅ Save and load dynamic UoDs (with history)")
        print(f"   ✅ List and filter UoDs")
        print(f"   ✅ Search UoDs (query, category, tags)")
        print(f"   ✅ Import literature examples")
        print(f"   ✅ Delete UoDs")
        print(f"   ✅ Corpus statistics")
        print()
        print("CorpusService is working correctly!")
        print("Ready to integrate with Organon/Ergasterion/Agon")
        print()
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
