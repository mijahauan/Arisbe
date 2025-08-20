#!/usr/bin/env python
"""
EGDF Structural Lock System

Stable protection system that validates structural integrity rather than exact hashes.
Focuses on logical consistency and API behavior rather than dynamic content.
"""

import json
import time
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class StructuralTestVector:
    """Test vector focusing on structural properties."""
    name: str
    egif_input: str
    expected_structure: Dict[str, int]
    critical_properties: Dict[str, Any]

class EGDFStructuralProtector:
    """
    Structural integrity protector for EGDF serialization.
    
    Validates that core functionality works correctly without
    being sensitive to timestamps, formatting, or other dynamic content.
    """
    
    def __init__(self):
        self.lock_file = Path(__file__).parent / "egdf_structural.lock"
        
    def create_structural_lock(self) -> bool:
        """Create structural protection lock."""
        
        print("🔒 Creating EGDF Structural Protection Lock")
        print("=" * 50)
        
        # Core test vectors that must always work
        test_vectors = [
            StructuralTestVector(
                name='simple_predicate',
                egif_input='*x (Human x)',
                expected_structure={'vertices': 1, 'edges': 1, 'cuts': 0},
                critical_properties={
                    'has_vertices': True,
                    'has_edges': True,
                    'has_cuts': False,
                    'vertex_count': 1,
                    'edge_count': 1
                }
            ),
            StructuralTestVector(
                name='nested_cut',
                egif_input='*x (Human x) ~[ (Mortal x) ]',
                expected_structure={'vertices': 1, 'edges': 2, 'cuts': 1},
                critical_properties={
                    'has_vertices': True,
                    'has_edges': True,
                    'has_cuts': True,
                    'vertex_count': 1,
                    'edge_count': 2,
                    'cut_count': 1
                }
            ),
            StructuralTestVector(
                name='isolated_vertices',
                egif_input='[*x] [*y] (Knows x y)',
                expected_structure={'vertices': 2, 'edges': 1, 'cuts': 0},
                critical_properties={
                    'has_vertices': True,
                    'has_edges': True,
                    'has_cuts': False,
                    'vertex_count': 2,
                    'edge_count': 1,
                    'supports_isolated_vertices': True
                }
            )
        ]
        
        # Validate each test vector
        validation_results = {}
        
        for vector in test_vectors:
            print(f"Testing {vector.name}...")
            
            try:
                # Test DAU YAML system
                yaml_result = self._test_dau_yaml_system_simple(vector)
                
                # Test EGDF parser system
                egdf_result = self._test_egdf_parser_system(vector)
                
                validation_results[vector.name] = {
                    'dau_yaml': yaml_result,
                    'egdf_parser': egdf_result,
                    'overall_success': yaml_result['success'] and egdf_result['success']
                }
                
                if validation_results[vector.name]['overall_success']:
                    print(f"  ✓ {vector.name} - All systems working")
                else:
                    print(f"  ✗ {vector.name} - Issues detected")
                    
            except Exception as e:
                print(f"  ✗ {vector.name} - Exception: {e}")
                validation_results[vector.name] = {
                    'dau_yaml': {'success': False, 'error': str(e)},
                    'egdf_parser': {'success': False, 'error': str(e)},
                    'overall_success': False
                }
        
        # Create lock data
        lock_data = {
            'version': '1.0.0',
            'created_at': time.time(),
            'test_vectors': [
                {
                    'name': v.name,
                    'egif_input': v.egif_input,
                    'expected_structure': v.expected_structure,
                    'critical_properties': v.critical_properties
                }
                for v in test_vectors
            ],
            'validation_results': validation_results,
            'success_count': sum(1 for r in validation_results.values() if r['overall_success']),
            'total_count': len(test_vectors)
        }
        
        # Save lock
        with open(self.lock_file, 'w') as f:
            json.dump(lock_data, f, indent=2)
        
        success_rate = lock_data['success_count'] / lock_data['total_count'] * 100
        print(f"✓ Structural lock created: {lock_data['success_count']}/{lock_data['total_count']} tests passed ({success_rate:.1f}%)")
        
        return lock_data['success_count'] == lock_data['total_count']
    
    def _test_dau_yaml_system_simple(self, vector: StructuralTestVector) -> Dict[str, Any]:
        """Test DAU YAML system with structural validation."""
        
        try:
            from dau_yaml_serializer import DAUYAMLConversionSystem
            
            yaml_system = DAUYAMLConversionSystem()
            result = yaml_system.test_round_trip(vector.egif_input)
            
            # Simple success check - just verify round-trip works
            return {
                'success': result.success,
                'round_trip_success': result.success,
                'conversion_time': result.metadata.get('conversion_time', 0) if hasattr(result, 'metadata') and result.metadata else 0
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_egdf_parser_system(self, vector: StructuralTestVector) -> Dict[str, Any]:
        """Test EGDF parser system with structural validation."""
        
        try:
            from egdf_parser import EGDFParser
            from egif_parser_dau import EGIFParser
            
            # Parse EGI
            parser = EGIFParser(vector.egif_input)
            egi = parser.parse()
            
            # Validate structure matches expected
            actual_structure = {
                'vertices': len(egi.V),
                'edges': len(egi.E),
                'cuts': len(egi.Cut)
            }
            
            structure_match = actual_structure == vector.expected_structure
            
            if not structure_match:
                return {
                    'success': False,
                    'error': f"Structure mismatch: expected {vector.expected_structure}, got {actual_structure}"
                }
            
            # Test EGDF creation and serialization
            egdf_parser = EGDFParser()
            
            # Create minimal spatial primitives
            spatial_primitives = []
            for i, vertex in enumerate(egi.V):
                spatial_primitives.append({
                    'element_id': vertex.id,
                    'element_type': 'vertex',
                    'position': (100 + i * 50, 100),
                    'bounds': (90 + i * 50, 90, 110 + i * 50, 110)
                })
            
            for i, edge in enumerate(egi.E):
                spatial_primitives.append({
                    'element_id': edge.id,
                    'element_type': 'predicate',
                    'position': (200 + i * 50, 150),
                    'bounds': (180 + i * 50, 140, 220 + i * 50, 160)
                })
            
            for i, cut in enumerate(egi.Cut):
                spatial_primitives.append({
                    'element_id': cut.id,
                    'element_type': 'cut',
                    'position': (150 + i * 100, 200),
                    'bounds': (100 + i * 100, 150, 200 + i * 100, 250)
                })
            
            # Create EGDF document
            egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
            
            # Test serialization
            json_output = egdf_parser.egdf_to_json(egdf_doc)
            yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
            
            # Test round-trip
            parsed_json = egdf_parser.parse_egdf(json_output, "json")
            extracted_egi = egdf_parser.extract_egi_from_egdf(parsed_json)
            
            # Validate round-trip structure
            roundtrip_structure = {
                'vertices': len(extracted_egi.V),
                'edges': len(extracted_egi.E),
                'cuts': len(extracted_egi.Cut)
            }
            
            roundtrip_match = roundtrip_structure == vector.expected_structure
            
            return {
                'success': roundtrip_match,
                'original_structure': actual_structure,
                'roundtrip_structure': roundtrip_structure,
                'json_size': len(json_output),
                'yaml_size': len(yaml_output),
                'spatial_primitives': len(spatial_primitives)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_structural_integrity(self) -> Tuple[bool, List[str]]:
        """Validate structural integrity against lock."""
        
        if not self.lock_file.exists():
            return False, ["No structural lock found"]
        
        try:
            with open(self.lock_file, 'r') as f:
                lock_data = json.load(f)
            
            errors = []
            
            # Re-run all test vectors
            for vector_data in lock_data['test_vectors']:
                vector = StructuralTestVector(
                    name=vector_data['name'],
                    egif_input=vector_data['egif_input'],
                    expected_structure=vector_data['expected_structure'],
                    critical_properties=vector_data['critical_properties']
                )
                
                try:
                    # Test DAU YAML system
                    yaml_result = self._test_dau_yaml_system_simple(vector)
                    if not yaml_result['success']:
                        errors.append(f"DAU YAML system failed for {vector.name}: {yaml_result.get('error', 'Unknown error')}")
                    
                    # Test EGDF parser system
                    egdf_result = self._test_egdf_parser_system(vector)
                    if not egdf_result['success']:
                        errors.append(f"EGDF parser system failed for {vector.name}: {egdf_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    errors.append(f"Test {vector.name} failed with exception: {e}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Lock validation failed: {e}"]
    
    def status_report(self) -> Dict[str, Any]:
        """Generate structural integrity status report."""
        
        if not self.lock_file.exists():
            return {
                'protected': False,
                'message': 'No structural protection lock found'
            }
        
        try:
            with open(self.lock_file, 'r') as f:
                lock_data = json.load(f)
            
            is_valid, errors = self.validate_structural_integrity()
            
            return {
                'protected': True,
                'valid': is_valid,
                'errors': errors,
                'lock_created': time.ctime(lock_data['created_at']),
                'test_vectors': len(lock_data['test_vectors']),
                'baseline_success_rate': f"{lock_data['success_count']}/{lock_data['total_count']}",
                'version': lock_data['version']
            }
            
        except Exception as e:
            return {
                'protected': True,
                'valid': False,
                'errors': [f"Status check failed: {e}"]
            }

def main():
    """Main function for structural protection."""
    
    protector = EGDFStructuralProtector()
    
    print("EGDF Structural Protection System")
    print("=" * 40)
    
    if protector.lock_file.exists():
        print("🔍 Validating structural integrity...")
        is_valid, errors = protector.validate_structural_integrity()
        
        if is_valid:
            print("✅ Structural integrity VALIDATED")
            status = protector.status_report()
            print(f"   Lock created: {status['lock_created']}")
            print(f"   Test vectors: {status['test_vectors']}")
            print(f"   Baseline success: {status['baseline_success_rate']}")
        else:
            print("❌ Structural integrity COMPROMISED")
            for error in errors:
                print(f"   • {error}")
    else:
        print("🔒 Creating structural protection lock...")
        success = protector.create_structural_lock()
        
        if success:
            print("✅ Structural protection lock created successfully")
            print("🛡️  EGDF serialization system is now structurally protected")
        else:
            print("⚠️  Structural lock created with some test failures")

if __name__ == "__main__":
    main()
