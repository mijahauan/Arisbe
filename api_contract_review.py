#!/usr/bin/env python3
"""
API Contract Review and Standardization

This script systematically reviews and identifies API contract inconsistencies
across the EGDF pipeline, then provides recommendations for standardization.

Issues to address:
1. Inconsistent primitive class attribute names
2. Missing element correspondence between EGI and visual primitives  
3. Contract validation failures
4. Import/parameter mismatches
"""

import sys
import os
import inspect
from typing import Dict, List, Set, Any, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def analyze_primitive_classes():
    """Analyze primitive class APIs for consistency."""
    print("🔍 PRIMITIVE CLASS API ANALYSIS")
    print("=" * 50)
    
    try:
        from egdf_parser import VertexPrimitive, PredicatePrimitive, CutPrimitive, IdentityLinePrimitive
        from layout_engine_clean import SpatialPrimitive
        
        classes_to_analyze = [
            ('SpatialPrimitive', SpatialPrimitive),
            ('VertexPrimitive', VertexPrimitive), 
            ('PredicatePrimitive', PredicatePrimitive),
            ('CutPrimitive', CutPrimitive),
            ('IdentityLinePrimitive', IdentityLinePrimitive)
        ]
        
        print("Class Attribute Analysis:")
        print("-" * 30)
        
        for class_name, cls in classes_to_analyze:
            print(f"\n📋 {class_name}:")
            
            # Get class attributes
            if hasattr(cls, '__dataclass_fields__'):
                # Dataclass
                fields = cls.__dataclass_fields__
                for field_name, field in fields.items():
                    print(f"   • {field_name}: {field.type}")
            else:
                # Regular class - check __init__ signature
                try:
                    sig = inspect.signature(cls.__init__)
                    for param_name, param in sig.parameters.items():
                        if param_name != 'self':
                            print(f"   • {param_name}: {param.annotation}")
                except Exception as e:
                    print(f"   ❌ Could not analyze {class_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing primitive classes: {e}")
        return False

def analyze_layout_engine_output():
    """Analyze what the layout engine actually produces."""
    print("\n🔍 LAYOUT ENGINE OUTPUT ANALYSIS")
    print("=" * 50)
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Test with simple EGIF
        egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
        egi = parse_egif(egif)
        
        layout_engine = GraphvizLayoutEngine()
        layout_result = layout_engine.create_layout_from_graph(egi)
        
        print(f"EGI Elements:")
        print(f"   Vertices: {[v.id for v in egi.V]}")
        print(f"   Edges: {[e.id for e in egi.E]}")
        print(f"   Cuts: {[c.id for c in egi.Cut]}")
        
        print(f"\nLayout Result Primitives:")
        for primitive_id, primitive in layout_result.primitives.items():
            print(f"   • {primitive.element_id} ({primitive.element_type})")
        
        # Check for mismatches
        egi_ids = set()
        egi_ids.update(v.id for v in egi.V)
        egi_ids.update(e.id for e in egi.E) 
        egi_ids.update(c.id for c in egi.Cut)
        
        layout_ids = {p.element_id for p in layout_result.primitives.values()}
        
        missing_in_layout = egi_ids - layout_ids
        extra_in_layout = layout_ids - egi_ids
        
        if missing_in_layout:
            print(f"\n⚠️  EGI elements missing from layout: {missing_in_layout}")
        if extra_in_layout:
            print(f"⚠️  Extra elements in layout: {extra_in_layout}")
        
        return layout_result
        
    except Exception as e:
        print(f"❌ Error analyzing layout engine: {e}")
        return None

def analyze_contract_enforcement():
    """Analyze pipeline contract enforcement."""
    print("\n🔍 CONTRACT ENFORCEMENT ANALYSIS")
    print("=" * 50)
    
    try:
        from pipeline_contracts import (
            validate_spatial_primitive,
            validate_layout_result,
            validate_relational_graph_with_cuts
        )
        
        print("Available contract validators:")
        validators = [
            validate_spatial_primitive,
            validate_layout_result, 
            validate_relational_graph_with_cuts
        ]
        
        for validator in validators:
            sig = inspect.signature(validator)
            print(f"   • {validator.__name__}{sig}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing contracts: {e}")
        return False

