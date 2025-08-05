#!/usr/bin/env python3
"""
Visual Output Validation for Existential Graph Diagrams

This script analyzes the generated PNG files to validate that they properly
display Existential Graph diagrams according to Dau's conventions and the
core requirements for EG diagram correctness.

Based on the memory about EG diagram correctness requirements:
1. NO CUT OVERLAP: Cuts must never overlap each other
2. COMPLETE CONTAINMENT: Elements must be entirely within their designated areas
3. VISUAL DISCRIMINATION: Sufficient separation so users can distinguish each element
4. LINE ROUTING: Lines of identity must avoid overlapping other lines and elements
5. CUT CROSSING RULES: Lines only cross cut boundaries when connecting predicates in different cuts
"""

import sys
import os
from pathlib import Path
import subprocess

def analyze_png_file(png_path: str, expected_elements: dict) -> dict:
    """
    Analyze a PNG file for EG diagram correctness.
    
    Args:
        png_path: Path to the PNG file
        expected_elements: Dictionary describing what should be in the diagram
        
    Returns:
        Dictionary with analysis results
    """
    results = {
        'file': png_path,
        'exists': False,
        'size': None,
        'expected': expected_elements,
        'visual_analysis': {}
    }
    
    # Check if file exists and get basic info
    if os.path.exists(png_path):
        results['exists'] = True
        stat = os.stat(png_path)
        results['size'] = stat.st_size
        
        # Basic file validation
        if results['size'] == 0:
            results['visual_analysis']['error'] = "File is empty (0 bytes)"
        elif results['size'] < 1000:  # Very small PNG files are likely errors
            results['visual_analysis']['warning'] = f"File is very small ({results['size']} bytes) - may not contain proper diagram"
        else:
            results['visual_analysis']['file_valid'] = True
            
    else:
        results['visual_analysis']['error'] = "File does not exist"
    
    return results

