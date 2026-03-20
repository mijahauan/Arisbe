# 🚨 COHERENCE FRAMEWORK ACTIVE - READ THIS FIRST! 🚨

**If you're seeing this file, you've likely forgotten about the coherence framework.**

## 🎯 **WHAT IS THE COHERENCE FRAMEWORK?**

The **Arisbe Coherence Framework** is an **automated quality assurance and documentation system** that:

1. **🔒 PROTECTS THE CORE** - 16 validated modules with 87 passing tests
2. **📚 ELIMINATES GUESSWORK** - Complete API documentation for all core functions
3. **🛡️ PREVENTS BREAKAGE** - Quality gates block commits that break validated functionality
4. **📊 PROVIDES VISIBILITY** - Daily quality dashboard shows system health

## 🚨 **IMMEDIATE ACTIONS WHEN YOU'VE FORGOTTEN:**

### **1. CHECK SYSTEM STATUS**
```bash
# Get current quality status
python tools/daily_quality_dashboard.py

# Check core protection status  
python tools/core_protection_system.py --report
```

### **2. REVIEW API DOCUMENTATION**
- **`ARISBE_CORE_API_REFERENCE.md`** - Complete API signatures (NO MORE GUESSING!)
- **`CORE_API_USAGE_GUIDE.md`** - Usage patterns and examples
- **`CORE_PROTECTION_FRAMEWORK.md`** - What's protected and why

### **3. UNDERSTAND WHAT'S VALIDATED**
- **87 core tests passing** - Mathematical foundation is solid
- **16 protected modules** - Core API is stable and documented
- **0 failing tests** - System is in excellent health

## 🔍 **QUICK CONTEXT RECOVERY**

### **What You Can Trust:**
```python
# These are VALIDATED and DOCUMENTED:
from egi_core_dau import create_empty_graph, create_vertex, create_edge
from egi_io import save_egi_json, load_egi_json
from formal_transformation_rules import DeiterationRule, TransformationContext
from syntactic_equivalence_checker import SyntacticEquivalenceChecker

# NEW: DiagramController with layered Command pattern architecture
from diagram_controller import (
    DiagramController, CommandExecutor,
    OrganonCommands, ErgasterionCommands, AgonCommands
)

# Exact signatures available in ARISBE_CORE_API_REFERENCE.md
```

### **What's Protected:**
- **Core modules** (16) - Cannot be modified without authorization
- **API signatures** - Changing them requires explicit override
- **Test suite** - All 87 core tests must pass

### **What's Available:**
- **Complete API documentation** - Every function signature documented
- **Usage patterns** - Common development patterns provided
- **Quality monitoring** - Daily dashboard and protection system

## 🚀 **HOW TO USE THE FRAMEWORK:**

### **For Development:**
1. **Check API docs FIRST** - Don't guess at function signatures
2. **Run quality checks** - `python tools/quality_gate_system.py`
3. **Use documented patterns** - Follow examples in usage guide

### **For Commits:**
1. **Quality gates run automatically** - They'll catch issues
2. **Core protection active** - Unauthorized core changes blocked
3. **All tests must pass** - 87 core tests validate foundation

### **For Context Recovery:**
1. **Daily dashboard** - Current system health
2. **API reference** - What functions exist and how to use them
3. **Protection report** - What's safe to modify

## 📋 **COHERENCE FRAMEWORK FILES (SELF-DISCOVERY):**

### **📚 Documentation:**
- `ARISBE_CORE_API_REFERENCE.md` - **COMPLETE API DOCUMENTATION**
- `CORE_API_USAGE_GUIDE.md` - Usage patterns and examples
- `CORE_PROTECTION_FRAMEWORK.md` - Protection strategy
- `COHERENCE_FRAMEWORK_SUCCESS_SUMMARY.md` - Framework validation results

### **🔧 Tools:**
- `tools/daily_quality_dashboard.py` - System health monitoring
- `tools/core_protection_system.py` - Core protection enforcement
- `tools/extract_core_api.py` - API documentation generator
- `tools/quality_gate_system.py` - Quality enforcement

### **📊 Reports:**
- `CORE_CAPABILITIES_AND_COHERENCE_ANALYSIS.md` - What actually works
- Quality reports in `quality_reports/` directory

## ⚠️ **CRITICAL REMINDERS:**

### **DON'T:**
- ❌ Guess at function signatures (they're documented!)
- ❌ Modify core modules without authorization
- ❌ Bypass quality gates (they prevent real issues)
- ❌ Ignore failing tests (they indicate real problems)

### **DO:**
- ✅ Check API documentation first
- ✅ Use documented usage patterns  
- ✅ Run quality checks before committing
- ✅ Trust the 87 validated core tests

## 🎯 **BOTTOM LINE:**

**The coherence framework has transformed Arisbe from a codebase with accumulating technical debt into a well-monitored, quality-assured, production-ready system with comprehensive documentation.**

**You have 87 validated core tests, 16 protected modules, and complete API documentation. USE THEM!**

---

**Next time you forget: Look for files with "COHERENCE" in the name - they'll remind you of this system.**
