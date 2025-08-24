#!/usr/bin/env python3
"""
PDF specification reader for Common Logic and CGIF documents.
Uses PyPDF2 to extract text from specification PDFs.
"""

import PyPDF2
import os
from typing import List, Dict


def read_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def extract_clif_syntax_rules(pdf_text: str) -> List[str]:
    """Extract CLIF syntax rules from Common Logic specification."""
    rules = []
    lines = pdf_text.split('\n')
    
    # Look for syntax sections
    in_syntax_section = False
    for line in lines:
        line = line.strip()
        if 'syntax' in line.lower() or 'grammar' in line.lower():
            in_syntax_section = True
        elif line.startswith('::=') or '::=' in line:
            rules.append(line)
        elif in_syntax_section and line and not line.isspace():
            if any(keyword in line.lower() for keyword in ['forall', 'exists', 'and', 'or', 'not', 'atom']):
                rules.append(line)
    
    return rules


def extract_cgif_syntax_rules(pdf_text: str) -> List[str]:
    """Extract CGIF syntax rules from specification."""
    rules = []
    lines = pdf_text.split('\n')
    
    # Look for CGIF-specific syntax
    for line in lines:
        line = line.strip()
        if any(keyword in line for keyword in ['[', ']', ':', '->', '<-', 'concept', 'relation']):
            rules.append(line)
    
    return rules


def main():
    """Read and analyze PDF specifications."""
    docs_dir = "docs/references"
    
    # Read Common Logic specification
    common_logic_path = os.path.join(docs_dir, "Common_Logic_final.pdf")
    if os.path.exists(common_logic_path):
        print("=== Reading Common Logic Specification ===")
        cl_text = read_pdf_text(common_logic_path)
        print(f"Extracted {len(cl_text)} characters")
        
        clif_rules = extract_clif_syntax_rules(cl_text)
        print(f"\nFound {len(clif_rules)} CLIF syntax rules:")
        for rule in clif_rules[:10]:  # Show first 10
            print(f"  {rule}")
        
        # Save extracted text
        with open("common_logic_extracted.txt", "w") as f:
            f.write(cl_text)
        print("\nFull text saved to common_logic_extracted.txt")
    
    # Look for CGIF specifications
    cgif_files = [f for f in os.listdir(docs_dir) if 'cgif' in f.lower() or 'conceptual' in f.lower()]
    for cgif_file in cgif_files:
        if cgif_file.endswith('.pdf'):
            print(f"\n=== Reading {cgif_file} ===")
            cgif_path = os.path.join(docs_dir, cgif_file)
            cgif_text = read_pdf_text(cgif_path)
            print(f"Extracted {len(cgif_text)} characters")
            
            cgif_rules = extract_cgif_syntax_rules(cgif_text)
            print(f"Found {len(cgif_rules)} CGIF syntax elements")
            
            # Save extracted text
            output_name = cgif_file.replace('.pdf', '_extracted.txt')
            with open(output_name, "w") as f:
                f.write(cgif_text)
            print(f"Full text saved to {output_name}")


if __name__ == "__main__":
    main()
