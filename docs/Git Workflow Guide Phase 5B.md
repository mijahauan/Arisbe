# Git Workflow Guide: Phase 5B Halt & Architecture Rework

## 🎯 **Situation Analysis**

You're in a common but critical software development scenario:
- **Phase 5B branch**: Contains GUI work that needs to be halted (but preserved)
- **Fundamental architecture issue**: Requires rework of Phases 1-4
- **Need clean workflow**: To manage the transition properly

## 📋 **Recommended Git Strategy**

### **Step 1: Preserve Phase 5B Work**
First, let's properly document and preserve your Phase 5B work:

```bash
# Ensure you're on your Phase 5B branch
git status
git branch

# Commit any uncommitted changes
git add .
git commit -m "Phase 5B: Final state before architectural rework

- Implemented PySide6 GUI with Bullpen tools
- Fixed predicate visual appearance (rectangular)
- Identified fundamental hypergraph mapping issue
- HALT: Architecture rework required before continuing"

# Push the branch to preserve it remotely
git push origin feature/phase5b-pyside6-gui
```

### **Step 2: Create Architecture Rework Branch**
Create a new branch for the fundamental rework:

```bash
# Switch to main/master branch (clean starting point)
git checkout main  # or master, depending on your default branch

# Create and switch to architecture rework branch
git checkout -b rework/hypergraph-architecture

# Push the new branch
git push -u origin rework/hypergraph-architecture
```

### **Step 3: Document the Transition**
Create a clear record of what's happening:

```bash
# Create a rework documentation file
echo "# Architecture Rework: Hypergraph Mapping Correction

## Issue Identified
- Fundamental hypergraph mapping error in Phases 1-4
- Nodes/Edges mapped backwards (Predicates↔Entities)
- Phase 5B GUI built on flawed foundation

## Rework Plan
- Phase 1-2: Correct data structures
- Phase 3: Fix CLIF parsing
- Phase 4: Rebuild rendering system
- Phase 5: Return to GUI with solid foundation

## Branch Strategy
- feature/phase5b-pyside6-gui: Preserved GUI work (HALTED)
- rework/hypergraph-architecture: Architecture fixes (ACTIVE)
" > ARCHITECTURE_REWORK.md

git add ARCHITECTURE_REWORK.md
git commit -m "Document architecture rework plan and branch strategy"
```

## 🔄 **Development Workflow During Rework**

### **Working on the Rework Branch**
```bash
# Daily workflow on rework branch
git checkout rework/hypergraph-architecture

# Make changes to core architecture
# ... edit files ...

# Commit frequently with clear messages
git add src/
git commit -m "Phase 1: Redesign EGGraph with correct hypergraph mapping

- Entities as nodes (Lines of Identity)
- Predicates as hyperedges (Relations)
- Update core data structures"

# Push regularly
git push origin rework/hypergraph-architecture
```

### **Phase-by-Phase Commits**
Structure your commits to match the rework phases:

```bash
# Phase 1 completion
git commit -m "Phase 1 COMPLETE: Core data structures redesigned

- EGGraph now uses correct hypergraph mapping
- Entity class represents Lines of Identity
- Predicate class represents relations
- Context class for logical scopes
- All tests passing"

# Phase 2 completion  
git commit -m "Phase 2 COMPLETE: CLIF parser rewritten

- Correct entity extraction from variables/constants
- Proper predicate parsing with arity
- Quantifier scope mapping to contexts
- Bidirectional CLIF↔EG translation working"
```

## 🔀 **Branch Management Strategy**

### **Current Branch Structure**
```
main/master
├── feature/phase5b-pyside6-gui (PRESERVED - do not continue)
└── rework/hypergraph-architecture (ACTIVE - current work)
```

### **Future Branch Strategy**
After rework completion:

```bash
# When architecture rework is complete and tested
git checkout main
git merge rework/hypergraph-architecture
git push origin main

# Create new Phase 5B branch with correct foundation
git checkout -b feature/phase5b-v2-correct-architecture
git push -u origin feature/phase5b-v2-correct-architecture
```

## 📊 **Tracking Progress**

### **Use Issues/Milestones**
If using GitHub/GitLab, create issues for each phase:

```bash
# Create issues for tracking
- Issue #1: "Phase 1: Redesign core data structures"
- Issue #2: "Phase 2: Rewrite CLIF parser" 
- Issue #3: "Phase 3: Rebuild rendering system"
- Issue #4: "Phase 4: Implement constraints and transformations"
```

### **Tag Important Milestones**
```bash
# Tag when each phase is complete
git tag -a "rework-phase1-complete" -m "Phase 1: Core data structures redesigned"
git push origin rework-phase1-complete

git tag -a "rework-phase2-complete" -m "Phase 2: CLIF parser rewritten"
git push origin rework-phase2-complete
```

## 🔍 **Referencing Phase 5B Work**

### **When You Need to Reference GUI Code**
```bash
# View Phase 5B files without switching branches
git show feature/phase5b-pyside6-gui:gui/widgets/graph_canvas.py

# Compare approaches
git diff feature/phase5b-pyside6-gui:src/graph.py rework/hypergraph-architecture:src/graph.py

# Cherry-pick specific commits if needed (rare)
git cherry-pick <commit-hash>
```

