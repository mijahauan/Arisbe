#!/usr/bin/env python3
"""
Validate the EGRF v3.0 corpus examples.

This script validates all examples in the corpus against the EG-HG and CLIF
representations to ensure logical correctness.
"""

import os
import sys
import argparse
from src.egrf.v3.corpus_validator import validate_corpus


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Validate EGRF v3.0 corpus examples.')
    parser.add_argument('--corpus-root', '-c', default='corpus',
                        help='Root directory of the corpus (default: corpus)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print verbose output')
    
    args = parser.parse_args()
    
    corpus_root = os.path.abspath(args.corpus_root)
    
    print(f"Validating corpus at {corpus_root}...")
    
    valid_count, total_count, errors = validate_corpus(corpus_root)
    
    print(f"\nValidation complete: {valid_count}/{total_count} examples valid")
    
    if errors:
        print(f"\n{len(errors)} examples have errors:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("\nAll examples are valid!")
        sys.exit(0)


if __name__ == '__main__':
    main()

