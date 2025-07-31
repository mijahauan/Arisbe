#!/usr/bin/env python3
"""
Comprehensive Bidirectional YAML Conversion Test Suite
Tests complete EGI ↔ YAML conversion with validation and round-trip verification

CHANGES: Implements comprehensive testing of bidirectional YAML conversion including
round-trip verification, structural integrity validation, and performance analysis.
Ensures the YAML serialization system is production-ready for data persistence.
"""

import sys
import os
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egif_parser import parse_egif
    from egi_yaml import serialize_egi_to_yaml, deserialize_egi_from_yaml
    from yaml_to_egi_parser import ImprovedYAMLToEGIParser
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


@dataclass
class ConversionTestResult:
    """Result of a bidirectional conversion test."""
    egif: str
    success: bool
    original_structure: Dict[str, int]
    yaml_size: int
    conversion_time: float
    round_trip_success: bool
    structural_integrity: bool
    errors: List[str]
    warnings: List[str]


class BidirectionalYAMLTester:
    """
    Comprehensive tester for bidirectional YAML conversion.
    
    CHANGES: Provides thorough testing of EGI ↔ YAML conversion including
    performance metrics, structural validation, and round-trip verification.
    """
    
    def __init__(self):
        self.improved_parser = ImprovedYAMLToEGIParser()
        self.test_results = []
    
    def run_comprehensive_test_suite(self) -> List[ConversionTestResult]:
        """Run comprehensive bidirectional conversion tests."""
        
        print("Comprehensive Bidirectional YAML Conversion Test Suite")
        print("=" * 70)
        print("Testing EGI ↔ YAML conversion with validation and round-trip verification")
        print()
        
        # Test cases covering various EGI structures
        test_cases = [
            # Simple cases
            "(P *x)",
            "[*x]",
            "~[(P *x)]",
            
            # Medium complexity
            "(man *x) ~[(mortal x)]",
            "[*x] [*y] (loves x y)",
            "~[~[(happy *x)]]",
            
            # Complex nested structures
            "(P *x) (Q *y) ~[(R x y) ~[(S x)]]",
            "~[(A *x) (B *y) ~[~[~[(C x) (B y)]]]]",
            
            # Multiple variables and relations
            "(human *x) (human *y) ~[(loves x y) ~[(happy x) (happy y)]]",
            
            # Deep nesting
            "~[~[~[~[(deep *x)]]]]",
            
            # Complex variable binding
            "(teacher *x) (student *y) (student *z) ~[(teaches x y) (teaches x z) ~[(learns y) (learns z)]]"
        ]
        
        self.test_results = []
        
        for i, egif in enumerate(test_cases, 1):
            print(f"Test {i:2d}: {egif}")
            print("-" * 50)
            
            result = self._test_bidirectional_conversion(egif)
            self.test_results.append(result)
            
            # Print test result
            if result.success:
                status = "✅ SUCCESS"
                if not result.round_trip_success:
                    status += " (⚠️ Round-trip issues)"
                elif not result.structural_integrity:
                    status += " (⚠️ Structural issues)"
            else:
                status = "❌ FAILED"
            
            print(f"Result: {status}")
            print(f"Structure: {result.original_structure}")
            print(f"YAML size: {result.yaml_size} bytes")
            print(f"Time: {result.conversion_time:.3f}s")
            
            if result.errors:
                print(f"Errors: {len(result.errors)}")
                for error in result.errors[:2]:  # Show first 2 errors
                    print(f"  - {error}")
            
            if result.warnings:
                print(f"Warnings: {len(result.warnings)}")
                for warning in result.warnings[:2]:  # Show first 2 warnings
                    print(f"  - {warning}")
            
            print()
        
        return self.test_results
    
    def _test_bidirectional_conversion(self, egif: str) -> ConversionTestResult:
        """Test bidirectional conversion for a single EGIF."""
        
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            # Step 1: Parse EGIF to EGI
            original_egi = parse_egif(egif)
            original_structure = {
                'vertices': len(original_egi.vertices),
                'edges': len(original_egi.edges),
                'cuts': len(original_egi.cuts)
            }
            
            # Step 2: Serialize EGI to YAML
            yaml_str = serialize_egi_to_yaml(original_egi)
            yaml_size = len(yaml_str.encode('utf-8'))
            
            # Step 3: Deserialize YAML back to EGI (using basic deserializer)
            restored_egi_basic = deserialize_egi_from_yaml(yaml_str)
            
            # Step 4: Deserialize YAML using improved parser
            restored_egi_improved, parse_errors, parse_warnings = self.improved_parser.parse_yaml_to_egi(yaml_str)
            
            errors.extend(parse_errors)
            warnings.extend(parse_warnings)
            
            # Step 5: Verify structural integrity
            structural_integrity = self._verify_structural_integrity(
                original_egi, restored_egi_basic, restored_egi_improved
            )
            
            # Step 6: Test round-trip conversion
            round_trip_success = False
            if restored_egi_improved:
                try:
                    # Serialize restored EGI back to YAML
                    yaml_str2 = serialize_egi_to_yaml(restored_egi_improved)
                    
                    # Check if YAML structures are equivalent (ignoring ID differences)
                    round_trip_success = self._compare_yaml_structures(yaml_str, yaml_str2)
                    
                except Exception as e:
                    errors.append(f"Round-trip serialization failed: {str(e)}")
            
            conversion_time = time.time() - start_time
            
            success = (
                restored_egi_basic is not None and 
                restored_egi_improved is not None and
                len(errors) == 0
            )
            
            return ConversionTestResult(
                egif=egif,
                success=success,
                original_structure=original_structure,
                yaml_size=yaml_size,
                conversion_time=conversion_time,
                round_trip_success=round_trip_success,
                structural_integrity=structural_integrity,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            conversion_time = time.time() - start_time
            errors.append(f"Conversion failed: {str(e)}")
            
            return ConversionTestResult(
                egif=egif,
                success=False,
                original_structure={'vertices': 0, 'edges': 0, 'cuts': 0},
                yaml_size=0,
                conversion_time=conversion_time,
                round_trip_success=False,
                structural_integrity=False,
                errors=errors,
                warnings=warnings
            )
    
    def _verify_structural_integrity(self, original_egi, restored_basic, restored_improved) -> bool:
        """Verify structural integrity of restored EGIs."""
        
        try:
            # Check basic restoration
            if restored_basic is None:
                return False
            
            basic_match = (
                len(original_egi.vertices) == len(restored_basic.vertices) and
                len(original_egi.edges) == len(restored_basic.edges) and
                len(original_egi.cuts) == len(restored_basic.cuts)
            )
            
            # Check improved restoration
            if restored_improved is None:
                return basic_match
            
            improved_match = (
                len(original_egi.vertices) == len(restored_improved.vertices) and
                len(original_egi.edges) == len(restored_improved.edges) and
                len(original_egi.cuts) == len(restored_improved.cuts)
            )
            
            return basic_match and improved_match
            
        except Exception:
            return False
    
    def _compare_yaml_structures(self, yaml1: str, yaml2: str) -> bool:
        """Compare YAML structures ignoring ID differences."""
        
        try:
            import yaml
            
            # Parse both YAML strings
            data1 = yaml.safe_load(yaml1)
            data2 = yaml.safe_load(yaml2)
            
            # Compare structural elements (ignoring specific IDs)
            egi1 = data1['egi']
            egi2 = data2['egi']
            
            # Compare counts
            structure1 = {
                'vertices': len(egi1.get('vertices', [])),
                'edges': len(egi1.get('edges', [])),
                'cuts': len(egi1.get('cuts', [])),
                'ligatures': len(egi1.get('ligatures', []))
            }
            
            structure2 = {
                'vertices': len(egi2.get('vertices', [])),
                'edges': len(egi2.get('edges', [])),
                'cuts': len(egi2.get('cuts', [])),
                'ligatures': len(egi2.get('ligatures', []))
            }
            
            return structure1 == structure2
            
        except Exception:
            return False
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report."""
        
        if not self.test_results:
            return "No test results available"
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        round_trip_success = sum(1 for r in self.test_results if r.round_trip_success)
        structural_integrity = sum(1 for r in self.test_results if r.structural_integrity)
        
        total_errors = sum(len(r.errors) for r in self.test_results)
        total_warnings = sum(len(r.warnings) for r in self.test_results)
        
        avg_conversion_time = sum(r.conversion_time for r in self.test_results) / total_tests
        total_yaml_size = sum(r.yaml_size for r in self.test_results)
        
        report = []
        report.append("=" * 70)
        report.append("BIDIRECTIONAL YAML CONVERSION TEST REPORT")
        report.append("=" * 70)
        report.append("")
        
        # Overall Statistics
        report.append("📊 OVERALL STATISTICS")
        report.append("-" * 30)
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Successful Conversions: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        report.append(f"Round-trip Success: {round_trip_success}/{total_tests} ({round_trip_success/total_tests*100:.1f}%)")
        report.append(f"Structural Integrity: {structural_integrity}/{total_tests} ({structural_integrity/total_tests*100:.1f}%)")
        report.append(f"Total Errors: {total_errors}")
        report.append(f"Total Warnings: {total_warnings}")
        report.append("")
        
        # Performance Statistics
        report.append("⚡ PERFORMANCE STATISTICS")
        report.append("-" * 30)
        report.append(f"Average Conversion Time: {avg_conversion_time:.3f} seconds")
        report.append(f"Total YAML Size: {total_yaml_size:,} bytes")
        report.append(f"Average YAML Size: {total_yaml_size/total_tests:.0f} bytes")
        report.append("")
        
        # Success Rate Analysis
        report.append("🎯 SUCCESS RATE ANALYSIS")
        report.append("-" * 30)
        
        if successful_tests == total_tests:
            report.append("✅ EXCELLENT: Perfect conversion success rate")
        elif successful_tests >= total_tests * 0.9:
            report.append("🎯 VERY GOOD: High conversion success rate")
        elif successful_tests >= total_tests * 0.75:
            report.append("⚠️ GOOD: Moderate conversion success rate")
        else:
            report.append("❌ NEEDS WORK: Low conversion success rate")
        
        if round_trip_success == total_tests:
            report.append("✅ EXCELLENT: Perfect round-trip consistency")
        elif round_trip_success >= total_tests * 0.9:
            report.append("🎯 VERY GOOD: High round-trip consistency")
        else:
            report.append("⚠️ ISSUES: Round-trip consistency problems")
        
        report.append("")
        
        # Detailed Results
        report.append("📋 DETAILED TEST RESULTS")
        report.append("-" * 30)
        
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result.success else "❌"
            round_trip = "🔄" if result.round_trip_success else "⚠️"
            integrity = "🏗️" if result.structural_integrity else "⚠️"
            
            report.append(f"Test {i:2d}: {status} {round_trip} {integrity} {result.egif}")
            report.append(f"         Structure: {result.original_structure}")
            report.append(f"         Time: {result.conversion_time:.3f}s, Size: {result.yaml_size} bytes")
            
            if result.errors:
                report.append(f"         Errors: {len(result.errors)}")
            if result.warnings:
                report.append(f"         Warnings: {len(result.warnings)}")
            
            report.append("")
        
        # Recommendations
        report.append("🔧 RECOMMENDATIONS")
        report.append("-" * 30)
        
        if successful_tests == total_tests and round_trip_success == total_tests:
            report.append("🚀 PRODUCTION READY")
            report.append("• YAML conversion system is fully functional")
            report.append("• Perfect bidirectional conversion achieved")
            report.append("• Ready for production use and data persistence")
        elif successful_tests >= total_tests * 0.9:
            report.append("🔧 MINOR IMPROVEMENTS NEEDED")
            report.append("• Address remaining conversion failures")
            report.append("• Improve round-trip consistency")
            report.append("• Consider production deployment after fixes")
        else:
            report.append("🛠️ SIGNIFICANT DEVELOPMENT NEEDED")
            report.append("• Fix major conversion issues")
            report.append("• Improve structural integrity validation")
            report.append("• Enhance error handling and recovery")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    """Main test execution."""
    
    tester = BidirectionalYAMLTester()
    
    # Run comprehensive test suite
    results = tester.run_comprehensive_test_suite()
    
    # Generate and print report
    report = tester.generate_test_report()
    print(report)
    
    # Return appropriate exit code
    successful_tests = sum(1 for r in results if r.success)
    if successful_tests == len(results):
        print("🎉 ALL TESTS PASSED - YAML CONVERSION SYSTEM READY!")
        return 0
    else:
        failed_tests = len(results) - successful_tests
        print(f"⚠️ {failed_tests} TESTS FAILED - REVIEW NEEDED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

