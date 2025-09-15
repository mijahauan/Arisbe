#!/bin/bash
# Context Check Script - Run before implementing new features
# This script helps avoid reinventing existing solutions

PROBLEM="$1"

if [ -z "$PROBLEM" ]; then
    echo "Usage: $0 '<problem description>'"
    echo "Example: $0 'polarity calculation'"
    exit 1
fi

echo "🔍 Checking existing solutions for: $PROBLEM"
echo "="*50

# Check 1: polarity calculation: Check existing HierarchicalIndex.get_polarity() O(1) solution
if echo "$PROBLEM" | grep -iE "(polarity|positive|negative|area polarity)" > /dev/null; then
    echo "⚠️  🔍 BEFORE implementing polarity calculation: Check existing HierarchicalIndex.get_polarity() O(1) solution"
    echo "Run these commands:"
    echo "  python tools/function_lookup.py "polarity""
    echo "  grep -n "get_polarity\|calculate.*polarity" src/*.py"
    echo ""
fi

# Check 2: hierarchy/nesting: Check existing HierarchicalIndex and spatial indexing solutions
if echo "$PROBLEM" | grep -iE "(hierarchy|nesting|containment|depth|level)" > /dev/null; then
    echo "⚠️  🔍 BEFORE implementing hierarchy/nesting: Check existing HierarchicalIndex and spatial indexing solutions"
    echo "Run these commands:"
    echo "  python tools/function_lookup.py "hierarchy""
    echo "  python tools/architectural_mapper.py | grep -i hierarchy"
    echo ""
fi

# Check 3: transformation: Check formal_transformation_rules.py and transformation wizard patterns
if echo "$PROBLEM" | grep -iE "(transformation|rule|apply|transform)" > /dev/null; then
    echo "⚠️  🔍 BEFORE implementing transformation: Check formal_transformation_rules.py and transformation wizard patterns"
    echo "Run these commands:"
    echo "  python tools/pattern_catalog.py | grep -A5 "Transformation""
    echo "  python tools/function_lookup.py "transformation""
    echo ""
fi

# Check 4: spatial operations: Check R-tree indexing in legacy/ directory
if echo "$PROBLEM" | grep -iE "(spatial|bounds|containment|region|area)" > /dev/null; then
    echo "⚠️  🔍 BEFORE implementing spatial operations: Check R-tree indexing in legacy/ directory"
    echo "Run these commands:"
    echo "  python tools/function_lookup.py "spatial""
    echo "  ls src/legacy/*spatial* src/legacy/*rtree*"
    echo ""
fi

# Check 5: GUI: Check existing PySide6 patterns and transformation wizard system
if echo "$PROBLEM" | grep -iE "(gui|dialog|wizard|interface|user)" > /dev/null; then
    echo "⚠️  🔍 BEFORE implementing GUI: Check existing PySide6 patterns and transformation wizard system"
    echo "Run these commands:"
    echo "  python tools/pattern_catalog.py | grep -A5 "User Interface""
    echo "  find src/gui -name "*.py" | head -5"
    echo ""
fi

# Check 6: 🔍 BEFORE optimizing: Check existing O(1) solutions and performance patterns
if echo "$PROBLEM" | grep -iE "(performance|efficient|fast|o(1)|lookup)" > /dev/null; then
    echo "⚠️  🔍 BEFORE optimizing: Check existing O(1) solutions and performance patterns"
    echo "Run these commands:"
    echo "  python tools/function_lookup.py --o1"
    echo "  python tools/pattern_catalog.py | grep -A3 "Performance""
    echo ""
fi

# Check 7: indexing: Check existing indexing systems (HierarchicalIndex, R-tree, corpus index)
if echo "$PROBLEM" | grep -iE "(index|search|find|lookup|query)" > /dev/null; then
    echo "⚠️  🔍 BEFORE implementing indexing: Check existing indexing systems (HierarchicalIndex, R-tree, corpus index)"
    echo "Run these commands:"
    echo "  python tools/semantic_code_analyzer.py | grep -A5 "cluster""
    echo "  python tools/function_lookup.py "index""
    echo ""
fi

echo "💡 Always check:"
echo "  1. python tools/function_lookup.py '<your problem>'"
echo "  2. python tools/architectural_mapper.py (for subsystem guidance)"
echo "  3. python tools/pattern_catalog.py (for established patterns)"
echo "  4. python tools/semantic_code_analyzer.py (for relationships)"
