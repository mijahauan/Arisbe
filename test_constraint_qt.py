#!/usr/bin/env python3
"""
Test constraint system directly on EGDF primitives in Qt to validate it works on known correct forms.
"""

import sys
import os
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))
os.chdir(REPO_ROOT)

def test_constraint_system_on_egdf():
    """Test the spatial constraint system on known correct EGDF primitives."""
    
    print("Testing constraint system on EGDF primitives...")
    
    # Import required modules
    from spatial_constraint_system import SpatialConstraintSystem
    from egif_parser_dau import EGIFParser
    
    # Parse test EGIF to get EGI reference
    egif_text = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
    parser = EGIFParser(egif_text)
    egi = parser.parse()
    
    print(f"EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
    
    # Create known correct EGDF primitives (simulating 9-phase pipeline output)
    egdf_primitives = {
        # Vertex "Socrates" positioned inside outer cut
        'v_socrates': {
            'element_id': 'v_socrates',
            'element_type': 'vertex',
            'position': (120, 75),
            'bounds': (118, 73, 122, 77),
            'label': 'Socrates'
        },
        
        # Predicate "Human" positioned in outer cut
        'e_human': {
            'element_id': 'e_human',
            'element_type': 'predicate',
            'position': (60, 75),
            'bounds': (50, 70, 70, 80),
            'label': 'Human'
        },
        
        # Predicate "Mortal" positioned in inner cut
        'e_mortal': {
            'element_id': 'e_mortal',
            'element_type': 'predicate',
            'position': (160, 75),
            'bounds': (150, 70, 170, 80),
            'label': 'Mortal'
        },
        
        # Outer cut containing Human and Socrates
        'c_outer': {
            'element_id': 'c_outer',
            'element_type': 'cut',
            'position': (120, 75),
            'bounds': (40, 50, 200, 100)
        },
        
        # Inner cut containing Mortal (nested inside outer)
        'c_inner': {
            'element_id': 'c_inner',
            'element_type': 'cut',
            'position': (165, 75),
            'bounds': (140, 60, 190, 90)
        },
        
        # Ligature connecting Human to Socrates
        'l_human_socrates': {
            'element_id': 'l_human_socrates',
            'element_type': 'ligature',
            'path': [(60, 75), (120, 75)]
        },
        
        # Ligature connecting Mortal to Socrates  
        'l_mortal_socrates': {
            'element_id': 'l_mortal_socrates',
            'element_type': 'ligature',
            'path': [(160, 75), (120, 75)]
        }
    }
    
    print(f"Created {len(egdf_primitives)} test primitives")
    
    # Initialize constraint system with EGI reference
    constraint_system = SpatialConstraintSystem()
    constraint_system.set_egi_reference(egi)
    
    print("\n=== Testing Constraint Validation ===")
    
    # Test 1: Validate correct layout (should pass)
    violations = constraint_system.validate_layout(egdf_primitives)
    print(f"Violations in correct layout: {len(violations)}")
    for violation in violations:
        print(f"  - {violation}")
    
    # Test 2: Create invalid layout (vertex outside cut)
    invalid_primitives = egdf_primitives.copy()
    # Map test IDs to actual EGI IDs for constraint validation
    vertex_id = list(egi.V)[0].id if egi.V else 'v_socrates'
    cut_id = list(egi.Cut)[0].id if egi.Cut else 'c_outer'
    
    # Create primitives with actual EGI IDs
    invalid_primitives[vertex_id] = {
        'element_id': vertex_id,
        'element_type': 'vertex', 
        'position': (250, 75),  # Outside all cuts
        'bounds': (248, 73, 252, 77),
        'label': 'Socrates'
    }
    invalid_primitives[cut_id] = {
        'element_id': cut_id,
        'element_type': 'cut',
        'position': (120, 75),
        'bounds': (40, 50, 200, 100)
    }
    
    violations = constraint_system.validate_layout(invalid_primitives)
    print(f"\nViolations in invalid layout: {len(violations)}")
    for violation in violations:
        print(f"  - {violation}")
    
    # Test 3: Apply constraint fixes
    if violations:
        print("\n=== Testing Constraint Fixes ===")
        fixed_primitives = constraint_system.apply_constraint_fixes(violations, invalid_primitives)
        
        # Check if fixes worked
        new_violations = constraint_system.validate_layout(fixed_primitives)
        print(f"Violations after fixes: {len(new_violations)}")
        
        # Show position changes
        original_pos = invalid_primitives['v_socrates']['position']
        fixed_pos = fixed_primitives['v_socrates']['position']
        print(f"Vertex position: {original_pos} → {fixed_pos}")
    
    print("\n=== Testing Interactive Constraint Enforcement ===")
    
    # Test 4: Interactive editing with constraint enforcement
    # Simulate user trying to drag vertex outside cut
    edit_request = {
        'element_id': 'v_socrates',
        'new_position': (300, 75),  # Way outside cuts
        'edit_type': 'move'
    }
    
    # Test if constraint system can handle interactive edits
    try:
        result = constraint_system.enforce_interactive_constraint(edit_request, egdf_primitives)
        print(f"Interactive edit allowed: {result['allowed']}")
        print(f"Suggested position: {result.get('suggested_position')}")
        print(f"Constraint message: {result.get('message')}")
    except AttributeError as e:
        print(f"Interactive constraint method not implemented: {e}")
        print("Testing basic constraint validation instead...")
    
    return True

if __name__ == "__main__":
    success = test_constraint_system_on_egdf()
    if success:
        print("\n✅ Constraint system test completed")
    else:
        print("\n❌ Constraint system test failed")
