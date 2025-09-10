#!/usr/bin/env python3
"""Test script to verify area polarity calculation is correct."""

from src.interactive_egif_transformer import InteractiveEGIFTransformer

def test_polarity_calculations():
    """Test polarity calculations on various graphs."""
    
    transformer = InteractiveEGIFTransformer()
    
    test_cases = [
        {
            "name": "stanford_nested_quantifiers", 
            "egif": "~[ *x *y (Loves x y) ]",
            "expected_areas": {
                "sheet": {"polarity": "positive", "depth": 0},
                "cut_0": {"polarity": "negative", "depth": 1}
            }
        },
        {
            "name": "roberts_disjunction",
            "egif": "~[ ~[ (P \"x\") ] ~[ (Q \"x\") ] ]", 
            "expected_areas": {
                "sheet": {"polarity": "positive", "depth": 0},
                "cut_0": {"polarity": "negative", "depth": 1},  # Outer cut
                "cut_1": {"polarity": "positive", "depth": 2}, # First inner cut
                "cut_2": {"polarity": "positive", "depth": 2}  # Second inner cut
            }
        },
        {
            "name": "peirce_man_mortal",
            "egif": "~[ (Human \"Socrates\") ~[ (Mortal \"Socrates\") ] ]",
            "expected_areas": {
                "sheet": {"polarity": "positive", "depth": 0},
                "cut_0": {"polarity": "positive", "depth": 2},  # Inner cut (indexed first)
                "cut_1": {"polarity": "negative", "depth": 1}   # Outer cut (indexed second)
            }
        }
    ]
    
    print("🧪 Testing Area Polarity Calculations")
    print("=" * 50)
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        print(f"EGIF: {test_case['egif']}")
        
        try:
            analysis = transformer.analyze_graph(test_case['egif'])
            
            # Check each expected area
            for area_name, expected in test_case['expected_areas'].items():
                if area_name in analysis.areas:
                    actual = analysis.areas[area_name]
                    if (actual['polarity'] == expected['polarity'] and 
                        actual['depth'] == expected['depth']):
                        print(f"  ✅ {area_name}: {actual['polarity']} depth {actual['depth']}")
                    else:
                        print(f"  ❌ {area_name}: Expected {expected['polarity']} depth {expected['depth']}, got {actual['polarity']} depth {actual['depth']}")
                        all_passed = False
                else:
                    print(f"  ❌ {area_name}: Area not found")
                    all_passed = False
                    
        except Exception as e:
            print(f"  💥 Error analyzing graph: {e}")
            all_passed = False
    
    print(f"\n{'🎉 All tests passed!' if all_passed else '⚠️  Some tests failed'}")
    return all_passed

if __name__ == "__main__":
    test_polarity_calculations()