def analyze_egdf_serialization():
    """Analyze EGDF serialization compatibility."""
    print("\n🔍 EGDF SERIALIZATION ANALYSIS")
    print("=" * 50)
    
    try:
        from egdf_parser import EGDFParser, EGDFLayoutGenerator
        
        # Test serialization with current primitives
        layout_gen = EGDFLayoutGenerator()
        
        # Check what methods expect vs what they get
        print("EGDFLayoutGenerator methods:")
        methods = [method for method in dir(layout_gen) if not method.startswith('_')]
        for method in methods:
            try:
                sig = inspect.signature(getattr(layout_gen, method))
                print(f"   • {method}{sig}")
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing EGDF serialization: {e}")
        return False

def generate_standardization_recommendations():
    """Generate recommendations for API standardization."""
    print("\n📋 STANDARDIZATION RECOMMENDATIONS")
    print("=" * 50)
    
    recommendations = [
        {
            'issue': 'Inconsistent Element ID Attributes',
            'problem': 'Classes use different attribute names: element_id vs id vs egi_element_id',
            'solution': 'Standardize on element_id across all primitive classes',
            'priority': 'HIGH'
        },
        {
            'issue': 'Missing Element Type Attributes', 
            'problem': 'Some classes lack element_type attribute expected by contracts',
            'solution': 'Add element_type property to all primitive classes',
            'priority': 'HIGH'
        },
        {
            'issue': 'Layout Engine Element ID Mismatch',
            'problem': 'Layout engine creates synthetic IDs not matching EGI elements',
            'solution': 'Ensure layout engine preserves exact EGI element IDs',
            'priority': 'CRITICAL'
        },
        {
            'issue': 'Contract Validation Failures',
            'problem': 'Pipeline contracts expect attributes that classes do not provide',
            'solution': 'Update contracts to match actual class interfaces or vice versa',
            'priority': 'HIGH'
        },
        {
            'issue': 'Missing Base Class Interface',
            'problem': 'No common interface for all primitive types',
            'solution': 'Create abstract base class with required interface',
            'priority': 'MEDIUM'
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['issue']} [{rec['priority']}]")
        print(f"   Problem: {rec['problem']}")
        print(f"   Solution: {rec['solution']}")
    
    return recommendations

def create_api_contract_fixes():
    """Create specific fixes for identified issues."""
    print("\n🔧 PROPOSED API CONTRACT FIXES")
    print("=" * 50)
    
    fixes = [
        {
            'file': 'src/egdf_parser.py',
            'change': 'Add element_id and element_type properties to all primitive classes',
            'code': '''
# Add to each primitive class:
@property
def element_id(self) -> str:
    return self.id

@property  
def element_type(self) -> str:
    return self.type
'''
        },
        {
            'file': 'src/layout_engine_clean.py',
            'change': 'Ensure SpatialPrimitive interface is consistently implemented',
            'code': '''
# Update SpatialPrimitive to enforce interface:
class SpatialPrimitive:
    def __init__(self, element_id: str, element_type: str, ...):
        self.element_id = element_id
        self.element_type = element_type
'''
        },
        {
            'file': 'src/graphviz_layout_engine_v2.py',
            'change': 'Preserve exact EGI element IDs in layout output',
            'code': '''
# Ensure layout primitives use exact EGI IDs:
for cut in egi.Cut:
    cut_primitive = SpatialPrimitive(
        element_id=cut.id,  # Use exact EGI ID
        element_type='cut',
        ...
    )
'''
        }
    ]
    
    for i, fix in enumerate(fixes, 1):
        print(f"\n{i}. {fix['file']}")
        print(f"   Change: {fix['change']}")
        print(f"   Code:{fix['code']}")
    
    return fixes

def run_full_api_review():
    """Run complete API contract review."""
    print("🎯 COMPREHENSIVE API CONTRACT REVIEW")
    print("=" * 60)
    print("Analyzing pipeline for contract consistency and enforcement...")
    print()
    
    results = {}
    
    # Run all analyses
    results['primitives'] = analyze_primitive_classes()
    results['layout'] = analyze_layout_engine_output()
    results['contracts'] = analyze_contract_enforcement() 
    results['serialization'] = analyze_egdf_serialization()
    
    # Generate recommendations
    recommendations = generate_standardization_recommendations()
    fixes = create_api_contract_fixes()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 API CONTRACT REVIEW SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Analysis Results: {passed}/{total} components analyzed successfully")
    print(f"Recommendations: {len(recommendations)} issues identified")
    print(f"Proposed Fixes: {len(fixes)} specific fixes recommended")
    
    if passed < total:
        print("\n⚠️  CRITICAL: API contract inconsistencies detected!")
        print("   Immediate action required to stabilize pipeline.")
    else:
        print("\n✅ API analysis complete. Review recommendations above.")
    
    return results, recommendations, fixes

if __name__ == "__main__":
    run_full_api_review()
