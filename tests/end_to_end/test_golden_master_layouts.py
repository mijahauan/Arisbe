"""
Golden Master Testing for Layout Engine.

Tests that layout output remains stable and deterministic across code changes.
Any differences from the golden master indicate potential regressions.
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import asdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'fixtures'))

from diagram_controller import DiagramController
from egi_io import load_egi_json
from egif_parser_dau import parse_egif
from test_egis import TEST_EGIS, get_test_egi


# Golden master directory
GOLDEN_DIR = Path(__file__).parent.parent / "golden_masters"
GOLDEN_DIR.mkdir(exist_ok=True)


def serialize_dto_for_comparison(dto) -> Dict[str, Any]:
    """
    Serialize a LayoutDTO to a comparable JSON format.
    
    Extracts key structural and positional information while
    maintaining deterministic ordering for comparison.
    IDs are normalized to be order-based since they're randomly generated.
    
    Args:
        dto: LayoutDTO from controller
        
    Returns:
        Dictionary suitable for JSON comparison
    """
    # Sort vertices by position for deterministic ordering
    sorted_vertices = sorted(dto.vertices, key=lambda x: (x.pos[0], x.pos[1], x.parent_area_id))
    
    # Sort edges by position
    sorted_edges = sorted(dto.edge_labels, key=lambda x: (x.rect.x, x.rect.y, x.label))
    
    # Sort areas by whether it's sheet, then by rect
    sorted_areas = sorted(dto.areas, key=lambda x: (not x.is_sheet, x.rect.x, x.rect.y))
    
    return {
        'vertices': [
            {
                'index': i,  # Order-based identifier
                'pos': [round(v.pos[0], 2), round(v.pos[1], 2)]  # Round to avoid floating point issues
            }
            for i, v in enumerate(sorted_vertices)
        ],
        'edge_labels': [
            {
                'index': i,
                'label': e.label,
                'rect': {
                    'x': round(e.rect.x, 2),
                    'y': round(e.rect.y, 2),
                    'width': round(e.rect.width, 2),
                    'height': round(e.rect.height, 2)
                }
            }
            for i, e in enumerate(sorted_edges)
        ],
        'areas': [
            {
                'index': i,
                'is_sheet': a.is_sheet,
                'rect': {
                    'x': round(a.rect.x, 2),
                    'y': round(a.rect.y, 2),
                    'width': round(a.rect.width, 2),
                    'height': round(a.rect.height, 2)
                }
            }
            for i, a in enumerate(sorted_areas)
        ],
        'ligatures': [
            {
                'index': i,
                'end_hook_index': lig.end_hook_index,
                'path_points': [[round(pt[0], 2), round(pt[1], 2)] for pt in lig.path_points]
            }
            for i, lig in enumerate(sorted(dto.ligatures, key=lambda x: (x.start_vertex_id, x.end_edge_id)))
        ],
        'counts': {
            'vertices': len(dto.vertices),
            'edges': len(dto.edge_labels),
            'areas': len(dto.areas),
            'ligatures': len(dto.ligatures)
        }
    }


def compute_dto_hash(dto_dict: Dict[str, Any]) -> str:
    """
    Compute a hash of the DTO for quick comparison.
    
    Args:
        dto_dict: Serialized DTO dictionary
        
    Returns:
        SHA256 hash string
    """
    json_str = json.dumps(dto_dict, sort_keys=True, indent=None)
    return hashlib.sha256(json_str.encode()).hexdigest()


def load_golden_master(test_name: str) -> Dict[str, Any]:
    """Load golden master for a test."""
    golden_file = GOLDEN_DIR / f"{test_name}_golden.json"
    if not golden_file.exists():
        return None
    with open(golden_file, 'r') as f:
        return json.load(f)


def save_golden_master(test_name: str, dto_dict: Dict[str, Any]):
    """Save a new golden master."""
    golden_file = GOLDEN_DIR / f"{test_name}_golden.json"
    with open(golden_file, 'w') as f:
        json.dump(dto_dict, f, indent=2, sort_keys=True)


def compare_dtos(actual: Dict[str, Any], expected: Dict[str, Any]) -> tuple:
    """
    Compare two DTO dictionaries and return differences.
    
    Returns:
        (is_identical, list_of_differences)
    """
    differences = []
    
    # Compare counts first
    if actual['counts'] != expected['counts']:
        differences.append(f"Element counts changed: {actual['counts']} vs {expected['counts']}")
    
    # Compare vertices
    if len(actual['vertices']) == len(expected['vertices']):
        for actual_v, expected_v in zip(actual['vertices'], expected['vertices']):
            if actual_v['pos'] != expected_v['pos']:
                differences.append(
                    f"Vertex #{actual_v['index']} position changed: "
                    f"{actual_v['pos']} vs {expected_v['pos']}"
                )
    
    # Compare edges
    if len(actual['edge_labels']) == len(expected['edge_labels']):
        for actual_e, expected_e in zip(actual['edge_labels'], expected['edge_labels']):
            if actual_e['label'] != expected_e['label']:
                differences.append(
                    f"Edge #{actual_e['index']} label changed: "
                    f"{actual_e['label']} vs {expected_e['label']}"
                )
            if actual_e['rect'] != expected_e['rect']:
                differences.append(
                    f"Edge #{actual_e['index']} ({actual_e['label']}) rect changed: "
                    f"{actual_e['rect']} vs {expected_e['rect']}"
                )
    
    # Compare areas
    if len(actual['areas']) == len(expected['areas']):
        for actual_a, expected_a in zip(actual['areas'], expected['areas']):
            if actual_a['is_sheet'] != expected_a['is_sheet']:
                differences.append(
                    f"Area #{actual_a['index']} is_sheet changed: "
                    f"{actual_a['is_sheet']} vs {expected_a['is_sheet']}"
                )
            if actual_a['rect'] != expected_a['rect']:
                differences.append(
                    f"Area #{actual_a['index']} rect changed: "
                    f"{actual_a['rect']} vs {expected_a['rect']}"
                )
    
    # Compare ligatures
    if len(actual['ligatures']) == len(expected['ligatures']):
        for actual_l, expected_l in zip(actual['ligatures'], expected['ligatures']):
            if actual_l['path_points'] != expected_l['path_points']:
                differences.append(
                    f"Ligature #{actual_l['index']} path changed"
                )
    
    return (len(differences) == 0, differences)


class GoldenMasterTests:
    """Golden Master test suite for layout stability."""
    
    def __init__(self, update_masters: bool = False):
        """
        Initialize golden master tests.
        
        Args:
            update_masters: If True, update golden masters instead of comparing
        """
        self.update_masters = update_masters
        self.controller = DiagramController()
    
    def test_simple_vertex(self):
        """Test golden master for simple vertex graph."""
        test_name = "simple_vertex"
        egi = get_test_egi('simple_vertex')
        
        # Generate layout
        self.controller.load_egi(egi)
        dto = self.controller.current_dto
        serialized = serialize_dto_for_comparison(dto)
        
        if self.update_masters:
            save_golden_master(test_name, serialized)
            return True, "Golden master updated"
        
        # Load and compare with golden master
        golden = load_golden_master(test_name)
        if golden is None:
            save_golden_master(test_name, serialized)
            return True, "Golden master created (first run)"
        
        is_identical, differences = compare_dtos(serialized, golden)
        return is_identical, differences
    
    def test_two_vertices(self):
        """Test golden master for two-vertex graph."""
        test_name = "two_vertices"
        egi = get_test_egi('two_vertices')
        
        self.controller.load_egi(egi)
        dto = self.controller.current_dto
        serialized = serialize_dto_for_comparison(dto)
        
        if self.update_masters:
            save_golden_master(test_name, serialized)
            return True, "Golden master updated"
        
        golden = load_golden_master(test_name)
        if golden is None:
            save_golden_master(test_name, serialized)
            return True, "Golden master created (first run)"
        
        is_identical, differences = compare_dtos(serialized, golden)
        return is_identical, differences
    
    def test_nested_cuts(self):
        """Test golden master for nested cuts graph."""
        test_name = "nested_cuts"
        egi = get_test_egi('nested_cuts')
        
        self.controller.load_egi(egi)
        dto = self.controller.current_dto
        serialized = serialize_dto_for_comparison(dto)
        
        if self.update_masters:
            save_golden_master(test_name, serialized)
            return True, "Golden master updated"
        
        golden = load_golden_master(test_name)
        if golden is None:
            save_golden_master(test_name, serialized)
            return True, "Golden master created (first run)"
        
        is_identical, differences = compare_dtos(serialized, golden)
        return is_identical, differences
    
    def test_complex_nested(self):
        """Test golden master for complex nested graph."""
        test_name = "complex_nested"
        egi = get_test_egi('complex_nested')
        
        self.controller.load_egi(egi)
        dto = self.controller.current_dto
        serialized = serialize_dto_for_comparison(dto)
        
        if self.update_masters:
            save_golden_master(test_name, serialized)
            return True, "Golden master updated"
        
        golden = load_golden_master(test_name)
        if golden is None:
            save_golden_master(test_name, serialized)
            return True, "Golden master created (first run)"
        
        is_identical, differences = compare_dtos(serialized, golden)
        return is_identical, differences
    
    def test_multiple_predicates(self):
        """Test golden master for multiple predicates on same vertex."""
        test_name = "multiple_predicates"
        egi = get_test_egi('multiple_predicates')
        
        self.controller.load_egi(egi)
        dto = self.controller.current_dto
        serialized = serialize_dto_for_comparison(dto)
        
        if self.update_masters:
            save_golden_master(test_name, serialized)
            return True, "Golden master updated"
        
        golden = load_golden_master(test_name)
        if golden is None:
            save_golden_master(test_name, serialized)
            return True, "Golden master created (first run)"
        
        is_identical, differences = compare_dtos(serialized, golden)
        return is_identical, differences
    
    def test_single_cut(self):
        """Test golden master for single cut containing vertex."""
        test_name = "single_cut"
        egi = get_test_egi('single_cut')
        
        self.controller.load_egi(egi)
        dto = self.controller.current_dto
        serialized = serialize_dto_for_comparison(dto)
        
        if self.update_masters:
            save_golden_master(test_name, serialized)
            return True, "Golden master updated"
        
        golden = load_golden_master(test_name)
        if golden is None:
            save_golden_master(test_name, serialized)
            return True, "Golden master created (first run)"
        
        is_identical, differences = compare_dtos(serialized, golden)
        return is_identical, differences


def test_corpus_graphs():
    """Test all graphs in the corpus directory against golden masters."""
    corpus_dir = Path(__file__).parent.parent.parent / "corpus" / "graphs"
    if not corpus_dir.exists():
        return []
    
    results = []
    controller = DiagramController()
    
    for corpus_file in sorted(corpus_dir.glob("*.json")):
        test_name = f"corpus_{corpus_file.stem}"
        
        try:
            # Load corpus EGI
            egi = load_egi_json(str(corpus_file))
            controller.load_egi(egi)
            dto = controller.current_dto
            serialized = serialize_dto_for_comparison(dto)
            
            # Load or create golden master
            golden = load_golden_master(test_name)
            if golden is None:
                save_golden_master(test_name, serialized)
                results.append((test_name, True, "Golden master created"))
                continue
            
            # Compare
            is_identical, differences = compare_dtos(serialized, golden)
            results.append((test_name, is_identical, differences if not is_identical else "OK"))
            
        except Exception as e:
            results.append((test_name, False, f"Error: {e}"))
    
    return results


def run_all_golden_master_tests(update_masters: bool = False):
    """Run all golden master tests."""
    print("🎯 RUNNING GOLDEN MASTER TESTS")
    print("=" * 70)
    
    if update_masters:
        print("⚠️  UPDATE MODE: Golden masters will be updated, not compared")
        print("=" * 70)
    
    tests = GoldenMasterTests(update_masters=update_masters)
    test_methods = [m for m in dir(tests) if m.startswith('test_')]
    
    total_tests = 0
    passed_tests = 0
    
    for method_name in test_methods:
        total_tests += 1
        try:
            method = getattr(tests, method_name)
            is_ok, result = method()
            
            if is_ok:
                print(f"   ✅ {method_name}: {result if isinstance(result, str) else 'PASS'}")
                passed_tests += 1
            else:
                print(f"   ❌ {method_name}:")
                if isinstance(result, list):
                    for diff in result[:5]:  # Show first 5 differences
                        print(f"      - {diff}")
                    if len(result) > 5:
                        print(f"      ... and {len(result) - 5} more differences")
                else:
                    print(f"      {result}")
        except Exception as e:
            print(f"   💥 {method_name}: {e}")
    
    # Test corpus graphs
    print(f"\n📚 Testing corpus graphs...")
    corpus_results = test_corpus_graphs()
    for test_name, passed, result in corpus_results:
        total_tests += 1
        if passed:
            print(f"   ✅ {test_name}: {result if isinstance(result, str) else 'PASS'}")
            passed_tests += 1
        else:
            print(f"   ❌ {test_name}:")
            if isinstance(result, list):
                for diff in result[:3]:
                    print(f"      - {diff}")
            else:
                print(f"      {result}")
    
    print(f"\n{'=' * 70}")
    print(f"📊 RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests < total_tests:
        print(f"\n⚠️  REGRESSION DETECTED!")
        print(f"   Layout output has changed from golden masters.")
        print(f"   If changes are intentional, run with --update flag:")
        print(f"   python {Path(__file__).name} --update")
    
    print(f"{'=' * 70}")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    import sys
    update = "--update" in sys.argv or "-u" in sys.argv
    success = run_all_golden_master_tests(update_masters=update)
    sys.exit(0 if success else 1)
