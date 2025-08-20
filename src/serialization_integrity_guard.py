#!/usr/bin/env python
"""
Serialization Integrity Guard

Comprehensive protection system for EGDF YAML/JSON serialization to prevent
corruption and regression. Implements version locking, validation hooks,
and automated regression testing.
"""

import hashlib
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import os

# Import from current directory (we're already in src/)
from egif_parser_dau import EGIFParser
from layout_phase_implementations import DependencyOrderedPipeline
from egdf_parser import EGDFParser, EGDFMetadata
from dau_yaml_serializer import DAUYAMLConversionSystem

@dataclass
class SerializationSignature:
    """Cryptographic signature for serialization components."""
    component_name: str
    version: str
    api_hash: str
    test_vectors_hash: str
    timestamp: float
    
@dataclass
class RegressionTestVector:
    """Test vector for regression detection."""
    name: str
    egif_input: str
    expected_structure: Dict[str, int]
    json_hash: str
    yaml_hash: str
    pipeline_hash: str

class SerializationIntegrityGuard:
    """
    Guards against corruption and regression in EGDF serialization system.
    
    Features:
    - API signature validation
    - Regression test vectors
    - Automated corruption detection
    - Version locking
    """
    
    def __init__(self):
        self.signatures: Dict[str, SerializationSignature] = {}
        self.test_vectors: List[RegressionTestVector] = []
        self.egdf_parser = EGDFParser()
        self.yaml_system = DAUYAMLConversionSystem()
        
        # Initialize baseline signatures
        self._initialize_baseline_signatures()
        self._create_regression_test_vectors()
    
    def _initialize_baseline_signatures(self):
        """Create baseline signatures for critical components."""
        
        # EGDF Parser signature
        egdf_api_methods = [
            'parse_egdf', 'egdf_to_json', 'egdf_to_yaml', 'create_egdf_from_egi',
            'extract_egi_from_egdf', 'validate_round_trip'
        ]
        egdf_api_hash = self._hash_api_methods(self.egdf_parser, egdf_api_methods)
        
        self.signatures['egdf_parser'] = SerializationSignature(
            component_name='egdf_parser',
            version='1.0.0',
            api_hash=egdf_api_hash,
            test_vectors_hash='',  # Will be set after test vectors created
            timestamp=time.time()
        )
        
        # DAU YAML System signature
        yaml_api_methods = [
            'egif_to_yaml', 'yaml_to_graph', 'test_round_trip'
        ]
        yaml_api_hash = self._hash_api_methods(self.yaml_system, yaml_api_methods)
        
        self.signatures['dau_yaml_system'] = SerializationSignature(
            component_name='dau_yaml_system',
            version='1.0.0',
            api_hash=yaml_api_hash,
            test_vectors_hash='',  # Will be set after test vectors created
            timestamp=time.time()
        )
    
    def _hash_api_methods(self, obj: Any, method_names: List[str]) -> str:
        """Create hash of API method signatures."""
        signatures = []
        for method_name in method_names:
            if hasattr(obj, method_name):
                method = getattr(obj, method_name)
                # Get method signature info
                sig_info = f"{method_name}:{method.__doc__}"
                signatures.append(sig_info)
        
        combined = '|'.join(sorted(signatures))
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _create_regression_test_vectors(self):
        """Create comprehensive regression test vectors."""
        
        test_cases = [
            {
                'name': 'simple_predicate',
                'egif': '*x (Human x)',
                'description': 'Basic predicate serialization'
            },
            {
                'name': 'nested_cut',
                'egif': '*x (Human x) ~[ (Mortal x) ]',
                'description': 'Nested cut serialization'
            },
            {
                'name': 'isolated_vertices',
                'egif': '[*x] [*y] (Knows x y)',
                'description': 'Isolated vertex handling'
            },
            {
                'name': 'complex_structure',
                'egif': '*x *y (Human x) (Loves x y) ~[ (Mortal x) (Happy y) ]',
                'description': 'Complex multi-element structure'
            },
            {
                'name': 'double_negation',
                'egif': '~[~[(happy *x)]]',
                'description': 'Double negation structure'
            }
        ]
        
        for test_case in test_cases:
            try:
                # Generate test vector
                vector = self._generate_test_vector(test_case['name'], test_case['egif'])
                self.test_vectors.append(vector)
            except Exception as e:
                print(f"⚠️  Failed to create test vector for {test_case['name']}: {e}")
        
        # Update signatures with test vector hashes
        test_vectors_hash = self._hash_test_vectors()
        for signature in self.signatures.values():
            signature.test_vectors_hash = test_vectors_hash
    
    def _generate_test_vector(self, name: str, egif: str) -> RegressionTestVector:
        """Generate a complete test vector for the given EGIF."""
        
        # Parse and generate layout
        parser = EGIFParser(egif)
        egi = parser.parse()
        
        pipeline = DependencyOrderedPipeline()
        layout_result = pipeline.execute_pipeline(egi)
        
        # Create EGDF
        spatial_primitives = []
        for element_id, element in layout_result.elements.items():
            primitive_dict = {
                'element_id': element_id,
                'element_type': element.element_type,
                'position': element.position,
                'bounds': element.bounds
            }
            spatial_primitives.append(primitive_dict)
        
        metadata = EGDFMetadata(title=name, source=egif)
        egdf_doc = self.egdf_parser.create_egdf_from_egi(egi, spatial_primitives, metadata)
        
        # Generate serializations
        json_output = self.egdf_parser.egdf_to_json(egdf_doc)
        yaml_output = self.egdf_parser.egdf_to_yaml(egdf_doc)
        
        # Create hashes
        json_hash = hashlib.sha256(json_output.encode()).hexdigest()[:16]
        yaml_hash = hashlib.sha256(yaml_output.encode()).hexdigest()[:16]
        
        # Pipeline structure hash
        pipeline_structure = {
            'elements': len(layout_result.elements),
            'types': sorted(set(e.element_type for e in layout_result.elements.values()))
        }
        pipeline_hash = hashlib.sha256(str(pipeline_structure).encode()).hexdigest()[:16]
        
        expected_structure = {
            'vertices': len(egi.V),
            'edges': len(egi.E),
            'cuts': len(egi.Cut)
        }
        
        return RegressionTestVector(
            name=name,
            egif_input=egif,
            expected_structure=expected_structure,
            json_hash=json_hash,
            yaml_hash=yaml_hash,
            pipeline_hash=pipeline_hash
        )
    
    def _hash_test_vectors(self) -> str:
        """Create hash of all test vectors."""
        vector_data = []
        for vector in self.test_vectors:
            vector_dict = asdict(vector)
            vector_data.append(str(vector_dict))
        
        combined = '|'.join(sorted(vector_data))
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def validate_integrity(self) -> Tuple[bool, List[str]]:
        """Validate complete serialization system integrity."""
        
        errors = []
        
        # 1. API Signature Validation
        api_valid, api_errors = self._validate_api_signatures()
        if not api_valid:
            errors.extend(api_errors)
        
        # 2. Regression Test Validation
        regression_valid, regression_errors = self._validate_regression_tests()
        if not regression_valid:
            errors.extend(regression_errors)
        
        # 3. Cross-validation between systems
        cross_valid, cross_errors = self._validate_cross_system_consistency()
        if not cross_valid:
            errors.extend(cross_errors)
        
        return len(errors) == 0, errors
    
    def _validate_api_signatures(self) -> Tuple[bool, List[str]]:
        """Validate that API signatures haven't changed unexpectedly."""
        
        errors = []
        
        # Check EGDF Parser
        current_egdf_hash = self._hash_api_methods(
            self.egdf_parser, 
            ['parse_egdf', 'egdf_to_json', 'egdf_to_yaml', 'create_egdf_from_egi',
             'extract_egi_from_egdf', 'validate_round_trip']
        )
        
        expected_egdf_hash = self.signatures['egdf_parser'].api_hash
        if current_egdf_hash != expected_egdf_hash:
            errors.append(f"EGDF Parser API signature changed: {expected_egdf_hash} → {current_egdf_hash}")
        
        # Check DAU YAML System
        current_yaml_hash = self._hash_api_methods(
            self.yaml_system,
            ['egif_to_yaml', 'yaml_to_graph', 'test_round_trip']
        )
        
        expected_yaml_hash = self.signatures['dau_yaml_system'].api_hash
        if current_yaml_hash != expected_yaml_hash:
            errors.append(f"DAU YAML System API signature changed: {expected_yaml_hash} → {current_yaml_hash}")
        
        return len(errors) == 0, errors
    
    def _validate_regression_tests(self) -> Tuple[bool, List[str]]:
        """Run all regression test vectors and validate outputs."""
        
        errors = []
        
        for vector in self.test_vectors:
            try:
                # Re-run the test case
                parser = EGIFParser(vector.egif_input)
                egi = parser.parse()
                
                # Check structure preservation
                current_structure = {
                    'vertices': len(egi.V),
                    'edges': len(egi.E),
                    'cuts': len(egi.Cut)
                }
                
                if current_structure != vector.expected_structure:
                    errors.append(f"Structure regression in {vector.name}: {vector.expected_structure} → {current_structure}")
                    continue
                
                # Generate layout and EGDF
                pipeline = DependencyOrderedPipeline()
                layout_result = pipeline.execute_pipeline(egi)
                
                spatial_primitives = []
                for element_id, element in layout_result.elements.items():
                    primitive_dict = {
                        'element_id': element_id,
                        'element_type': element.element_type,
                        'position': element.position,
                        'bounds': element.bounds
                    }
                    spatial_primitives.append(primitive_dict)
                
                metadata = EGDFMetadata(title=vector.name, source=vector.egif_input)
                egdf_doc = self.egdf_parser.create_egdf_from_egi(egi, spatial_primitives, metadata)
                
                # Check serialization hashes
                json_output = self.egdf_parser.egdf_to_json(egdf_doc)
                yaml_output = self.egdf_parser.egdf_to_yaml(egdf_doc)
                
                current_json_hash = hashlib.sha256(json_output.encode()).hexdigest()[:16]
                current_yaml_hash = hashlib.sha256(yaml_output.encode()).hexdigest()[:16]
                
                if current_json_hash != vector.json_hash:
                    errors.append(f"JSON serialization regression in {vector.name}: {vector.json_hash} → {current_json_hash}")
                
                if current_yaml_hash != vector.yaml_hash:
                    errors.append(f"YAML serialization regression in {vector.name}: {vector.yaml_hash} → {current_yaml_hash}")
                
            except Exception as e:
                errors.append(f"Regression test {vector.name} failed with exception: {e}")
        
        return len(errors) == 0, errors
    
    def _validate_cross_system_consistency(self) -> Tuple[bool, List[str]]:
        """Validate consistency between EGDF and DAU YAML systems."""
        
        errors = []
        
        test_egif = "*x (Human x)"
        
        try:
            # Test via EGDF system
            parser = EGIFParser(test_egif)
            egi1 = parser.parse()
            
            pipeline = DependencyOrderedPipeline()
            layout_result = pipeline.execute_pipeline(egi1)
            
            spatial_primitives = []
            for element_id, element in layout_result.elements.items():
                primitive_dict = {
                    'element_id': element_id,
                    'element_type': element.element_type,
                    'position': element.position,
                    'bounds': element.bounds
                }
                spatial_primitives.append(primitive_dict)
            
            egdf_doc = self.egdf_parser.create_egdf_from_egi(egi1, spatial_primitives)
            extracted_egi1 = self.egdf_parser.extract_egi_from_egdf(egdf_doc)
            
            # Test via DAU YAML system
            yaml_result = self.yaml_system.egif_to_yaml(test_egif)
            if yaml_result.success:
                graph_result = self.yaml_system.yaml_to_graph(yaml_result.data)
                if graph_result.success:
                    egi2 = graph_result.data
                    
                    # Compare structures
                    struct1 = {'V': len(extracted_egi1.V), 'E': len(extracted_egi1.E), 'Cut': len(extracted_egi1.Cut)}
                    struct2 = {'V': len(egi2.V), 'E': len(egi2.E), 'Cut': len(egi2.Cut)}
                    
                    if struct1 != struct2:
                        errors.append(f"Cross-system inconsistency: EGDF={struct1}, YAML={struct2}")
                else:
                    errors.append(f"DAU YAML graph reconstruction failed: {graph_result.errors}")
            else:
                errors.append(f"DAU YAML conversion failed: {yaml_result.errors}")
                
        except Exception as e:
            errors.append(f"Cross-system validation failed: {e}")
        
        return len(errors) == 0, errors
    
    def save_integrity_baseline(self, filepath: str):
        """Save current integrity baseline to file."""
        
        baseline_data = {
            'signatures': {name: asdict(sig) for name, sig in self.signatures.items()},
            'test_vectors': [asdict(vector) for vector in self.test_vectors],
            'created_at': time.time(),
            'version': '1.0.0'
        }
        
        with open(filepath, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        print(f"✓ Integrity baseline saved to {filepath}")
    
    def load_integrity_baseline(self, filepath: str) -> bool:
        """Load integrity baseline from file."""
        
        try:
            with open(filepath, 'r') as f:
                baseline_data = json.load(f)
            
            # Load signatures
            self.signatures = {}
            for name, sig_data in baseline_data['signatures'].items():
                self.signatures[name] = SerializationSignature(**sig_data)
            
            # Load test vectors
            self.test_vectors = []
            for vector_data in baseline_data['test_vectors']:
                self.test_vectors.append(RegressionTestVector(**vector_data))
            
            print(f"✓ Integrity baseline loaded from {filepath}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to load integrity baseline: {e}")
            return False

def create_integrity_protection():
    """Create and initialize the serialization integrity protection system."""
    
    print("🛡️  Creating Serialization Integrity Protection System")
    print("=" * 60)
    
    guard = SerializationIntegrityGuard()
    
    # Run initial validation
    print("Running initial integrity validation...")
    is_valid, errors = guard.validate_integrity()
    
    if is_valid:
        print("✅ All integrity checks passed")
        
        # Save baseline
        baseline_path = Path(__file__).parent / "serialization_integrity_baseline.json"
        guard.save_integrity_baseline(str(baseline_path))
        
        print(f"📊 Created {len(guard.test_vectors)} regression test vectors")
        print(f"🔒 Protected {len(guard.signatures)} critical components")
        
        return guard, str(baseline_path)
        
    else:
        print("❌ Integrity validation failed:")
        for error in errors:
            print(f"   • {error}")
        
        return None, None

if __name__ == "__main__":
    guard, baseline_path = create_integrity_protection()
    
    if guard:
        print("\n🎉 Serialization integrity protection system created successfully!")
        print(f"Baseline saved to: {baseline_path}")
        print("\nTo validate integrity in the future, run:")
        print(f"  python -c \"from serialization_integrity_guard import SerializationIntegrityGuard; g=SerializationIntegrityGuard(); g.load_integrity_baseline('{baseline_path}'); print('Valid:', g.validate_integrity()[0])\"")
    else:
        print("\n⚠️  Failed to create integrity protection system")
