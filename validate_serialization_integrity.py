#!/usr/bin/env python
"""
Serialization Integrity Validator

Standalone script to validate EGDF serialization system integrity.
Can be run as part of CI/CD or pre-commit hooks.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def main():
    """Main validation function."""
    print("🔍 Validating EGDF Serialization Integrity")
    print("=" * 45)
    
    try:
        from egdf_structural_lock import EGDFStructuralProtector
        
        protector = EGDFStructuralProtector()
        
        # Check if lock exists
        if not protector.lock_file.exists():
            print("❌ No structural protection lock found")
            print("   Run: cd src && python egdf_structural_lock.py")
            return 1
        
        # Validate integrity
        is_valid, errors = protector.validate_structural_integrity()
        
        if is_valid:
            print("✅ SERIALIZATION INTEGRITY VALIDATED")
            
            # Show status
            status = protector.status_report()
            print(f"   Lock created: {status['lock_created']}")
            print(f"   Test vectors: {status['test_vectors']}")
            print(f"   Baseline success: {status['baseline_success_rate']}")
            print("🛡️  EGDF YAML/JSON serialization is structurally protected")
            return 0
        else:
            print("❌ SERIALIZATION INTEGRITY COMPROMISED")
            for error in errors:
                print(f"   • {error}")
            print("\n⚠️  Serialization system may have been corrupted!")
            print("   This could indicate:")
            print("   - Code regression in serialization components")
            print("   - Unintended changes to critical algorithms")
            print("   - Import/dependency issues")
            return 1
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
