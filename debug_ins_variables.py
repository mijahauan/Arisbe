#!/usr/bin/env python3
"""
Debug script to understand variable scoping in INS rule
"""

from src.egif_parser_dau import parse_egif
import re

# Test the problematic case
egif = "*x ~[ (P x) ] ~[ (Q x) ]"
print(f"Original EGIF: {egif}")

# Test new variable extraction logic using regex
var_pattern = r'\*([a-zA-Z][a-zA-Z0-9_]*)'
logical_vars = re.findall(var_pattern, egif)
print(f"Logical vars found: {logical_vars}")

# Test context EGIF creation
insertion_spec = "~[ (R x)]"
if logical_vars:
    existing_var_decls = [f"*{var}" for var in set(logical_vars)]
    context_egif = f"{' '.join(existing_var_decls)} {insertion_spec}"
    print(f"Context EGIF: {context_egif}")
    
    try:
        temp_full_egi = parse_egif(context_egif)
        print("✓ Context EGIF parsed successfully")
        print(f"New vertices: {[v.id for v in temp_full_egi.V]}")
        print(f"New edges: {[e.id for e in temp_full_egi.E]}")
        print(f"New cuts: {[c.id for c in temp_full_egi.Cut]}")
    except Exception as e:
        print(f"✗ Context EGIF parsing failed: {e}")

# Test direct parsing
try:
    direct_egi = parse_egif(insertion_spec)
    print("✓ Direct parsing succeeded")
except Exception as e:
    print(f"✗ Direct parsing failed: {e}")
