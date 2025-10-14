#!/usr/bin/env python3
"""
Validate Architecture Documentation

Checks architecture documents against actual code structure to detect drift.
Ensures documentation stays synchronized with implementation.

USAGE:
    python tools/validate_architecture_docs.py
    python tools/validate_architecture_docs.py --doc BOTTOM_UP_D3_ARCHITECTURE.md
    
Scans architecture docs for claims about code structure and validates them.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import argparse


class ArchitectureValidator:
    """Validates architecture documentation against code."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        
        # Findings
        self.validated_claims: List[Tuple[str, str]] = []
        self.invalid_claims: List[Tuple[str, str, str]] = []
        self.warnings: List[Tuple[str, str]] = []
    
    def find_architecture_docs(self) -> List[Path]:
        """Find architecture documentation files."""
        patterns = [
            "*ARCHITECTURE*.md",
            "*DESIGN*.md",
            "*_IMPLEMENTATION*.md"
        ]
        
        docs = []
        for pattern in patterns:
            docs.extend(self.project_root.glob(pattern))
        
        return sorted(set(docs))
    
    def extract_code_references(self, doc_path: Path) -> List[Tuple[int, str, str]]:
        """Extract code references from documentation."""
        if not doc_path.exists():
            return []
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        references = []
        
        # Patterns to detect code references
        patterns = [
            # Module references: src/module_name.py
            (r'`src/([a-z_0-9]+\.py)`', 'module'),
            # Function references: function_name()
            (r'`([a-z_][a-z_0-9]+)\(\)`', 'function'),
            # Class references: ClassName
            (r'`([A-Z][a-zA-Z0-9]+)`', 'class'),
            # File paths
            (r'`([a-z_0-9/]+\.py)`', 'file'),
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, ref_type in patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    ref = match.group(1)
                    references.append((line_num, ref_type, ref))
        
        return references
    
    def validate_module_reference(self, module_name: str) -> bool:
        """Check if a module file exists."""
        if module_name.endswith('.py'):
            module_path = self.src_path / module_name
        else:
            module_path = self.src_path / f"{module_name}.py"
        
        return module_path.exists()
    
    def validate_file_reference(self, file_path: str) -> bool:
        """Check if a file exists."""
        if file_path.startswith('src/'):
            full_path = self.project_root / file_path
        else:
            full_path = self.src_path / file_path
        
        return full_path.exists()
    
    def validate_function_or_class_reference(self, name: str) -> bool:
        """Check if a function or class name exists in codebase."""
        # Search all Python files for this name
        for py_file in self.src_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for class or function definition
                if re.search(rf'\bclass\s+{name}\b', content):
                    return True
                if re.search(rf'\bdef\s+{name}\b', content):
                    return True
            
            except Exception:
                continue
        
        return False
    
    def validate_document(self, doc_path: Path) -> None:
        """Validate all code references in a document."""
        print(f"\n📄 Validating: {doc_path.name}")
        print("=" * 60)
        
        references = self.extract_code_references(doc_path)
        
        if not references:
            print("ℹ️  No code references found in document")
            return
        
        print(f"Found {len(references)} code references")
        
        valid_count = 0
        invalid_count = 0
        
        for line_num, ref_type, ref in references:
            valid = False
            reason = ""
            
            if ref_type == 'module' or ref_type == 'file':
                valid = self.validate_module_reference(ref) or self.validate_file_reference(ref)
                if not valid:
                    reason = f"File not found: {ref}"
            
            elif ref_type in ('function', 'class'):
                valid = self.validate_function_or_class_reference(ref)
                if not valid:
                    reason = f"{ref_type.capitalize()} not found in codebase: {ref}"
            
            if valid:
                self.validated_claims.append((doc_path.name, ref))
                valid_count += 1
            else:
                self.invalid_claims.append((doc_path.name, f"Line {line_num}", reason))
                invalid_count += 1
                print(f"❌ Line {line_num}: {reason}")
        
        if invalid_count == 0:
            print(f"✅ All {valid_count} references validated")
        else:
            print(f"⚠️  {valid_count} valid, {invalid_count} invalid references")
    
    def generate_report(self) -> str:
        """Generate validation report."""
        lines = [
            "# Architecture Documentation Validation Report",
            "",
            f"**Generated**: {self.project_root}",
            "",
        ]
        
        # Summary
        total_claims = len(self.validated_claims) + len(self.invalid_claims)
        lines.extend([
            "## Summary",
            "",
            f"- **Total References**: {total_claims}",
            f"- **Valid**: {len(self.validated_claims)}",
            f"- **Invalid**: {len(self.invalid_claims)}",
            f"- **Warnings**: {len(self.warnings)}",
            "",
        ])
        
        # Invalid claims
        if self.invalid_claims:
            lines.extend([
                "## ❌ Invalid References",
                "",
            ])
            
            for doc, location, reason in self.invalid_claims:
                lines.append(f"- **{doc}** ({location}): {reason}")
            
            lines.append("")
        
        # Warnings
        if self.warnings:
            lines.extend([
                "## ⚠️  Warnings",
                "",
            ])
            
            for doc, warning in self.warnings:
                lines.append(f"- **{doc}**: {warning}")
            
            lines.append("")
        
        # Recommendations
        if self.invalid_claims or self.warnings:
            lines.extend([
                "## Recommendations",
                "",
                "1. Update documentation to reflect current code structure",
                "2. Remove references to deleted modules/classes/functions",
                "3. Add timestamps to architecture docs: \"Last Validated: YYYY-MM-DD\"",
                "",
            ])
        
        return '\n'.join(lines)
    
    def run(self, specific_doc: Optional[Path] = None) -> bool:
        """Run architecture validation."""
        print("=" * 60)
        print("ARCHITECTURE DOCUMENTATION VALIDATOR")
        print("=" * 60)
        
        # Get documents to validate
        if specific_doc:
            docs = [specific_doc]
        else:
            docs = self.find_architecture_docs()
        
        if not docs:
            print("ℹ️  No architecture documents found")
            return True
        
        print(f"\nFound {len(docs)} architecture document(s)")
        
        # Validate each document
        for doc in docs:
            self.validate_document(doc)
        
        # Generate report
        report = self.generate_report()
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)
        
        # Return success if no invalid claims
        if self.invalid_claims:
            print(f"\n⚠️  Found {len(self.invalid_claims)} invalid reference(s)")
            print("   Documentation may be out of sync with code")
            return False
        else:
            print("\n✅ All architecture documentation validated")
            return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate architecture documentation against code"
    )
    parser.add_argument(
        '--doc',
        type=str,
        default=None,
        help='Specific document to validate (default: all architecture docs)'
    )
    
    args = parser.parse_args()
    
    validator = ArchitectureValidator()
    
    specific_doc = Path(args.doc) if args.doc else None
    success = validator.run(specific_doc=specific_doc)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
