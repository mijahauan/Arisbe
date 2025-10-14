# Current Development Plan

**Last Updated**: 2025-10-13  
**Next Review**: 2025-10-20  
**Status**: Coherence Framework Implementation

---

## 🎯 Active Phase: Coherence Framework Implementation

### Objective
Establish meta-framework to prevent context drift, documentation lag, and code archaeology accumulation.

### Why This Phase
The coherence framework itself suffered from amnesia (forgot about `coherence_framework/` package while analyzing coherence). This demonstrates the critical need for persistent context systems.

### Success Criteria
- [ ] Session state persists between AI sessions
- [ ] Documentation auto-updates on commits
- [ ] Code archaeology automatically detected
- [ ] Component status hierarchy maintained
- [ ] Plan remains visible and current

---

## ✅ Phase 0: Foundation Documents (COMPLETE)

### Completed
- [x] **PRODUCT_VISION.md** - Guiding star document (what/who/why)
- [x] **AI_CONDUCT_GUIDELINES.md** - Professional conduct standards
- [x] **.coherence_session_state.json** - Persistent context tracking
- [x] **CURRENT_PLAN.md** - This document (plan visibility)

### Impact
AI assistants now have immediate context recovery and clear conduct expectations.

---

## 🔄 Phase 1: Session State Automation (IN PROGRESS)

### Active Tasks

#### High Priority
- [ ] **Create WHAT_WORKS_NOW.md** - Auto-generated component index
  - Status hierarchy (Production → Stable → Experimental → Deprecated)
  - Import relationships
  - Last modification dates
  
- [ ] **Implement tools/update_session_state.py** - Auto-update on commits
  - Update last_updated timestamp
  - Add recent accomplishments from git log
  - Track modified files
  
- [ ] **Enhance git pre-commit hook** - Integrate coherence checks
  - Auto-update session state
  - Verify guiding star documents exist
  - Check plan staleness (warn if >14 days)

#### Medium Priority
- [ ] **Implement tools/generate_working_code_index.py**
  - Scan codebase for import relationships
  - Detect orphaned modules
  - Generate WHAT_WORKS_NOW.md automatically
  
- [ ] **Implement tools/detect_code_archaeology.py**
  - Find test_debug_*.py files
  - Detect orphaned modules (no imports)
  - Flag deprecated components
  - Generate CODE_CLEANUP_CANDIDATES.md

### Expected Completion
End of week (2025-10-18)

---

## 📋 Phase 2: Documentation Sync (PLANNED)

### Planned Tasks
- [ ] Auto-regenerate API docs when core modules change
- [ ] Expand API docs to Tier 2 (stable) modules
- [ ] Validate architecture documents against code
- [ ] Add coverage.py to quality gates

### Dependencies
Requires Phase 1 automation infrastructure

### Expected Start
Week of 2025-10-21

---

## 🔮 Future Phases (Backlog)

### Option A: Corpus Validation
Test diachronic workflow on all 51 corpus graphs
- Validates layout persistence
- Stress tests area containment
- Identifies edge cases

### Option B: Transformation UI
Visual rule application in Ergasterion mode
- Drag-and-drop transformation selection
- Preview transformation results
- Undo/redo with provenance tracking

### Option C: Agon Mode
Endoporeutic Game implementation
- Proposer vs Skeptic interface
- Turn-based transformation application
- Automated soundness checking

### Decision Point
User will choose next focus after Phase 2 completes

---

## 📝 Active Task List

### This Week (2025-10-14 to 2025-10-18)

| Priority | Task | Owner | Status |
|----------|------|-------|--------|
| HIGH | Create WHAT_WORKS_NOW.md template | AI | TODO |
| HIGH | Implement update_session_state.py | AI | TODO |
| HIGH | Enhance git pre-commit hook | AI | TODO |
| MED | Implement generate_working_code_index.py | AI | TODO |
| MED | Implement detect_code_archaeology.py | AI | TODO |

### Next Week (2025-10-21 to 2025-10-25)
- [ ] Auto-regenerate API docs on commit
- [ ] Integrate coverage.py measurement
- [ ] Validate architecture documents

### Blocked Tasks
None currently

---

## 🗑️ Tasks Removed (No Longer Needed)

### Recently Removed
- ~~Manual position override system~~ (2025-10-13)
  - **Reason**: Replaced by diachronic delta workflow
  - **Impact**: Cleaner architecture, less code to maintain

- ~~Separate layout delta storage format~~ (2025-10-13)
  - **Reason**: Integrated directly into JSON serialization
  - **Impact**: Simpler persistence model

- ~~Legacy layout engine cleanup~~ (2025-10-13)
  - **Reason**: Superseded by unified_d3_engine
  - **Impact**: Clear which engine is production

### Why Track Removed Tasks
Prevents re-adding tasks that were already deemed unnecessary. Documents architectural decisions.

---

## 🎯 Alignment with Product Vision

All current work aligns with **PRODUCT_VISION.md**:

### ✅ In Scope
- **Coherence framework** → Maintains mathematical rigor and code quality
- **Session state** → Enables effective AI-assisted development
- **Documentation sync** → Supports researchers using the system

### ❌ Out of Scope
Not adding features unrelated to EG system or researcher needs.

---

## 📊 Progress Metrics

### Phase 0 (Foundation)
- **Status**: ✅ Complete
- **Completion**: 2025-10-13
- **Duration**: 1 day

### Phase 1 (Session State)
- **Status**: 🔄 In Progress (20% complete)
- **Started**: 2025-10-13
- **Expected Complete**: 2025-10-18
- **Blockers**: None

### Overall Coherence Framework
- **Status**: 20% complete
- **Risk Level**: Low
- **Confidence**: High

---

## 🔄 Plan Review Process

### Weekly Review (Every Monday)
- Update task statuses
- Remove completed tasks
- Add new tasks as they become clear
- Adjust priorities based on learnings

### Biweekly Validation (Every other Friday)
- Check alignment with PRODUCT_VISION.md
- Verify removed tasks still shouldn't be re-added
- Confirm next phase is still appropriate

### Monthly Strategic Review (Last day of month)
- Assess overall progress
- Validate product vision remains current
- Consider architectural changes
- Plan next month's focus

### Next Reviews
- **Weekly**: 2025-10-20 (Monday)
- **Biweekly**: 2025-10-25 (Friday)
- **Monthly**: 2025-10-31 (Thursday)

---

## 📌 How to Use This Document

### For AI Assistants
1. **Read at session start** - Understand current focus
2. **Check before proposing work** - Ensure alignment with plan
3. **Update when completing tasks** - Keep status current
4. **Flag tasks for removal** - Note if something no longer makes sense

### For Developers
1. **Consult before starting new work** - Avoid conflicts
2. **Update when priorities change** - Keep plan realistic
3. **Review periodically** - Ensure plan reflects reality
4. **Challenge if misaligned** - Plan serves the work, not vice versa

### For Plan Reviews
1. **What completed?** - Move to history
2. **What blocked?** - Identify impediments
3. **What changed?** - Update priorities
4. **What's next?** - Add emerging tasks
5. **What's obsolete?** - Remove unnecessary tasks

---

*This plan reflects current reality and evolves as we learn. It's a living document, not a fixed contract.*

**Last Updated**: 2025-10-13  
**Next Update**: 2025-10-20 (or when significant changes occur)
