# How to Remember to Use the Layered Strategy

## 1. Pre-Implementation Checklist

Before implementing ANY new functionality, run:
```bash
./tools/context_check.sh '<problem description>'
```

## 2. IDE Integration

Add these as IDE snippets or shortcuts:

### Quick Function Lookup
```bash
python tools/function_lookup.py "$SELECTION"
```

### Architecture Check
```bash
python tools/architectural_mapper.py | grep -i "$CONCEPT"
```

### Pattern Check
```bash
python tools/pattern_catalog.py | grep -A5 "$PROBLEM"
```

## 3. Memory Triggers

Set up these memory triggers:

### 🔍 BEFORE implementing polarity calculation: Check existing HierarchicalIndex.get_polarity() O(1) solution
**Triggers**: polarity, positive, negative, area polarity
**Priority**: high
**Commands**:
- `python tools/function_lookup.py "polarity"`
- `grep -n "get_polarity\|calculate.*polarity" src/*.py`

### 🔍 BEFORE implementing hierarchy/nesting: Check existing HierarchicalIndex and spatial indexing solutions
**Triggers**: hierarchy, nesting, containment, depth, level
**Priority**: high
**Commands**:
- `python tools/function_lookup.py "hierarchy"`
- `python tools/architectural_mapper.py | grep -i hierarchy`

### 🔍 BEFORE implementing transformation: Check formal_transformation_rules.py and transformation wizard patterns
**Triggers**: transformation, rule, apply, transform
**Priority**: high
**Commands**:
- `python tools/pattern_catalog.py | grep -A5 "Transformation"`
- `python tools/function_lookup.py "transformation"`

### 🔍 BEFORE implementing spatial operations: Check R-tree indexing in legacy/ directory
**Triggers**: spatial, bounds, containment, region, area
**Priority**: medium
**Commands**:
- `python tools/function_lookup.py "spatial"`
- `ls src/legacy/*spatial* src/legacy/*rtree*`

### 🔍 BEFORE implementing GUI: Check existing PySide6 patterns and transformation wizard system
**Triggers**: gui, dialog, wizard, interface, user
**Priority**: medium
**Commands**:
- `python tools/pattern_catalog.py | grep -A5 "User Interface"`
- `find src/gui -name "*.py" | head -5`

### 🔍 BEFORE optimizing: Check existing O(1) solutions and performance patterns
**Triggers**: performance, efficient, fast, o(1), lookup
**Priority**: high
**Commands**:
- `python tools/function_lookup.py --o1`
- `python tools/pattern_catalog.py | grep -A3 "Performance"`

### 🔍 BEFORE implementing indexing: Check existing indexing systems (HierarchicalIndex, R-tree, corpus index)
**Triggers**: index, search, find, lookup, query
**Priority**: medium
**Commands**:
- `python tools/semantic_code_analyzer.py | grep -A5 "cluster"`
- `python tools/function_lookup.py "index"`

## 4. Automated Integration

### Git Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
# Check for potential reinvention
git diff --cached --name-only | grep '\.py$' | while read file; do
    if git diff --cached "$file" | grep -E '(def|class).*polarity|hierarchy|transformation'; then
        echo "⚠️  Check existing solutions before implementing polarity/hierarchy/transformation"
        echo "Run: python tools/function_lookup.py '<your concept>'"
    fi
done
```

### VS Code Integration
Add to `.vscode/tasks.json`:
```json
{
    "label": "Check Existing Solutions",
    "type": "shell",
    "command": "python",
    "args": ["tools/function_lookup.py", "${selectedText}"],
    "group": "build"
}
```

## 5. Memory System Integration

The key is to make checking existing solutions **easier than implementing from scratch**.

### Quick Commands (add to .bashrc/.zshrc)
```bash
alias arisbe-check='python tools/function_lookup.py'
alias arisbe-arch='python tools/architectural_mapper.py'
alias arisbe-patterns='python tools/pattern_catalog.py'
```

### Development Workflow
1. **Problem identified** → Run context check
2. **Existing solution found** → Use it
3. **No solution found** → Implement + document pattern
4. **Update tools** → Add new pattern to catalog
