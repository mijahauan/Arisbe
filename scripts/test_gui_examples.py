#!/usr/bin/env python3
"""
Test EGIF Examples for GUI

This script provides various EGIF examples that can be copied and pasted into the GUI
to test different visual rendering scenarios, including the rounded rectangle cuts.
"""

def print_test_examples():
    """Print various EGIF examples for testing."""
    
    print("🎯 EGIF Test Examples for GUI")
    print("=" * 60)
    print("Copy and paste these into the GUI's EGIF Input field:")
    print()
    
    examples = [
        {
            'name': 'Simple Predicate',
            'egif': '(Human "Socrates")',
            'description': 'Basic predicate with constant'
        },
        {
            'name': 'Single Cut',
            'egif': '~[ (Mortal "Socrates") ]',
            'description': 'Test rounded rectangle cut rendering'
        },
        {
            'name': 'Shared Constant (Current)',
            'egif': '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            'description': 'Current example - shared constant across areas'
        },
        {
            'name': 'Nested Cuts',
            'egif': '~[ ~[ (P "x") ] ]',
            'description': 'Double negation - nested rounded rectangles'
        },
        {
            'name': 'Multiple Cuts',
            'egif': '~[ (P "x") ] ~[ (Q "y") ]',
            'description': 'Multiple separate cuts'
        },
        {
            'name': 'Quantified Variable',
            'egif': '*x (Human x) ~[ (Mortal x) ]',
            'description': 'Variable with ligature crossing cut'
        },
        {
            'name': 'Complex Nesting',
            'egif': '*x ~[ (P x) ~[ (Q x) ] ]',
            'description': 'Variable with nested cuts'
        },
        {
            'name': 'Roberts Disjunction',
            'egif': '*x ~[ ~[ (P x) ] (Q x) ]',
            'description': 'Classic EG pattern'
        },
        {
            'name': 'Multiple Variables',
            'egif': '*x *y (Loves x y) ~[ (Human x) (Human y) ]',
            'description': 'Two variables with shared predicates'
        },
        {
            'name': 'Deep Nesting',
            'egif': '~[ ~[ ~[ (P "x") ] ] ]',
            'description': 'Triple nested cuts - multiple rounded rectangles'
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['name']}")
        print(f"   EGIF: {example['egif']}")
        print(f"   Description: {example['description']}")
        print()
    
    print("📋 Instructions:")
    print("1. Copy any EGIF expression above")
    print("2. Paste it into the GUI's 'EGIF Input' text field")
    print("3. Click 'Parse & Render' button")
    print("4. Observe the visual rendering with rounded rectangle cuts")
    print()
    print("🎯 Focus Areas to Test:")
    print("- Rounded rectangle cuts (not ovals)")
    print("- Identity line connections")
    print("- Vertex positioning")
    print("- Nested cut containment")
    print("- Ligature paths across cuts")

if __name__ == '__main__':
    print_test_examples()
