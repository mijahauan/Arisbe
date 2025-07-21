#!/usr/bin/env python3
"""
Fix Containing Context Error

The containing_context_id variable is being used before it's defined.
This script fixes the variable ordering issue.
"""

import sys
from pathlib import Path

def fix_variable_ordering():
    """Fix the variable ordering in _convert_predicates method."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    # Find the problematic section and fix the ordering
    old_section = '''        for predicate_id, predicate in eg_graph.predicates.items():
            position = self._calculate_safe_predicate_position(predicate_id, containing_context_id, eg_graph)
            
            # Find the context containing this predicate
            containing_context_id = None
            for context_id, context in eg_graph.context_manager.contexts.items():
                if predicate_id in context.contained_items:
                    containing_context_id = context_id
                    break
            
            # Default to root context if not found
            if containing_context_id is None:
                containing_context_id = eg_graph.context_manager.root_context.id'''
    
    new_section = '''        for predicate_id, predicate in eg_graph.predicates.items():
            # Find the context containing this predicate FIRST
            containing_context_id = None
            for context_id, context in eg_graph.context_manager.contexts.items():
                if predicate_id in context.contained_items:
                    containing_context_id = context_id
                    break
            
            # Default to root context if not found
            if containing_context_id is None:
                containing_context_id = eg_graph.context_manager.root_context.id
            
            # Now calculate safe position with known context
            position = self._calculate_safe_predicate_position(predicate_id, containing_context_id, eg_graph)'''
    
    if old_section in content:
        content = content.replace(old_section, new_section)
        print("✅ Fixed containing_context_id variable ordering")
    else:
        print("❌ Could not find the problematic section to fix")
        return False
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Fix the containing context variable error."""
    
    print("🔧 FIXING CONTAINING CONTEXT VARIABLE ERROR")
    print("=" * 50)
    
    try:
        success = fix_variable_ordering()
        
        if success:
            print("✅ Variable ordering fixed successfully")
            print("✅ containing_context_id now defined before use")
            return True
        else:
            print("❌ Failed to fix variable ordering")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