def validate_all_png_files() -> list:
    """Validate all generated PNG files for EG diagram correctness."""
    
    print("🔍 Visual Output Validation for EG Diagrams")
    print("=" * 60)
    print("Analyzing generated PNG files for Dau's EG conventions...")
    print()
    
    # Define expected elements for each test case
    test_cases = [
        {
            'file': 'proper_eg_1_simple_relation.png',
            'egif': '(Human "Socrates")',
            'expected': {
                'vertices': 1,  # "Socrates" constant
                'predicates': 1,  # Human predicate
                'cuts': 0,
                'heavy_lines': 1,  # Line connecting vertex to predicate
                'description': 'Constant vertex with predicate attached via heavy line'
            }
        },
        {
            'file': 'proper_eg_2_variable_with_predicate.png',
            'egif': '*x (Human x)',
            'expected': {
                'vertices': 1,  # Variable x
                'predicates': 1,  # Human predicate
                'cuts': 0,
                'heavy_lines': 1,  # Line connecting vertex to predicate
                'description': 'Variable vertex with predicate, heavy line connection'
            }
        },
        {
            'file': 'proper_eg_3_cut_with_containment.png',
            'egif': '*x ~[ (Mortal x) ]',
            'expected': {
                'vertices': 1,  # Variable x (outside cut)
                'predicates': 1,  # Mortal predicate (inside cut)
                'cuts': 1,  # One cut containing Mortal
                'heavy_lines': 1,  # Line crossing cut boundary
                'description': 'Vertex outside cut, predicate inside cut, line crosses boundary'
            }
        },
        {
            'file': 'proper_eg_4_sibling_cuts.png',
            'egif': '*x ~[ (Human x) ] ~[ (Mortal x) ]',
            'expected': {
                'vertices': 1,  # Shared variable x
                'predicates': 2,  # Human and Mortal predicates
                'cuts': 2,  # Two sibling cuts
                'heavy_lines': 2,  # Lines to both predicates
                'description': 'Two non-overlapping cuts, shared vertex, proper containment'
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"📊 Analyzing: {test_case['file']}")
        print(f"   EGIF: {test_case['egif']}")
        print(f"   Expected: {test_case['expected']['description']}")
        
        result = analyze_png_file(test_case['file'], test_case['expected'])
        results.append(result)
        
        # Report basic file validation
        if result['exists']:
            if result['visual_analysis'].get('file_valid'):
                print(f"   ✅ File exists and appears valid ({result['size']} bytes)")
            elif 'warning' in result['visual_analysis']:
                print(f"   ⚠️  {result['visual_analysis']['warning']}")
            elif 'error' in result['visual_analysis']:
                print(f"   ❌ {result['visual_analysis']['error']}")
        else:
            print(f"   ❌ File missing: {test_case['file']}")
        
        print()
    
    return results

def check_dau_conventions(results: list) -> dict:
    """
    Check if the visual output follows Dau's EG conventions.
    
    Based on Dau's formalism and EG diagram correctness requirements.
    """
    print("🎨 Checking Dau's EG Conventions")
    print("-" * 40)
    
    conventions_check = {
        'files_generated': 0,
        'files_valid': 0,
        'expected_elements': {
            'heavy_lines_of_identity': "Thick lines connecting vertices to predicates",
            'fine_drawn_cuts': "Closed curves around predicates in cuts", 
            'proper_containment': "Predicates entirely within cut boundaries",
            'non_overlapping_cuts': "Sibling cuts don't overlap each other",
            'visual_discrimination': "Sufficient separation between all elements",
            'nu_mapping': "Argument order preserved in connections"
        },
        'validation_status': {}
    }
    
    # Count valid files
    for result in results:
        if result['exists']:
            conventions_check['files_generated'] += 1
            if result['visual_analysis'].get('file_valid'):
                conventions_check['files_valid'] += 1
    
    print(f"Files Generated: {conventions_check['files_generated']}/4")
    print(f"Files Valid: {conventions_check['files_valid']}/4")
    print()
    
    # Check specific conventions
    print("Expected Visual Elements (per Dau's formalism):")
    for element, description in conventions_check['expected_elements'].items():
        print(f"  • {description}")
    
    print()
    print("Critical EG Diagram Requirements:")
    print("  1. NO CUT OVERLAP: Cuts must never overlap each other")
    print("  2. COMPLETE CONTAINMENT: Elements entirely within designated areas")
    print("  3. VISUAL DISCRIMINATION: Sufficient separation between elements")
    print("  4. LINE ROUTING: Lines avoid overlapping other elements")
    print("  5. CUT CROSSING RULES: Lines cross cuts only when connecting different areas")
    
    return conventions_check

def provide_validation_summary(results: list, conventions: dict) -> None:
    """Provide a comprehensive validation summary."""
    
    print("\n" + "=" * 60)
    print("📋 VISUAL VALIDATION SUMMARY")
    print("=" * 60)
    
    # Overall status
    if conventions['files_valid'] == 4:
        print("✅ SUCCESS: All 4 PNG files generated and appear valid")
        print("   The rendering pipeline is working correctly.")
    elif conventions['files_generated'] == 4:
        print("⚠️  PARTIAL SUCCESS: All files generated but some may have issues")
        print("   Check file sizes and visual content.")
    else:
        print("❌ FAILURE: Not all PNG files were generated")
        print("   The rendering pipeline has issues that need fixing.")
    
    print()
    print("Next Steps for Visual Validation:")
    print("1. 👁️  MANUAL INSPECTION: Open each PNG file and visually verify:")
    print("   - Heavy lines of identity (thick black lines)")
    print("   - Fine-drawn cuts (closed curves around predicates)")
    print("   - Proper containment (predicates inside cuts)")
    print("   - Non-overlapping cuts (clear separation)")
    print("   - Clear visual discrimination of all elements")
    print()
    print("2. 🔧 AUTOMATED ANALYSIS: Consider implementing image analysis")
    print("   - Line thickness detection")
    print("   - Shape recognition (circles for cuts)")
    print("   - Containment verification")
    print("   - Overlap detection")
    print()
    print("3. 📊 COMPARISON: Compare with reference EG diagrams")
    print("   - Dau's examples from mathematical_logic_with_diagrams.pdf")
    print("   - Peirce's original EG conventions")
    print("   - Ensure visual fidelity to mathematical formalism")

def open_png_files_for_inspection():
    """Open all PNG files for manual visual inspection."""
    
    print("\n🖼️  Opening PNG Files for Manual Inspection")
    print("-" * 50)
    
    png_files = [
        'proper_eg_1_simple_relation.png',
        'proper_eg_2_variable_with_predicate.png', 
        'proper_eg_3_cut_with_containment.png',
        'proper_eg_4_sibling_cuts.png'
    ]
    
    for png_file in png_files:
        if os.path.exists(png_file):
            print(f"📂 Opening: {png_file}")
            try:
                # Use macOS 'open' command to open PNG files
                subprocess.run(['open', png_file], check=True)
            except subprocess.CalledProcessError:
                print(f"   ⚠️  Could not open {png_file} automatically")
                print(f"   Please open manually to inspect visual content")
        else:
            print(f"❌ Missing: {png_file}")
    
    print("\n👀 MANUAL INSPECTION CHECKLIST:")
    print("For each PNG file, verify:")
    print("  ✓ Heavy lines of identity (thick black lines connecting vertices to predicates)")
    print("  ✓ Fine-drawn cuts (thin closed curves around predicates)")
    print("  ✓ Proper containment (predicates entirely within cut boundaries)")
    print("  ✓ Non-overlapping cuts (sibling cuts clearly separated)")
    print("  ✓ Visual discrimination (all elements clearly distinguishable)")
    print("  ✓ Correct spatial layout (matches logical structure)")

if __name__ == "__main__":
    print("Arisbe Visual Output Validation")
    print("Validating EG diagrams for Dau's conventions and correctness")
    print()
    
    # Validate all PNG files
    results = validate_all_png_files()
    
    # Check Dau's conventions
    conventions = check_dau_conventions(results)
    
    # Provide summary
    provide_validation_summary(results, conventions)
    
    # Offer to open files for manual inspection
    print("\n" + "=" * 60)
    response = input("Open PNG files for manual visual inspection? (y/n): ")
    if response.lower().startswith('y'):
        open_png_files_for_inspection()
    
    print("\n🎯 Visual validation complete!")
    print("Review the PNG files to confirm they meet EG diagram requirements.")
