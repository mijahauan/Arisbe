#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from clif_parser_dau import parse_clif
    from clif_generator_dau import generate_clif
    print("Imports successful")
    
    # Simple test
    clif_text = "(Loves Socrates Plato)"
    print(f"Parsing: {clif_text}")
    
    egi = parse_clif(clif_text)
    print(f"Parse successful, EGI type: {type(egi)}")
    
    generated = generate_clif(egi)
    print(f"Generated CLIF: {generated}")
    
except Exception as e:
    import traceback
    print("Error occurred:")
    traceback.print_exc()
