# Development Practices to Prevent Code Bloat

## 1. Continuous Code Health Monitoring

### Coverage-Driven Development
```bash
# Run before each commit
coverage run --source=. src/arisbe_unified_app.py
coverage report --fail-under=80  # Fail if coverage drops below 80%
```

### Dead Code Detection
```bash
# Weekly dead code scan
vulture tools/ --min-confidence 80 > dead_code_report.txt
```

### Automated Checks (CI/CD Integration)
```yaml
# .github/workflows/code-health.yml
- name: Check code coverage
  run: |
    coverage run --source=. tests/
    coverage report --fail-under=75
    
- name: Find dead code
  run: vulture . --min-confidence 80
```

## 2. File Size Limits

### Enforce Maximum File Size
- **Hard limit:** 1,000 lines per file
- **Soft limit:** 500 lines per file
- **Action:** Automatic refactoring trigger at 800 lines

### Modularization Strategy
```python
# Instead of one 6,000-line file:
from .egdf_loader import EGDFLoader
from .graphics_manager import GraphicsManager  
from .interaction_handler import InteractionHandler

class DrawingEditor:
    def __init__(self):
        self.loader = EGDFLoader()
        self.graphics = GraphicsManager()
        self.interaction = InteractionHandler()
```

## 3. Feature Flag Architecture

### Runtime Configuration
```python
class FeatureFlags:
    """Centralized feature control"""
    DEBUG_GRAPHICS = os.environ.get('DEBUG_GRAPHICS', 'false').lower() == 'true'
    EXPERIMENTAL_LIGATURES = os.environ.get('EXPERIMENTAL_LIGATURES', 'false').lower() == 'true'
    LEGACY_IMPORT = os.environ.get('LEGACY_IMPORT', 'false').lower() == 'true'

# Usage
if FeatureFlags.DEBUG_GRAPHICS:
    self.show_debug_overlay()
```

### Gradual Feature Removal
```python
# Phase 1: Disable by default
LEGACY_FEATURE = False

# Phase 2: Remove after 2 releases
# Delete the code entirely
```

## 4. Documentation-Driven Cleanup

### Function Purpose Documentation
```python
def complex_function():
    """
    Purpose: [If you can't fill this in clearly, delete the function]
    Used by: [List calling functions - if none, delete]
    Last modified: [Date - if >6 months ago, review for deletion]
    """
```

### Decision Log
```markdown
# decisions.md
## 2025-01-03: Removed legacy CGIF parser
- **Why:** Not used for 6 months, coverage showed 0% execution
- **Impact:** None - replaced by new parser
- **Rollback:** Git commit abc123 if needed
```

## 5. Refactoring Triggers

### Automatic Triggers
- File exceeds 800 lines → Split into modules
- Function exceeds 50 lines → Extract helper functions  
- Coverage drops below 75% → Remove dead code
- Complexity score > 10 → Simplify

### Regular Reviews
- **Weekly:** Run vulture scan
- **Monthly:** Coverage analysis and dead code removal
- **Quarterly:** Architecture review and modularization

## 6. Testing Strategy

### Test-Driven Deletion
```python
# Before deleting code, ensure no tests break
pytest tests/ --cov=tools/drawing_editor.py
# If coverage shows function is untested AND unused → safe to delete
```

### Integration Tests for Core Paths
```python
def test_egdf_loading_complete_workflow():
    """Test the 21% of code that actually matters"""
    editor = DrawingEditor()
    editor.load_payload(sample_egdf)
    assert editor.model.vertices
    assert editor.model.predicates  
    assert positions_preserved()
```

## 7. Metrics Dashboard

### Key Metrics to Track
- Lines of code per module
- Test coverage percentage
- Dead code percentage (via vulture)
- Function complexity scores
- Import dependency graph

### Alerts
- File size > 1000 lines
- Coverage < 75%
- Dead code > 20%
- Circular dependencies detected

This systematic approach prevents the accumulation of technical debt and keeps codebases maintainable.