### **Extract Useful Components**
```bash
# Copy specific files from Phase 5B if they're still useful
git checkout feature/phase5b-pyside6-gui -- gui/widgets/graph_builder_palette.py
git add gui/widgets/graph_builder_palette.py
git commit -m "Adapt: Import graph builder palette from Phase 5B

- Extracted from halted Phase 5B branch
- Will be adapted for correct architecture
- Original implementation preserved in feature/phase5b-pyside6-gui"
```

## ⚠️ **Important Guidelines**

### **DO NOT:**
- ❌ Continue development on `feature/phase5b-pyside6-gui`
- ❌ Delete the Phase 5B branch (preserve the work)
- ❌ Merge Phase 5B into main (it's built on wrong architecture)
- ❌ Try to "fix" Phase 5B incrementally (fundamental issue)

### **DO:**
- ✅ Work exclusively on `rework/hypergraph-architecture`
- ✅ Commit frequently with clear phase markers
- ✅ Test thoroughly at each phase completion
- ✅ Document the rework process clearly
- ✅ Reference Phase 5B work when useful

## 🎯 **Success Criteria**

### **Rework Branch Ready for Phase 5B v2 When:**
- ✅ All core data structures use correct hypergraph mapping
- ✅ CLIF parser works with proper entity/predicate extraction
- ✅ Rendering system displays authentic EG notation
- ✅ Constraint system enforces logical rules
- ✅ All existing tests pass with new architecture
- ✅ New tests validate correct hypergraph behavior

### **Then Create Phase 5B v2:**
```bash
git checkout main
git merge rework/hypergraph-architecture
git checkout -b feature/phase5b-v2-correct-architecture
# Start GUI development on solid foundation
```

This workflow preserves your work, provides a clean rework path, and sets up for successful GUI development on the correct architectural foundation.



## 🚀 **Immediate Action Commands**

### **Right Now - Execute These Commands:**

```bash
# 1. Check your current status
git status
git branch -v

# 2. Commit any uncommitted Phase 5B work
git add .
git commit -m "Phase 5B: Final commit before architecture rework

- Applied predicate visual fix (rectangular)
- Identified fundamental hypergraph mapping issue
- HALT: Requires architecture rework of Phases 1-4
- Preserving GUI work for future reference"

# 3. Push Phase 5B branch to preserve it
git push origin feature/phase5b-pyside6-gui

# 4. Switch to main branch (clean starting point)
git checkout main

# 5. Create architecture rework branch
git checkout -b rework/hypergraph-architecture

# 6. Create documentation file
cat > ARCHITECTURE_REWORK.md << 'EOF'
# Architecture Rework: Hypergraph Mapping Correction

## Critical Issue Identified
- **Fundamental Error**: Hypergraph mapping implemented backwards
- **Wrong**: Nodes→Predicates, Edges→Ligatures  
- **Correct**: Nodes→Entities (Lines of Identity), Edges→Predicates (Relations)

## Impact
- All graph rendering incorrect
- CLIF parsing produces wrong structures
- Logical constraints don't work
- Phase 5B GUI built on flawed foundation

## Rework Plan
1. **Phase 1**: Redesign core data structures (src/eg_types.py, src/graph.py)
2. **Phase 2**: Rewrite CLIF parser (src/clif_parser.py)
3. **Phase 3**: Rebuild rendering system (src/transformations.py)
4. **Phase 4**: Implement proper constraints and game engine
5. **Phase 5**: Return to GUI with correct foundation

## Branch Strategy
- `feature/phase5b-pyside6-gui`: Preserved GUI work (HALTED)
- `rework/hypergraph-architecture`: Architecture fixes (ACTIVE)

## Success Criteria
- Correct hypergraph mapping throughout system
- Authentic Peirce EG notation and behavior
- Solid foundation for professional GUI
EOF

# 7. Commit the rework plan
git add ARCHITECTURE_REWORK.md
git commit -m "Initialize architecture rework branch

- Document hypergraph mapping correction plan
- Establish branch strategy for rework
- Ready to begin Phase 1 redesign"

# 8. Push the new rework branch
git push -u origin rework/hypergraph-architecture

# 9. Verify your setup
git branch -v
echo "✅ Setup complete. Ready to begin architecture rework."
```

### **Verification Commands:**
```bash
# Check that you have both branches
git branch -a

# Should show:
# * rework/hypergraph-architecture
#   feature/phase5b-pyside6-gui
#   main

# Verify Phase 5B work is preserved
git log --oneline feature/phase5b-pyside6-gui -5

# Verify you're on the rework branch
git branch --show-current
# Should output: rework/hypergraph-architecture
```

## 📋 **Next Steps After Setup**

1. **Begin Phase 1**: Start with `src/eg_types.py` and `src/graph.py`
2. **Focus on data structures**: Implement correct hypergraph mapping
3. **Test incrementally**: Ensure each change maintains system integrity
4. **Commit frequently**: Clear messages marking progress through phases

**You're now set up for a clean, professional rework that will create the solid foundation your EG-HG system needs!**

