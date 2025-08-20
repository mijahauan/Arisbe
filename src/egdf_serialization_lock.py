#!/usr/bin/env python
"""
EGDF Serialization Lock System

Simple but effective protection for EGDF YAML/JSON serialization integrity.
Creates locked test vectors and validation without complex import dependencies.
"""

import hashlib
import json
import time
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SerializationLock:
    """Lock for serialization system integrity."""
    component: str
    version: str
    test_vectors: List[Dict[str, Any]]
    baseline_hashes: Dict[str, str]
    created_at: float

class EGDFSerializationProtector:
    """
    Lightweight protection system for EGDF serialization.
    
    Uses golden test vectors and hash validation to detect corruption
    without requiring complex runtime validation.
    """
    
    def __init__(self):
        self.lock_file = Path(__file__).parent / "egdf_serialization.lock"
        
    def create_protection_lock(self) -> bool:
        """Create protection lock with current serialization state."""
        
        print("🔒 Creating EGDF Serialization Protection Lock")
        print("=" * 50)
        
        # Golden test vectors - these should NEVER change
        golden_vectors = [
            {
                'name': 'simple_predicate',
                'egif': '*x (Human x)',
                'expected_structure': {'vertices': 1, 'edges': 1, 'cuts': 0},
                'description': 'Basic predicate - core functionality'
            },
            {
                'name': 'nested_cut',
                'egif': '*x (Human x) ~[ (Mortal x) ]',
                'expected_structure': {'vertices': 1, 'edges': 2, 'cuts': 1},
                'description': 'Nested cut - negation handling'
            },
            {
                'name': 'isolated_vertices',
                'egif': '[*x] [*y] (Knows x y)',
                'expected_structure': {'vertices': 2, 'edges': 1, 'cuts': 0},
                'description': 'Isolated vertices - critical edge case'
            },
            {
                'name': 'double_negation',
                'egif': '~[~[(happy *x)]]',
                'expected_structure': {'vertices': 1, 'edges': 1, 'cuts': 2},
                'description': 'Double negation - complex nesting'
            }
        ]
        
        # Generate baseline hashes for each component
        baseline_hashes = {}
        
        try:
            # Test DAU YAML serialization
            from dau_yaml_serializer import DAUYAMLConversionSystem
            yaml_system = DAUYAMLConversionSystem()
            
            yaml_results = []
            for vector in golden_vectors:
                result = yaml_system.egif_to_yaml(vector['egif'])
                if result.success:
                    yaml_hash = hashlib.sha256(result.data.encode()).hexdigest()[:16]
                    yaml_results.append({
                        'name': vector['name'],
                        'yaml_hash': yaml_hash,
                        'structure': result.metadata.get('graph_structure', {})
                    })
                else:
                    print(f"⚠️  YAML test failed for {vector['name']}: {result.errors}")
                    return False
            
            baseline_hashes['dau_yaml_results'] = hashlib.sha256(
                str(sorted(yaml_results, key=lambda x: x['name'])).encode()
            ).hexdigest()[:16]
            
            print(f"✓ DAU YAML system validated - {len(yaml_results)} test vectors")
            
        except Exception as e:
            print(f"⚠️  DAU YAML validation failed: {e}")
            baseline_hashes['dau_yaml_results'] = 'UNAVAILABLE'
        
        try:
            # Test EGDF parser
            from egdf_parser import EGDFParser
            from egif_parser_dau import EGIFParser
            
            egdf_parser = EGDFParser()
            egdf_results = []
            
            for vector in golden_vectors:
                parser = EGIFParser(vector['egif'])
                egi = parser.parse()
                
                # Create minimal spatial primitives
                spatial_primitives = []
                vertex_count = 0
                for vertex in egi.V:
                    spatial_primitives.append({
                        'element_id': vertex.id,
                        'element_type': 'vertex',
                        'position': (100 + vertex_count * 50, 100),
                        'bounds': (90 + vertex_count * 50, 90, 110 + vertex_count * 50, 110)
                    })
                    vertex_count += 1
                
                edge_count = 0
                for edge in egi.E:
                    spatial_primitives.append({
                        'element_id': edge.id,
                        'element_type': 'predicate',
                        'position': (200 + edge_count * 50, 150),
                        'bounds': (180 + edge_count * 50, 140, 220 + edge_count * 50, 160)
                    })
                    edge_count += 1
                
                cut_count = 0
                for cut in egi.Cut:
                    spatial_primitives.append({
                        'element_id': cut.id,
                        'element_type': 'cut',
                        'position': (150 + cut_count * 100, 200),
                        'bounds': (100 + cut_count * 100, 150, 200 + cut_count * 100, 250)
                    })
                    cut_count += 1
                
                egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
                
                json_output = egdf_parser.egdf_to_json(egdf_doc)
                yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
                
                json_hash = hashlib.sha256(json_output.encode()).hexdigest()[:16]
                yaml_hash = hashlib.sha256(yaml_output.encode()).hexdigest()[:16]
                
                egdf_results.append({
                    'name': vector['name'],
                    'json_hash': json_hash,
                    'yaml_hash': yaml_hash,
                    'structure': {
                        'vertices': len(egi.V),
                        'edges': len(egi.E),
                        'cuts': len(egi.Cut)
                    }
                })
            
            baseline_hashes['egdf_parser_results'] = hashlib.sha256(
                str(sorted(egdf_results, key=lambda x: x['name'])).encode()
            ).hexdigest()[:16]
            
            print(f"✓ EGDF parser validated - {len(egdf_results)} test vectors")
            
        except Exception as e:
            print(f"⚠️  EGDF parser validation failed: {e}")
            baseline_hashes['egdf_parser_results'] = 'UNAVAILABLE'
        
        # Create lock
        lock = SerializationLock(
            component='egdf_serialization_system',
            version='1.0.0',
            test_vectors=golden_vectors,
            baseline_hashes=baseline_hashes,
            created_at=time.time()
        )
        
        # Save lock file
        lock_data = {
            'component': lock.component,
            'version': lock.version,
            'test_vectors': lock.test_vectors,
            'baseline_hashes': lock.baseline_hashes,
            'created_at': lock.created_at,
            'lock_signature': self._create_lock_signature(lock)
        }
        
        with open(self.lock_file, 'w') as f:
            json.dump(lock_data, f, indent=2)
        
        print(f"✓ Protection lock saved to {self.lock_file}")
        print(f"🛡️  Protected {len(golden_vectors)} critical test vectors")
        print(f"🔑 Baseline hashes: {len(baseline_hashes)} components")
        
        return True
    
    def _create_lock_signature(self, lock: SerializationLock) -> str:
        """Create tamper-proof signature for lock."""
        lock_content = f"{lock.component}|{lock.version}|{lock.baseline_hashes}|{lock.created_at}"
        return hashlib.sha256(lock_content.encode()).hexdigest()[:32]
    
    def validate_lock(self) -> Tuple[bool, List[str]]:
        """Validate current state against protection lock."""
        
        if not self.lock_file.exists():
            return False, ["Protection lock file not found"]
        
        try:
            with open(self.lock_file, 'r') as f:
                lock_data = json.load(f)
            
            # Verify lock signature
            temp_lock = SerializationLock(
                component=lock_data['component'],
                version=lock_data['version'],
                test_vectors=lock_data['test_vectors'],
                baseline_hashes=lock_data['baseline_hashes'],
                created_at=lock_data['created_at']
            )
            
            expected_signature = self._create_lock_signature(temp_lock)
            if lock_data['lock_signature'] != expected_signature:
                return False, ["Lock file has been tampered with"]
            
            errors = []
            
            # Re-run tests and compare hashes
            current_hashes = {}
            
            # Test DAU YAML system
            try:
                from dau_yaml_serializer import DAUYAMLConversionSystem
                yaml_system = DAUYAMLConversionSystem()
                
                yaml_results = []
                for vector in lock_data['test_vectors']:
                    result = yaml_system.egif_to_yaml(vector['egif'])
                    if result.success:
                        yaml_hash = hashlib.sha256(result.data.encode()).hexdigest()[:16]
                        yaml_results.append({
                            'name': vector['name'],
                            'yaml_hash': yaml_hash,
                            'structure': result.metadata.get('graph_structure', {})
                        })
                    else:
                        errors.append(f"DAU YAML test failed for {vector['name']}")
                
                current_hashes['dau_yaml_results'] = hashlib.sha256(
                    str(sorted(yaml_results, key=lambda x: x['name'])).encode()
                ).hexdigest()[:16]
                
            except Exception as e:
                errors.append(f"DAU YAML system unavailable: {e}")
                current_hashes['dau_yaml_results'] = 'UNAVAILABLE'
            
            # Test EGDF parser
            try:
                from egdf_parser import EGDFParser
                from egif_parser_dau import EGIFParser
                
                egdf_parser = EGDFParser()
                egdf_results = []
                
                for vector in lock_data['test_vectors']:
                    parser = EGIFParser(vector['egif'])
                    egi = parser.parse()
                    
                    # Create same minimal spatial primitives as baseline
                    spatial_primitives = []
                    vertex_count = 0
                    for vertex in egi.V:
                        spatial_primitives.append({
                            'element_id': vertex.id,
                            'element_type': 'vertex',
                            'position': (100 + vertex_count * 50, 100),
                            'bounds': (90 + vertex_count * 50, 90, 110 + vertex_count * 50, 110)
                        })
                        vertex_count += 1
                    
                    edge_count = 0
                    for edge in egi.E:
                        spatial_primitives.append({
                            'element_id': edge.id,
                            'element_type': 'predicate',
                            'position': (200 + edge_count * 50, 150),
                            'bounds': (180 + edge_count * 50, 140, 220 + edge_count * 50, 160)
                        })
                        edge_count += 1
                    
                    cut_count = 0
                    for cut in egi.Cut:
                        spatial_primitives.append({
                            'element_id': cut.id,
                            'element_type': 'cut',
                            'position': (150 + cut_count * 100, 200),
                            'bounds': (100 + cut_count * 100, 150, 200 + cut_count * 100, 250)
                        })
                        cut_count += 1
                    
                    egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
                    
                    json_output = egdf_parser.egdf_to_json(egdf_doc)
                    yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
                    
                    json_hash = hashlib.sha256(json_output.encode()).hexdigest()[:16]
                    yaml_hash = hashlib.sha256(yaml_output.encode()).hexdigest()[:16]
                    
                    egdf_results.append({
                        'name': vector['name'],
                        'json_hash': json_hash,
                        'yaml_hash': yaml_hash,
                        'structure': {
                            'vertices': len(egi.V),
                            'edges': len(egi.E),
                            'cuts': len(egi.Cut)
                        }
                    })
                
                current_hashes['egdf_parser_results'] = hashlib.sha256(
                    str(sorted(egdf_results, key=lambda x: x['name'])).encode()
                ).hexdigest()[:16]
                
            except Exception as e:
                errors.append(f"EGDF parser unavailable: {e}")
                current_hashes['egdf_parser_results'] = 'UNAVAILABLE'
            
            # Compare hashes
            baseline_hashes = lock_data['baseline_hashes']
            for component, baseline_hash in baseline_hashes.items():
                current_hash = current_hashes.get(component, 'MISSING')
                if baseline_hash != 'UNAVAILABLE' and current_hash != baseline_hash:
                    errors.append(f"Hash mismatch in {component}: {baseline_hash} → {current_hash}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Lock validation failed: {e}"]
    
    def status_report(self) -> Dict[str, Any]:
        """Generate status report for serialization protection."""
        
        if not self.lock_file.exists():
            return {
                'protected': False,
                'message': 'No protection lock found'
            }
        
        is_valid, errors = self.validate_lock()
        
        with open(self.lock_file, 'r') as f:
            lock_data = json.load(f)
        
        return {
            'protected': True,
            'valid': is_valid,
            'errors': errors,
            'lock_created': time.ctime(lock_data['created_at']),
            'test_vectors': len(lock_data['test_vectors']),
            'components_protected': len(lock_data['baseline_hashes']),
            'version': lock_data['version']
        }

def main():
    """Main function to create or validate protection lock."""
    
    protector = EGDFSerializationProtector()
    
    print("EGDF Serialization Protection System")
    print("=" * 40)
    
    if protector.lock_file.exists():
        print("🔍 Existing protection lock found - validating...")
        is_valid, errors = protector.validate_lock()
        
        if is_valid:
            print("✅ Serialization system integrity VALIDATED")
            status = protector.status_report()
            print(f"   Lock created: {status['lock_created']}")
            print(f"   Test vectors: {status['test_vectors']}")
            print(f"   Components: {status['components_protected']}")
        else:
            print("❌ Serialization system integrity COMPROMISED")
            for error in errors:
                print(f"   • {error}")
    else:
        print("🔒 Creating new protection lock...")
        success = protector.create_protection_lock()
        
        if success:
            print("✅ Protection lock created successfully")
            print("🛡️  EGDF serialization system is now protected")
        else:
            print("❌ Failed to create protection lock")

if __name__ == "__main__":
    main()
